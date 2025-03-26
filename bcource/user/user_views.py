from flask import Blueprint, render_template, request, flash, request, redirect
from flask_babel import _
from flask_security import current_user
from bcource.models import UserSettings
from flask import current_app as app
from flask_security import auth_required
from bcource.user.forms  import AccountDetailsForm, UserSettingsForm
from werkzeug.security import generate_password_hash, check_password_hash
from bcource.helpers import get_url
from bcource.user.user_status import UserProfileChecks
from bcource import db

# Blueprint Configuration
user_bp = Blueprint(
    'user_bp', __name__,
    url_prefix="/account",
    template_folder='templates',
    static_folder='static'
)


@user_bp.route('/', methods=['GET', 'POST'])
@auth_required()
def index():
    
    validator = UserProfileChecks()
    validator.validate()
    
    return render_template("user/profile-check.html", validator=validator)

@user_bp.route('/account-details', methods=['GET', 'POST'])
@auth_required()
def update():
    
    form = AccountDetailsForm(obj=current_user)    
    url = get_url(form)
    
    if form.validate_on_submit():
        user = current_user
        form.populate_obj(user)   
        db.session.commit()
        flash(_("Account details are update successfully."))
        return redirect(url)
    
    return render_template("user/update-account.html", form=form)

@user_bp.route('/account-settings', methods=['GET', 'POST'])
@auth_required()
def settings():
    form = UserSettingsForm(obj=current_user.usersettings)
    
    url = get_url(form)
    
    if form.validate_on_submit():
        settings = current_user.usersettings
        if not settings:
            settings = UserSettings()
            settings.user = current_user
            db.session.add(settings)
        form.populate_obj(settings)
        
        db.session.commit()
        flash(_("Account Settings are update successfully."))
        return redirect(url)
    
    return render_template("user/update-settings.html", form=form)
