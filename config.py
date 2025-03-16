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
    # SQLALCHEMY_ENGINE_OPTIONS = {"options": "-c timezone=utc"}

    LANGUAGES = ['en', 'nl']
    LANGUAGE_DEFAULT = 'en'
    
    BABEL_DEFAULT_LOCALE = LANGUAGE_DEFAULT
    
    
    # FLASK_ADMIN_SWATCH = 'cerulean'

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

    MAIL_SERVER = environ.get('MAIL_SERVER')
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_DEFAULT_SENDER = environ.get('MAIL_DEFAULT_SENDER')
    
    SECURITY_AUTHORIZE_REQUEST = {'admin.index': "admin_views"}
    
    ADMIN_USER   = environ.get("ADMIN_USER")
    ADMIN_PASSWORD = environ.get("ADMIN_PASSWORD")

settings = Config


