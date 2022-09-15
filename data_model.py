# coding: utf-8
from flask_babel import Babel
from flask_user import UserMixin
from datetime import datetime
from sqlalchemy import and_, not_
from geoalchemy2.types import Geometry
from flask_user import current_user
from sqlalchemy import Boolean, CHAR, CheckConstraint, Column, DateTime, ForeignKey, \
    Integer, String, Table, Float, Text, LargeBinary
from sqlalchemy.orm import relationship
from supports import import_data as dms
import supports.app_object as app_object_support
import supports.dbquery as dbquery

db = app_object_support.db

session = dbquery.getSession()

def getUserId():
    return current_user.id

class Profile(db.Model):
    __tablename__ = 'profile'

    id = Column(Integer, primary_key=True)
    profilename = Column(String(255), nullable=False, unique=True)
    is_administrator = Column(Boolean, nullable=False)
    can_upload = Column(Boolean, nullable=False)

    def __repr__(self):
        return self.profilename


def getUploadProfileId():
    return session.query(Profile.id).filter(and_(not_(Profile.is_administrator), Profile.can_upload)).first()[0]


class User(db.Model, UserMixin):
    __tablename__ = u'user'

    id = Column(Integer, nullable=False, primary_key=True)
    username = Column(String(20), nullable=False, unique=True)
    password = Column(String(255), nullable=False, server_default='')
    active = Column(Boolean, nullable=False, default=1)
    email = Column(String(255), nullable=False, unique=True)
    confirmed_at = Column(DateTime())
    profile_id = Column(Integer(), ForeignKey('profile.id'), default=getUploadProfileId)

    profile = relationship('Profile')

    def __unicode__(self):
        return u"name : {name}; filename : {filename})".format(name=self.name, filename=self.filename)

    def __repr__(self):
        return self.username

class AltresActuacionsDelPla(db.Model):
    __tablename__ = 'altres_actuacions_del_pla'

    id = Column(Integer, primary_key=True)
    nom = Column(String(255))

    def __repr__(self):
        return self.nom

class DadesPropietat(db.Model):
    __tablename__ = 'dades_propietat'

    id = Column(Integer, primary_key=True)
    nom = Column(String(255))
    cif = Column(Integer)
    adreca = Column(String)
    contacte = Column(String(255))

    def __repr__(self):
        return self.nom

class RelForestHabitat(db.Model):
    __tablename__ = 'rel_forest_habitat'

    id = Column(Integer, primary_key=True)
    forest_id = Column(ForeignKey('forest.id'))
    habitati_formacio_id = Column(ForeignKey('formacio_habitat.id'))
    superficie_ha = Column(Integer)
    percent = Column(Integer)

    formacio_habitat = relationship('FormacioHabitat')


class FormacioHabitat(db.Model):
    __tablename__ = 'formacio_habitat'

    id = Column(Integer, primary_key=True)
    nom = Column(String(255))

    def __repr__(self):
        return self.nom

geometry_columns = Table(
    'geometry_columns', app_object_support.Base.metadata,
    Column('f_table_catalog', String(256)),
    Column('f_table_schema', String),
    Column('f_table_name', String),
    Column('f_geometry_column', String),
    Column('coord_dimension', Integer),
    Column('srid', Integer),
    Column('type', String(30))
)


class LlistatActuacion(db.Model):
    __tablename__ = 'llistat_actuacions'

    id = Column(Integer, primary_key=True)
    nom = Column(String(255))
    tipus_actuacio = Column(ForeignKey('tipus_actuacio.id'), nullable=False)
    codi = Column(String(255))
    actuacions_ptgmf_id = Column(ForeignKey('actuacions_ptgmf.id'))

    tipus = relationship('TipusActuacio')
    actuacions_ptgmf = relationship('ActuacionsPTGMF')

    def __repr__(self):
        return self.nom

class PersonaDeContacte(db.Model):
    __tablename__ = 'persona_de_contacte'

    id = Column(Integer, nullable=False, primary_key=True)
    dni = Column(String(255))
    nom = Column(String(255))
    primer_cognom = Column(String(255))
    segon_cognom = Column(String(255))
    adreca = Column(String)
    municipi = Column(String(255))
    cp = Column(Integer)
    email = Column(String(255))
    telef1 = Column(String(255))
    telef2 = Column(String(255))

    def __repr__(self):
        return self.nom

class PropietariDade(db.Model):
    __tablename__ = 'propietari_dades'

    id = Column(Integer, nullable=False, primary_key=True)
    pla_id = Column(Integer, ForeignKey('pla.id', ondelete='CASCADE'))
    tipus = Column(String(255))
    d_ni = Column(String(255))
    nom = Column(String(255))
    primer_cognom = Column(String(255))
    segon_cognom = Column(String(255))
    adreca = Column(String)
    telef_1 = Column(String(255))
    telef_2 = Column(String(255))
    email = Column(String(255))
    municipi = Column(String(255))
    cp = Column(Integer)

    pla = relationship('Pla')

    def __repr__(self):
        return self.nom

class SpatialRefSy(db.Model):
    __tablename__ = 'spatial_ref_sys'
    __table_args__ = (
        CheckConstraint('(srid > 0) AND (srid <= 998999)'),
    )

    srid = Column(Integer, primary_key=True)
    auth_name = Column(String(256))
    auth_srid = Column(Integer)
    srtext = Column(String(2048))
    proj4text = Column(String(2048))


class TecnicRedactor(db.Model):
    __tablename__ = 'tecnic_redactor'

    id = Column(Integer, primary_key=True)
    nom = Column(String(255))
    titol = Column(String(255))
    email = Column(String(255))
    telef = Column(Integer)
    num_colegiat = Column(Integer)
    id_tecnic_redacto_tecnic__redacto = Column(CHAR(10))

    def __repr__(self):
        return self.nom

class TipusActuacio(db.Model):
    __tablename__ = 'tipus_actuacio'

    id = Column(Integer, primary_key=True)
    nom = Column(String(255))

    def __repr__(self):
        return self.nom


class TipusAfectacioLegal(db.Model):
    __tablename__ = 'tipus_afectacio_legal'

    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)
    nom_extens = Column(String(255))

    def __repr__(self):
        return self.nom


class TipusDeBestiar(db.Model):
    __tablename__ = 'tipus_de_bestiar'

    id = Column(Integer, primary_key=True)
    tipus = Column(String(255))

    def __repr__(self):
        return self.nom


class TipusDePla(db.Model):
    __tablename__ = 'tipus_de_pla'

    id = Column(Integer, primary_key=True)
    nome = Column(String(255))

    def __repr__(self):
        return self.nom


class TipusDeTramit(db.Model):
    __tablename__ = 'tipus_de_tramit'

    id = Column(String(255), primary_key=True)
    nom = Column(String)

    def __repr__(self):
        return self.nom


class TipusQualificacioEspecial(db.Model):
    __tablename__ = 'tipus_qualificacio_especial'

    id = Column(Integer, primary_key=True)
    inicials = Column(String(255))
    nom = Column(String(255))

    def __repr__(self):
        return self.nom

class AltresAfectacionsLegal(db.Model):
    __tablename__ = 'altres_afectacions_legals'

    id = Column(Integer, primary_key=True)
    tipus_id = Column(ForeignKey('tipus_afectacio_legal.id'), nullable=False)
    nom = Column(String(255))
    superficie_afectada = Column(Integer)
    forest_id = Column(ForeignKey('forest.id'))
    observacions = Column(String)

    forest = relationship('Forest')
    tipus = relationship('TipusAfectacioLegal')

    def __repr__(self):
        return self.nom

class Rodal(db.Model):
    __tablename__ = 'rodal'

    id = Column(Integer, primary_key=True)
    num_rodal = Column(String(255))
    formacion_forestal = Column(String(255))
    area = Column(Float)
    forestal = Column(Integer)
    especie = Column(String(255))
    arbrada = Column(Integer)
    estat_sanitari = Column(String(255))
    pla_id = Column(Integer, ForeignKey('pla.id', ondelete='CASCADE'))
    objectiu_general = Column(Text)
    objectiu_preferent = Column(Text)
    forest_id = Column(ForeignKey('forest.id'))
    orgest = Column(String(255))
    descripcio_model_gestio = Column(String)
    superficie_ordenada = Column(Float)
    superficie_forestal = Column(Float)
    superficie_arbrada = Column(Float)
    superficie_especial = Column(Float)
    codi_form_forestal = Column(String(255))
    descriptio_objectiu = Column(Text)
    descriptio_model_gestio = Column(Text)
    descriptio_itinerari_silvicola = Column(Text)
    qualitat_estacio_id = Column(Integer, ForeignKey('qualitat_estacio.id'))
    vulnerabilitat_id = Column(Integer, ForeignKey('vulnerabilitat.id'))
    geometry = Column(Geometry("MULTIPOLYGON", srid=4326))

    pla = relationship('Pla')
    forest = relationship('Forest')
    qualitat_estacio = relationship('QualitatEstacio')
    vulnerabilitat = relationship('Vulnerabilitat')

    def __repr__(self):
        return f"{self.pla}/{self.num_rodal}"

class InventariCd(db.Model):
    __tablename__ = 'inventari_cd'

    id = Column(Integer, primary_key=True)
    rodal_id = Column(Integer, ForeignKey('rodal.id', ondelete='CASCADE'))
    especies_id = Column(ForeignKey('especies.id'))
    specie_o_total = Column(Integer)
    c_d = Column(Float)
    npeus = Column(Float)
    a_b = Column(Float)
    especies = relationship('Especies')
    rodal = relationship('Rodal')

class Pla(db.Model):
    __tablename__ = 'pla'

    id = Column(Integer, primary_key=True)
    nom = Column(String(255))
    tipus_de_pla = Column(String(255))
    numero_expediente = Column(String(255))
    any_del_pla = Column(Integer)
    vigencia = Column(DateTime)
    propietari = Column(String(255))
    municipi = Column(String(255))
    comarca = Column(String(255))
    persona_contacte__dn_i = Column(Integer)
    superficie_total = Column(Float)
    superficie_ordenada = Column(Float)
    superficie_no_ordenada = Column(Float)
    superficie_forestal = Column(Float)
    superficie_no_forestal = Column(Float)
    superficie_arbrada = Column(Float)
    superficie_no_arbrada = Column(Float)
    dens_camins_principals = Column(Float)
    dens_camins_primaris = Column(Float)
    dens_camins_secundaris = Column(Float)
    dens_camins_desembosc = Column(Float)
    dens_total_camins = Column(Float)
    long_camins_principals = Column(Float)
    long_camins_primaris = Column(Float)
    long_camins_secundaris = Column(Float)
    long_camins_desembosc = Column(Float)
    long_total_camins = Column(Float)
    info_complement_camins_existents = Column(String)
    info_complement_camins_nous = Column(String)
    info_complement_r_om_p__pastures = Column(String)
    info_complement_r_om_p__puntsaigua = Column(String)
    afectacio_e_np_e = Column(Boolean)
    afectacio_p_ei_n_p_e = Column(Boolean)
    afect_p_ei_n = Column(Boolean)
    afect_l_u = Column(Boolean)
    afect_u_p = Column(Boolean)
    afect_z_au = Column(Boolean)
    afect_lic = Column(Boolean)
    afect_z_ep_a = Column(Boolean)
    p_pp = Column(Boolean)
    r_nc = Column(Boolean)
    p_rea = Column(Boolean)
    tecnic_redactor__id = Column(ForeignKey('tecnic_redactor.id'))
    tecnic_redactor_ = relationship('TecnicRedactor')
    __table_args__ = (app_object_support.db.UniqueConstraint('nom', 'vigencia'),)

    inline_models = (Rodal,)

    def __repr__(self):
        return self.nom

class Forest(db.Model):
    __tablename__ = 'forest'

    id = Column(Integer, primary_key=True)
    pla_id = Column(Integer, ForeignKey('pla.id', ondelete='CASCADE'))
    forest_nom = Column(String(255))
    formacio_i_habitat = Column(String(255))
    codi = Column(String(255))
    flora = Column(Integer)
    municipi = Column(String(255))
    descripcio = Column(String)
    superficie_arbrada = Column(Float)
    superficie_no_arbrada = Column(Float)
    superficie_forestal = Column(Float)
    superficie_ordenada = Column(Float)
    superficie_no_ordenada = Column(Float)
    superficie_ha = Column(Float)
    superficie_no_forestal = Column(Float)

    def __repr__(self):
        return self.forest_nom

class QualificacionsEspecial(db.Model):
    __tablename__ = 'qualificacions_especials'

    id = Column(Integer, primary_key=True)
    tipus_id = Column(ForeignKey('tipus_qualificacio_especial.id'), nullable=False)
    nom = Column(String(255))
    superficie_afectada = Column(Integer)
    forest_id = Column(ForeignKey('forest.id'))
    observacions = Column(String)

    forest = relationship('Forest')
    tipus = relationship('TipusQualificacioEspecial')

    def __repr__(self):
        return self.nom

class Tramit(db.Model):
    __tablename__ = 'tramit'

    id = Column(Integer, primary_key=True)
    tramit_id = Column(ForeignKey('tipus_de_tramit.id'))
    id_persona_contacte_dni = Column(String(255))
    id_propietat = Column(Integer)
    forest_id = Column(ForeignKey('forest.id'))
    any_presentacio = Column(Integer)
    aprovat = Column(Boolean)

    forest = relationship('Forest')
    tipus_de_tramit = relationship('TipusDeTramit')

class InfoComplementariaPla(db.Model):
    __tablename__ = 'info_complementaria_pla'

    id = Column(Integer, primary_key=True)
    pla_id = Column(Integer, ForeignKey('pla.id', ondelete='CASCADE'))
    activitat_cinegetica = Column(String)
    ramaderia_extensiva = Column(String)
    tipus_de_bestiar = Column(Integer)
    numero_de_caps = Column(Float)
    observacions_ramaderia = Column(String)
    info_complementaria_pla = Column(String)
    antecedents_gestio = Column(String)

    pla = relationship('Pla')


class LineasDefensaPuntsAigua(db.Model):
    __tablename__ = 'lineas_defensa_punts_aigua'

    id = Column(Integer, primary_key=True)
    pla_id = Column(Integer, ForeignKey('pla.id', ondelete='CASCADE'))
    llistat_actuacions_id = Column(ForeignKey('llistat_actuacions.id'))
    tipus_est_prev = Column(String(255))
    any_real_actuacio = Column(Integer)
    codi = Column(String(255))
    tipus = Column(String(255))
    amidament = Column(Float)
    any_o_periodicitat = Column(Integer)
    observacions = Column(Text)
    despeses = Column(String(255))
    realitzada = Column(Boolean)
    ajut_concedit = Column(Boolean)
    quantitat_ajut = Column(Integer)
    geometry = Column(Geometry("MULTIPOLYGON", srid=4326))

    pla = relationship('Pla')
    actuacio = relationship('LlistatActuacion')

class PlaPersContact(db.Model):
    __tablename__ = 'pla_pers_contact'

    id = Column(Integer, primary_key=True)
    pla_id = Column(Integer, ForeignKey('pla.id', ondelete='CASCADE'))
    persona_de_contacte_id = Column(ForeignKey('persona_de_contacte.id'))

    persona_de_contacte = relationship('PersonaDeContacte')
    pla = relationship('Pla')


class PlaProp(db.Model):
    __tablename__ = 'pla_prop'

    id = Column(Integer, primary_key=True)
    pla_id = Column(Integer, ForeignKey('pla.id', ondelete='CASCADE'))
    propietari_dades_id = Column(ForeignKey('propietari_dades.id'))

    propietari_dade = relationship('PropietariDade')
    pla = relationship('Pla')

    def __repr__(self):
        return self.nom

'''
class BlobMixin(object):
    id = Column(Integer, nullable=False, primary_key=True)
    camins_fname = Column(String(length=255), nullable=False)
    camins_blob = Column(LargeBinary(), nullable=False)
    canvi_us_fname = Column(String(length=255), nullable=False)
    canvi_us_blob = Column(LargeBinary(), nullable=False)
    infraestructures_incedis_fname = Column(String(length=255), nullable=False)
    infraestructures_incedis_blob = Column(LargeBinary(), nullable=False)
    unitats_actuacio_fname = Column(String(length=255), nullable=False)
    unitats_actuacio_blob = Column(LargeBinary(), nullable=False)
    usos_vege_fname = Column(String(length=255), nullable=False)
    usos_vege_blob = Column(LargeBinary(), nullable=False)
    informacio_addicional_fname = Column(String(length=255), nullable=True)
    informacio_addicional_blob = Column(LargeBinary(), nullable=True)
'''

class ProjecteZip(db.Model):
    __tablename__ = 'projecte_zip'
    id = Column(Integer, primary_key=True)
    pla_id = Column(Integer, ForeignKey('pla.id', ondelete='CASCADE'))
    name = Column(String(255), nullable=False)
    numero_expediente = Column(String(255), nullable=False)
    any_del_pla = Column(Integer, nullable=False)
    pdf_fname = Column(String(length=255), nullable=False)
    pdf_blob = Column(LargeBinary(), nullable=False)
    camins_fname = Column(String(length=255), nullable=True)
    camins_blob = Column(LargeBinary(), nullable=True)
    canvi_us_fname = Column(String(length=255), nullable=True)
    canvi_us_blob = Column(LargeBinary(), nullable=True)
    infraestructures_incedis_fname = Column(String(length=255), nullable=True)
    infraestructures_incedis_blob = Column(LargeBinary(), nullable=True)
    unitats_actuacio_fname = Column(String(length=255), nullable=False)
    unitats_actuacio_blob = Column(LargeBinary(), nullable=False)
    usos_vege_fname = Column(String(length=255), nullable=True)
    usos_vege_blob = Column(LargeBinary(), nullable=True)
    informacio_addicional_fname = Column(String(length=255), nullable=True)
    informacio_addicional_blob = Column(LargeBinary(), nullable=True)

    user_id = Column(ForeignKey('user.id'))

    user = relationship('User')

    pla = relationship('Pla')

    label = 'Project files'

    def __repr__(self):
        return self.filename


@db.event.listens_for(ProjecteZip, "before_insert")
def insert_projectezip(mapper, connection, target):
    process_upload_project_Data = dms.ProcessUploadProjectData(target)
    process_upload_project_Data.process()
    target.pla_id = process_upload_project_Data.Pla.id

class XarxaNovaConstruccio(db.Model):
    __tablename__ = 'xarxa_nova_construccio'

    id = Column(Integer, primary_key=True)
    pla_id = Column(Integer, ForeignKey('pla.id', ondelete='CASCADE'))
    actuacio_id = Column(ForeignKey('llistat_actuacions.id', ondelete="CASCADE"))
    any_o_periodicitat = Column(Integer)
    any_real_actuacio = Column(Integer)
    codi = Column(String(255))
    tipus = Column(String(255))
    longidud = Column(Float)
    despeses = Column(String(255))
    realitzada = Column(Boolean)
    ajut_concedit = Column(Boolean)
    quantitat_ajut = Column(Integer)
    geometry = Column(Geometry("MULTILINESTRING", srid=4326))

    pla = relationship('Pla')
    actuacio = relationship('LlistatActuacion')


class XarxaViariaExistent(db.Model):
    __tablename__ = 'xarxa_viaria_existent'

    id = Column(Integer, primary_key=True)
    pla_id = Column(Integer, ForeignKey('pla.id', ondelete='CASCADE'))
    actuacio_id = Column(ForeignKey('llistat_actuacions.id', ondelete="CASCADE"))
    codi = Column(String(255))
    tipus = Column(String(255))
    longidud = Column(Float)
    any_o_periodicitat = Column(Integer)
    any_real_actuacio = Column(Integer)
    geometry = Column(Geometry("MULTILINESTRING", srid=4326))

    pla = relationship('Pla')
    actuacio = relationship('LlistatActuacion', cascade="delete, merge, save-update")

class ActuacionsDelPla(db.Model):
    __tablename__ = 'actuacions_del_pla'
    id = Column(Integer, primary_key=True)
    rodal_id = Column(Integer, ForeignKey('rodal.id', ondelete='CASCADE'))
    actuacio_id = Column(ForeignKey('llistat_actuacions.id'))
    any_o_periodicitat = Column(Integer)
    notificacio = Column(Boolean)
    area_afectada = Column(Float)
    perc_afectada = Column(Float)
    volum_estimat = Column(Float)
    producte = Column(String(255))
    quantitat_de_producte_estimat = Column(Float)
    unitats_de_la_quantitat_de_prod = Column(String(255))
    observacions_actuacio = Column(String)
    ingressos_estimats = Column(Float)
    despesses_estimades = Column(Float)
    balanc_estimat = Column(Float)
    fonrs_millora_estimat = Column(Float)
    any_real_actuacio = Column(Integer)
    parcialment = Column(Integer)
    ajut_condecit = Column(Boolean)
    quantia_ajut = Column(Integer)
    quantitat_de_producte_obtingut = Column(String(255))
    ingressos_obtinguts = Column(Float)
    despesses_reals = Column(Float)
    balanc_final = Column(Float)
    fons_millora = Column(Integer)

    actuacio = relationship('LlistatActuacion')
    rodal = relationship('Rodal')


class ActuacionsNoProgramablesDelpla(db.Model):
    __tablename__ = 'actuacions_no_programables_delpla'

    id = Column(Integer, primary_key=True)
    rodal_id = Column(Integer, ForeignKey('rodal.id', ondelete='CASCADE'))
    actuacio_id = Column(ForeignKey('llistat_actuacions.id'))
    periodicitat = Column(Integer)
    unitat_damidament = Column(Integer)
    amidament = Column(Integer)
    num_actuacions = Column(Integer)
    notificacio = Column(Boolean)
    any_real_actuacio = Column(Integer)
    parcialment = Column(Integer)
    ajut_condecit = Column(Boolean)
    quantia_ajut = Column(Integer)
    quantitat_de_producte_obtingut = Column(Integer)
    ingressos_obtinguts = Column(Integer)
    despesses_reals = Column(Integer)

    actuacio = relationship('LlistatActuacion')
    rodal = relationship('Rodal')


class Inventari(db.Model):
    __tablename__ = 'inventari'

    id = Column(Integer, primary_key=True)
    rodal_id = Column(Integer, ForeignKey('rodal.id', ondelete='CASCADE'))
    tipus_inventari = Column(String(255))
    intensitat_mostreig = Column(String(255))
    tipus_parcel_la = Column('tipus_parcella', String(255))
    observacions = Column(String(255))

    rodal = relationship('Rodal')

class Especies(db.Model):
    __tablename__ = 'especies'

    id = Column(Integer, primary_key=True)
    nom = Column(String(255))
    acronym = Column(String(255))

    def __repr__(self):
        return self.nom

class ResultatsInventariFusta(db.Model):
    __tablename__ = 'resultats_inventari_fusta'

    id = Column(Integer, primary_key=True)
    rodal_id = Column(Integer, ForeignKey('rodal.id', ondelete='CASCADE'))
    any_ = Column(Integer)
    especies_id = Column(ForeignKey('especies.id'))
    fcc = Column(Float)
    d_m = Column(Float)
    h_m = Column(Float)
    n_peusperha = Column(Float)
    vol = Column(Float)
    a_b = Column(Float)
    descripcio_silvicola = Column(String(255))
    v_ae_gt_7_5_cm__creixement_m3ha = Column(Integer)
    v_ae_gt_7_5_cm_m3 = Column(Integer)
    creixement_m3ha = Column(Float)
    creixement_gt_7_5cm__m3_ha_any_ = Column(Float)
    biomassa_aeria_tns_per_ha = Column(Float)
    biomassa_aeria_tns = Column(Float)
    edat = Column(Float)
    forma_principal = Column(String(255))
    composicio_especifica = Column(String(255))
    distribucio_espaial = Column(String(255))

    rodal = relationship('Rodal')
    especies = relationship('Especies')


class ResumInventariFusta(db.Model):
    __tablename__ = 'resum_inventari_fusta'

    id = Column(Integer, primary_key=True)
    rodal_id = Column(Integer, ForeignKey('rodal.id', ondelete='CASCADE'))
    tipus_inventari_id=Column(Integer, ForeignKey('tipus_inventari.id'))
    forma_principal=Column(String(255))
    any = Column(Integer)
    n_peus_ha = Column(Float)
    vol = Column(Float)
    ab = Column(Float)
    descripcio_silvicola = Column(String(255))
    biomassa_aeria_tns_ha = Column(Integer)
    biomassa_aeria_tns = Column(Integer)
    formaprincipal = Column(String(255))
    composicio_especifica = Column(String(255))
    distribucio_espacial = Column(String(255))
    observacions_inventari = Column(String)

    rodal = relationship('Rodal')
    tipus_inventari = relationship('TipusInventari')

class ResumInventariSuro(db.Model):
    __tablename__ = 'resum_inventari_suro'

    id = Column(Integer, primary_key=True)
    rodal_id = Column(Integer, ForeignKey('rodal.id', ondelete='CASCADE'))
    any_ = Column(Integer)
    specie = Column(String(255))
    n_peusperha = Column(Float)
    coef_de_lleva = Column(Float)
    alcada_mitja = Column(Float)
    temps_ultima_pela = Column(Float)
    estimacio_aprofitament_tns_per_ha = Column(Float)
    existencies_pelegri_tnsperha = Column(Float)
    gruix_mitja_mm = Column(Float)
    existencies_suro_tperha = Column(Float)

    rodal = relationship('Rodal')


class Despes(db.Model):
    __tablename__ = 'despeses'

    id = Column(Integer, primary_key=True)
    actuacio_id = Column(ForeignKey('actuacions_del_pla.id'))
    rodal_id = Column(Integer, ForeignKey('rodal.id', ondelete='CASCADE'))
    concepte = Column(String(255))
    amidament = Column(Integer)
    unitats = Column(Integer)
    valor_unitari = Column(Integer)
    despeses = Column(Integer)
    total_despeses = Column(Integer)

    actuacio = relationship('ActuacionsDelPla')
    rodal = relationship('Rodal')


class IngresActuacion(db.Model):
    __tablename__ = 'ingres_actuacions'

    id = Column(Integer, primary_key=True)
    actuacio_id = Column(ForeignKey('actuacions_del_pla.id'))
    rodal_id = Column(Integer, ForeignKey('rodal.id', ondelete='CASCADE'))
    tipus_producte = Column(Integer)
    contacte = Column(String(255))
    amidament = Column(Integer)
    unitats = Column(Integer)
    valor_unitari = Column(Integer)
    ingressos = Column(Integer)

    actuacio = relationship('ActuacionsDelPla')
    rodal = relationship('Rodal')


class CanviUs(db.Model):
    __tablename__ = 'canvi_us'

    id = Column(Integer, primary_key=True)
    pla_id = Column(Integer, ForeignKey('pla.id', ondelete='CASCADE'))
    llistat_actuacions_id = Column(ForeignKey('llistat_actuacions.id'))
    codi = Column(String(255))
    tipus_ex_prev = Column(String(255))
    tipus = Column(String(255))
    amidament = Column(Integer)
    ani_o_periodicidat = Column(Integer)
    despeses = Column(Float)
    realitzada = Column(Boolean)
    any_realitzat = Column(Integer)
    ajut_concedit = Column(Boolean)
    quantitat_ajut = Column(Float)
    observacions = Column(Text)
    geometry = Column(Geometry("MULTIPOLYGON", srid=4326))

    pla = relationship('Pla')
    actuacio = relationship('LlistatActuacion')


class LogErr(db.Model):
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now())
    nom_pla = Column(String(255))
    message = Column(Text)


class ImportShpLines(db.Model):
    __tablename__ = 'import_shp_lines'

    id = Column(Integer, primary_key=True)
    pla_id = Column(Integer, ForeignKey('pla.id', ondelete='CASCADE'))
    data_type = Column(String(255))
    field1 = Column(String(255))
    field2 = Column(String(255))
    geometry = Column(Geometry("LINESTRING", srid=4326))

    pla = relationship('Pla')

class ImportShpPolygons(db.Model):
    __tablename__ = 'import_shp_polygons'

    id = Column(Integer, primary_key=True)
    pla_id = Column(Integer, ForeignKey('pla.id', ondelete='CASCADE'))
    data_type = Column(String(255))
    field1 = Column(String(255))
    field2 = Column(String(255))
    geometry = Column(Geometry("POLYGON", srid=4326))

    pla = relationship('Pla', cascade="delete, merge, save-update")

class UsosVege(db.Model):
    __tablename__ = 'usos_vege'

    id = Column(Integer, primary_key=True)
    pla_id = Column(Integer, ForeignKey('pla.id', ondelete='CASCADE'))
    data_type = Column(String(255))
    field1 = Column(String(255))
    field2 = Column(String(255))
    geometry = Column(Geometry("POLYGON", srid=4326))

    pla = relationship('Pla', cascade="delete, merge, save-update")

class Consultes(db.Model):
    __tablename__ = 'consultes'
    id = Column(Integer, primary_key=True)
    nom = Column(String(255))
    sql = Column(Text)
    categoria = Column(String(255))
    nom_filtre = Column(String(255))
    camp_filtre = Column(String(255))
    sql_filtre = Column(Text)
    etiqueta = Column(String(255))
    nomes_administradors = Column(Boolean, default=False)

class EspeciePrincipal(db.Model):
    __tablename__ = 'especie_principal'
    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)
    rmges_orgest = Column(String(1), nullable=False)

    def __repr__(self):
        return self.nom

class EspecieFormacioArborea(db.Model):
    __tablename__ = 'especie_formacio_arborea'
    id = Column(Integer, primary_key=True)
    acronym = Column(String(255), nullable=False)
    nom = Column(String(255), nullable=False)

    def __repr__(self):
        return self.nom

class Orgest(db.Model):
    __tablename__ = 'orgest'
    id = Column(Integer, primary_key=True)
    acronym = Column(String(255))
    descripcio = Column(Text)
    especie_principal_id = Column(Integer, ForeignKey('especie_principal.id', ondelete='CASCADE'))

    especie_principal = relationship('EspeciePrincipal')

class TipologiaFormacioForestal(db.Model):
    __tablename__ = 'tipologia_formacio_forestal'
    id = Column(Integer, primary_key=True)
    acronym = Column(String(255), nullable=False)
    nom = Column(String(255), nullable=False)
    especie_principal_id = Column(Integer, ForeignKey('especie_principal.id', ondelete='CASCADE'), nullable=False)

    especie_principal = relationship('EspeciePrincipal')

class ObjectiuGeneral(db.Model):
    __tablename__ = 'objectiu_general'
    id = Column(Integer, primary_key=True)
    acronym = Column(String(1), nullable=False)
    nom = Column(String(255), nullable=False)

    def __repr__(self):
        return self.nom

class ObjectiuPreferent(db.Model):
    __tablename__ = 'objectiu_preferent'
    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)
    objectiu_general_id = Column(Integer, ForeignKey('objectiu_general.id', ondelete='CASCADE'), nullable=False)

    objectiu_general = relationship('ObjectiuGeneral')

class ActuacionsPTGMF(db.Model):
    __tablename__ = 'actuacions_ptgmf'
    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)
    altre = Column(String(5))

    def __repr__(self):
        return self.nom

class Unitat(db.Model):
    __tablename__ = 'unitat'
    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)

    def __repr__(self):
        return self.nom

class Vulnerabilitat(db.Model):
    __tablename__ = 'vulnerabilitat'
    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)

    def __repr__(self):
        return self.nom

class TipusInventari(db.Model):
    __tablename__ = 'tipus_inventari'
    id = Column(Integer, primary_key=True)
    acronym = Column(String(1), nullable=False)
    nom = Column(String(255), nullable=False)

    def __repr__(self):
        return self.nom

class TipusEstruturaMassa(db.Model):
    __tablename__ = 'tipus_estrutura_massa'
    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)

    def __repr__(self):
        return self.nom

class QualitatEstacio(db.Model):
    __tablename__ = 'qualitat_estacio'
    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)

    def __repr__(self):
        return self.nom
'''
class GeoEntitat(db.Model):
    __tablename__ = 'geo_entitat'
    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)

    def __repr__(self):
        return self.nom
'''

class AnyActuacio(db.Model):
    __tablename__ = 'any_actuacio'
    id = Column(Integer, primary_key=True)
    actuacions_del_pla_id = Column(Integer, ForeignKey('actuacions_del_pla.id', ondelete='CASCADE'), nullable=False)
    any_programat = Column(Integer, nullable=False)

    actuacions_del_pla = relationship('ActuacionsDelPla')

from flask_user import UserManager, SQLAlchemyAdapter
db_adapter = SQLAlchemyAdapter(db, User)
user_manager = UserManager(db_adapter, app_object_support.app)

