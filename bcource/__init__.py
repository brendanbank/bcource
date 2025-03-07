"""Initialize Flask app."""
from flask import Flask, request
from flask_babel import Babel
import config
from flask_wtf.csrf import CSRFProtect


from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    __abstract__ = True
    def to_dict(self):
        return {field.name:getattr(self, field.name) for field in self.__table__.c}

db = SQLAlchemy(model_class=Base)

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
    
    with app.app_context():
        # Import parts of our application
        from .home import home
        from .auth import auth
        from .api import api
        from .students import students
        
        from . import models

        # Register Blueprints
        app.register_blueprint(home.home_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(api.api_bp)
        app.register_blueprint(students.students_bp)

        db.create_all()  # Create sql tables for our data models

        def get_locale():
            return request.accept_languages.best_match(app.config['LANGUAGES'])
        


        return app
    
    