from gettext import gettext
import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy, event
from flask_user import UserMixin
from datetime import datetime
from sqlalchemy import and_, not_
from geoalchemy2.types import Geometry
from flask_user import current_user
from flask_babel import lazy_gettext

app = Flask(__name__)
app.config.from_pyfile('config.cfg')

db =SQLAlchemy(app)

def getUserId():
    return current_user.id

def getUploadProfileId():
    return db.session.query(Profile.id).filter(and_(not_(Profile.is_administrator),Profile.can_upload)).first()[0]


class BlobMixin(object):
    mimetype = db.Column(db.String(length=255), nullable=False)
    filename = db.Column(db.String(length=255), nullable=False)
    blob = db.Column(db.LargeBinary(), nullable=False)
    size = db.Column(db.Integer, nullable=False)

    def __unicode__(self):
        return u"name : {name}; filename : {filename})".format(name=self.name, filename=self.filename)


class ProjectePdf(db.Model, BlobMixin):
    __tablename__ = u'projecte_pdf'
    label = lazy_gettext('Project PDF file')
    column_labels = dict(name=lazy_gettext('Name'),user=lazy_gettext('User'))

    id = db.Column(db.Integer(), db.Sequence('public.projecte_map_id_seq'), primary_key=True, nullable=False)
    name = db.Column(db.String(255),nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), default=getUserId)

    user = db.relationship('User', primaryjoin='ProjectePdf.user_id == User.id')

    def __repr__(self):
        return self.nom

class ProjecteMap(db.Model):
    __tablename__ = u'projecte_map'
    label = lazy_gettext('Project Map')

    id = db.Column(db.Integer(), db.Sequence('public.projecte_map_id_seq'), primary_key=True, nullable=False)
    nom = db.Column(db.String(255),nullable=False)
    plaord_forestal_id = db.Column(db.Integer(), db.ForeignKey('plaord_forestal.id'))
    geom = db.Column(Geometry("MULTIPOLYGON"))

    PlaordForestal = db.relationship('PlaordForestal', primaryjoin='ProjecteMap.plaord_forestal_id == PlaordForestal.id')

    def __repr__(self):
        return self.nom

class Profile(db.Model):
    __tablename__ = u'profile'

    id = db.Column(db.Integer(), db.Sequence('public.profile_id_seq'), primary_key=True, nullable=False)
    profilename = db.Column(db.String(255), nullable=False, unique=True)
    is_administrator = db.Column(db.Boolean(), nullable=False)
    can_upload = db.Column(db.Boolean(), nullable=False, default=False)

    def __repr__(self):
        return self.profilename

def insert_initial_profiles(*args, **kwargs):
    admin_profile = Profile(profilename='administrator',is_administrator=True, can_upload=True)
    upload_profile = Profile(profilename='upload',is_administrator=False, can_upload=True)
    guest_profile = Profile(profilename='guest',is_administrator=False, can_upload=False)
    db.session.add_all([admin_profile,upload_profile,guest_profile])
    db.session.commit()

# region Tables definition
class User(db.Model, UserMixin):
    __tablename__ = u'user'

    id = db.Column(db.Integer,db.Sequence('public.actuacions_descripcio_id_seq'), nullable=False, primary_key=True)
    username = db.Column(db.String(20),nullable=False,unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    active = db.Column(db.Boolean, nullable=False, default=1)
    email = db.Column(db.String(255),nullable=False, unique=True)
    confirmed_at = db.Column(db.DateTime())
    profile_id = db.Column(db.Integer(), db.ForeignKey('profile.id'), default=getUploadProfileId)
    profile = db.relationship('Profile', primaryjoin='User.profile_id == Profile.id')

    def __repr__(self):
        return self.username

def insert_administrator_user(*args, **kwargs):
    if db.engine.dialect.has_table(db.engine, 'profile'):
        administrator_profile_id = db.session.query(Profile.id).filter(Profile.is_administrator).first()[0]
        adm_user = User(username='administrator',
                        #Jatoba@12
                        password=u'$2b$12$fTbRZzCD18t/EU/2nrXSF.O0WqjImRUuSEV9HW1jay1rmc5TDCnzq',
                        active=True,
                        email='assismauro@hotmail.com',
                        confirmed_at=datetime.now(),
                        profile_id=administrator_profile_id)
        db.session.add(adm_user)
        db.session.commit()

event.listen(Profile.__table__, 'after_create', insert_initial_profiles)
event.listen(User.__table__, 'after_create', insert_administrator_user)

class ActuacionsDescripcio(db.Model):
    __tablename__ = u'actuacions_descripcio'

    id = db.Column(db.Integer(), db.Sequence('public.actuacions_descripcio_id_seq'), primary_key=True, nullable=False)
    nom_actuacio = db.Column(db.String(4096))
    cost_ha = db.Column(db.Integer())
    tipus = db.Column(db.String(255))

    def to_json(self):
        obj = {
            'id': self.id,
            'nom_actuacio': self.nom_actuacio,
            'cost_ha': self.cost_ha,
            'tipus': self.tipus,
        }
        return json.dumps(obj)


class ActuacionsDelPla(db.Model):
    __tablename__ = u'actuacions_del_pla'
    label = lazy_gettext('Planning Performances')

    id = db.Column(db.Integer(), db.Sequence('public.actuacions_del_pla_id_seq'), primary_key=True, nullable=False)
    plaord_forestal_id = db.Column(db.Integer(), db.ForeignKey('plaord_forestal.id'))
    rodal_id = db.Column(db.Integer(), db.ForeignKey('rodal.id'))
    actuacio_id = db.Column(db.Integer(), db.ForeignKey('actuacions_descripcio.id'))
    any_programat = db.Column(db.Integer())
    periodicitat = db.Column(db.Integer())
    perc_afectada = db.Column(db.Integer())
    volum_estimat = db.Column(db.Integer())
    producte = db.Column(db.String(255))
    quantitat_de_producte_estimat = db.Column(db.Integer())
    any_real_actuacio = db.Column(db.Integer())
    parcialment = db.Column(db.Integer())
    ajut_condecit = db.Column(db.Boolean())
    quantia_ajut = db.Column(db.Integer())
    quantitat_de_producte_obtingut = db.Column(db.String(255))

    # relation definitions: many to one with backref (also takes care of one to many)
    ActuacionsDelPlaRodal = db.relationship('Rodal', primaryjoin='ActuacionsDelPla.rodal_id == Rodal.id')
    ActuacionsDelPlaPlan = db.relationship('PlaordForestal', primaryjoin='ActuacionsDelPla.plaord_forestal_id == PlaordForestal.id')
    ActuacionsDelPlaActuacio = db.relationship('ActuacionsDescripcio',
                                            primaryjoin='ActuacionsDelPla.actuacio_id == ActuacionsDescripcio.id')

    def to_json(self):
        obj = {
            'id': self.id,
            'plaord_forestal_id': self.plaord_forestal_id,
            'rodal_id': self.rodal_id,
            'actuacio_id': self.actuacio_id,
            'any_programat': self.any_programat,
            'periodicitat': self.periodicitat,
            'perc_afectada': self.perc_afectada,
            'volum_estimat': self.volum_estimat,
            'producte': self.producte,
            'quantitat_de_producte_estimat': self.quantitat_de_producte_estimat,
            'any_real_actuacio': self.any_real_actuacio,
            'parcialment': self.parcialment,
            'ajut_condecit': self.ajut_condecit,
            'quantia_ajut': self.quantia_ajut,
            'quantitat_de_producte_obtingut': self.quantitat_de_producte_obtingut,
        }
        return json.dumps(obj)


class AltresAfectacionsLegals(db.Model):
    __tablename__ = u'altres_afectacions_legals'
    label = lazy_gettext('Other Legal Affections')

    id = db.Column(db.Integer(), db.Sequence('public.altres_afectacions_legals_id_seq'), primary_key=True, nullable=False)
    tipus_id = db.Column(db.String(255))
    nom = db.Column(db.String(255))
    superficie_afectada = db.Column(db.Integer())
    id_forest = db.Column(db.Integer())
    observacions = db.Column(db.String(4096))

    def to_json(self):
        obj = {
            'id': self.id,
            'tipus_id': self.tipus_id,
            'nom': self.nom,
            'superficie_afectada': self.superficie_afectada,
            'id_forest': self.id_forest,
            'observacions': self.observacions,
        }
        return json.dumps(obj)


class Despeses(db.Model):
    __tablename__ = u'despeses'
    label = lazy_gettext('Expenses')

    id = db.Column(db.Integer(), db.Sequence('public.despeses_id_seq'), primary_key=True, nullable=False)
    actuacio_id = db.Column(db.Integer())
    rodal_id = db.Column(db.Integer())
    concepte = db.Column(db.String(255))
    amidament = db.Column(db.Integer())
    unitats = db.Column(db.Integer())
    valor_unitari = db.Column(db.Integer())
    despeses = db.Column(db.Integer())
    total_despeses = db.Column(db.Integer())

    def to_json(self):
        obj = {
            'id': self.id,
            'actuacio_id': self.actuacio_id,
            'rodal_id': self.rodal_id,
            'concepte': self.concepte,
            'amidament': self.amidament,
            'unitats': self.unitats,
            'valor_unitari': self.valor_unitari,
            'despeses': self.despeses,
            'total_despeses': self.total_despeses,
        }
        return json.dumps(obj)


class Inventari(db.Model):
    __tablename__ = u'inventari'
    lable = lazy_gettext('Inventories')

    id = db.Column(db.Integer(), db.Sequence('public.inventari_id_seq'), primary_key=True, nullable=False)
    rodal = db.Column(db.Integer())
    tipus_inventari = db.Column(db.String(255))
    intensitat_mostreig = db.Column(db.String(255))
    tipus_parcella = db.Column(db.String(255))
    observacions = db.Column(db.String(255))

    def to_json(self):
        obj = {
            'id': self.id,
            'rodal': self.rodal,
            'tipus_inventari': self.tipus_inventari,
            'intensitat_mostreig': self.intensitat_mostreig,
            'tipus_parcella': self.tipus_parcella,
            'observacions': self.observacions,
        }
        return json.dumps(obj)


class PlaordProp(db.Model):
    __tablename__ = u'plaord_prop'
    label = lazy_gettext('Planning Ord Prop')

    # db.Column definitions
    id = db.Column(db.Integer(), db.Sequence('public.plaord_prop_id_seq'), primary_key=True, nullable=False)
    idpla = db.Column(db.Integer())
    dniprop = db.Column(db.Integer())

    def to_json(self):
        obj = {
            'id': self.id,
            'idpla': self.idpla,
            'dniprop': self.dniprop,
        }
        return json.dumps(obj)


class PlaordForestal(db.Model):
    __tablename__ = u'plaord_forestal'
    label = lazy_gettext('Planning Ord Forest')

    id = db.Column(db.Integer(), db.Sequence('public.plaord_forestal_id_seq'), primary_key=True, nullable=False)
    nom = db.Column(db.String(255))
    numero = db.Column(db.Integer())
    propietari = db.Column(db.String(255))
    municipi = db.Column(db.String(255))
    comarca = db.Column(db.String(255))
    id_forest = db.Column(db.Integer(),db.ForeignKey('forest.id'))
    superficie_total = db.Column(db.Integer())
    superficie_forestal = db.Column(db.Integer())
    superf_no_forestal = db.Column(db.Integer())
    any_del_pla = db.Column(db.Integer())
    vigencia = db.Column(db.Integer())
    arbrada = db.Column(db.Integer())
    no_arbrada = db.Column(db.Integer())
    persona_contacte_id = db.Column(db.Integer(),db.ForeignKey('persona_de_contacte.id'))
    afectacio_enpe = db.Column(db.Boolean())
    afectacio_pein_pe = db.Column(db.Boolean())
    afect_pein = db.Column(db.Boolean())
    afect_lu = db.Column(db.Boolean())
    afect_up = db.Column(db.Boolean())
    afect_zau = db.Column(db.Boolean())
    afect_lic = db.Column(db.Boolean())
    afect_zepa = db.Column(db.Boolean())
    ppp = db.Column(db.Boolean())
    rnc = db.Column(db.Boolean())
    prea = db.Column(db.Boolean())
    tipus_de_pla = db.Column(db.String(255))

    # relation definitions: many to one with backref (also takes care of one to many)
    PlaordForestalIdForest =db.relationship('Forest', primaryjoin='PlaordForestal.id_forest == Forest.id')
    PlaordForestalPersonaContacte =db.relationship('PersonaDeContacte',
                                                 primaryjoin='PlaordForestal.persona_contacte_id == PersonaDeContacte.id')

    def to_json(self):
        obj = {
            'id': self.id,
            'nom': self.nom,
            'numero': self.numero,
            'propietari': self.propietari,
            'municipi': self.municipi,
            'comarca': self.comarca,
            'id_forest': self.id_forest,
            'superficie_total': self.superficie_total,
            'superficie_forestal': self.superficie_forestal,
            'superf_no_forestal': self.superf_no_forestal,
            'any_del_pla': self.any_del_pla,
            'vigencia': self.vigencia,
            'arbrada': self.arbrada,
            'no_arbrada': self.no_arbrada,
            'persona_contacte_id': self.persona_contacte_id,
            'afectacio_enpe': self.afectacio_enpe,
            'afectacio_pein_pe': self.afectacio_pein_pe,
            'afect_pein': self.afect_pein,
            'afect_lu': self.afect_lu,
            'afect_up': self.afect_up,
            'afect_zau': self.afect_zau,
            'afect_lic': self.afect_lic,
            'afect_zepa': self.afect_zepa,
            'ppp': self.ppp,
            'rnc': self.rnc,
            'prea': self.prea,
            'tipus_de_pla': self.tipus_de_pla,
        }
        return json.dumps(obj)

 #   def __repr__(self):
 #       return self.nom

class PropietariDades(db.Model):
    __tablename__ = u'propietari_dades'
    label = lazy_gettext('Owner Data')

    ordre = db.Column(db.Integer())
    dni = db.Column(db.Integer(), nullable=False)
    nom = db.Column(db.String(255))
    adreca = db.Column(db.String(4096))
    contacte = db.Column(db.String(255))
    id = db.Column(db.Integer(), db.Sequence('public.propietari_dades_id_seq'), primary_key=True, nullable=False)

    def to_json(self):
        obj = {
            'ordre': self.ordre,
            'dni': self.dni,
            'nom': self.nom,
            'adreca': self.adreca,
            'contacte': self.contacte,
            'id': self.id,
        }
        return json.dumps(obj)

class DadesPropietat(db.Model):
    __tablename__ = u'dades_propietat'

    label = lazy_gettext('Property Data')
    id = db.Column(db.Integer(), db.Sequence('public.dades_propietat_id_seq'), primary_key=True, nullable=False)
    nom = db.Column(db.String(255))
    cif = db.Column(db.Integer())
    adreca = db.Column(db.String(4096))
    contacte = db.Column(db.String(255))

    def to_json(self):
        obj = {
            'id': self.id,
            'nom': self.nom,
            'cif': self.cif,
            'adreca': self.adreca,
            'contacte': self.contacte,
        }
        return json.dumps(obj)


class Tipusdepla(db.Model):
    __tablename__ = u'tipusdepla'
    label = lazy_gettext('Planning Data')

    id = db.Column(db.Integer(), db.Sequence('public.tipusdepla_id_seq'), primary_key=True, nullable=False)
    campo1 = db.Column(db.String(255))

    def to_json(self):
        obj = {
            'id': self.id,
            'campo1': self.campo1,
        }
        return json.dumps(obj)


class TipusQualificacioEspecial(db.Model):
    __tablename__ = u'tipus_qualificacio_especial'
    label = lazy_gettext('Special Qualification Types')

    tipus_id = db.Column(db.String(255))
    nom_extens = db.Column(db.String(255))
    id = db.Column(db.Integer(), db.Sequence('public.tipus_qualificacio_especial_id_seq'), primary_key=True, nullable=False)

    def to_json(self):
        obj = {
            'tipus_id': self.tipus_id,
            'nom_extens': self.nom_extens,
            'id': self.id,
        }
        return json.dumps(obj)


class AltresActuacionsDelPla(db.Model):
    __tablename__ = u'altres_actuacions_del_pla'
    label = lazy_gettext('Plan Other Players')

    id = db.Column(db.Integer(), db.Sequence('public.altres_actuacions_del_pla_id_seq'), primary_key=True, nullable=False)
    nom = db.Column(db.String(255))

    def to_json(self):
        obj = {
            'id': self.id,
            'nom': self.nom,
        }
        return json.dumps(obj)


class IngresActuacions(db.Model):
    __tablename__ = u'ingres_actuacions'
    label = lazy_gettext('Peorformance Query')

    id = db.Column(db.Integer(), db.Sequence('public.ingres_actuacions_id_seq'), primary_key=True, nullable=False)
    actuacio_id = db.Column(db.Integer())
    rodal_id = db.Column(db.Integer())
    tipus_producte = db.Column(db.Integer())
    concepte = db.Column(db.String(255))
    amidament = db.Column(db.Integer())
    unitats = db.Column(db.Integer())
    valor_unitari = db.Column(db.Integer())
    ingressos = db.Column(db.Integer())

    def to_json(self):
        obj = {
            'id': self.id,
            'actuacio_id': self.actuacio_id,
            'rodal_id': self.rodal_id,
            'tipus_producte': self.tipus_producte,
            'concepte': self.concepte,
            'amidament': self.amidament,
            'unitats': self.unitats,
            'valor_unitari': self.valor_unitari,
            'ingressos': self.ingressos,
        }
        return json.dumps(obj)


class ResultatsInventariFusta(db.Model):
    __tablename__ = u'resultats_inventari_fusta'
    label = lazy_gettext('Wood Inventory Results')

    id = db.Column(db.Integer(), db.Sequence('public.resultats_inventari_fusta_id_seq'), primary_key=True, nullable=False)
    id_rodal = db.Column(db.Integer())
    any = db.Column(db.Integer())
    codi_formacio = db.Column(db.String(255))
    d_m = db.Column(db.Integer())
    h_m = db.Column(db.Integer())
    n_peusha = db.Column(db.Integer())
    vol = db.Column(db.Integer())
    ab = db.Column(db.Integer())
    descripcio_silvicola = db.Column(db.String(255))
    qualitat = db.Column(db.Integer())
    vae_75_cm_creixement_m3ha = db.Column(db.Integer())
    vae_75_cm_m3 = db.Column(db.Integer())
    creixement_m3ha = db.Column(db.Integer())
    creixement_75cm_m3_ha_any = db.Column(db.Integer())
    biomassa_aeria_tns_ha = db.Column(db.Integer())
    biomassa_aeria_tns = db.Column(db.Integer())

    def to_json(self):
        obj = {
            'id': self.id,
            'id_rodal': self.id_rodal,
            'any': self.any,
            'codi_formacio': self.codi_formacio,
            'd_m': self.d_m,
            'h_m': self.h_m,
            'n_peusha': self.n_peusha,
            'vol': self.vol,
            'ab': self.ab,
            'descripcio_silvicola': self.descripcio_silvicola,
            'qualitat': self.qualitat,
            'vae_75_cm_creixement_m3ha': self.vae_75_cm_creixement_m3ha,
            'vae_75_cm_m3': self.vae_75_cm_m3,
            'creixement_m3ha': self.creixement_m3ha,
            'creixement_75cm_m3_ha_any': self.creixement_75cm_m3_ha_any,
            'biomassa_aeria_tns_ha': self.biomassa_aeria_tns_ha,
            'biomassa_aeria_tns': self.biomassa_aeria_tns,
        }
        return json.dumps(obj)


class QualificacionsEspecials(db.Model):
    __tablename__ = u'qualificacions_especials'
    label = lazy_gettext('Special Qualifications')

    id = db.Column(db.Integer(), db.Sequence('public.qualificacions_especials_id_seq'), primary_key=True, nullable=False)
    tipus_id = db.Column(db.Integer(),db.ForeignKey('qualificacions_especials.id'))
    nom = db.Column(db.String(255))
    superficie_afectada = db.Column(db.Integer())
    id_forest = db.Column(db.Integer())
    observacions = db.Column(db.String(4096))

    # relation definitions: many to one with backref (also takes care of one to many)
    QualificacionsEspecialsTipus =db.relationship('QualificacionsEspecials',
                                                primaryjoin='QualificacionsEspecials.tipus_id == QualificacionsEspecials.id')

    def to_json(self):
        obj = {
            'id': self.id,
            'tipus_id': self.tipus_id,
            'nom': self.nom,
            'superficie_afectada': self.superficie_afectada,
            'id_forest': self.id_forest,
            'observacions': self.observacions,
        }
        return json.dumps(obj)


class TipusAfectacioLegal(db.Model):
    __tablename__ = u'tipus_afectacio_legal'
    label = lazy_gettext('Legal Affection Types')

    tipus_id = db.Column(db.Integer())
    nom_extens = db.Column(db.String(255))
    id = db.Column(db.Integer(), db.Sequence('public.tipus_afectacio_legal_id_seq'), primary_key=True, nullable=False)

    def to_json(self):
        obj = {
            'tipus_id': self.tipus_id,
            'nom_extens': self.nom_extens,
            'id': self.id,
        }
        return json.dumps(obj)


class PersonaDeContacte(db.Model):
    __tablename__ = u'persona_de_contacte'
    label = lazy_gettext('Contact Person')

    # db.Column definitions
    id = db.Column(db.Integer(), db.Sequence('public.persona_de_contacte_id_seq'), primary_key=True, nullable=False)
    ordre = db.Column(db.Integer())
    dni = db.Column(db.Integer(), nullable=False)
    nom = db.Column(db.String(255))
    adreca = db.Column(db.String(4096))
    contacte = db.Column(db.String(255))

    def to_json(self):
        obj = {
            'ordre': self.ordre,
            'dni': self.dni,
            'nom': self.nom,
            'adreca': self.adreca,
            'contacte': self.contacte,
            'id': self.id,
        }
        return json.dumps(obj)
    def __repr__(self):
        return self.nom

class TipusDeTramit(db.Model):
    __tablename__ = u'tipus_de_tramit'
    label = lazy_gettext('Procedure Type')

    descripcio = db.Column(db.String(4096), nullable=False)
    id = db.Column(db.Integer(), db.Sequence('tipus_de_tramit_id_seq'), primary_key=True, nullable=False)

    tramits = db.relationship('Tramit', backref='tipus_de_tramit', lazy='dynamic')

    def to_json(self):
        obj = {
            'descripcio': self.descripcio,
            'id': self.id,
        }
        return json.dumps(obj)


class Tramit(db.Model):
    __tablename__ = u'tramit'
    label = lazy_gettext('Procedure Types')

    id = db.Column(db.Integer(), db.Sequence('public.id_tramit_id_seq'), primary_key=True, nullable=False)
    id_tramit = db.Column(db.Integer(),db.ForeignKey('tipus_de_tramit.id'), nullable=False)
    id_personacontacte = db.Column(db.Integer(),db.ForeignKey('persona_de_contacte.id'), nullable=False)
    id_propietat = db.Column(db.Integer())
    id_forest = db.Column(db.Integer())
    any_presentacio = db.Column(db.Integer())
    aprovat = db.Column(db.Boolean())

    def to_json(self):
        obj = {
            'id': self.id,
            'id_tramit': self.id_tramit,
            'id_personacontacte': self.id_personacontacte,
            'id_propietat': self.id_propietat,
            'id_forest': self.id_forest,
            'any_presentacio': self.any_presentacio,
            'aprovat': self.aprovat,
        }
        return json.dumps(obj)

class Rodal(db.Model):
    __tablename__ = u'rodal'
    label = lazy_gettext('Stand')

    # db.Column definitions
    id = db.Column(db.Integer(), db.Sequence('public.rodal_id_seq'), primary_key=True, nullable=False)
    code = db.Column(db.String(10))
    formacionforestal = db.Column(db.String(255), nullable=False)
    area = db.Column(db.Integer(), nullable=False)
    perc_forestal = db.Column(db.Integer(), nullable=False)
    perc_arbrada = db.Column(db.Integer(), nullable=False)
    estatsanitari = db.Column(db.String(255))
    idplagestio = db.Column(db.Integer())
    idinventari = db.Column(db.Integer())
    id_forest = db.Column(db.Integer(),db.ForeignKey('forest.id'))

    def __repr__(self):
        return self.code

    def to_json(self):
        obj = {
            'id': self.id,
            'formacionforestal': self.formacionforestal,
            'area': self.area,
            'perc_forestal': self.perc_forestal,
            'perc_arbrada': self.perc_arbrada,
            'estatsanitari': self.estatsanitari,
            'idplagestio': self.idplagestio,
            'idinventari': self.idinventari,
            'id_forest': self.id_forest,
        }
        return json.dumps(obj)


class Forest(db.Model):
    __tablename__ = u'forest'
    label = lazy_gettext('Forest')

    # db.Column definitions
    id = db.Column(db.Integer(), db.Sequence('public.forest_id_seq'), primary_key=True, nullable=False)
    forest_nom = db.Column(db.String(255), nullable=False)
    formacio_i_habitat = db.Column(db.String(255), nullable=False)
    codi = db.Column(db.String(255), nullable=False)
    superficie_ha = db.Column(db.Integer(), nullable=False)
    percentatge = db.Column(db.Integer(), nullable=False)
    flora = db.Column(db.Integer())
    finca = db.Column(db.String(255))
    municipi = db.Column(db.String(255))
    descripcio = db.Column(db.String(4096))

    def __repr__(self):
        return self.forest_nom

    rodals = db.relationship('Rodal',backref='forest',lazy='dynamic')

    def to_json(self):
        obj = {
            'id': self.id,
            'forest_nom': self.forest_nom,
            'formacio_i_habitat': self.formacio_i_habitat,
            'codi': self.codi,
            'superficie_ha': self.superficie_ha,
            'percentatge': self.percentatge,
            'flora': self.flora,
            'finca': self.finca,
            'municipi': self.municipi,
            'descripcio': self.descripcio,
        }
        return json.dumps(obj)

# endregion