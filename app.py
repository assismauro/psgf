import io
from os import path
from flask import send_file, request, send_from_directory
from flask_migrate import Migrate
from logging.config import dictConfig
import supports.maps_form as maps_support
import supports.actuacions_form as actuacions_form
import json
import supports.queries_form as queries
import supports.app_object as app_object
import data_model
import data_view

app = app_object.app

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

try:
    from wtforms.fields.core import _unset_value as unset_value
except ImportError:
    from wtforms.utils import unset_value


@app.route('/callback/<endpoint>')
def callbacks(endpoint):
    args = request.args
    if endpoint == 'getMap':
        return json.dumps({'Map': maps_support.getFigAreas(args.get('pla_id'),
                                                           args.get('class'),
                                                           args.get('baselayer'),
                                                           args.get('opacity'))})
    elif endpoint == 'getQueryResult':
        return json.dumps({'Map': queries.getFigQuery(args.get('filter_value'))})
    elif endpoint == 'showActuacion':
        if args.get('download') == 'true':
            fname = actuacions_form.createDownloadFile(int(args.get('pla_id')),
                                                       args.get('startyear'),
                                                       args.get('endyear'),
                                                       args.get('actuacions'))
            return send_file(f"downloads/{fname}", mimetype='text/csv',
                             attachment_filename=f"downloads/{fname}",
                             as_attachment=True)
        else:
            _map, actuationsJSON = \
                actuacions_form.getFigAreas(int(args.get('pla_id')),
                                            args.get('baselayer'),
                                            args.get('startyear'),
                                            args.get('endyear'),
                                            args.get('actuacions'),
                                            args.get('opacity'))
            return json.dumps({'Map': _map,
                               #'Table': actuationsDF,
                               'TableJSON': actuationsJSON})


@app.route("/download/<int:id>", methods=['GET'])
def download_blob(id):
    projecteZip = data_model.ProjecteZip.query.get_or_404(id)
    return send_file(
        io.BytesIO(projecteZip.pdf_blob),
        as_attachment=True,
        attachment_filename=projecteZip.pdf_fname
    )


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


'''
@app.babel.localeselector
def getLocale():
    if request.args.get('lang'):
        app_object_support.db.session['lang'] = request.args.get('lang')
        return request.args.get('lang')
    else:
        return request.accept_languages.best_match(['en_US', 'es', 'ca'])
'''

migrate = Migrate()
data_view.addViews(app_object.admin)


def create_app():
    return app


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
