from bcource import db
from bcource import table_admin
from bcource.models import User, Role, Permission, Content
from flask_security import current_user, hash_password
from wtforms.fields import PasswordField
from flask import current_app, url_for, abort, redirect, request
from flask_security import SmsSenderBaseClass
from flask_admin.menu import MenuLink
import uuid
from flask_security import naive_utcnow
from bcource.admin.helper import AuthModelView, PhoneField, CkModelView
from sqlalchemy import not_, func


class MainIndexLink(MenuLink):
    def get_url(self):
        return url_for("home_bp.home")

table_admin.add_link(MainIndexLink(name="Main Page"))

# Customized User model for SQL-Admin
class UserAdmin(AuthModelView):
    permission = "admin-user-edit"
    # Don't display the password on the list of Users

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
            model.confirmed_at = naive_utcnow()

class RoleAdmin(AuthModelView):
    form_columns = ["name", "permissions_items", "description"]
    permission = "admin-role-edit"


class PerminssonAdmin(AuthModelView):
    form_columns = ["name", "description"]
    permission = "admin-permission-edit"


table_admin.add_view(UserAdmin(User, db.session, category='User'))
table_admin.add_view(RoleAdmin(Role, db.session, category='User'))
table_admin.add_view(PerminssonAdmin(Permission, db.session, category='User'))


class ContentModelView(CkModelView, AuthModelView):
    column_display_pk = True
    form_columns = ('tag', 'text', 'lang')
    edit_template = 'admin/cms.html'
    column_list = ['tag', 'lang']
    permission = "cms-admin"
    column_searchable_list = ['tag']

    def get_query(self):
        return self.session.query(self.model).filter(not_(self.model.tag.regexp_match(r'\_\d+$')))
    
    def get_count_query(self):
        return self.session.query(func.count('*')).filter(not_(self.model.tag.regexp_match(r'\_\d+$')))   

table_admin.add_view(ContentModelView(Content, db.session, ckfields=["text"])) #@UndefinedVariable

