"""Initialize Flask app."""
from flask import Flask, request
from flask_babel import Babel
import config
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_admin import Admin
from flask_security.models import sqla
import flask_security.mail_util
from flask_mailman import Mail
from flask_migrate import Migrate


class Base(DeclarativeBase):
    # __abstract__ = True
    def to_dict(self):
        return {field.name:getattr(self, field.name) for field in self.__table__.c}

db = SQLAlchemy(model_class=Base)


sqla.FsModels.set_db_info(base_model=Base)

cors = CORS()
admin = Admin(name=__name__, template_mode='bootstrap3')

from flask_security import Security, SQLAlchemySessionUserDatastore

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
    
    db.init_app(app)
    
    babel.init_app(app)
    csrf.init_app(app)
    cors.init_app(app, resources={r'/*': {'origins': ["http://localhost:8000", "https://example.com"]}})
    admin.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
    from . import models as models
        
    user_datastore = SQLAlchemySessionUserDatastore(db.session, models.User, models.Role)

    security.init_app(app, user_datastore)  
    
    with app.app_context():
        # Import parts of our application
        from .home import home
        from .auth import auth
        from .api import api
        from .students import students
        

        # Register Blueprints
        app.register_blueprint(home.home_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(api.api_bp)
        app.register_blueprint(students.students_bp)
        app.config["SECURITY_EMAIL_VALIDATOR_ARGS"] = {"check_deliverability": False}


        db.create_all()  # Create sql tables for our data models

        def get_locale():
            return request.accept_languages.best_match(app.config['LANGUAGES'])
        


        return app
    
    