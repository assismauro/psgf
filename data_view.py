from gettext import gettext
from flask_admin.contrib.geoa import ModelView
from flask_user import current_user
from markupsafe import Markup
from werkzeug.datastructures import FileStorage
from wtforms import ValidationError, fields, StringField, PasswordField
from wtforms.validators import required
from wtforms.widgets import FileInput
from flask_babel import lazy_gettext
import supports.categories as categories
import supports.app_object as app_object_support
import supports.dbquery as dbquery
import data_model
import supports.maps_form as maps_form
import supports.actuacions_form as actuacions_form


# region Models definition
class psgfPlaDataView(ModelView):

    def is_accessible(self):
        self.can_create = dbquery.canEditProjectData(current_user)
        self.can_delete = dbquery.canEditProjectData(current_user)
        self.can_edit = dbquery.canEditProjectData(current_user)
        self.can_export = True
        return current_user is not None and current_user.is_authenticated # should be logged, at least

class psgfAdmView(ModelView):

    def is_accessible(self):
        return dbquery.isAdministrator(current_user)


class userView(psgfAdmView):
    column_labels = dict(username=lazy_gettext('username'),
                         password=lazy_gettext('password'),
                         active=lazy_gettext('active'),
                         email=lazy_gettext('email'),
                         confirmed_at=lazy_gettext('confirmed_at'),
                         profile=lazy_gettext('profile'), )
    password=PasswordField('Password', validators=[required()])
    create_modal = True


class profileView(psgfAdmView):
    column_labels = dict(profilename=lazy_gettext('profilename'),
                         is_administrator=lazy_gettext('is_administrator'),
                         can_upload=lazy_gettext('can_upload'))


class ForestView(psgfPlaDataView):
    column_editable_list = ['forest_nom', 'formacio_i_habitat', 'codi']


class TipusDeTramitsView(psgfAdmView):
    pass
    # inline_models = [data_model.Tramit]


class PlaView(psgfPlaDataView):
    column_list = ['nom', 'numero_expediente', 'any_del_pla', 'vigencia', 'municipi']


class RodalView(psgfPlaDataView):
    column_list = ['pla', 'num_rodal', 'area', 'geometry']
    form_columns = ['pla_id', 'num_rodal', 'area', 'formacion_forestal', 'especie', 'objectiu_general',
                    'objectiu_preferent', 'descriptio_objectiu', 'descriptio_model_gestio',
                    'descriptio_itinerari_silvicola', 'forest_id', 'orgest',
                    'descripcio_model_gestio', 'vulnerabilitat', 'qualitat_estacio',
                    'superficie_ordenada', 'superficie_forestal', 'superficie_arbrada', 'superficie_especial',
                    'geometry']

class ResumInventariFustaView(psgfPlaDataView):
    column_list = ['rodal', 'tipus_inventari', 'forma_principal', 'any', 'n_peus_ha', 'vol',
                   'ab', 'composicio_especifica', 'distribucio_espacial']


class InventariCdGrup(psgfPlaDataView):
    can_delete = False
    can_create = False
    can_edit = False
    column_list = ['id', 'pla', 'num_rodal', 'c_d', 'npeus', 'a_b']


class ActuacionsDelPlaView(psgfPlaDataView):
    column_list = ['rodal', 'actuacio', 'any_programat', 'area_afectada']


class PlaForestView(psgfPlaDataView):
    column_list = ['pla', 'forest']


class BlobUploadField(fields.StringField):
    widget = FileInput()

    def __init__(self, label=None, allowed_extensions=None, size_field=None, filename_field=None, mimetype_field=None,
                 nullable=False,
                 **kwargs):
        self.allowed_extensions = allowed_extensions
        self.size_field = size_field
        self.filename_field = filename_field
        self.mimetype_field = mimetype_field
        validators = [required()] if not nullable else []

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
    '''
    column_list = ('pdf_fname', 'pdf_blob', 'camins_fname', 'camins_blob', 'canvi_us_fname', 'canvi_us_blob',
                   'infraestructures_incedis_fname', 'infraestructures_incedis_blob',
                   'unitats_actuacio_fname', 'unitats_actuacio_blob', 'usos_vege_fname', 'usos_vege_blob')
    form_columns = ('pla_id', 'pdf_fname', 'pdf_blob', 'camins_blob', 'canvi_us_blob', 'infraestructures_incedis_blob',
                    'unitats_actuacio_blob', 'usos_vege_blob', 'informacio_addicional_blob')
    '''
    column_list = ('name', 'numero_expediente', 'any_del_pla'
                   # , 'download'
                   )
    form_columns = ('name', 'numero_expediente', 'any_del_pla',
                    'pdf_blob', 'camins_blob', 'canvi_us_blob', 'infraestructures_incedis_blob',
                    'unitats_actuacio_blob', 'usos_vege_blob', 'informacio_addicional_blob')

    create_modal = True

    column_labels = dict(name='name', last_name=' Name')
    form_extra_fields = {
        'pdf_blob': BlobUploadField(
            label='PDF',
            allowed_extensions=['pdf'],
            filename_field='pdf_fname'),

        'camins_blob': BlobUploadField(
            label='Camins',
            allowed_extensions=['zip'],
            filename_field='camins_fname',
            nullable=True),

        'canvi_us_blob': BlobUploadField(
            label='Canvi Us',
            allowed_extensions=['zip'],
            filename_field='canvi_us_fname',
            nullable=True),

        'infraestructures_incedis_blob': BlobUploadField(
            label='Infraestricures Incendis',
            allowed_extensions=['zip'],
            filename_field='infraestructures_incedis_fname',
            nullable=True),

        'unitats_actuacio_blob': BlobUploadField(
            label='Rodals',
            allowed_extensions=['zip'],
            filename_field='unitats_actuacio_fname'),

        'usos_vege_blob': BlobUploadField(
            label='Usos Vege',
            allowed_extensions=['zip'],
            filename_field='usos_vege_fname',
            nullable=True),

        'informacio_addicional_blob': BlobUploadField(
            label='Informació Addicional',
            allowed_extensions=['zip'],
            filename_field='informacio_addicional_fname',
            nullable=True)
    }

    def _download_formatter(self, context, model, name):
        return Markup(
            "<a href='{url}' target='_blank'>Download</a>".format(url=self.get_url('download_blob', id=model.id)))

    column_formatters = {
        'download': _download_formatter,
    }

    def is_accessible(self):
        try:
            return dbquery.isAdministrator(current_user) or \
                   ((not (current_user is None) and
                     current_user.profile.can_upload))
        except:
            return False


def addViews(admin):
    admin.add_view(ProjectUploadView(data_model.ProjecteZip, data_model.db.session,
                                     name=data_model.ProjecteZip.label,
                                     category=categories.Categories.category['Upload']))

    # Pla Data
    admin.add_view(PlaView(data_model.Pla, data_model.db.session, category=categories.Categories.category['Pla Data']))
    admin.add_view(
        ForestView(data_model.Forest, data_model.db.session, category=categories.Categories.category['Pla Data']))
    admin.add_view(
        RodalView(data_model.Rodal, data_model.db.session, category=categories.Categories.category['Pla Data']))
    admin.add_view(psgfPlaDataView(data_model.XarxaNovaConstruccio, data_model.db.session,
                               category=categories.Categories.category['Pla Data']))
    admin.add_view(psgfPlaDataView(data_model.XarxaViariaExistent, data_model.db.session,
                               category=categories.Categories.category['Pla Data']))
    admin.add_view(psgfPlaDataView(data_model.LineasDefensaPuntsAigua, data_model.db.session,
                               category=categories.Categories.category['Pla Data']))
    admin.add_view(psgfPlaDataView(data_model.CanviUs, data_model.db.session,
                               category=categories.Categories.category['Pla Data']))
    admin.add_view(psgfPlaDataView(data_model.PropietariDade, data_model.db.session,
                               category=categories.Categories.category['Pla Data']))
    admin.add_view(psgfPlaDataView(data_model.ActuacionsDelPla, data_model.db.session,
                                        category=categories.Categories.category['Pla Data']))

    # Queries
    # admin.add_view(InventariCdGrup(data_model.InventariCdGrup, data_model.db.session,
    #                                         category=categories.Categories.category['Queries']))
    app_object_support.admin.add_view(
        maps_form.mapView(name=" Maps", endpoint='maps', category=categories.Categories.category['Queries']))
    app_object_support.admin.add_view(actuacions_form.actuacionsView(name=" Actuacions", endpoint='actuacions',
                                                                     category=categories.Categories.category[
                                                                         'Queries']))

    # Administration
    admin.add_view(psgfAdmView(data_model.Consultes, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(
        profileView(data_model.Profile, data_model.db.session,
                    category=categories.Categories.category['Administration'],
                    name=lazy_gettext('Profile')))
    admin.add_view(
        userView(data_model.User, data_model.db.session, category=categories.Categories.category['Administration'],
                 name=lazy_gettext('User')))
    admin.add_view(psgfAdmView(data_model.LlistatActuacion, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(TipusDeTramitsView(data_model.TipusDeTramit, data_model.db.session,
                                      category=categories.Categories.category['Administration']))
    admin.add_view(psgfAdmView(data_model.Especies, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(psgfAdmView(data_model.EspeciePrincipal, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(psgfAdmView(data_model.EspecieFormacioArborea, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(psgfAdmView(data_model.Orgest, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(psgfAdmView(data_model.TipologiaFormacioForestal, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(psgfAdmView(data_model.ObjectiuGeneral, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(psgfAdmView(data_model.ObjectiuPreferent, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(psgfAdmView(data_model.Unitat, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(psgfAdmView(data_model.Vulnerabilitat, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(psgfAdmView(data_model.TipusInventari, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(psgfAdmView(data_model.TipusEstruturaMassa, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(psgfAdmView(data_model.QualitatEstacio, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(psgfAdmView(data_model.ActuacionsPTGMF, data_model.db.session,
                               category=categories.Categories.category['Administration']))
    admin.add_view(psgfAdmView(data_model.LogImport, data_model.db.session,
                               category=categories.Categories.category['Administration']))


    # Inventari
    admin.add_sub_category(name=categories.Categories.category['Inventari'],
                           parent_name=categories.Categories.category['Pla Data'])
    admin.add_view(
        psgfPlaDataView(data_model.Inventari, data_model.db.session, category=categories.Categories.category['Inventari']))
    admin.add_view(psgfPlaDataView(data_model.ResultatsInventariFusta, data_model.db.session,
                               category=categories.Categories.category['Inventari']))
    admin.add_view(ResumInventariFustaView(data_model.ResumInventariFusta, data_model.db.session,
                               category=categories.Categories.category['Inventari']))
    admin.add_view(
        psgfPlaDataView(data_model.InventariCd, data_model.db.session,
                    category=categories.Categories.category['Inventari']))
