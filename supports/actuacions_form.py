# https://towardsdatascience.com/how-to-create-outstanding-custom-choropleth-maps-with-plotly-and-dash-49ac918a5f05
# https://plotly.com/python/table/
# About hover labels:
# https://plotly.com/python/hover-text-and-formatting/
# https://plotly.com/python/reference/?_ga=2.135691057.1478852968.1662893046-231659727.1654351901#scatter-hovertemplate
import os
import plotly
import plotly.express as px
import json
import openpyxl

from flask_login import current_user

import supports.dbquery as dbquery
from flask_admin import BaseView, expose

import plotly.graph_objects as go
import numpy as np
from datetime import datetime

maxnomlength = 30

def breakString(mystring):
    longi = len(mystring)
    s = mystring[0]
    for i in range(1, longi):
        if i % maxnomlength == 0:
            position = s.rfind(' ') + (i % maxnomlength) * len('br')
            s = s[:position] + '<br>' + s[position + 1:]
        else:
            s += mystring[i]
    return s


class actuacionsView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/actuacions.html', plas=getPlas(), years=getYears(), opacities=getOpacities())

    def is_accessible(self):
        return dbquery.isAdministrator(current_user)


def getPlas():
    return dbquery.getDictResultset(
        f"select id, nom from " 
        f"(select 0 as id, '(Totes els plans)' as nom "
        f"union select id,nom from pla) a "
        f"order by nom")

def getYears():
    return dbquery.getDictResultset("select distinct any_programat, any_programat "
                                    "from any_actuacio order by any_programat")


def getOpacities():
    return dbquery.getDictResultset("SELECT generate_series(1,10) as id, concat(cast(generate_series(1,10) * 10 "
                                    "as varchar), '%') as value")


def getAreas(pla_id, startyear, endyear):
    if_pla = f"and pla_id = {pla_id}    " if pla_id != 0 else ""
    df = dbquery.getDataframeResultSet(
        f"select  id, num_rodal "
        f"from rodal where geometry is not null "
        f"and id in (select distinct rodal_id from actuacions_del_pla adp "
        f"inner join any_actuacio aa "
        f"on adp.id = aa.actuacions_del_pla_id "
        f"where any_programat between {startyear} and {endyear}) {if_pla} ")

    gjson = dbquery.getJSONResultset(
        f"select json_build_object('type', 'FeatureCollection','features', json_agg(ST_AsGeoJSON(t.*)::json)) "
        f"from (select  id, num_rodal, geometry from rodal where geometry is not null {if_pla} "
        f"and id in (select distinct rodal_id from actuacions_del_pla adp "
        f"inner join any_actuacio aa "
        f"on adp.id = aa.actuacions_del_pla_id "
        f"where any_programat between {startyear} and {endyear})) "
        "as t(id, name, geometry)")

    centroid = dbquery.executeSQL(f"select st_x(centroid) as long,st_y(centroid) as lat from "
                                  f"(select st_centroid(st_union(geometry)) as centroid from rodal "
                                  f"where geometry is not null {if_pla} "
                                  f"and id in (select distinct rodal_id from actuacions_del_pla adp "
                                  f"inner join any_actuacio aa "
                                  f"on adp.id = aa.actuacions_del_pla_id "
                                  f"where any_programat between {startyear} and {endyear})"
                                  f") a ").first()


    extent = dbquery.executeSQL(f"select st_extent(geometry) from rodal "
                                f"where geometry is not null {if_pla} "
                                f"and id in (select distinct rodal_id from actuacions_del_pla adp "
                                f"inner join any_actuacio aa "
                                f"on adp.id = aa.actuacions_del_pla_id "
                                f"where any_programat between {startyear} and {endyear})"
                                ).first()
    if extent[0] is not None:
        values = extent[0].replace(',', ' ').replace('(', ' ').replace(')', ' ').split(' ')
        max_bound = max(abs(float(values[1]) - float(values[3])), abs(float(values[2]) - float(values[4]))) * 111
        zoom = 13.5 - np.log(max_bound)
    else:
        zoom = 13.5
    return df, gjson, {"lat": centroid[1], "lon": centroid[0]}, zoom

def getTableData(pla_id, startyear, endyear, actuacions):
    if_pla = f"and pla_id = '{pla_id}'" if pla_id != 0 else ""
    if actuacions == 'totes':
        return dbquery.getDataframeResultSet(
            f"select p.nom , num_rodal, actuacion, area_afectada, a.any_o_periodicitat, aa.any_programat "
            f"from actuacions a "
            f"inner join any_actuacio aa "
            f"on aa.actuacions_del_pla_id = a.id "
            f"inner join pla p "
            f"on a.pla_id = p.id "
            f"where any_programat between {startyear} and {endyear} {if_pla} "
            f"order by p.nom, num_rodal,actuacion, aa.any_programat")
    else:
        return dbquery.getDataframeResultSet(
            f"select p.nom, num_rodal, actuacion, area_afectada, a.any_o_periodicitat, min(aa.any_programat) "
            f"as any_programat "
            f"from actuacions a "
            f"inner join any_actuacio aa "
            f"on aa.actuacions_del_pla_id = a.id "
            f"inner join pla p "
            f"on a.pla_id = p.id "
            f"where any_programat between {startyear} and {endyear} {if_pla} "
            f"group by p.nom, num_rodal, actuacion, area_afectada, a.any_o_periodicitat "
            f"order by p.nom, num_rodal,actuacion, min(aa.any_programat)")


def getTable(pla_id, startyear, endyear, actuacions):
    df = getTableData(pla_id, startyear, endyear, actuacions)
    fig = go.Figure(data=[go.Table(
        columnwidth=[150, 25, 250, 30, 40, 40],
        header=dict(
            values=['Pla', 'Rodal', 'Actuació', 'Area', 'Any o Periodicitat', 'Any programat'],
            #line_color='darkslategray',
            fill_color='paleturquoise',
            align='left',
            font_size=12,
            height=40
        ),
        cells=dict(
            values=[df.nom, df.num_rodal, df.actuacion, df.area_afectada,
                    df.any_o_periodicitat,  df.any_programat],
            align='left',
            font_size=12,
            height=30)
    )
    ])
    return df, fig


def getFigAreas(pla_id, baselayer, startyear, endyear, actuacions, opacity):
    area, geo, centroid, zoom = getAreas(pla_id, startyear, endyear)

    fig = px.choropleth_mapbox(area, geojson=geo, color=area.id,
                               locations=area.id, featureidkey="properties.id",
                               center=centroid,
                               hover_name=area.num_rodal, hover_data={'id': False},
                               mapbox_style="carto-positron", zoom=zoom,
                               opacity=float(opacity)/10)
    if baselayer != 'orto':
        fig.update_layout(
            mapbox_style="open-street-map",
            mapbox_layers=[
                {
                    "below": 'traces',
                    "sourcetype": "raster"
                }
            ])
    else:
        fig.update_layout(
            mapbox_style="white-bg",
            mapbox_layers=[
                {
                    # https://www.icgc.cat/en/Innovation/Resources-for-developers/Services-for-APIs-and-Widgets
                    "below": 'traces',
                    "sourcetype": "raster",
                    "sourceattribution": "Institut Cartogràfic i Geològic de Catalunya",
                    "source": [
                         f"https://geoserveis.icgc.cat/icc_mapesmultibase/noutm/wmts/{baselayer}/GRID3857/{{z}}/{{x}}/{{y}}.jpeg"
                    ]
                }
            ])
    fig.update_layout(coloraxis_showscale=False)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    actuationsDf, actuationsJSON = getTable(pla_id, startyear, endyear, actuacions)
    tableJSON = json.dumps(actuationsJSON, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON, tableJSON

def createDownloadFile(pla_id, startyear, endyear, actuacions):
    df = getTableData(pla_id, startyear, endyear, actuacions)
    df.columns = ['Pla', 'Rodal', 'Actuació', 'Area', 'Any o Periodicitat', 'Any programat']
    fname = f"pgf_{datetime.now().strftime('%m_%d_%Y_%H%M%S')}.xlsx"
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    df.to_excel(f"downloads/{fname}", index=False)
    return fname



