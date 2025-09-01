import os
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REFRESH_INTERVAL = int(os.environ.get('REFRESH_INTERVAL', 10))  # seconds
    MAX_POINTS = int(os.environ.get('MAX_POINTS', 1000))  # max records returned for chart/API
