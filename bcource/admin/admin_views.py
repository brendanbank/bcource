from bcource import db
from bcource import table_admin
from bcource.models import User, Role, Permission, Content
from flask_security import current_user, hash_password
from wtforms.fields import PasswordField
from flask import current_app, url_for, abort, redirect, request, flash
from flask_admin import BaseView, expose
from flask_admin.menu import MenuLink
import uuid
from flask_security import naive_utcnow
from bcource.admin.helper import AuthModelView, PhoneField, CkModelView, accessible_as_admin
from bcource.helpers import can_impersonate
from flask_admin.actions import action
from flask_babel import lazy_gettext as _l
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

    # Enable search functionality
    column_searchable_list = ['email', 'first_name', 'last_name', 'phone_number']

    # Enable filtering
    column_filters = ['active', 'roles']

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

    @action('impersonate', _l('Impersonate User'), _l('Are you sure you want to impersonate the selected user?'))
    def action_impersonate(self, ids):
        """Action to impersonate a user from the admin list view."""
        try:
            # Only allow impersonating one user at a time
            if len(ids) > 1:
                flash(_l('You can only impersonate one user at a time.'), 'error')
                return

            user_id = ids[0]
            target_user = User.query.get(user_id)

            if not target_user:
                flash(_l('User not found.'), 'error')
                return

            # Check if admin can impersonate this user
            can_impersonate_user, error_msg = can_impersonate(current_user._get_current_object(), target_user)
            if not can_impersonate_user:
                flash(error_msg, 'error')
                return

            # Redirect to the impersonation route
            return redirect(url_for('user_bp.impersonate_user', user_id=user_id))

        except Exception as e:
            flash(_l('Error initiating impersonation: %(error)s', error=str(e)), 'error')

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
    form_columns = ('tag', 'text', 'lang', 'subject')
    edit_template = 'admin/cms.html'
    column_list = ['tag', 'lang']
    permission = "cms-admin"
    column_searchable_list = ['tag']

    def get_query(self):
        return self.session.query(self.model).filter(not_(self.model.tag.regexp_match(r'\_\d+$')))
    
    def get_count_query(self):
        return self.session.query(func.count('*')).filter(not_(self.model.tag.regexp_match(r'\_\d+$')))   

table_admin.add_view(ContentModelView(Content, db.session, ckfields=["text"])) #@UndefinedVariable


class ApiTokenView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        token = None
        expires_in = current_app.config['JWT_EXPIRATION_SECONDS']
        if request.method == 'POST':
            from bcource.admin_api.auth import generate_admin_token
            token = generate_admin_token(current_user._get_current_object())
        return self.render('admin/api_token.html', token=token, expires_in=expires_in)

    def is_accessible(self):
        return accessible_as_admin()

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)
            else:
                return redirect(url_for("security.login", next=request.url))

table_admin.add_view(ApiTokenView(name='API Token', category='User'))

