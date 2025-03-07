from os import environ, path
import sys
import logging


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

    # General Config\
    ENVIRONMENT = environ.get("ENVIRONMENT")

    # Flask Config
    SECRET_KEY = environ.get("SECRET_KEY")
    FLASK_DEBUG = environ.get("FLASK_DEBUG")
    FLASK_APP = "wsgi.py"

    # Static Assets
    STATIC_FOLDER = "static"
    TEMPLATES_FOLDER = "templates"
    COMPRESSOR_DEBUG = environ.get("COMPRESSOR_DEBUG")
    EXPLAIN_TEMPLATE_LOADING = environ.get("EXPLAIN_TEMPLATE_LOADING")
    DEBUG = environ.get("DEBUG")
    
    SQLALCHEMY_DATABASE_URI = environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    LANGUAGES = ['en', 'nl']
    
settings = Config


