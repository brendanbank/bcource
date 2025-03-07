from flask import Blueprint, render_template, request
from flask import current_app as app

from .forms  import LoginForm, CreateAccountForm

# Blueprint Configuration
auth_bp = Blueprint(
    'auth_bp', __name__,
    url_prefix="/account",
    template_folder='templates',
    static_folder='static'
)

@auth_bp.route('/login', methods=['GET', 'POST'])
def home():

    form = LoginForm()
    return render_template("auth/login.html", form=form)

@auth_bp.route('/create-account', methods=['GET', 'POST'])
def new():
    
    form = CreateAccountForm()
    
    print (request.form )
    return render_template("auth/create-account.html", form=form)
