from flask import Blueprint, render_template, request, flash
from flask_babel import _
from flask_security import current_user
from flask import current_app as app
from bcource.auth.forms  import LoginForm, AccountDetailsForm
from bcource.admin import User, UserStatus
from werkzeug.security import generate_password_hash, check_password_hash

from bcource import db

# Blueprint Configuration
auth_bp = Blueprint(
    'auth_bp', __name__,
    url_prefix="/account",
    template_folder='templates',
    static_folder='static'
)

@auth_bp.route('/account-details', methods=['GET', 'POST'])
def update():
    
    form = AccountDetailsForm(obj=current_user)    
            
    if form.validate_on_submit():
        user = current_user
        form.populate_obj(user)   
        db.session.commit()
        flash(_("Account details are update successfully."))
    
    return render_template("auth/create-account.html", form=form)
