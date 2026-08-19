"""
ElevateIQ — Configuration Module
Supports Development, Testing, and Production environments.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def fix_database_uri(uri: str) -> str:
    """Convert any postgres:// or postgresql:// URI to use psycopg2."""
    if not uri:
        return uri
    if uri.startswith('postgres://'):
        uri = uri.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif uri.startswith('postgresql://') and 'psycopg2' not in uri:
        uri = uri.replace('postgresql://', 'postgresql+psycopg2://', 1)
    elif uri.startswith('postgresql+pg8000://'):
        uri = uri.replace('postgresql+pg8000://', 'postgresql+psycopg2://', 1)

    # Strip SSL query parameters — psycopg2 handles SSL via sslmode in the URI
    if '&channel_binding=' in uri:
        uri = uri.split('&channel_binding=')[0]
    return uri


def get_engine_options(db_uri: str):
    """Return appropriate engine options based on dialect (PostgreSQL vs SQLite)."""
    if 'postgresql' in (db_uri or ''):
        return {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_timeout': 30,
            'pool_recycle': 300,  # Recycle every 5 min for serverless Postgres
            'pool_pre_ping': True,
            'connect_args': {
                'connect_timeout': 10,
            },
        }
    else:
        return {
            'connect_args': {
                'check_same_thread': False
            }
        }


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


class DevelopmentConfig(Config):
    DEBUG = True
    _db_raw = os.environ.get('ASSESSMENT_DATABASE_URL') or os.environ.get('DATABASE_URL', '')
    SQLALCHEMY_DATABASE_URI = fix_database_uri(_db_raw) if _db_raw else 'sqlite:///assessment_dev.db'
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True
    SQLALCHEMY_ENGINE_OPTIONS = get_engine_options(SQLALCHEMY_DATABASE_URI)


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    _db_raw = os.environ.get('ASSESSMENT_DATABASE_URL') or os.environ.get('DATABASE_URL', '')
    SQLALCHEMY_DATABASE_URI = fix_database_uri(_db_raw) if _db_raw else 'sqlite:///assessment.db'
    SQLALCHEMY_ENGINE_OPTIONS = get_engine_options(SQLALCHEMY_DATABASE_URI)


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {'connect_args': {'check_same_thread': False}}


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}


def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)
