from flask import Blueprint, render_template, send_from_directory, g, flash
from flask import current_app as app
from flask_security import current_user
import os
from flask_security import auth_required
import flask_security.decorators as fsd
from bcource.user.user_status import UserProfileChecks, UserProfileSystemChecks

# Blueprint Configuration
home_bp = Blueprint(
    'home_bp', __name__,
    # url_prefix="/home",
    template_folder='templates',
    static_folder='static',
    static_url_path='/home/static'
)

@home_bp.route('/', methods=['GET'])
@auth_required()
def home():
    # return render_template("home/index.html")

    #check if system tables are OK for user
    UserProfileSystemChecks().validate()
    
    validator = UserProfileChecks()
    validator.validate()
    
    return render_template("user/profile-check.html", validator=validator)
    
    return render_template("user/profile-check.html", validator=validator)


@home_bp.route('/ckeditor', methods=['GET'])
@auth_required()
def ckeditor():
    return render_template("home/ckeditor.html")


@home_bp.route('/home.test', methods=['GET'])
@auth_required()
@fsd.permissions_required('user-write')
def home2():
    print (g.identity)
    return render_template("home/index.html")

@home_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')