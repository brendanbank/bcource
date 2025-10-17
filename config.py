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

    ENVIRONMENT = environ.get("ENVIRONMENT", "DEVELOPMENT")
    DEVELOPMENT_EMAIL = environ.get("DEVELOPMENT_EMAIL", "admin@example.com")
    DEVELOPMENT_PHONE = environ.get("DEVELOPMENT_PHONE", "+1234567890")
    
    POSTS_PER_PAGE = 22

    # Flask Config
    SECRET_KEY = environ.get("SECRET_KEY")
    FLASK_DEBUG = environ.get("FLASK_DEBUG")
    FLASK_APP = "wsgi.py"
    
    # url config
    SERVER_NAME=environ.get("SERVER_NAME", "bcourse.nl")
    APPLICATION_ROOT="/"
    PREFERRED_URL_SCHEME=environ.get("PREFERRED_URL_SCHEME", "https")

    # Static Assets
    STATIC_FOLDER = "static"
    TEMPLATES_FOLDER = "templates"
    COMPRESSOR_DEBUG = environ.get("COMPRESSOR_DEBUG")
    EXPLAIN_TEMPLATE_LOADING = False
    DEBUG = environ.get("DEBUG")
    
    SQLALCHEMY_DATABASE_URI = environ.get("SQLALCHEMY_DATABASE_URI")
    
    SQLALCHEMY_BINDS = {
        'postalcodes': environ.get("SQLALCHEMY_BINDS_POSTALCODES")
    }

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
    SECURITY_TWO_FACTOR_ENABLED_METHODS = ['email', 'authenticator']
    #SECURITY_TWO_FACTOR_ENABLED_METHODS = ['email', 'authenticator', 'sms']
    SECURITY_TWO_FACTOR_MAIL_VALIDITY = 600
    SECURITY_TOTP_SECRETS = {1: environ.get("SECURITY_TOTP_SECRETS")}
    SECURITY_TOTP_ISSUER = environ.get("SECURITY_TOTP_ISSUER")
    SECURITY_TWO_FACTOR_RESCUE_EMAIL = False
    SECURITY_PHONE_REGION_DEFAULT = "NL"  # Default region for phone validation
    SECURITY_SMS_SERVICE = "aws_sns"  # Use our custom AWS SNS SMS sender
    SECURITY_TWO_FACTOR_ALWAYS_VALIDATE = False  # Don't require phone number if already set

    # AWS SNS Configuration for SMS
    AWS_REGION = environ.get("AWS_REGION", "eu-central-1")
    AWS_ACCESS_KEY_ID = environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_SNS_SENDER_ID = environ.get("AWS_SNS_SENDER_ID", "BCOURSE")
    
    # SMS Rate Limiting (prevent abuse)
    SMS_RATE_LIMIT_PER_HOUR = int(environ.get("SMS_RATE_LIMIT_PER_HOUR", "5"))  # Max SMS per number per hour
    SMS_RATE_LIMIT_PER_DAY = int(environ.get("SMS_RATE_LIMIT_PER_DAY", "10"))  # Max SMS per number per day
    SMS_COOLDOWN_SECONDS = int(environ.get("SMS_COOLDOWN_SECONDS", "60"))  # Min seconds between SMS

    MAIL_SERVER = environ.get('MAIL_SERVER')
    MAIL_PORT = environ.get('MAIL_PORT')
    MAIL_USE_TLS = environ.get('MAIL_USE_TLS') 
    MAIL_DEFAULT_SENDER = environ.get('MAIL_DEFAULT_SENDER')
    MAIL_BACKEND = 'smtp'
    MAIL_USERNAME = environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = environ.get('MAIL_PASSWORD')
    
    
    ## Application settings:
    BCOURSE_ADMIN_USER   = environ.get("BCOURSE_ADMIN_USER")
    BCOURSE_ADMIN_PASSWORD = environ.get("BCOURSE_ADMIN_PASSWORD")
    # BCOURSE Default Settings
    BCOURSE_DEFAULT_PRACTICE = environ.get("BCOURSE_DEFAULT_PRACTICE", "Hans van Wechem")
    BCOURSE_DEFAULT_PRACTICE_SHORTNAME = environ.get("BCOURSE_DEFAULT_PRACTICE_SHORTNAME", "default")
    
    BCOURSE_PRACTICE = BCOURSE_DEFAULT_PRACTICE_SHORTNAME
    
    BCOURSE_DEFAULT_STUDENT_TYPE = environ.get("BCOURSE_DEFAULT_STUDENT_TYPE", "default")
    BCOURSE_DEFAULT_STUDENT_STATUS = environ.get("BCOURSE_DEFAULT_STUDENT_STATUS", "inactive")
    BCOURSE_DEFAULT_STUDENT_ROLE = environ.get("BCOURSE_DEFAULT_STUDENT_ROLE", "student")
    BCOURSE_SUPER_USER_ROLE = environ.get("BCOURSE_SUPER_USER_ROLE", "db-admin")
    
    BCOURSE_DEFAULT_TRAINING_TYPE = environ.get("BCOURSE_DEFAULT_TRAINING_TYPE", "Bonding")
    BCOURSE_DEFAULT_TRAINING_POLICY = environ.get("BCOURSE_DEFAULT_TRAINING_POLICY", "default")
    
    # Location Settings
    BCOURSE_LOCATION_NAME = environ.get("BCOURSE_LOCATION_NAME", "Grote Trainingsruimte")
    BCOURSE_LOCATION_STREET = environ.get("BCOURSE_LOCATION_STREET", "Frans Halsstraat")
    BCOURSE_LOCATION_HN = environ.get("BCOURSE_LOCATION_HN", 7)
    BCOURSE_LOCATION_CITY = environ.get("BCOURSE_LOCATION_CITY", "Amsterdam")
    BCOURSE_LOCATION_POSTALCODE = environ.get("BCOURSE_LOCATION_POSTALCODE", "1072 BJ")
    
    BCOURSE_SYSTEM_USER = environ.get("BCOURSE_SYSTEM_USER", 'do-not-reply@bcourse.nl')
    BCOURSE_SYSTEM_FIRSTNAME = environ.get("BCOURSE_SYSTEM_FIRSTNAME", 'Bcourse')
    BCOURSE_SYSTEM_LASTNAME = environ.get("BCOURSE_SYSTEM_LASTNAME", 'Reservation System')
    
    BCOURSE_SUPPORT_EMAIL = environ.get("BCOURSE_SUPPORT_EMAIL", 'brendan.bank@gmail.com')

    SECURITY_AUTHORIZE_REQUEST = {'admin.index': [ BCOURSE_SUPER_USER_ROLE, 'cms-admin' ]}
    
    #sheduler
    
    SCHEDULER_API_ENABLED: True
    
    # APScheduler configuration
    SCHEDULER_JOBSTORES = {
        'default': {
            'type': 'sqlalchemy',
            'url': SQLALCHEMY_DATABASE_URI # Use the same database for Flask and APScheduler
        }
    }
    SCHEDULER_EXECUTORS = {
        'default': {'type': 'threadpool', 'max_workers': 1}
    }
    SCHEDULER_JOB_DEFAULTS = {
        'coalesce': True,
        'max_instances': 1
    }
    SCHEDULER_TIMEZONE = 'UTC' # Store/process all internal times in UTC
    SCHEDULER_API_ENABLED = True # For Flask-APScheduler, if you want its API
    
    
    BCOURSE_LOCK_HOST="127.0.0.1"
    BCOURSE_LOCK_PORT=53462


settings = Config


