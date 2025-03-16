from bcource import db
from bcource import table_admin
from bcource.admin.models import User, Role, Permission, ClientStatus
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user, hash_password
from wtforms.fields import PasswordField
from flask import current_app, url_for, abort, redirect, request
from flask_security import SmsSenderBaseClass
from flask_admin.menu import MenuLink
import uuid


class MainIndexLink(MenuLink):
    def get_url(self):
        return url_for("home_bp.home")

table_admin.add_link(MainIndexLink(name="Main Page"))

def accessible_as_admin(role="admin_views"):
    role = Role().query.filter(Role.name==role).first()
    if not role:
        role = Role(name=role)
        db.session.add(role)
        db.session.commit()
        
    return (
        current_user.is_active
        and current_user.is_authenticated
        and current_user.has_role(role)
    )
    
def accessible_by_permission(permission="db-admin"):
    permissionObj = Permission().query.filter(Permission.name==permission).first()
    if not permissionObj:
        permissionObj = Permission(name=permission)
        db.session.add(permissionObj)
        db.session.commit()

    return (
        current_user.is_active
        and current_user.is_authenticated
        and current_user.has_permission(permission)
    )


def authorize_user():
    if current_app.config.get('SECURITY_AUTHORIZE_REQUEST'):
        for endpoint, role in current_app.config.get('SECURITY_AUTHORIZE_REQUEST').items():
            url = url_for(endpoint)
            if url == request.path:
                if not accessible_as_admin(role):
                    abort(403)
 

from wtforms import TelField
from wtforms.widgets import TelInput

class PhoneWidget(TelInput):
    def __call__(self, field, **kwargs):
        if kwargs.get('class'):
            kwargs['class'] = 'phone_number ' + kwargs['class'] 
        else:
            kwargs.setdefault('class', 'phone_number')
        return super(PhoneWidget, self).__call__(field, **kwargs)

class PhoneField(TelField):
    widget = PhoneWidget()

# Create customized model view class
class AuthModelView(ModelView):
    
    
    edit_template = 'admin/admin-edit.html'
    form_overrides = { 'phone_number': PhoneField }
    form_excluded_columns = ['update_datetime']
    
    def is_accessible(self):
        if hasattr(self, 'permission'):
            permission = self.permission
        else:
            permission = 'db-admin'
        
        return accessible_as_admin() and accessible_by_permission(permission)
    
    
    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not
        accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for("security.login", next=request.url))

    def render(self, template, **kwargs):
        """
        using extra js in render method allow use
        url_for that itself requires an app context
        """
        self.extra_js = [ 'https://cdn.jsdelivr.net/npm/intl-tel-input@25.3.0/build/js/intlTelInput.min.js',
                        '/static/local.js']

        return super(AuthModelView, self).render(template, **kwargs)



# Customized User model for SQL-Admin
class UserAdmin(AuthModelView):
    permission = "admin-user-edit"
    # Don't display the password on the list of Users

    def __init__(self, *args, **kwargs):
        
        self.column_exclude_list = list ('password')
        return super(UserAdmin, self).__init__(*args, **kwargs)

    form_columns = ["email", "first_name", "last_name", "phone_number", "active", "roles"]
    column_list = ["email", "first_name", "last_name", "phone_number", "active", "roles"]
    
    column_auto_select_related = True

    form_overrides = {
        'phone_number': PhoneField
    }

    def scaffold_form(self):

        form_class = super(UserAdmin, self).scaffold_form()
        form_class.password2 = PasswordField('New Password')
        return form_class

    def on_model_change(self, form, model, is_created):

        # If the password field isn't blank...
        if len(model.password2):

            # ... then encrypt the new password prior to storing it in the database. If the password field is blank,
            # the existing password in the database will be retained.
            model.password = hash_password(model.password2)
            
        if is_created:
            model.fs_uniquifier = uuid.uuid4().hex

class RoleAdmin(AuthModelView):
    form_columns = ["name", "permissions_items", "description"]
    permission = "admin-role-edit"


class PerminssonAdmin(AuthModelView):
    form_columns = ["name", "description"]
    permission = "admin-permission-edit"


class ClientStatusAdmin(AuthModelView):
    form_columns = ["status"]
    permission = "admin-userstatus-edit"


table_admin.add_view(UserAdmin(User, db.session, category='User'))
table_admin.add_view(RoleAdmin(Role, db.session, category='User'))
table_admin.add_view(PerminssonAdmin(Permission, db.session, category='User'))
table_admin.add_view(ClientStatusAdmin(ClientStatus, db.session, category='User')) #@UndefinedVariable
