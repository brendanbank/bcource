from flask import Blueprint, render_template, send_from_directory, g, flash, url_for, redirect, render_template_string
from flask import current_app as app
from flask_security import current_user
import os
from flask_security import auth_required
import flask_security.decorators as fsd
from bcource.user.user_status import UserProfileChecks, UserProfileSystemChecks
from bcource import db, menu_structure, security
from datetime import datetime, timezone

import bcource.messages as bmsg 
# Blueprint Configuration
home_bp = Blueprint(
    'home_bp', __name__,
    # url_prefix="/home",
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)

@home_bp.route('/privacy', methods=['GET'])
def privacy():
    return render_template("home/privacy-policy.html")

@home_bp.route('/tandc', methods=['GET'])
def tandc():
    return render_template("home/tandc.html")

@home_bp.route('/', methods=['GET'])
def home():

    if current_user.is_anonymous:
        return render_template("home/index.html")
    
    #check if system tables are OK for user
    UserProfileSystemChecks().validate()
        
    validators = UserProfileChecks()
    if not validators.validate():
        for validator in validators:
            if not validator.status:
                return render_template("user/profile-check.html", validator=validators)
    else:
        if not current_user.usersettings.registration_complete:
            current_user.usersettings.registration_complete = datetime.now(timezone.utc)
            db.session.commit()
            
            msg = bmsg.EmailStudentWelcomeMessage(envelop_to=current_user,
                                     user=current_user).send()
        
        
            msg = bmsg.EmailStudentCreated(
                                     envelop_to=security.datastore.find_or_create_role('student-admin').users,
                                     user=current_user.student_from_practice).send()
        
            msg = bmsg.EmailStudentApplicationToBeReviewed(envelop_to=current_user,
                                     user=current_user).send(),

    return render_template("home/index.html")

@home_bp.route('/ckeditor', methods=['GET'])
@auth_required()
def ckeditor():
    return render_template("home/ckeditor.html")


@home_bp.route('/home.test', methods=['GET'])
@auth_required()
@fsd.permissions_required('user-write')
def home2():
    return render_template("home/index.html")

@home_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')