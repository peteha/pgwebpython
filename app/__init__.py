# Flask app initialization
from flask import Flask
import socket
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
try:
    # Prefer multiprocess-aware exporter under gunicorn; fallback to single-process exporter
    from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics
except Exception:
    GunicornPrometheusMetrics = None
try:
    from prometheus_flask_exporter import PrometheusMetrics
except Exception:
    PrometheusMetrics = None

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object('app.config.Config')

    # Use SQLite for initial setup
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///setup.db'
    db.init_app(app)
    with app.app_context():
        db.create_all()
        try:
            from app.models import DeploymentInfo
            info = DeploymentInfo.query.first()
            if info:
                # Build Postgres URI from stored info
                uri = f"postgresql://{info.db_user}:{info.db_password}@{info.db_host}:{info.db_port}/{info.db_name}"
                app.config['SQLALCHEMY_DATABASE_URI'] = uri
                db.engine.dispose()
        except Exception:
            pass

    from app import routes, api
    app.register_blueprint(routes.bp)
    app.register_blueprint(api.bp, url_prefix='/api')

    # Metrics and health
    import os
    if GunicornPrometheusMetrics and (os.getenv('PROMETHEUS_MULTIPROC_DIR') or os.getenv('prometheus_multiproc_dir')):
        metrics = GunicornPrometheusMetrics(app, group_by='endpoint')
        metrics.info('pgwebpython_info', 'Application info', version='1.0.0')
    elif PrometheusMetrics:
        metrics = PrometheusMetrics(app, group_by='endpoint')
        metrics.info('pgwebpython_info', 'Application info', version='1.0.0')

    # Liveness/health endpoint (works regardless of exporter availability)
    @app.get('/healthz')
    def healthz():
        return {'status': 'ok'}, 200

    @app.context_processor
    def inject_server_hostname():
        try:
            hn = socket.getfqdn()
        except Exception:
            hn = 'unknown'
        return { 'server_hostname': hn }

    return app
