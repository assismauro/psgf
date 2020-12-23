import io
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.geoa import ModelView
from flask_admin.contrib.fileadmin import FileAdmin
from flask import send_file
from flask_mail import Mail
from flask_user import UserManager, UserMixin, SQLAlchemyAdapter, login_required, current_user
import data_model as dm
from markupsafe import Markup
from werkzeug.datastructures import FileStorage
from wtforms import ValidationError, fields
from wtforms.validators import required
from wtforms.widgets import HTMLString, html_params, FileInput
from gettext import gettext
from waitress import serve

try:
    from wtforms.fields.core import _unset_value as unset_value
except ImportError:
    from wtforms.utils import unset_value

app = dm.app
admin = Admin(app, template_mode='bootstrap3',  index_view=AdminIndexView(
        name='Home',
        url=r'/'))

db_adapter = SQLAlchemyAdapter(dm.db, dm.User)
user_manager = UserManager(db_adapter, app)
mail = Mail(app)

def isAcessible(current_user, only_admin = False):
    if (current_user is None) or (not current_user.is_active):
        return False
    else:
        if only_admin:
            if current_user.profile is None:
                return False
            else:
                return current_user.profile.is_administrator
        else:
            return True

#region Models definition
class psgfAdmView(ModelView):
    can_create = True
    can_delete = True
    can_edit = True
    can_export = True
#    create_modal = True
#    edit_modal = True

    def is_accessible(self):
        return isAcessible(current_user, True)

 #   def inaccessible_callback(self, name, **kwargs):

class ForestView(psgfAdmView):
        inline_models = [dm.Rodal]
        column_editable_list = ['forest_nom', 'formacio_i_habitat', 'codi', 'superficie_ha']

class TipusDeTramitsView(psgfAdmView):
        inline_models = [dm.Tramit]


class BlobUploadField(fields.StringField):

    widget = FileInput()

    def __init__(self, label=None, allowed_extensions=None, size_field=None, filename_field=None, mimetype_field=None, **kwargs):

        self.allowed_extensions = allowed_extensions
        self.size_field = size_field
        self.filename_field = filename_field
        self.mimetype_field = mimetype_field
        validators = [required()]

        super(BlobUploadField, self).__init__(label, validators, **kwargs)

    def is_file_allowed(self, filename):
        if not self.allowed_extensions:
            return True

        return ('.' in filename and
                filename.rsplit('.', 1)[1].lower() in
                map(lambda x: x.lower(), self.allowed_extensions))

    def _is_uploaded_file(self, data):
        return (data and isinstance(data, FileStorage) and data.filename)

    def pre_validate(self, form):
        super(BlobUploadField, self).pre_validate(form)
        if self._is_uploaded_file(self.data) and not self.is_file_allowed(self.data.filename):
            raise ValidationError(gettext('Invalid file extension'))

    def process_formdata(self, valuelist):
        if valuelist:
            data = valuelist[0]
            self.data = data

    def populate_obj(self, obj, name):
        if self._is_uploaded_file(self.data):
            _blob = self.data.read()
            setattr(obj, name, _blob)
            if self.size_field:
                setattr(obj, self.size_field, len(_blob))
            if self.filename_field:
                setattr(obj, self.filename_field, self.data.filename)
            if self.mimetype_field:
                setattr(obj, self.mimetype_field, self.data.content_type)

class ProjectUploadView(ModelView):

    column_list = ('name', 'size', 'filename', 'mimetype', 'download')
    form_columns = ('name', 'blob')

    form_extra_fields = {'blob': BlobUploadField(
        label='File',
        allowed_extensions=['pdf'],
        size_field='size',
        filename_field='filename',
        mimetype_field='mimetype'
    )}

    def _download_formatter(self, context, model, name):
        return Markup(
            "<a href='{url}' target='_blank'>Download</a>".format(url=self.get_url('download_blob', id=model.id)))

    column_formatters = {
        'download': _download_formatter,
    }

    def is_accessible(self):
        return isAcessible(current_user, True) or \
               ((not (current_user is None) and
                current_user.profile.can_upload))
#endregion

#region addView
admin.add_view(psgfAdmView(dm.Profile, dm.db.session, category='Administrative'))
admin.add_view(psgfAdmView(dm.User, dm.db.session, category='Administrative'))
admin.add_view(psgfAdmView(dm.Inventari, dm.db.session, category='Administrative'))
admin.add_view(psgfAdmView(dm.PlaordForestal, dm.db.session, category='Administrative'))
admin.add_view(psgfAdmView(dm.PlaordProp, dm.db.session, category='Administrative'))
admin.add_view(psgfAdmView(dm.TipusQualificacioEspecial, dm.db.session, category='Administrative'))
admin.add_view(psgfAdmView(dm.DadesPropietat, dm.db.session, category='Administrative'))
admin.add_view(psgfAdmView(dm.TipusAfectacioLegal, dm.db.session, category='Administrative'))
admin.add_view(psgfAdmView(dm.Tipusdepla, dm.db.session, category='Administrative'))
admin.add_view(psgfAdmView(dm.ActuacionsDescripcio, dm.db.session, category='Administrative'))
admin.add_view(psgfAdmView(dm.PropietariDades, dm.db.session, category='Administrative'))
admin.add_view(psgfAdmView(dm.IngresActuacions, dm.db.session, category='Administrative'))
admin.add_view(psgfAdmView(dm.PersonaDeContacte, dm.db.session, category='Administrative'))

admin.add_view(TipusDeTramitsView(dm.TipusDeTramit, dm.db.session, category='Administrative'))
admin.add_view(ForestView(dm.Forest, dm.db.session, category='Administrative'))
admin.add_view(psgfAdmView(dm.Rodal, dm.db.session, category='Administrative'))
admin.add_view(ProjectUploadView(dm.ProjectePdf, dm.db.session, category='Administrative'))
admin.add_view(psgfAdmView(dm.ProjecteMap, dm.db.session, category='Administrative'))
#endregion

@app.route("/download/<int:id>", methods=['GET'])
def download_blob(id):
    _image = dm.ProjectePdf.query.get_or_404(id)
    return send_file(
        io.BytesIO(_image.blob),
        attachment_filename=_image.filename,
        mimetype=_image.mimetype
    )


if __name__ == '__main__':
#    app.run(debug=True)
    serve(app, host='0.0.0.0',port=80)