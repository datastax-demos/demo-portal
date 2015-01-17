from flask import Flask
from flask.ext.mail import Mail

from DemoPortalFlask.logic.cassandracluster import CassandraCluster

from DemoPortalFlask.routes.admin import admin_api
from DemoPortalFlask.routes.authentication import authentication_api
from DemoPortalFlask.routes.dashboard import dashboard_api
from DemoPortalFlask.routes.pem import pem_api
from DemoPortalFlask.routes.topright import topright_api

app = Flask(__name__)
app.config.from_pyfile('application.cfg')

mail = Mail(app)
app.mail = Mail(app)
app.cluster = CassandraCluster(app)

app.register_blueprint(admin_api)
app.register_blueprint(authentication_api)
app.register_blueprint(dashboard_api)
app.register_blueprint(pem_api)
app.register_blueprint(topright_api)

def start():
    if app.debug:
        app.run(host='0.0.0.0',
                port=5000,
                use_reloader=True,
                threaded=True)
    else:
        app.run(host='0.0.0.0',
                port=5000,
                use_reloader=True,
                threaded=True)
