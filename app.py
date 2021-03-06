import io
from gettext import gettext
from flask import send_file, request
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.geoa import ModelView
from flask_mail import Mail
from flask_user import UserManager, SQLAlchemyAdapter, current_user
from markupsafe import Markup
from waitress import serve
from werkzeug.datastructures import FileStorage
from wtforms import ValidationError, fields
from wtforms.validators import required
from wtforms.widgets import FileInput
from flask_babel import Babel, lazy_gettext

import data_model as dm

try:
    from wtforms.fields.core import _unset_value as unset_value
except ImportError:
    from wtforms.utils import unset_value

app = dm.app
admin = Admin(app, template_mode='bootstrap3', index_view=AdminIndexView(
    name='psgf',
    url=r'/'))
db_adapter = SQLAlchemyAdapter(dm.db, dm.User)
user_manager = UserManager(db_adapter, app)
mail = Mail(app)
babel = Babel(app)


@babel.localeselector
def getLocale():
    if request.args.get('lang'):
        dm.db.session['lang'] = request.args.get('lang')
        return request.args.get('lang')
    else:
        return request.accept_languages.best_match(['en_US', 'es', 'ca'])


def isAcessible(current_user, only_admin=False):
    try:
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
    except:
        return False


# region Models definition
class psgfAdmView(ModelView):
    can_create = True
    can_delete = True
    can_edit = True
    can_export = True

    def is_accessible(self):
        return isAcessible(current_user, True)


class profileView(psgfAdmView):
    column_labels = dict(profilename=lazy_gettext('profilename'),
                         is_administrator=lazy_gettext('is_administrator'),
                         can_upload=lazy_gettext('can_upload'))

class userView(psgfAdmView):
    column_labels = dict(username=lazy_gettext('username'),
                         password=lazy_gettext('password'),
                         active=lazy_gettext('active'),
                         email=lazy_gettext('email'),
                         confirmed_at=lazy_gettext('confirmed_at'),
                         profile=lazy_gettext('profile'),)

class ForestView(psgfAdmView):
    inline_models = [dm.Rodal]
    column_editable_list = ['forest_nom', 'formacio_i_habitat', 'codi', 'superficie_ha']


class TipusDeTramitsView(psgfAdmView):
    inline_models = [dm.Tramit]


class BlobUploadField(fields.StringField):
    widget = FileInput()

    def __init__(self, label=None, allowed_extensions=None, size_field=None, filename_field=None, mimetype_field=None,
                 **kwargs):

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
        try:
            return isAcessible(current_user, True) or \
                   ((not (current_user is None) and
                     current_user.profile.can_upload))
        except:
            return False


# endregion

# region addView
projectCategory = lazy_gettext('Project')
administrationCategory = lazy_gettext('Administration')
admin.add_view(ProjectUploadView(dm.ProjectePdf, dm.db.session,
                                 name=dm.ProjectePdf.label, category=projectCategory))
admin.add_view(psgfAdmView(dm.ProjecteMap, dm.db.session, category=projectCategory))
admin.add_view(profileView(dm.Profile, dm.db.session, category=administrationCategory, name=lazy_gettext('Profile')))
admin.add_view(userView(dm.User, dm.db.session, category=administrationCategory, name=lazy_gettext('User')))
admin.add_view(psgfAdmView(dm.Inventari, dm.db.session, category=administrationCategory))
admin.add_view(psgfAdmView(dm.PlaordForestal, dm.db.session, category=administrationCategory))
admin.add_view(psgfAdmView(dm.PlaordProp, dm.db.session, category=administrationCategory))
admin.add_view(psgfAdmView(dm.TipusQualificacioEspecial, dm.db.session, category=administrationCategory))
admin.add_view(psgfAdmView(dm.DadesPropietat, dm.db.session, category=administrationCategory))
admin.add_view(psgfAdmView(dm.TipusAfectacioLegal, dm.db.session, category=administrationCategory))
admin.add_view(psgfAdmView(dm.Tipusdepla, dm.db.session, category=administrationCategory))
admin.add_view(psgfAdmView(dm.ActuacionsDescripcio, dm.db.session, category=administrationCategory))
admin.add_view(psgfAdmView(dm.PropietariDades, dm.db.session, name=dm.PropietariDades.label, category=administrationCategory))
admin.add_view(psgfAdmView(dm.IngresActuacions, dm.db.session, category=administrationCategory))
admin.add_view(psgfAdmView(dm.PersonaDeContacte, dm.db.session, category=administrationCategory))
admin.add_view(TipusDeTramitsView(dm.TipusDeTramit, dm.db.session, category=administrationCategory))
admin.add_view(ForestView(dm.Forest, dm.db.session, category=administrationCategory))
admin.add_view(psgfAdmView(dm.Rodal, dm.db.session, category=administrationCategory))
# endregion

@app.route("/download/<int:id>", methods=['GET'])
def download_blob(id):
    _image = dm.ProjectePdf.query.get_or_404(id)
    return send_file(
        io.BytesIO(_image.blob),
        attachment_filename=_image.filename,
        mimetype=_image.mimetype
    )


@babel.localeselector
def localeselector():
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys())


if __name__ == '__main__':
    #    app.run(debug=True)
    serve(app, host='0.0.0.0', port=80)
