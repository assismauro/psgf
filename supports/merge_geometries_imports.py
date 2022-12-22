merge_sqls = {
    'unitats_actuacio':
"""update rodal set geometry = a.geometry, area = a.area
from
(
 select field1 as num_rodal, st_multi(st_union(geometry)) as geometry, 
        round((st_area(st_multi(st_union(geometry))::geography)/10000)::numeric,2) as area
 from import_shp_polygons 
 where data_type  = 'unitats_actuacio'
 and field1 is not null
 group by data_type, field1 
) a
where rodal.num_rodal = a.num_rodal
and pla_id = {0}""",

    'camins':
"""update xarxa_nova_construccio set geometry = a.geometry
from
(
 select field1 as codi, st_multi(st_union(geometry)) as geometry
 from import_shp_lines
 where data_type  = 'camins'
 and field1 is not null
 and field1 like '%%P'
 group by data_type, field1 
) a
where xarxa_nova_construccio.codi = a.codi
and pla_id = {0};

update xarxa_viaria_existent set geometry = a.geometry
from
(
 select field1 as codi, st_multi(st_union(geometry)) as geometry
 from import_shp_lines
 where data_type  = 'camins'
 and field1 is not null
 and field1 like '%%E'
 group by data_type, field1 
) a
where xarxa_viaria_existent.codi = a.codi
and pla_id = {0}""",

    'infraestructures_incedis':
        """
        update lineas_defensa_punts_aigua set geometry = a.geometry
        from
        (
         select field1 as codi, st_multi(st_union(geometry)) as geometry
         from import_shp_polygons
         where data_type  = 'infraestructures_incedis'
         and field1 is not null
         group by data_type, field1 
        ) a
        where lineas_defensa_punts_aigua.codi = a.codi
        and pla_id = {0}""",

    'canvi_us':
        """
        update canvi_us set geometry = a.geometry
        from
        (
         select field1 as codi, st_multi(st_union(geometry)) as geometry
         from import_shp_polygons
         where data_type  = 'canvi_us'
         and field1 is not null
         group by data_type, field1 
        ) a
        where canvi_us.codi = a.codi
        and pla_id = {0}""",

    'usos_vege':
        """
        INSERT INTO usos_vege (pla_id, data_type, field1, field2, geometry) 
        select pla_id, data_type, field1, field2, geometry 
        from import_shp_polygons
        where data_type  = 'usos_vege'
        and pla_id = {0}"""
}