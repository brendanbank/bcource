from flask import Blueprint, render_template, request, flash, request, redirect, session, url_for, jsonify
from flask_babel import _
from flask_security import current_user
from bcource.models import UserSettings, Message, User, UserMessageAssociation
from flask import current_app as app
from flask_security import auth_required
from bcource.user.forms  import AccountDetailsForm, UserSettingsForm, UserMessages
from werkzeug.security import generate_password_hash, check_password_hash
from bcource.helpers import get_url
from bcource.user.user_status import UserProfileChecks, UserProfileSystemChecks
from bcource import db, menu_structure
from setuptools._vendor.jaraco.functools import except_
from sqlalchemy import and_, or_
from datetime import datetime, timezone
import pytz
from flask_babel import lazy_gettext as _l

# Blueprint Configuration
user_bp = Blueprint(
    'user_bp', __name__,
    url_prefix="/account",
    template_folder='templates',
    static_folder='static'
)

@user_bp.route('/practice', methods=['GET'])
@auth_required()
def set_practice():
    url = request.args.get('url')
    practice_id = request.args.get('practice')
    try:
        session['practice'] = int(practice_id)
    except:
        pass
    return redirect(url)


@user_bp.route('/', methods=['GET', 'POST'])
@auth_required()
def index():
    
    #check if system tables are OK for user
    UserProfileSystemChecks()
    
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


@user_bp.route('/messages', methods=['GET', 'POST'])
@auth_required()
def messages():
    q = UserMessageAssociation().query.join(Message).filter(and_(UserMessageAssociation.user==current_user,
                                                                UserMessageAssociation.message_id==Message.id,
                                                                UserMessageAssociation.message_deleted == None)).order_by(
                                                                    Message.created_date.desc())

    messages = q.all()
                                                 
    message_selected_id = request.args.get('m')
    message_selected=None
    if message_selected_id == None and messages:
        message_selected_id = messages[0].message.id
    
    try:
        message_selected_id = int(message_selected_id)
    except:
        message_selected_id = None
    
    # mark message as read
    if message_selected_id:
        user_association = UserMessageAssociation().query.join(Message).filter(and_(UserMessageAssociation.user==current_user,
                                                                UserMessageAssociation.message_id==message_selected_id))
        a = user_association.first()
        mark_unread = request.args.get('u')
        msg_delete = request.args.get('d')
        
        if a and mark_unread != "1" and msg_delete != "1" :
            a.message_read = datetime.now(timezone.utc)
            db.session.commit()
            message_selected = a.message
        elif(a and mark_unread == "1"):
            a.message_read = None
            db.session.commit()
            message_selected = a.message
        elif(a and  msg_delete == "1" ):
            a.message_deleted = datetime.now(timezone.utc)
            db.session.commit()
            messages = q.all()
            if messages:
                message_selected = messages[0].message
            else:
                message_selected = None



    return render_template("user/messages.html",messages=q.all(), message_selected=message_selected)

@user_bp.route('/message', methods=['GET', 'POST'])
@auth_required()
def message():
    form = UserMessages()
    
    reply_message_id = request.args.get('reply')
    
    
    if reply_message_id and not form.is_submitted():
        
        user_message_association = UserMessageAssociation().query.join(Message).filter(and_(UserMessageAssociation.user==current_user,
                                                                UserMessageAssociation.message_id==reply_message_id)).first()
                            
        if not user_message_association:
            flash(_("Message does not exists!"), 'error')
            return redirect(url_for('user_bp.messages'))                          

        if user_message_association:
            
            date = user_message_association.message.created_date
            date_tz = date.replace(tzinfo=pytz.timezone('UTC'))            
                        
            reply_message = f'On {date_tz.astimezone().strftime("%c %Z")}, {user_message_association.message.envelop_from} wrote: {user_message_association.message.body}'
            
            form.body.data = reply_message

            form.envelop_tos.data = [f"{user_message_association.message.envelop_from.id}"]
            form.envelop_tos.choices = [(user_message_association.message.envelop_from.id,user_message_association.message.envelop_from.fullname)]
            
            form.subject.data = f'Re: {user_message_association.message.subject}'
    
    if form.is_submitted():
        if form.envelop_tos.data:
            choices = []
            envelop_tos = User().query.filter(User.id.in_(form.envelop_tos.data)).all()
            for user in envelop_tos:
                choices.append((user.id, user.fullname ))
            
            form.envelop_tos.choices = choices
        else:
            form.envelop_tos.choices = form.envelop_tos.data

        
    if form.validate_on_submit():
        envelop_tos = User().query.filter(User.id.in_(form.envelop_tos.data)).all()
        if not envelop_tos:
            flash(_("Could not find user!"))
        else:
            message = Message.create_db_message(db.session,
                                             current_user,
                                             envelop_tos,
                                             form.subject.data,
                                             form.body.data)
    
            flash(_("Message sent!"))
            return redirect(url_for('user_bp.messages'))

    return render_template("user/message.html", form=form)
    

@user_bp.route('/search',methods=['GET'])
def search():
    results = {}
    results.update({"results": []})

    query_term = request.args.get('q')
    r = []
    
    if query_term:
        r = User().query.filter(or_( 
            User.first_name.ilike(f'%{query_term}%'), 
            User.last_name.ilike(f'%{query_term}%'),
            User.email.ilike(f'%{query_term}%'))).order_by(User.first_name, User.last_name).all()

    for student in r:
        results["results"].append({"id": student.id,  "text":  student.fullname})
    return jsonify(results)


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


