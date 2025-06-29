from os import environ, path
import sys
import logging
import secrets


log = logging.getLogger(__name__)
log_level = environ.get("LOG", "INFO")
logging.basicConfig(format='%(name)s.%(funcName)s(%(lineno)s): %(message)s',
                    stream=sys.stderr,
                    level=getattr(logging, log_level, logging.INFO))

"""Class-based Flask app configuration."""
from dotenv import load_dotenv

BASE_DIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASE_DIR, ".env"))

class Config:
    """Configuration from environment variables."""

    ENVIRONMENT = environ.get("ENVIRONMENT")
    DEVELOPMENT_EMAIL = environ.get("DEVELOPMENT_TO_EMAIL")
    DEVELOPMENT_PHONE = environ.get("DEVELOPMENT_TO_PHONE")
    
    POSTS_PER_PAGE = 18

    # Flask Config
    SECRET_KEY = environ.get("SECRET_KEY")
    FLASK_DEBUG = environ.get("FLASK_DEBUG")
    FLASK_APP = "wsgi.py"

    # Static Assets
    STATIC_FOLDER = "static"
    TEMPLATES_FOLDER = "templates"
    COMPRESSOR_DEBUG = environ.get("COMPRESSOR_DEBUG")
    EXPLAIN_TEMPLATE_LOADING = False
    DEBUG = environ.get("DEBUG")
    
    SQLALCHEMY_DATABASE_URI = environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True
    }

    
    # SQLALCHEMY_ENGINE_OPTIONS = {"query_cache_size": 0 }

    LANGUAGES = ['en', 'nl']
    LANGUAGE_DEFAULT = 'en'
    
    BABEL_DEFAULT_LOCALE = LANGUAGE_DEFAULT
    
    
    FLASK_ADMIN_SWATCH = 'cerulean'

    #Flask Security
    SECURITY_USERNAME_ENABLE = False
    SECURITY_PASSWORD_SALT = environ.get("SECURITY_PASSWORD_SALT")
    SECURITY_REGISTERABLE = True
    SECURITY_USE_REGISTER_V2 = True
    SECURITY_SEND_REGISTER_EMAIL = True
    SECURITY_CHANGEABLE = True
    SECURITY_URL_PREFIX = "/auth"
    SECURITY_CONFIRMABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_PASSWORD_COMPLEXITY_CHECKER = True
    SECURITY_RECOVERABLE = True
    SECURITY_TWO_FACTOR = True
    SECURITY_TWO_FACTOR_ENABLED_METHODS = ['email']
    SECURITY_TWO_FACTOR_MAIL_VALIDITY = 600
    SECURITY_TOTP_SECRETS = {1: environ.get("SECURITY_TOTP_SECRETS")}
    SECURITY_TOTP_ISSUER = environ.get("SECURITY_TOTP_ISSUER")
    SECURITY_TWO_FACTOR_RESCUE_EMAIL = False

    MAIL_SERVER = environ.get('MAIL_SERVER')
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_DEFAULT_SENDER = environ.get('MAIL_DEFAULT_SENDER')
    MAIL_BACKEND = 'smtp'
    
    
    ## Application settings:
    BCOURSE_ADMIN_USER   = environ.get("BCOURSE_ADMIN_USER")
    BCOURSE_ADMIN_PASSWORD = environ.get("BCOURSE_ADMIN_PASSWORD")
    BCOURSE_DEFAULT_PRACTICE = environ.get("BCOURSE_DEFAULT_PRACTICE", "default")
    BCOURSE_DEFAULT_PRACTICE_SHORTNAME = environ.get("BCOURSE_DEFAULT_PRACTICE_SHORTNAME", "default")
    
    BCOURSE_PRACTICE = BCOURSE_DEFAULT_PRACTICE_SHORTNAME
    
    BCOURSE_DEFAULT_STUDENT_TYPE = environ.get("BCOURSE_DEFAULT_STUDENT_TYPE", "default")
    BCOURSE_DEFAULT_STUDENT_STATUS = environ.get("BCOURSE_DEFAULT_STUDENT_STATUS", "default")
    BCOURSE_SUPER_USER_ROLE = environ.get("BCOURSE_SUPER_USER_ROLE", "db-admin")
    
    BCOURSE_LOCATION_NAME = environ.get("BCOURSE_LOCATION_NAME")
    BCOURSE_LOCATION_STREET = environ.get("BCOURSE_LOCATION_STREET")
    BCOURSE_LOCATION_HN = environ.get("BCOURSE_LOCATION_HN")
    BCOURSE_LOCATION_CITY = environ.get("BCOURSE_LOCATION_CITY")
    BCOURSE_DEFAULT_STUDENT_ROLE = environ.get("BCOURSE_DEFAULT_STUDENT_ROLE")
    BCOURSE_DEFAULT_TRAINING_TYPE=environ.get("BCOURSE_DEFAULT_TRAINING_TYPE")
    BCOURSE_DEFAULT_TRAINING_POLICY = environ.get("BCOURSE_DEFAULT_TRAINING_POLICY")
    
    BCOURSE_SYSTEM_USER = environ.get("BCOURSE_SYSTEM_USER", 'do-not-reply@bgwlan.nl')
    BCOURSE_SYSTEM_FIRSTNAME = environ.get("BCOURSE_SYSTEM_FIRSTNAME", 'Bcource')
    BCOURSE_SYSTEM_LASTNAME = environ.get("BCOURSE_SYSTEM_LASTNAME", 'Reservation System')

    SECURITY_AUTHORIZE_REQUEST = {'admin.index': [ BCOURSE_SUPER_USER_ROLE, 'cms-admin' ]}
    
    SCHEDULER_API_ENABLED: True
    

settings = Config


