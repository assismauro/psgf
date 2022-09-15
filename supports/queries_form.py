import supports.dbquery as dbqs
from flask import session
from flask_admin import BaseView, expose
from flask_user import current_user
from plotly.utils import PlotlyJSONEncoder
import plotly.express as px
import json
import supports.app_object as app_object
import supports.categories as categories
import supports.dbquery as dbquery


class queryView(BaseView):
    @expose('/')
    def index(self):
        query_id=self.endpoint.split('/')[1]
        sql=f"SELECT id, nom, sql, categoria, nom_filtre, camp_filtre, sql_filtre " \
        f"FROM consultes where id = {query_id}"
        query = dbquery.getDataframeResultSet(sql)
        filter = dbquery.getDictResultset(query.sql_filtre.values[0])
        session['query_id'] = query_id
        return self.render(template='admin/query.html', filter=filter)

    def is_accessible(self):
        return dbquery.isAcessible(current_user, True)

def getQueryData(sql, filter, label):
    sql = sql.format(filter=filter)
    df = dbquery.getDataframeResultSet(sql)

    gjson = dbquery.getJSONResultset(
        f"select json_build_object('type', 'FeatureCollection','features', json_agg(ST_AsGeoJSON(t.*)::json)) "
        f"from ({sql})"
        f"as t(id, {label}, geometry)")

    centroid = dbquery.executeSQL(f"""	select st_x(centroid) as long,st_y(centroid) as lat from
    	(select st_centroid(st_union(geometry)) as centroid from ({sql}) a) b""").first()
    return df, gjson, {"lat": centroid[1], "lon": centroid[0]}


def getFigQuery(filter_value):
    query = dbquery.getDataframeResultSet(f"select * from consultes where id = {session['query_id']}").iloc[0]
    area, geo, centroid = getQueryData(query.sql, filter_value, query.etiqueta)
    fig = px.choropleth_mapbox(area, geojson=geo, color=area.id,
                               locations=area.id, featureidkey=f"properties.id",
                               center=centroid,
                               hover_name=area[query.etiqueta], hover_data={'id': False},
                               mapbox_style="carto-positron", zoom=12)
    fig.update_layout(
        mapbox_style="white-bg",
        mapbox_layers=[
            {
                "below": 'traces',
                "sourcetype": "raster",
                "sourceattribution": "Institut Cartogràfic i Geològic de Catalunya",
                "source": [
                    # https://www.icgc.cat/en/Innovation/Resources-for-developers/Services-for-APIs-and-Widgets
                    "https://geoserveis.icgc.cat/icc_mapesmultibase/noutm/wmts/topo/GRID3857/{z}/{x}/{y}.jpeg"
                ]
            }
        ])
    fig.update_layout(coloraxis_showscale=False)
    graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)
    return graphJSON

def addQueryViews(admin):
    queries = dbquery.getDataframeResultSet("select id, nom, nomes_administradors from consultes")
    for _, query in queries.iterrows():
        admin.add_view(queryView(name=query.nom, endpoint=f'queries/{query.id}', category=categories.Categories.category['Queries']))

if dbquery.tableExists('consultes'):
    addQueryViews(app_object.admin)

