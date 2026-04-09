from flask import Blueprint, render_template, send_from_directory, g, flash, url_for, redirect, render_template_string, request, jsonify
from flask import current_app as app
from flask_security import current_user
import os
from flask_security import auth_required
import flask_security.decorators as fsd
from bcource.user.user_status import UserProfileChecks, UserProfileSystemChecks
from bcource import db, menu_structure, security
from datetime import datetime, timezone
from bcource.models import UserSettings, TranslationFeedback

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
def home(error_msg=None):

    if current_user.is_anonymous:
        return redirect(url_for('security.login'))
    
    #check if system tables are OK for user
    UserProfileSystemChecks().validate()
        
    validators = UserProfileChecks()
    if not validators.validate():
        if not error_msg:
            error_msg = 'no_profile_complete'
            
        for validator in validators:
            if not validator.status:
                return render_template("home/index.html", error_msg=error_msg, validator=validators)
    else:
        if not current_user.usersettings:
            user_setting = UserSettings()
            current_user.usersettings = user_setting
            db.session.commit()
        
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

    return render_template("home/index.html", validator=validators, error_msg=error_msg)

@home_bp.route('/ckeditor', methods=['GET'])
@auth_required()
def ckeditor():
    return render_template("home/ckeditor.html")


@home_bp.route('/home.test', methods=['GET'])
@auth_required()
@fsd.permissions_required('user-write')
def home2():
    return render_template("home/index.html")

@home_bp.route('/translation-feedback', methods=['POST'])
def translation_feedback():
    data = request.get_json(silent=True) or {}
    feedback_text = (data.get('feedback') or '').strip()
    if not feedback_text:
        return jsonify({'ok': False, 'error': 'empty'}), 400

    fb = TranslationFeedback(
        url=data.get('url', '')[:512],
        lang=data.get('lang', 'en')[:10],
        page_title=data.get('page_title', '')[:256],
        feedback=feedback_text,
        user_id=current_user.id if not current_user.is_anonymous else None,
    )
    db.session.add(fb)
    db.session.commit()
    return jsonify({'ok': True})


@home_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')