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
from bcource.helpers import MyFsModels, admin_has_role, db_datetime, db_datetime_str
from bcource.helpers import config_value as cv

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

    babel.init_app(app)
    csrf.init_app(app)

    table_admin.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)
    
     
    from bcource.models import Content, User, Role
    
    app.jinja_env.globals.update(get_tag=Content.get_tag)
    
    
    
    # app.jinja_env.globals.update(has_role=has_role)
    app.jinja_env.globals.update(menu_structure=menu_structure)
    app.jinja_env.globals.update(db_datetime=db_datetime)
    app.jinja_env.globals.update(db_datetime_str=db_datetime_str)
    
    
    user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)

    security.init_app(app, user_datastore)  
        
    with app.app_context():
        
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
        
        main_menu = menu_structure.add_menu('Privacy')
        main_menu.add_menu('Privacy Policy', 'home_bp.privacy')

        db.create_all()  # Create sql tables for our data models

        def get_locale():
            return request.accept_languages.best_match(cv('LANGUAGES'))
        
        models.db_init_data(app)
        return app
    

