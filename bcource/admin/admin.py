from .. import db
from .. import admin_views
from ..models import User, Role, Permission
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user, hash_password
from wtforms.fields import PasswordField
from flask import current_app, url_for, abort, redirect, request
from flask_security import SmsSenderBaseClass

from flask_admin.menu import MenuLink

class MainIndexLink(MenuLink):
    def get_url(self):
        return url_for("home_bp.home")


admin_views.add_link(MainIndexLink(name="Main Page"))

def accessible_as_admin(role="admin"):
    return (
        current_user.is_active
        and current_user.is_authenticated
        and current_user.has_role(role)
    )
    
def accessible_by_permission(permission="db-admin"):
    return (
        current_user.is_active
        and current_user.is_authenticated
        and current_user.has_permission(permission)
    )


def authorize_user():
    
    for endpoint, role in current_app.config['SECURITY_AUTHORIZE_REQUEST'].items():
        url = url_for(endpoint)
        if url == request.path:
            if not accessible_as_admin(role):
                abort(403)

# Create customized model view class
class AuthModelView(ModelView):
    def is_accessible(self):
        if hasattr(self, 'permission'):
            permission = self.permission
        else:
            permission = 'db-admin'
            
        return accessible_as_admin() and accessible_by_permission(permission)
        # return accessible_as_admin() 
        # accessible_by_permission(permission)
    
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

# Customized User model for SQL-Admin
class UserAdmin(AuthModelView):

    # Don't display the password on the list of Users
    column_exclude_list = list = ('password',)

    form_excluded_columns = ('password',)

    form_columns = ["email", "first_name", "last_name", "phone_number", "active", "roles"]
    column_list = ["email", "first_name", "last_name", "phone_number", "active", "roles"]
    
    column_auto_select_related = True
    
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

class RoleAdmin(AuthModelView):
    form_columns = ["name", "permissions_items", "description"]

class PerminssonAdmin(AuthModelView):
    form_columns = ["name", "description"]



admin_views.add_view(UserAdmin(User, db.session))
admin_views.add_view(RoleAdmin(Role, db.session))
admin_views.add_view(PerminssonAdmin(Permission, db.session))