from flask_security.models.sqla import FsModels
from sqlalchemy import ForeignKey, Table, Column
from flask import current_app as app
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from flask import url_for, current_app, request, abort, redirect
from flask_principal import Identity, Permission, RoleNeed, identity_changed
from collections import OrderedDict
import pytz
import string
import secrets

def db_datetime(db_datetime_notz):
    return db_datetime_notz.replace(tzinfo=pytz.timezone('UTC'))

def db_datetime_str(db_datetime_notz):
    dt = db_datetime(db_datetime_notz)
    TZ_NAME = app.config.get('BCOURCE_TZ', 'Europe/Amsterdam')
    TZ = pytz.timezone(TZ_NAME)    
    return dt.astimezone(TZ).strftime("%a, %b %d %Y, %H:%M %p %Z")

def get_url (form, default=None):
    
    if not default:
        default = 'home_bp.home'
        
    if form.is_submitted():
        url=form.url.data
    else:
        url = request.args.get('url')
        

    if url == None:
        if request.referrer:
            url = request.referrer
        
    for u in ['user_bp.settings', 'user_bp.update']:
        if url_for(u) == url:
            url = url_for(default)
            break
    if url:
        form.url.data = url
    else:
        form.url.data=url_for(default)
        
    return(url)

def admin_has_role(roles):
    _roles = roles
    if type(roles) == str:
        _roles = [roles]
        
    _roles.append(current_app.config['BCOURSE_SUPER_USER_ROLE'])
    perms = [Permission(RoleNeed(role)) for role in _roles]
    for perm in perms:
        if perm.can():
            return True
    
    abort(403)

class MyFsModels(FsModels):
    
    @classmethod
    def set_db_info(
        cls,
        *,
        base_model,
        user_table_name="user",
        role_table_name="role",
        webauthn_table_name="webauthn",
    ):
        """Initialize Model.
        This MUST be called PRIOR to declaring your User/Role/WebAuthn model in order
        for table name altering to work.

        .. note::
            This should only be used if you are utilizing the sqla data
            models. With your own models you would need similar but slightly
            different code.
        """
        cls.base_model = base_model
        cls.user_table_name = user_table_name
        cls.role_table_name = role_table_name
        cls.webauthn_table_name = webauthn_table_name
        cls.roles_users = Table(
            "roles_users",
            cls.base_model.metadata,
            Column(
                "user_id", ForeignKey(f"{cls.user_table_name}.id", ondelete="CASCADE"), primary_key=True
            ),
            Column(
                "role_id", ForeignKey(f"{cls.role_table_name}.id"), primary_key=True
            ),
        )
        

def config_value(key, app=None, default=None, strict=True):
    app = app or current_app
    key = f"BCOURSE_{key.upper()}"
    # protect against spelling mistakes
    if strict and key not in app.config:
        raise ValueError(f"Key {key} doesn't exist")
    return app.config.get(key, default)


    
def genpwd():
    letters = string.ascii_letters
    digits = string.digits
    special_chars = string.punctuation
    
    alphabet = letters + digits + special_chars
    
    # fix password length
    pwd_length = 16
    while True:
        pwd = ''
        for i in range(pwd_length):
            pwd += ''.join(secrets.choice(alphabet))
    
        break
    
    return (pwd)
