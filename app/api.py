from flask import Blueprint, request, jsonify, current_app
import datetime
from app import db
from app.models import ConnectionTest, DeploymentInfo
try:
    from prometheus_client import Counter, Histogram
except Exception:
    Counter = None
    Histogram = None
import time
import logging

bp = Blueprint('api', __name__)
logger = logging.getLogger('pgwebpython.api')

# Custom metrics
if Counter and Histogram:
    CONNECTION_TESTS_TOTAL = Counter('pgwebpython_connection_tests_total', 'Total connection tests', ['status'])
    CONNECTION_TEST_DURATION = Histogram('pgwebpython_connection_test_seconds', 'Connection test duration (s)')
else:
    CONNECTION_TESTS_TOTAL = None
    CONNECTION_TEST_DURATION = None

@bp.route('/test', methods=['POST'])
def test_connection():
    logger.info("API /test called: simulating connection test.")
    info = DeploymentInfo.query.first()
    if not info:
        logger.error("No deployment info configured.")
        return jsonify({'success': False, 'error': 'No deployment info configured'}), 400
    import psycopg2
    start = time.time()
    try:
        conn = psycopg2.connect(
            host=info.db_host,
            port=info.db_port,
            user=info.db_user,
            password=info.db_password,
            dbname=info.db_name
        )
        conn.close()
        response_time = time.time() - start
        test = ConnectionTest(response_time=response_time)
        db.session.add(test)
        db.session.commit()
        logger.info(f"Connection test recorded: response_time={response_time}")
        if CONNECTION_TESTS_TOTAL:
            CONNECTION_TESTS_TOTAL.labels(status='success').inc()
        if CONNECTION_TEST_DURATION:
            CONNECTION_TEST_DURATION.observe(response_time)
        return jsonify({'success': True, 'response_time': response_time})
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        if CONNECTION_TESTS_TOTAL:
            CONNECTION_TESTS_TOTAL.labels(status='error').inc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/add_record', methods=['POST'])
def add_record():
    data = request.json
    response_time = data.get('response_time')
    logger.info(f"API /add_record called: response_time={response_time}")
    test = ConnectionTest(response_time=response_time)
    db.session.add(test)
    db.session.commit()
    logger.info("Record added to DB.")
    return jsonify({'success': True})

@bp.route('/records', methods=['GET'])
def get_records():
    logger.info("API /records called.")
    max_points = getattr(current_app.config, 'MAX_POINTS', 1000)
    try:
        max_points = int(max_points)
    except Exception:
        max_points = 1000
    records = ConnectionTest.query.order_by(ConnectionTest.tested_at.desc()).limit(max_points).all()
    logger.info(f"Returning {len(records)} of max {max_points} records.")
    def fmt_iso_ms(dt: datetime.datetime) -> str:
        # Ensure UTC and milliseconds precision, ISO-8601
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.isoformat(timespec='milliseconds')

    return jsonify([
        {
            'response_time': r.response_time,
            'tested_at': fmt_iso_ms(r.tested_at)
        } for r in records
    ])
