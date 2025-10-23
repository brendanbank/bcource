"""Initialize Flask app."""
from flask import Flask, request, url_for
from flask_babel import Babel
import config
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_admin import Admin
from flask_security.models import sqla
import flask_security.mail_util
from flask_mailman import Mail
from flask_migrate import Migrate
from flask_security import Security, SQLAlchemySessionUserDatastore, roles_required, current_user, hash_password
from flask_moment import Moment
from bcource.menus import Menu
from bcource.helpers import (MyFsModels, admin_has_role, db_datetime, db_datetime_str,
                             format_phone_number, format_email, nh3_save, add_url_argument, message_date,
                             is_impersonating, get_original_user, get_impersonated_user)
from bcource.helpers import config_value as cv
from flask_mobility import Mobility

class Base(DeclarativeBase):
    # __abstract__ = True
    def to_dict(self):
        return {field.name:getattr(self, field.name) for field in self.__table__.c}
    
    @classmethod
    def default_row(cls):
        if not hasattr(cls, 'CONFIG'):
            raise NotImplemented(f'Default called on {cls.__name__} but CONFIG not defined.')
        
        obj = cls().query.filter(cls.name==cv(cls.CONFIG)).first()
        if not obj:
            obj = cls(name=cv(cls.CONFIG))
            db.session.add(obj)
        db.session.commit()
        return(obj)

#connect_args={"options": "-c timezone=utc"}

menu_structure = Menu('root')

moment = Moment()
mobility = Mobility()

db = SQLAlchemy(model_class=Base)

MyFsModels.set_db_info(base_model=Base)

table_admin = Admin(name=__name__, template_mode='bootstrap4', base_template='admin/mybase.html')

security = Security() 

mail = Mail()
migrate = Migrate()

def get_locale():
    return request.accept_languages.best_match(config.Config.LANGUAGES)

babel = Babel(locale_selector=get_locale)
csrf = CSRFProtect()

def create_app():
    """Create Flask application."""
    app = Flask(__name__, instance_relative_config=False)


    app.config.from_object('config.Config')
    from . import models
    
    db.app = app
    
    db.init_app(app)
    mobility.init_app(app)
    babel.init_app(app)
    csrf.init_app(app)
    table_admin.init_app(app)
    
    if app.config.get('ENVIRONMENT') == "DEVELOPMENT":
        app.config["MAIL_BACKEND"] = 'console'
    
    mail.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)
    
    from bcource.models import Content, User, Role
    
    app.jinja_env.globals.update(get_tag=Content.get_tag)
    
    # app.jinja_env.globals.update(has_role=has_role)
    app.jinja_env.globals.update(menu_structure=menu_structure)
    app.jinja_env.globals.update(db_datetime=db_datetime)
    app.jinja_env.globals.update(db_datetime_str=db_datetime_str)
    app.jinja_env.globals.update(show_mobile="d-lg-none")
    app.jinja_env.globals.update(hide_mobile="d-none d-lg-block d-xl-block d-xxl-block")
    app.jinja_env.globals.update(add_url_argument=add_url_argument)
    app.jinja_env.globals.update(is_impersonating=is_impersonating)
    app.jinja_env.globals.update(get_original_user=get_original_user)
    app.jinja_env.globals.update(get_impersonated_user=get_impersonated_user)
    
    app.jinja_env.filters.update(format_phone_number=format_phone_number)
    app.jinja_env.filters.update(format_email=format_email)
    app.jinja_env.filters.update(bcourse_safe=nh3_save)
    app.jinja_env.filters.update(message_date=message_date)
    
    user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)

    # Configure SMS sending for two-factor authentication BEFORE init_app
    from bcource import sms_util
    from bcource.sms_util import AwsSnsSender
    from flask_security import SmsSenderFactory

    # Register AWS SNS sender with Flask-Security
    SmsSenderFactory.senders['aws_sns'] = AwsSnsSender

    class CustomPhoneUtil:
        """Custom phone utility for Flask-Security phone number validation"""

        def __init__(self, app):
            self.app = app

        def validate_phone_number(self, phone_number):
            """
            Validate phone number format.
            Called by Flask-Security during form validation.
            Returns error message if invalid, None if valid.
            """
            is_valid, formatted, error = sms_util.validate_phone_number(phone_number)
            return None if is_valid else error

        def get_canonical_phone(self, phone_number):
            """
            Normalize phone number to E.164 format.
            Called by Flask-Security before storing/comparing phone numbers.
            """
            is_valid, formatted, error = sms_util.validate_phone_number(phone_number)
            return formatted if is_valid else phone_number

    # Now initialize Flask-Security with phone utility
    security.init_app(app, user_datastore, phone_util_cls=CustomPhoneUtil)

    with app.app_context():
        
        import bcource.commands

        # Import parts of our application
        import bcource.home as home
        import bcource.admin 
        import bcource.training as training
        import bcource.user as user
        import bcource.students as students
        import bcource.scheduler as scheduler
        
        from bcource.api import api_calls
        from bcource.admin import admin_views
        
        import bcource.errors
        
        # Register Blueprints
        
        app.register_blueprint(home.home_bp)
        app.register_blueprint(user.user_bp)
        app.register_blueprint(api_calls.api_bp)
        app.register_blueprint(students.students_bp)        
        app.register_blueprint(training.training_bp)   
        app.register_blueprint(scheduler.scheduler_bp)   
             
        app.before_request(bcource.admin.authorize_user)
        
        from bcource.errors import ( HTTPExceptionMustHaveTwoFactorEnabled, handle_no_2fa, 
                                     HTTPExceptionStudentNotActive, student_not_actieve,
                                     HTTPExceptionProfileInComplete, student_profile_incomplete)
        
        app.register_error_handler(HTTPExceptionMustHaveTwoFactorEnabled, handle_no_2fa)
        app.register_error_handler(HTTPExceptionStudentNotActive, student_not_actieve)
        app.register_error_handler(HTTPExceptionProfileInComplete, student_profile_incomplete)
        
        main_menu = menu_structure.add_menu('Terms', css="d-lg-none")
        main_menu.add_menu('Privacy Policy', 'home_bp.privacy')
        main_menu.add_menu('Terms and Conditions', 'home_bp.tandc')

        # db.create_all()  # Create sql tables for our data models
        
        
        def get_locale():
            return request.accept_languages.best_match(cv('LANGUAGES'))
        
        models.db_init_data(app)
                
        return app
    
