# https://stackoverflow.com/questions/11014148/how-to-decrypt-a-pdf-file-by-supplying-password-of-the-file-as-argument-using-c
from datetime import datetime
import os
import subprocess
from glob import glob
from collections import OrderedDict
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_
from sqlalchemy import sql
from supports.merge_geometries_imports import merge_sqls
import data_model as dm
import supports.dbquery as dbquery
import supports.app_object as app_object

pdfPassword = 'Artemis_76'

supportEngine = dbquery.getEngine()


def run_aux_inserts(conn):
    with open(r'{1}{0}sql{0}database_final_touches.sql'.format(os.sep, app_object.app.root_path),
              encoding='UTF-8') as scriptfile:
        script = scriptfile.read()
        script = script.split(';\n')
        try:
            for command in script:
                command = command.strip()
                if len(command) > 0 and not command.startswith('--'):
                    conn.execute(command)
        except Exception as ex:
            print(ex)
            print(command)
            raise ('Database final touches interrupted')


def final_db_touches(conn):
    run_aux_inserts(conn)
    conn.execute('ALTER TABLE public.spatial_ref_sys ALTER COLUMN srid SET DEFAULT 4326;')


if dbquery.tableExists('profile') and (dbquery.getValueFromDb('select count(1) from profile') == 0):
    final_db_touches(dbquery.getEngine())


class ProcessUploadProjectData:
    import zipfile
    import shutil
    import geopandas as gpd
    from pathlib import Path
    import io
    import xmltodict

    def __init__(self, projecteZip):
        self.projecteZip = projecteZip
        self.pla_files_path = \
            f"{app_object.app.root_path}{os.path.sep}{app_object.app.config['PLA_FILES_DEST']}" \
            f"{os.sep}{self.projecteZip.pdf_fname.replace(' ', '_').replace('.pdf', '')}"
        self.projecteZip.pdf_fname = f"{self.pla_files_path}{os.sep}{self.projecteZip.pdf_fname.replace(' ', '_')}"
        self.file_contents = {}
        self.file_contents['camins'] = self.projecteZip.camins_blob
        self.file_contents['canvi_us'] = self.projecteZip.canvi_us_blob
        self.file_contents['infraestructures_incedis'] = self.projecteZip.infraestructures_incedis_blob
        self.file_contents['unitats_actuacio'] = self.projecteZip.unitats_actuacio_blob
        self.file_contents['usos_vege'] = self.projecteZip.usos_vege_blob
        self.file_contents['informacio_addicional'] = self.projecteZip.informacio_addicional_blob

        session_factory = sessionmaker(supportEngine)
        self.session = scoped_session(session_factory)
        self.XMLDataRoot = None
        self.Pla = None
        self.Forest = None
        self.actuacio_ids = {
            'LineasDefensaPuntsAigua': {
                'LD': {'P': 77, 'E': 78},
                'PA': {'P': 75, 'E': 76}},
            'XarxaNovaConstruccio': {'PR': 65, 'PM': 67, 'SC': 69, 'DB': 71},
            'XarxaViariaExistent': {'PR': 65, 'PM': 67, 'SC': 69, 'DB': 71},
            'CanviUs': {'TP': 85, 'RM': 87}
        }

    def isDict(self, obj):
        return type(obj) == dict or type(obj) == OrderedDict

    def toInt(self, data: dict, key: str) -> int:
        if not key in data:
            return sql.null()
        value = data[key]
        if isinstance(value, str):
            p = value.find('.')
            if p > -1:
                value = value[:p]
            return int(value)
        else:
            return sql.null()

    def toFloat(self, value, default=0.0) -> float:
        if isinstance(value, str):
            try:
                ret = float(value)
            except:
                return default
            return ret
        return default

    def sumValues(self, values: list) -> float:
        sum: float = 0.0
        for value in values:
            sum += float(value) if not (value is None) else 0.0
        return sum

    class converts:
        def __init__(self, row):
            self.row = dict(row)

        def getInt(self, field: str):
            value = self.getValue(field)
            if isinstance(value, str):
                p = value.find('.')
                if p > -1:
                    value = value[:p]
                return int(value)
            else:
                return sql.null()

        def getFloat(self, field: str, default=sql.null()):
            value = self.getValue(field)
            if isinstance(value, str):
                return float(value.replace(',', '.'))
            else:
                return default

        def getValue(self, field: str):
            if field in self.row:
                return self.row[field]
            else:
                return sql.null()

        def getBoolean(self, field: str, default):
            if field in self.row:
                return self.row[field] == default
            else:
                return sql.null()

    def to_date_time(self, strDate) -> datetime:
        sep = '-' if strDate.find('-') > -1 else '/'
        x = [int(s) for s in strDate.split(sep)]
        if x[2] > 1000:
            if x[1] > 12:
                x = [x[1], x[0], x[2]]
            return datetime(int(x[2]), int(x[1]), int(x[0]))
        else:
            if x[1] > 12:
                x = [x[0], x[2], x[1]]
            return datetime(int(x[0]), int(x[1]), int(x[2]))

    def get_actuacio_id(self, tipus_infra: str, tipus_ep: str = '', table: str = '') -> int:
        if tipus_infra not in self.actuacio_ids[table].keys():
            return sql.null()
        else:
            table_data = self.actuacio_ids[table][tipus_infra]
            if type(table_data) is not dict:
                return table_data
            else:
                if tipus_ep not in table_data.keys():
                    return sql.null()
                else:
                    return table_data[tipus_ep]

    def getLlistatActuacionIdByTipusCodi(self, tipus_actuacio: int, codi: str) -> int:
        try:
            return self.session.query(dm.LlistatActuacion).filter(
                and_(dm.LlistatActuacion.tipus_actuacio == tipus_actuacio,
                     dm.LlistatActuacion.codi == codi)).first().id
        except:
            return sql.null()

    def getTipusInvetari(self, acronym: str):
        try:
            return self.session.query(dm.TipusInventari).filter(
                dm.TipusInventari.acronym == acronym).first().id
        except:
            return sql.null()

    def mergeRodalData(self, toMerge: list) -> dict:
        merged = {}
        for toMergeData, toMergeIdFieldName in toMerge:
            for item in toMergeData:
                for ikey, ivalue in item.items():
                    if ikey == toMergeIdFieldName:
                        idRodal = item[toMergeIdFieldName]
                        if idRodal not in merged.keys():
                            merged[idRodal] = {}
                    else:
                        if isinstance(ivalue, dict):
                            for jkey, jvalue in ivalue.items():
                                merged[idRodal][jkey] = jvalue
                        else:
                            merged[idRodal][ikey] = ivalue
        return merged

    def mergeForestData(self, data: list) -> dict:
        merged = {}
        for item in data:
            try:
                if item[0][item[1]] not in merged.keys():
                    merged[item[0][item[1]]] = {}
                for key, value in item[0].items():
                    if key != item[1]:
                        merged[item[0][item[1]]][key] = value
            except:
                pass
        return merged

    def renameFiles(self, path, shp_name):
        filenames = glob(f"{path}*.*", recursive=True)  # include .
        lastname = filenames[0][:filenames[0].find('.') + 1].split('/')[-1:][0]
        for filename in filenames:
            newname = filename.replace(lastname, f"{shp_name}.")
            if newname != filename:
                subprocess.call(["mv", filename, newname])

    def unpackData(self):
        if os.path.exists(self.pla_files_path):
            self.shutil.rmtree(self.pla_files_path)
        os.makedirs(self.pla_files_path)
        # write blobs on disk
        with open(self.projecteZip.pdf_fname, 'wb') as f:
            f.write(self.projecteZip.pdf_blob)
        for shp_name in self.file_contents.keys():
            if self.file_contents[shp_name] is not None:
                path = f"{self.pla_files_path}{os.sep}{shp_name}{os.sep}"
                os.mkdir(path)
                zip_name = f"{path}{shp_name}.zip"
                with open(zip_name, 'wb') as f:
                    f.write(self.file_contents[shp_name])
                with self.zipfile.ZipFile(zip_name, 'r') as zip_ref:
                    zip_ref.extractall(path)
                self.renameFiles(path, shp_name)

    def importShp(self):
        dbquery.executeSQL('delete from import_shp_polygons')
        dbquery.executeSQL('delete from import_shp_lines')
        shpfiles = glob(f"{self.pla_files_path}{os.sep}**{os.sep}*.shp", recursive=True)
        for shpfile in shpfiles:
            df = self.gpd.read_file(shpfile)
            df = df.to_crs("EPSG:4326")
            df.rename(columns={df.columns[0]: 'field1'}, inplace=True)
            if len(df.columns) >= 3:
                df.rename(columns={df.columns[1]: 'field2'}, inplace=True)
                df = df[['field1', 'field2', 'geometry']]
            else:
                df = df[['field1', 'geometry']]
            df['data_type'] = self.Path(shpfile).stem
            df['pla_id'] = self.Pla.id
            if (df.geom_type[0]) == "LineString":
                df.to_postgis(dm.ImportShpLines.__tablename__, supportEngine, if_exists='append')
            else:
                df.to_postgis(dm.ImportShpPolygons.__tablename__, supportEngine, if_exists='append')

    def checkIsUpdateAndClean(self, plaNom, plaVigencia):
        if self.session.query(dm.Pla).filter(dm.Pla.nom == plaNom,
                                             dm.Pla.vigencia == self.to_date_time(plaVigencia)).count() > 0:
            Pla = self.session.query(dm.Pla).filter(dm.Pla.nom == plaNom,
                                                    dm.Pla.vigencia == self.to_date_time(plaVigencia)).first()
            self.session.query(dm.Pla).filter(dm.Pla.id == Pla.id).delete()
            self.session.flush()

    def mergeForests(self, data: list) -> dict:
        merged = {}
        for item in data:
            if item[0][item[1]] not in merged.keys():
                merged[item[0][item[1]]] = {}
            for key, value in item[0].items():
                if key != item[1]:
                    merged[item[0][item[1]]][key] = value
        return merged

    def insertAnyActuacio(self, actuacions_del_pla_id, any_o_priodicitat):
        if any_o_priodicitat < 2000:
            for year in range(self.Pla.any_del_pla, self.Pla.vigencia.year + 1, any_o_priodicitat):
                AnyActuacio = dm.AnyActuacio(actuacions_del_pla_id=actuacions_del_pla_id,
                                             any_programat=year)
                self.session.add(AnyActuacio)
        else:
            AnyActuacio = dm.AnyActuacio(actuacions_del_pla_id=actuacions_del_pla_id,
                                         any_programat=any_o_priodicitat)
            self.session.add(AnyActuacio)
        self.session.flush()

    def importForestPla(self):
        plaData = dict(self.XMLDataRoot['DadesPortadaPlaPSGF'])

        # Forest

        IdentFincas = dict(self.XMLDataRoot['DadesGeneralsFinca']['DadesIdentFinca'])['LlistaIdentFinca']
        InfoFincas = dict(self.XMLDataRoot['DadesGeneralsFinca']['DadesInfoFinca'])['LlistaInfoFinca']

        fincas = self.mergeForestData([[IdentFincas, 'IdFNomFincaPla'],
                                       [InfoFincas, 'FINomFincaPla']])
        for nom, forest in fincas.items():
            if self.isDict(forest):
                vc = self.converts(forest)
                self.Forest = dm.Forest(
                    forest_nom=nom,
                    municipi=vc.getValue('IdFMunicipiFinca'),
                    superficie_ha=vc.getFloat('IdFIdSuperficie')
                )
            self.session.add(self.Forest)
            self.session.flush()

        # Pla
        DadesDescripcioModelGestio = self.converts(dict(self.XMLDataRoot['DadesDescripcioModelGestio']))
        InfoFinca = dict(self.XMLDataRoot['DadesGeneralsFinca']['DadesInfoFinca'])
        if self.isDict(InfoFinca):
            DadesInfoFinca = self.converts(InfoFinca)
            superficie_total = \
                DadesInfoFinca.getFloat('FISuperficieArbrada', 0.0) + \
                DadesInfoFinca.getFloat('FISuperficieNOArbrada', 0.0)
            self.Pla = dm.Pla(tipus_de_pla='PTGMF',
                              numero_expediente=self.projecteZip.numero_expediente,
                              any_del_pla=self.projecteZip.any_del_pla,
                              nom=plaData['NomPortadaPSGF'], municipi=plaData['MunicipiPortadaPSGF'],
                              comarca=plaData['ComarcaPortadaPSGF'],
                              vigencia=self.to_date_time(plaData['VigenciaPortadaPSGF']),
                              dens_camins_principals=DadesDescripcioModelGestio.getFloat('DensCaminsPR'),
                              dens_camins_primaris=DadesDescripcioModelGestio.getFloat('DensCaminsPM'),
                              dens_camins_secundaris=DadesDescripcioModelGestio.getFloat('DensCaminsSC'),
                              dens_camins_desembosc=DadesDescripcioModelGestio.getFloat('DensCaminsDB'),
                              dens_total_camins=DadesDescripcioModelGestio.getFloat('DensCaminsTOTAL'),
                              long_camins_principals=DadesDescripcioModelGestio.getFloat('LongCaminsPR'),
                              long_camins_primaris=DadesDescripcioModelGestio.getFloat('LongCaminsPM'),
                              long_camins_secundaris=DadesDescripcioModelGestio.getFloat('DensCaminsSC'),
                              long_camins_desembosc=DadesDescripcioModelGestio.getFloat('LongCaminsDB'),
                              long_total_camins=DadesDescripcioModelGestio.getFloat('LongCaminsTOTAL'),
                              info_complement_camins_existents=DadesDescripcioModelGestio.getValue('DescInfoComp1'),
                              info_complement_camins_nous=DadesDescripcioModelGestio.getValue('DescInfoComp2'),
                              info_complement_r_om_p__pastures=DadesDescripcioModelGestio.getValue('DescInfoComp3'),
                              info_complement_r_om_p__puntsaigua=DadesDescripcioModelGestio.getValue('DescInfoComp4'),
                              superficie_total=superficie_total,
                              superficie_ordenada=DadesInfoFinca.getFloat('FISuperficieOrdenada'),
                              superficie_no_ordenada=DadesInfoFinca.getFloat('FISuperficieNOOrdenada'),
                              superficie_forestal=DadesInfoFinca.getFloat('FISuperficieForestal'),
                              superficie_no_forestal=DadesInfoFinca.getFloat('FISuperficieNOForestal'),
                              superficie_arbrada=DadesInfoFinca.getFloat('FISuperficieArbrada'),
                              superficie_no_arbrada=DadesInfoFinca.getFloat('FISuperficieNOArbrada')
                              )

            self.session.add(self.Pla)
            self.session.flush()
        if not self.Forest is None:
            self.Forest.pla_id = self.Pla.id
        self.session.commit()

    def updatePlaWithRodalData(self):
        with supportEngine.connect() as conn:
            conn.execute(
                f'''update pla set superficie_forestal = b.superficie_forestal,
		       superficie_arbrada = b.superficie_arbrada, 
		       superficie_ordenada = b.superficie_ordenada,
		       superficie_no_arbrada = b.superficie_forestal - b.superficie_arbrada
from 
(select pla_id, sum(superficie_forestal) as superficie_forestal, 
sum(superficie_arbrada) as superficie_arbrada,sum(superficie_ordenada) as superficie_ordenada
from rodal
where pla_id = {self.Pla.id}
group by pla_id) b
where pla.id = b.pla_id''')

    def importRodals(self):
        # Rodal
        objectiusPreferents = dict(self.XMLDataRoot['DadesDescripcioForest']['ResumObjectiusPreferents'])[
            'LlistaResumObjectiusPreferents']
        modelGestio = dict(dict(self.XMLDataRoot['DadesDescripcioModelGestio'])['ResumModelGestio'])[
            'LlistaResumModelsGestio']
        rodalInfo = dict(dict(self.XMLDataRoot['DadesDescripcioRodals'])['LlistaGeneralRodal'])[
            'LlistaGeneralRodalInfo']
        detallRodalInfo = dict(dict(self.XMLDataRoot['DadesDescripcioRodals'])['FitxaDescriptivaRodal'])[
            'FDDetallRodalInfo']
        rodals = self.mergeRodalData([[objectiusPreferents, 'RMOPIdRodal'],
                                      [modelGestio, 'RMGIdRodal'],
                                      [rodalInfo, 'IdRodal'],
                                      [detallRodalInfo, 'IdRodal']])
        try:
            for num_rodal, rodal in rodals.items():
                vc = self.converts(rodal)
                if 'FDRodalEstructuraMassa' in rodal:
                    inventari = self.converts(rodal['FDRodalEstructuraMassa'])
                else:
                    inventari = None

                Rodal = dm.Rodal(pla_id=self.Pla.id,
                                 forest_id=self.Forest.id,
                                 num_rodal=num_rodal,
                                 objectiu_general=vc.getValue('RMOPTipusDesc'),
                                 objectiu_preferent=vc.getValue('RMOPDesc'),
                                 formacion_forestal=vc.getValue('RMGFFDesc'),
                                 especie=vc.getValue('FFEspecieRodal'),
                                 orgest=vc.getValue('FFOrgestRodal'),
                                 qualitat_estacio_id=vc.getValue('QERodal'),
                                 vulnerabilitat_id=vc.getValue('Vulnerabilitat'),
                                 superficie_ordenada=vc.getValue('SupOrdenada'),
                                 superficie_forestal=vc.getValue('SupForestal'),
                                 superficie_arbrada=vc.getValue('SupArbrada'),
                                 codi_form_forestal=vc.getValue('FFOrgestRodal'),
                                 superficie_especial=vc.getFloat('SupEspecial'),
                                 descriptio_objectiu=vc.getValue('PlanifObjectiuDescInicial'),
                                 descriptio_model_gestio=vc.getValue('PlanifPPalModelGestioDescPura'),
                                 descriptio_itinerari_silvicola=vc.getValue('PlanifPPalItinerariSilvicola')
                                 )
                self.session.add(Rodal)
                self.session.flush()
                self.session.commit()
                self.updatePlaWithRodalData()
                try:
                    if inventari != None:
                        FDRodalEMEspInfo = rodal['FDRodalEstructuraMassa']['InfoEstructuraRodal']['FDRodalEMEspInfo']
                        if type(FDRodalEMEspInfo) != list:
                            FDRodalEMEspInfo = [FDRodalEMEspInfo]
                        for rif in FDRodalEMEspInfo:
                            resultats_inventari_fusta = self.converts(rif)
                            ResultatsInventariFusta = dm.ResultatsInventariFusta(
                                rodal_id=Rodal.id,
                                especies_id=resultats_inventari_fusta.getValue('FormArbEspecieRodal'),
                                n_peusperha=resultats_inventari_fusta.getValue('FormArbDensitatRodal'),
                                fcc=resultats_inventari_fusta.getValue('FormArbFccRodal'),
                                d_m=resultats_inventari_fusta.getValue('FormArbDmRodal'),
                                h_m=resultats_inventari_fusta.getValue('FormArbHmRodal'),
                                edat=resultats_inventari_fusta.getValue('FormArbEdatRodal'),
                                a_b=resultats_inventari_fusta.getValue('FormArbABRodal'),
                                vol=resultats_inventari_fusta.getValue('FormArbVolumRodal')
                            )
                            self.session.add(ResultatsInventariFusta)
                        resum_inventari_fusta = self.converts(rodal['FDRodalEstructuraMassa']['InfoEstructuraRodal'])
                        ResumInventariFusta = dm.ResumInventariFusta(
                                rodal_id=Rodal.id,
                                tipus_inventari_id=self.getTipusInvetari(inventari.getValue('TipusInventariRodal')),
                                forma_principal=inventari.getValue('FormaRodal'),
                                n_peus_ha=resum_inventari_fusta.getFloat('FormArbSumDensitatRodal'),
                                ab=resum_inventari_fusta.getFloat('FormArbSumABRodal'),
                                vol=resum_inventari_fusta.getFloat('FormArbSumVolumRodal'),
                                distribucioespaial=inventari.getValue('DistribucioRodal'),
                                composicioespecifica=inventari.getValue('ComposicioRodal'),
                                observacionsinventari=inventari.getValue('ObsDasPerAltres')
                        )
                        self.session.add(ResumInventariFusta)

                        TipusDasometric = self.converts(inventari.getValue('InfoTipusDasometric'))
                        FDRodalTipusDasometricInfos = TipusDasometric.getValue('FDRodalTipusDasometricInfo')
                        if not (type(FDRodalTipusDasometricInfos) == list):
                            FDRodalTipusDasometricInfos = [FDRodalTipusDasometricInfos]
                        i = 1
                        for FDRodalTipusDasometricInfo in FDRodalTipusDasometricInfos:
                            while f'FDRTDTitol{i}' in TipusDasometric.row.keys():
                                InventariCd = dm.InventariCd(
                                    rodal_id=Rodal.id,
                                    c_d=TipusDasometric.getInt(f'FDRTDTitol{i}'),
                                    especies_id=self.toInt(FDRodalTipusDasometricInfo, 'FDRTDEspecieId'),
                                    npeus=self.toInt(FDRodalTipusDasometricInfo, f'FDRTPCol{i}'),
                                    a_b=TipusDasometric.getFloat(f'FDRTDAB{i}')
                                )
                                self.session.add(InventariCd)
                                i += 1
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)
        self.session.flush()
        self.session.commit()

    def importXarxas(self):
        #  XarxaNovaConstruccio
        InfraestructuraNOUEPs = \
            dict(dict(self.XMLDataRoot['DadesDescripcioModelGestio']['DadesInfraestructuresCaminsNOU'])[
                     'LlistaInfraestructuresNOUEP'])[
                'InfraestructuraNOUEP']
        for InfraestructuraNOUEP in InfraestructuraNOUEPs:
            if self.isDict(InfraestructuraNOUEP):
                vc = self.converts(InfraestructuraNOUEP)
                XarxaNovaConstruccio = dm.XarxaNovaConstruccio(
                    pla_id=self.Pla.id,
                    codi=vc.getValue('IdInfra'),
                    tipus=vc.getValue('TipusInfra'),
                    longidud=vc.getValue('AmidamentInfra'),
                    any_o_periodicitat=vc.getValue('AnyInfra'),
                    actuacio_id=self.get_actuacio_id(vc.getValue('TipusInfra'), table='XarxaNovaConstruccio'))
                self.session.add(XarxaNovaConstruccio)
        self.session.flush()

        #  XarxaViariaExistent
        InfraestructuraEXEPs = \
            dict(dict(self.XMLDataRoot['DadesDescripcioModelGestio']['DadesInfraestructuresCaminsEX'])[
                     'LlistaInfraestructuresEXEP'])[
                'InfraestructuraEXEP']
        for InfraestructuraEXEP in InfraestructuraEXEPs:
            if self.isDict(InfraestructuraEXEP):
                vc = self.converts(InfraestructuraEXEP)
                XarxaViariaExistent = dm.XarxaViariaExistent(pla_id=self.Pla.id,
                                                             codi=vc.getValue('IdInfra'),
                                                             tipus=vc.getValue('TipusInfra'),
                                                             longidud=vc.getValue('AmidamentInfra'),
                                                             any_o_periodicitat=vc.getValue('AnyInfra'),
                                                             actuacio_id=self.get_actuacio_id(vc.getValue('TipusInfra'),
                                                                                              table='XarxaViariaExistent'))
                self.session.add(XarxaViariaExistent)
        self.session.flush()

    def imporLineasDefensaPuntsAigua(self):
        InfraestructuraEPDEPUs = \
            dict(dict(self.XMLDataRoot['DadesDescripcioModelGestio']['DadesInfraestructuresDEPU'])[
                     'LlistaInfraestructuresDEPU'])[
                'InfraestructuraEPDEPU']
        for InfraestructuraEPDEPU in InfraestructuraEPDEPUs:
            if self.isDict(InfraestructuraEPDEPU):
                vc = self.converts(InfraestructuraEPDEPU)
                codi = vc.getValue('IdInfra')
                LineasDefensaPuntsAigua = dm.LineasDefensaPuntsAigua(
                    pla_id=self.Pla.id,
                    codi=codi,
                    llistat_actuacions_id=self.get_actuacio_id(
                        vc.getValue('TipusInfra'), vc.getValue('TipusEP'), 'LineasDefensaPuntsAigua'),
                    amidament=vc.getFloat('AmidamentInfra'),
                    any_o_periodicitat=vc.getValue('AnyInfra'),
                    tipus_est_prev=vc.getValue('TipusEP'),
                    tipus=vc.getValue('TipusInfra'),
                    observacions=vc.getValue('ObservacionsInfra')
                )
                self.session.add(LineasDefensaPuntsAigua)
        self.session.flush()

    def importCanviUs(self):
        InfraestructuraEPROPAs = \
            dict(dict(self.XMLDataRoot['DadesDescripcioModelGestio']['DadesInfraestructuresROPA'])[
                     'LlistaInfraestructuresROPA'])[
                'InfraestructuraEPROPA']
        try:
            for InfraestructuraEPROPA in InfraestructuraEPROPAs:
                if self.isDict(InfraestructuraEPROPA):
                    vc = self.converts(InfraestructuraEPROPA)
                    codi = vc.getValue('IdInfra')
                    CanviUs = dm.CanviUs(pla_id=self.Pla.id,
                                         codi=codi,
                                         tipus=codi[:2],
                                         llistat_actuacions_id=self.get_actuacio_id(
                                             vc.getValue('TipusInfra'), table='CanviUs'),
                                         amidament=vc.getFloat('AmidamentInfra'),
                                         ani_o_periodicidat=vc.getFloat('AnyInfra'),
                                         observacions=vc.getValue('ObservacionsInfra')
                                         )
                    self.session.add(CanviUs)
            self.session.flush()
        except:
            pass

    def importPropietariDade(self):
        DadesPropietari = \
            dict(dict(self.XMLDataRoot['DadesGeneralsFinca']['LlistaPropietaris']))['DadesPropietari']
        if type(DadesPropietari) != list:
            DadesPropietari = [DadesPropietari]
        for proprietari in DadesPropietari:
            if self.isDict(proprietari):
                vc = self.converts(proprietari)
                PropietariDade = dm.PropietariDade(
                    pla_id=self.Pla.id,
                    tipus=vc.getValue('TipusPropietari'),
                    d_ni=vc.getValue('DNIPropietari'),
                    nom=vc.getValue('NomPropietari'),
                    primer_cognom=vc.getValue('Cognom1Propietari'),
                    segon_cognom=vc.getValue('Cognom2Propietari'),
                    adreca=vc.getValue('adreca'),
                    municipi=vc.getValue('MunicipiPropietari'),
                    cp=vc.getValue('CPPropietari'),
                    telef_1=vc.getValue('Tfn1Propietari'),
                    telef_2=vc.getValue('Tfn2Propietari'),
                    email=vc.getValue('EmailPropietari')
                )
                self.session.add(PropietariDade)
        self.session.flush()

    def importInfoComplementariaPla(self):
        InfoComplementariaPla = \
            dict(self.XMLDataRoot['DadesDescripcioForest'])
        if self.isDict(InfoComplementariaPla):
            vc = self.converts(InfoComplementariaPla)
            InfoComplementariaPla = dm.InfoComplementariaPla(
                pla_id=self.Pla.id,
                activitat_cinegetica=vc.getValue('DescCinegetica'),
                tipus_de_bestiar=vc.getValue('TipusBestiar'),
                numero_de_caps=vc.getFloat('NumCapsBestiar'),
                observacions_ramaderia=vc.getValue('DescExtensiva'),
                info_complementaria_pla=vc.getValue('DescComplementaria'),
                antecedents_gestio=vc.getValue('AntecedentsGestio')
            )
            self.session.add(InfoComplementariaPla)
        self.session.flush()

    def importPersonaDeContacte(self):
        PersonaDeContacteData = \
            dict(self.XMLDataRoot['DadesGeneralsFinca']['PersonaContacte'])
        if self.isDict(PersonaDeContacteData):
            vc = self.converts(PersonaDeContacteData)
            dniProprietari = vc.getValue('DNIPropietari')
            PersonaDeContacte = self.session.query(dm.PersonaDeContacte).filter(
                dm.PersonaDeContacte.dni == dniProprietari).first()
            if PersonaDeContacte is None:
                PersonaDeContacte = dm.PersonaDeContacte(
                    dni=vc.getValue('DNIPropietari'),
                    nom=vc.getValue('NomPropietari'),
                    primer_cognom=vc.getValue('Cognom1Propietari'),
                    segon_cognom=vc.getValue('Cognom2Propietari'),
                    adreca=vc.getValue('AdrecaPropietari'),
                    municipi=vc.getValue('NomPropietari'),
                    cp=vc.getValue('CPPropietari'),
                    email=vc.getValue('EmailPropietari'),
                    telef1=vc.getValue('Tfn1Propietari'),
                    telef2=vc.getValue('Tfn2Propietari')
                )
                self.session.add(PersonaDeContacte)
            self.session.commit()
        PlaPersContact = self.session.query(dm.PlaPersContact).filter(
            and_(dm.PlaPersContact.pla_id == self.Pla.id,
                 dm.PlaPersContact.persona_de_contacte_id == PersonaDeContacte.id)).first()
        if PlaPersContact is None:
            PlaPersContact = dm.PlaPersContact(
                pla_id=self.Pla.id,
                persona_de_contacte_id=PersonaDeContacte.id
            )
            self.session.add(PlaPersContact)

    def importActuacionsDelPla(self):
        DadesDescripcioProgramesActs = dict(self.XMLDataRoot['DadesDescripcioProgramesAct']['ResumProgramesActProg'])[
            'LlistaResumProgramesAct']
        for DadesDescripcioProgramesAct in DadesDescripcioProgramesActs:
                if self.isDict(DadesDescripcioProgramesAct):
                    vc = self.converts(DadesDescripcioProgramesAct)
                    rodal = self.session.query(dm.Rodal).filter(
                        and_(dm.Rodal.pla_id == self.Pla.id,
                             dm.Rodal.num_rodal == vc.getValue('RPAIdRodal'))).first()
                    if rodal is None:
                        continue
                    try:
                        actuacio_id = self.session.query(dm.LlistatActuacion).filter(
                            dm.LlistatActuacion.actuacions_ptgmf_id == vc.getValue('RPARodalCodiActuacio')).first().id
                    except:
                        actuacio_id = None
                    ActuacionsDelPla = dm.ActuacionsDelPla(
                        rodal_id=rodal.id,
                        actuacio_id=actuacio_id,
                        area_afectada=vc.getFloat('RPARodalAmidament'),
                        any_o_periodicitat=vc.getInt('RPARodalAnyActuacio'),
                        notificacio=vc.getBoolean('RPARodalNotificacio', 'S'),
                        observacions_actuacio=vc.getValue('RPARodalAnyActuacio')  # ?
                    )
                    self.session.add(ActuacionsDelPla)
                    self.session.flush()
                    self.insertAnyActuacio(ActuacionsDelPla.id, ActuacionsDelPla.any_o_periodicitat)
        self.session.commit()

    def mergeGeometry2Data(self):
        with supportEngine.connect() as conn:
            for shp_name in self.file_contents.keys():
                if shp_name != 'informacio_addicional':
                    conn.execute(merge_sqls[shp_name].format(self.Pla.id))

    def importXML(self):
        with self.io.open(f'{self.projecteZip.pdf_fname.replace(".pdf", ".xml")}', mode="r",
                          encoding="utf-8") as f:
            s = f.read()
            doc = self.xmltodict.parse(s, encoding='utf-8')
        self.XMLDataRoot = doc['xfa:datasets']['xfa:data']['GSIT_PICA_GRO_SOLLICITUD']['Cos']['Contingut'][
            'DadesParticulars']

        self.checkIsUpdateAndClean(dict(self.XMLDataRoot['DadesPortadaPlaPSGF'])['NomPortadaPSGF'],
                                   dict(self.XMLDataRoot['DadesPortadaPlaPSGF'])['VigenciaPortadaPSGF'])
        self.importForestPla()
        self.importRodals()
        self.importXarxas()
        self.imporLineasDefensaPuntsAigua()
        self.importCanviUs()
        self.importPropietariDade()
        self.importInfoComplementariaPla()
        self.importPersonaDeContacte()
        self.importActuacionsDelPla()
        self.session.commit()

    def PDF2XMLWine(self):
        pdffilename = self.projecteZip.pdf_fname
        shell_command = "{0}{1}{2}exe{2}PDF2XML{2}PDF2XML.exe {3} {4}".format(
            'wine ' if os.name == 'posix' else '',
            app_object.app.root_path, os.sep, pdffilename,
            pdfPassword)
        subprocess.call(shell_command.split())

    def PDF2XMLJava(self):
        pdffilename = self.projecteZip.pdf_fname
        # ~/Atrium/CTFC/psgf/pdf2xml$ java -cp "./:./repository/*" Pdf2Xml ../pla_files/Solsones/Solsones.pdf Artemis_76
        pdf2xmlpath = f"{app_object.app.root_path}{os.sep}pdf2xml"
        shell_command = f'java -cp ./:./repository/* Pdf2Xml  {pdffilename} {pdfPassword}'
        subprocess.call(shell_command.split(), cwd=pdf2xmlpath)

    def removeImportedFiles(self):
        subprocess.call(["rm", "-rf", self.pla_files_path])

    def process(self):
        self.unpackData()
        self.PDF2XMLJava()
        self.importXML()
        self.importShp()
        self.mergeGeometry2Data()

