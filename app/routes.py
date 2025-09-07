from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app import db
from app.models import DeploymentInfo, ConnectionTest
import psycopg2
import time
import logging

bp = Blueprint('routes', __name__)
logger = logging.getLogger('pgwebpython.routes')
logging.basicConfig(level=logging.INFO)

@bp.route('/', methods=['GET', 'POST'])
def index():
    deployment = DeploymentInfo.query.first()
    if not deployment:
        logger.info("No deployment info found, redirecting to setup.")
        return redirect(url_for('routes.setup'))
    refresh_default = int(getattr(current_app.config, 'REFRESH_INTERVAL', 10))
    refresh_interval = int(request.args.get('refresh', refresh_default))
    logger.info(f"Rendering index with refresh_interval={refresh_interval} (data loads via /api/records)")
    return render_template('index.html', deployment=deployment, refresh_interval=refresh_interval)

@bp.route('/setup', methods=['GET', 'POST'])
def setup():
    deployment = DeploymentInfo.query.first()  # Get existing config for pre-population
    
    if request.method == 'POST':
        # Handle connection string input
        connection_string = request.form.get('connection_string', '').strip()
        if not connection_string:
            flash('Connection string is required', 'danger')
            return render_template('setup.html', deployment=deployment)
        
        # Parse connection string
        try:
            from urllib.parse import urlparse
            parsed = urlparse(connection_string)
            
            if parsed.scheme not in ('postgresql', 'postgres'):
                raise ValueError('Invalid protocol. Expected postgresql:// or postgres://')
            
            db_host = parsed.hostname
            db_port = parsed.port or 5432
            db_name = parsed.path.lstrip('/')
            db_user = parsed.username
            db_password = parsed.password or ''
            
            if not all([db_host, db_name, db_user]):
                raise ValueError('Missing required components (host, database, or username)')
                
        except Exception as e:
            logger.error(f"Error parsing connection string: {e}")
            flash(f'Invalid connection string format: {e}', 'danger')
            return render_template('setup.html', deployment=deployment)
        
        logger.info(f"Parsed connection string: host={db_host}, port={db_port}, db={db_name}, user={db_user}")
        # Try to connect and create DB if not exists
        try:
            # Connect to maintenance DB to manage databases
            conn = psycopg2.connect(host=db_host, port=db_port, user=db_user, password=db_password, dbname='postgres')
            conn.autocommit = True
            cur = conn.cursor()
            logger.info("Connected to Postgres server.")
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            if not cur.fetchone():
                logger.info(f"Database {db_name} does not exist, creating...")
                cur.execute(f'CREATE DATABASE {db_name}')
            else:
                logger.info(f"Database {db_name} already exists.")
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error connecting/creating database: {e}")
            flash(f'Error connecting/creating database: {e}', 'danger')
            return render_template('setup.html')
        # Save or update info (ensure only one deployment record exists)
        info = DeploymentInfo.query.first()
        if info:
            logger.info("Updating existing deployment info.")
            info.db_host = db_host
            info.db_port = db_port
            info.db_name = db_name
            info.db_user = db_user
            info.db_password = db_password
        else:
            logger.info("Creating new deployment info.")
            info = DeploymentInfo(db_host=db_host, db_port=db_port, db_name=db_name, db_user=db_user, db_password=db_password)
            db.session.add(info)
        db.session.commit()
        logger.info("Deployment info saved to DB.")
        # Switch app to Postgres DB and migrate tables
        from flask import current_app
        uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        current_app.config['SQLALCHEMY_DATABASE_URI'] = uri
        db.engine.dispose()
        db.create_all()
        logger.info("Switched to Postgres DB and migrated tables.")
        return redirect(url_for('routes.index'))
    return render_template('setup.html', deployment=deployment)

@bp.route('/info')
def info():
    deployment = DeploymentInfo.query.first()
    return render_template('info.html', deployment=deployment)
