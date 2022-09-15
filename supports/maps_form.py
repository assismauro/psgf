# https://towardsdatascience.com/how-to-create-outstanding-custom-choropleth-maps-with-plotly-and-dash-49ac918a5f05
import plotly
import plotly.express as px
import json
import numpy as np

from flask_login import current_user

import supports.dbquery as dbquery
from flask_admin import BaseView, expose
# mapbox_access_token = 'pk.eyJ1IjoiYXNzaXNtYXVybyIsImEiOiJja3RvcGt2eTgwZXc5Mm9taGd6MTltZ2o2In0.FJ2GqIssNuJxeYh0ewTpLw'

class mapView(BaseView):
    @expose('/')
    def index(self):
        plas = getPlas()
        classes = getAreasClasses()
        return self.render('admin/maps.html', plas=plas, classes=classes)

    def is_accessible(self):
        return dbquery.isAcessible(current_user, True)


def getPlas():
    return dbquery.getDictResultset("select id,nom from pla order by nom")


def getAreasClasses():
    classes = {'all': 'All'}
    classes.update(dbquery.getDictResultset("select distinct class, class from area order by class"))
    return classes


def getAreas(pla_id, classe):
    if_class = f"and class = '{classe}'" if classe != "all" else ""
    df = dbquery.getDataframeResultSet("select  id, name "
                               f"from area where pla_id = {pla_id} and geometry is not null {if_class}")

    gjson = dbquery.getJSONResultset(
        f"select json_build_object('type', 'FeatureCollection','features', json_agg(ST_AsGeoJSON(t.*)::json)) "
        f"from (select id, name, geometry from area where pla_id = {pla_id} and geometry is not null {if_class}) "
        "as t(id, name, geometry)")

    centroid = dbquery.executeSQL(
        f"select st_x(centroid) as long,st_y(centroid) as lat from "
        f"(select st_centroid(st_union(geometry)) as centroid from area where pla_id = {pla_id} {if_class}) a").first()

    extent = dbquery.executeSQL(f"select st_extent(geometry) from area where pla_id = {pla_id} {if_class}").first()
    if extent[0] != None:
        values = extent[0].replace(',', ' ').replace('(', ' ').replace(')', ' ').split(' ')
        max_bound = max(abs(float(values[1]) - float(values[3])), abs(float(values[2]) - float(values[4]))) * 111 # km/degree
        zoom = 13.5 - np.log(max_bound)
    else:
        zoom = 13.5

    return df, gjson, {"lat": centroid[1], "lon": centroid[0]}, zoom


def getFigAreas(pla_id, classe, baselayer):
    area, geo, centroid, zoom = getAreas(pla_id, classe)
    fig = px.choropleth_mapbox(area, geojson=geo, color=area.id,
                               locations=area.id, featureidkey="properties.id",
                               center=centroid,
                               hover_name=area.name, hover_data={'id': False},
                               mapbox_style="carto-positron", zoom=zoom)
    fig.update_layout(
        mapbox_style="white-bg",
        mapbox_layers=[
            {
                "below": 'traces',
                "sourcetype": "raster",
                "sourceattribution": "Institut Cartogràfic i Geològic de Catalunya",
                "source": [
                    # https://www.icgc.cat/en/Innovation/Resources-for-developers/Services-for-APIs-and-Widgets
                    f"https://geoserveis.icgc.cat/icc_mapesmultibase/noutm/wmts/{baselayer}/GRID3857/{{z}}/{{x}}/{{y}}.jpeg"
                ]
            }
        ])
    fig.update_layout(coloraxis_showscale=False)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON
