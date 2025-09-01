from app import db
import datetime

class DeploymentInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    db_host = db.Column(db.String(128))
    db_port = db.Column(db.Integer)
    db_name = db.Column(db.String(128))
    db_user = db.Column(db.String(128))
    db_password = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class ConnectionTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    response_time = db.Column(db.Float)
    tested_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
