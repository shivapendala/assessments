"""
ElevateIQ — Configuration Module
Supports Development, Testing, and Production environments.
"""
import os
import ssl
from dotenv import load_dotenv

load_dotenv()

# Build SQLALCHEMY_ENGINE_OPTIONS dynamically to support SSL context for pg8000
db_url = os.environ.get('DATABASE_URL', '')
engine_options = {
    'pool_size': 30,
    'max_overflow': 50,
    'pool_timeout': 30,
    'pool_recycle': 1800,
    'pool_pre_ping': True,
}
if db_url and ('postgres' in db_url or 'pg8000' in db_url):
    engine_options['connect_args'] = {'ssl': True}


class Config:
    """Base configuration shared by all environments."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 7200  # 2 hours

    # Session security
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 7200  # 2 hours

    # SQLAlchemy connection pool tuning (handles 100 concurrent users)
    # Note: overridden in DevelopmentConfig for SQLite
    SQLALCHEMY_ENGINE_OPTIONS = engine_options


def fix_database_uri(uri: str) -> str:
    if not uri:
        return uri
    # Convert postgres:// or postgresql:// to postgresql+pg8000:// for pure-Python driver compatibility
    is_postgres = False
    if uri.startswith('postgres://'):
        uri = uri.replace('postgres://', 'postgresql+pg8000://', 1)
        is_postgres = True
    elif uri.startswith('postgresql://'):
        uri = uri.replace('postgresql://', 'postgresql+pg8000://', 1)
        is_postgres = True
    
    # Strip all query parameters from PostgreSQL connection string
    # (they are handled cleanly via connect_args / ssl_context instead)
    if is_postgres and '?' in uri:
        uri = uri.split('?', 1)[0]
        
    return uri


class DevelopmentConfig(Config):
    DEBUG = True
    _db_raw = os.environ.get('ASSESSMENT_DATABASE_URL') or os.environ.get('DATABASE_URL')
    SQLALCHEMY_DATABASE_URI = fix_database_uri(_db_raw) if _db_raw else 'sqlite:///elevateiq_assessments.db'
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True
    SQLALCHEMY_ENGINE_OPTIONS = engine_options if _db_raw and ('postgres' in _db_raw or 'pg8000' in _db_raw) else {}


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    _db_raw = os.environ.get('ASSESSMENT_DATABASE_URL') or os.environ.get('DATABASE_URL')
    SQLALCHEMY_DATABASE_URI = fix_database_uri(_db_raw) if _db_raw else 'sqlite:///elevateiq_assessments.db'
    SQLALCHEMY_ENGINE_OPTIONS = engine_options if _db_raw and ('postgres' in _db_raw or 'pg8000' in _db_raw) else {}


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}


def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)
