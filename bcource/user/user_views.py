from flask import Blueprint, render_template, request, flash, request, redirect, session, url_for, jsonify, current_app
from flask_babel import _
from flask_security import current_user
from bcource.models import UserSettings, Message, User, UserMessageAssociation, Role
from flask import current_app as app
from flask_security import auth_required
from bcource.user.forms  import AccountDetailsForm, UserSettingsForm, UserMessages, MessageActionform
from werkzeug.security import generate_password_hash, check_password_hash
from bcource.helpers import get_url, message_date
from bcource.user.user_status import UserProfileChecks, UserProfileSystemChecks
from bcource import db, menu_structure
from setuptools._vendor.jaraco.functools import except_
from sqlalchemy import and_, or_
from datetime import datetime, timezone
import pytz
from flask_babel import lazy_gettext as _l
from bcource.helper_app_context import b_pagination
from jsonschema import validate, ValidationError
from bcource.filters import Filters
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


ACTION_JSON = {
  "type": "object",
  "properties": {
    "action": {
      "type": "string"
    },
    "message_ids": {  
      "type": "array",
      "items": {
        "type": "integer"
      }
    }
  },
  "required": ["action", "message_ids"] 
}


@user_bp.route('/messages/api/action', methods=['GET', 'POST'])
@auth_required()
def action():
    
    results= {"results": False,
              "errors": [],
              "messages": []}
    if not request.json:
        return jsonify(results)
    data = request.json

    try:
        validate(data,schema=ACTION_JSON)
    except ValidationError as e:
        results['errors'].append(e.message)
        return jsonify(results)
            
    results["echo"] = data
        
    messages = UserMessageAssociation().query.join(Message).filter(UserMessageAssociation.user==current_user,
                                                                       UserMessageAssociation.message_id.in_(data['message_ids'])).all()
    for message in messages:
        match data['action']:
            case "undelete":
                message.message_deleted = None
                results["messages"].append(message.message_id)
            case "unread":
                message.message_read = None
                results["messages"].append(message.message_id)
            case "read":
                message.message_read = datetime.now(timezone.utc)
                results["messages"].append(message.message_id)
            case "delete":
                message.message_deleted = datetime.now(timezone.utc)
                results["messages"].append(message.message_id)
            case _:
                results['errors'].append(f"unkonwn action {data['action']}")
                return jsonify(results)

    db.session.commit()
    results["results"] = True
    results["action"] = data['action']
    results["unread_messages"] = current_user.unread_messages
    
    return jsonify(results)

@user_bp.route('/messages/api/get/<int:id>', methods=['GET', 'POST'])
@auth_required()
def get_messages(id):
    envelop = UserMessageAssociation().query.join(Message, 
                                                  Message.id ==UserMessageAssociation.message_id).filter(
                                                      Message.id == id, 
                                                      UserMessageAssociation.user==current_user).first()
    results= {"results": False}
    if envelop:
        if envelop.message_read == None:
            envelop.message_read = datetime.now(timezone.utc)
            db.session.commit()
            
        results = {
            "results": True,
            "id": envelop.message.id, 
            "subject": envelop.message.subject,
            "created_date": envelop.message.created_date,
            "body": envelop.message.body,
            "tags": [tag.tag for tag in envelop.message.tags ],
            "from": f'{envelop.message.envelop_from}' if not current_app.config["BCOURSE_SYSTEM_USER"] == envelop.message.envelop_from.email else "do-not-reply",
            # "to": [ f'{envelop.user}' for envelop in envelop.message.envelop_to ],
            "to": f'{envelop.user}',
            "deleted": f'{message_date(envelop.message_deleted, mobile_date=True)}' if envelop.message_deleted != None else None,
            "read": f'{message_date(envelop.message_read, mobile_date=True)}' if envelop.message_read != None else None,
            }
        
    return jsonify(results)


def make_filters():

    filters = Filters("Training Filters")
    past_training_filter = filters.new_filter("read", _("Read status"))
    past_training_filter.add_filter_item( 1, _("Read"))
    past_training_filter.add_filter_item( 2, _("Unread"))
    past_training_filter.add_filter_item( 3, _("Deleted"))


    return(filters)

def make_message_select(filters, user_q=None):
    
    
    q = UserMessageAssociation().query
    
    q = q.filter(UserMessageAssociation.user==current_user)
             
    if filters.get_item_is_checked("read","1") and filters.get_item_is_checked("read","2"):
        pass
    elif filters.get_item_is_checked("read","1"):
        q = q.filter(UserMessageAssociation.message_read != None)

    elif filters.get_item_is_checked("read","2"):
        q = q.filter(UserMessageAssociation.message_read == None)

    if filters.get_item_is_checked("read","3"):
        q = q.filter(UserMessageAssociation.message_deleted != None)
    else:
        q = q.filter(UserMessageAssociation.message_deleted == None)
        
    if user_q:
        q =  q.join(Message).filter(or_(
            Message.body.like(f"%{user_q}%"),
            Message.subject.like(f"%{user_q}%"),
                                        ))
    else:
        q = q.join(Message)
    
    q = q.order_by(Message.created_date.desc())

    return (q)

@user_bp.route('/messages', methods=['GET', 'POST'])
@auth_required()
def messages():
    
    clear = request.args.getlist('submit_id')
    if clear and clear[0]=='clear':
        return redirect(url_for('user_bp.messages', show=request.args.getlist('show')))

    filters = make_filters().process_filters()


    user_q = request.args.get('q', None)

    q = make_message_select(filters, user_q)                                                 
       
    messages = b_pagination(q, per_page=22)

    
    
    return render_template("user/messages.html",
                           filters=filters,
                           user_q=user_q if user_q != None else "",
                           form=MessageActionform(),
                           page_name=_l("Messages"),
                           pagination=messages)

@user_bp.route('/message', methods=['GET', 'POST'])
@auth_required()
def message():
    form = UserMessages()
    
    get_url(form)

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

            reply_message = f'On {date_tz.astimezone().strftime("%c %Z")}, {user_message_association.message.envelop_from} wrote: <blockquote>{user_message_association.message.body}</blockquote>'

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
                                             form.body.data,
                                             tags=['User'])

            flash(_("Message sent!"))
            return redirect(url_for('user_bp.messages'))

    return render_template("user/message.html", form=form)
    

@user_bp.route('/search',methods=['GET'])
@auth_required()
def search():
    results = {}
    results.update({"results": []})

    query_term = request.args.get('q')
    
    q = User().query
    if not current_user.has_role('trainer'):
        q = q.join(User.roles).filter(Role.name == "trainer")

    if query_term:
        q = q.filter(or_( 
            User.first_name.ilike(f'%{query_term}%'), 
            User.last_name.ilike(f'%{query_term}%'),
            User.email.ilike(f'%{query_term}%')))

    r = q.order_by(User.first_name, User.last_name).limit(20).all()
            
    for user in r:
        results["results"].append({"id": user.id,  "text":  user.fullname})
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


