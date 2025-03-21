from flask_security.models.sqla import FsModels
from sqlalchemy import ForeignKey, Table, Column
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from flask import url_for, current_app, request, abort, redirect
from flask_principal import Identity, Permission, RoleNeed, identity_changed

def get_url (form):
    if form.is_submitted():
        url=form.url.data
    else:
        url = request.args.get('url')
        

    if url == None:
        if request.referrer:
            url = request.referrer
        
    for u in ['user_bp.settings', 'user_bp.update']:
        if url_for(u) == url:
            url = url_for('home_bp.home')
            break
    if url:
        form.url.data = url
    else:
        form.url.data=url_for('home_bp.home')
        
    return(url)

def has_role(roles):
    roles.append("admin_views")
    perms = [Permission(RoleNeed(role)) for role in roles]
    for perm in perms:
        if perm.can():
            return None
    
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
        

