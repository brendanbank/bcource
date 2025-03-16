from flask import Blueprint, render_template, request, flash
from flask_babel import _
from flask_security import current_user
from flask import current_app as app
from bcource.user.forms  import LoginForm, AccountDetailsForm
from werkzeug.security import generate_password_hash, check_password_hash

from bcource import db

# Blueprint Configuration
user_bp = Blueprint(
    'user_bp', __name__,
    url_prefix="/account",
    template_folder='templates',
    static_folder='static'
)

@user_bp.route('/account-details', methods=['GET', 'POST'])
def update():
    
    form = AccountDetailsForm(obj=current_user)    
            
    if form.validate_on_submit():
        user = current_user
        form.populate_obj(user)   
        db.session.commit()
        flash(_("Account details are update successfully."))
    
    return render_template("user/update-account.html", form=form)
