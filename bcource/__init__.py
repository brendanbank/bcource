"""Initialize Flask app."""
from flask import Flask, request, url_for
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
from flask_security import Security, SQLAlchemySessionUserDatastore, roles_required, current_user, hash_password

class Base(DeclarativeBase):
    # __abstract__ = True
    def to_dict(self):
        return {field.name:getattr(self, field.name) for field in self.__table__.c}

db = SQLAlchemy(model_class=Base)


sqla.FsModels.set_db_info(base_model=Base)

cors = CORS()
table_admin = Admin(name=__name__, template_mode='bootstrap3')


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

    table_admin.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
    from . import models 
    from .admin import Content, User, Role
    
    app.jinja_env.globals.update(get_tag=Content.get_tag)
        
    user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)

    security.init_app(app, user_datastore)  
    
    with app.app_context():
        
        # Import parts of our application
        from bcource.home import home
        from bcource.auth import auth
        from bcource.api import api_calls
        from bcource.students import students
        from bcource.admin import admin_views
        
        import bcource.helpers
        

        # Register Blueprints
        app.register_blueprint(home.home_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(api_calls.api_bp)
        app.register_blueprint(students.students_bp)        
        app.before_request(admin_views.authorize_user)

        db.create_all()  # Create sql tables for our data models

        def get_locale():
            return request.accept_languages.best_match(app.config['LANGUAGES'])
        
        app.config['ADMIN_USER']
        role = security.datastore.find_or_create_role('admin_views')
        security.datastore.add_permissions_to_role(role, {"user-read", "user-write"})

        
        user=security.datastore.find_user(email=app.config['ADMIN_USER'])
        
        if not user:
            user = security.datastore.create_user(email=app.config['ADMIN_USER'],
                                                  password=hash_password(app.config['ADMIN_PASSWORD']))
        
        security.datastore.add_role_to_user(user, role)
        
        db.session.commit()

        return app
    
    