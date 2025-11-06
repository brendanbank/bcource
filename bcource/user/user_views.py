from flask import Blueprint, render_template, request, flash, request, redirect, session, url_for, jsonify, current_app, abort
from flask_babel import _
from flask_security import current_user, logout_user
from bcource.models import UserSettings, Message, User, UserMessageAssociation, Role, MessageTag, Training, TrainingEnroll, Student, WebAuthn
from flask import current_app as app
from flask_security import auth_required
from bcource.user.forms  import AccountDetailsForm, UserSettingsForm, UserMessages, MessageActionform, SupportForm, PublicSupportForm
from werkzeug.security import generate_password_hash, check_password_hash
from bcource.helpers import (get_url, message_date, config_value as cv,
                             is_impersonating, get_original_user, get_impersonated_user,
                             start_impersonation, stop_impersonation, can_impersonate)
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
from bcource.messages import SendEmail
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
            "created_date": f'{message_date(envelop.message.created_date, mobile_date=True)}',
            "body": envelop.message.body,
            "tags": [tag.tag for tag in envelop.message.tags ],
            "from": f'{envelop.message.envelop_from}' if not current_app.config["BCOURSE_SYSTEM_USER"] == envelop.message.envelop_from.email else "do-not-reply",
            # "to": [ f'{envelop.user}' for envelop in envelop.message.envelop_to ],
            "to": f'{envelop.user}',
            "deleted": f'{message_date(envelop.message_deleted, mobile_date=True)}' if envelop.message_deleted != None else None,
            "read": f'{message_date(envelop.message_read, mobile_date=True)}' if envelop.message_read != None else None,
            "unread_messages": current_user.unread_messages
            }
        
    return jsonify(results)


def make_filters():

    filters = Filters("Training Filters")
    past_training_filter = filters.new_filter("read", _("Read status"))
    past_training_filter.add_filter_item( 1, _("Read"))
    past_training_filter.add_filter_item( 2, _("Unread"))
    past_training_filter.add_filter_item( 3, _("Deleted"))
    
    tags_filter = filters.new_filter("tag", _("Tags"))
    for tagobj in MessageTag().query.filter(MessageTag.hidden == False).order_by(MessageTag.tag).all():
        tags_filter.add_filter_item( tagobj.id, tagobj.tag)


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

    items_checked = filters.get_items_checked('tag')

    if items_checked:
        q = q.join(Message.tags).filter(MessageTag.id.in_(items_checked))

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
    training_id = request.args.get('training_id',None,int)
    
    
    if training_id and not form.is_submitted():
        training = Training().query.get(training_id)
        users = [ enrollemnt.student.user for enrollemnt in training.trainingenrollments ]
        
        uids =  [str(user.id) for user in users]
        form.envelop_tos.data = uids
        form.subject.data = training.name
        
        form.envelop_tos.choices = [(user.id, user.fullname) for user in users]

    elif reply_message_id and not form.is_submitted():

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
            flash(_("Could not find users!"))
        else:
            m = SendEmail(envelop_to=envelop_tos, 
                          envelop_from=current_user,
                          has_content=True,
                          body=form.body.data,
                          taglist=['email', 'form'],
                          subject=form.subject.data)
            
            m.send()
            
            flash(_("Message sent!"))
            return redirect(url_for('user_bp.messages'))

    return render_template("user/message.html", form=form)
    

@user_bp.route('/search',methods=['GET'])
@auth_required()
def search():
    results = {}
    results.update({"results": []})

    query_term = request.args.get('q')
    
    exclude = request.args.getlist('exclude',int)
    
    q = User().query
    if not current_user.has_role('trainer'):
        q = q.join(User.roles).filter(Role.name == "trainer")

    if exclude:
        q = q.filter(~User.id.in_(exclude))
    
    if query_term:
        q = q.filter(or_( 
            User.first_name.ilike(f'%{query_term}%'), 
            User.last_name.ilike(f'%{query_term}%'),
            User.email.ilike(f'%{query_term}%')))

    r = q.order_by(User.first_name, User.last_name).all()
            
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


@user_bp.route('/support', methods=['GET', 'POST'])
@auth_required()
def support():
    form = SupportForm()
    
    url = get_url(form)
    
    if form.validate_on_submit():
        # Find or create the support user
        support_user = User.query.filter_by(email=cv('SUPPORT_EMAIL')).first()
        if not support_user:
            # Create support user if it doesn't exist
            support_user = User(
                email=cv('SUPPORT_EMAIL'),
                first_name='Support',
                last_name='Team',
                active=True
            )
            db.session.add(support_user)
            db.session.commit()
        
        # Send email to support
        msg = SendEmail(
            envelop_to=[support_user],
            envelop_from=current_user,
            body=f"""
            <p><strong>Support Request from {current_user.fullname} ({current_user.email})</strong></p>
            <hr>
            <p><strong>Subject:</strong> {form.subject.data}</p>
            <p><strong>Message:</strong></p>
            <p>{form.body.data}</p>
            """,
            subject=f"Support Request: {form.subject.data}",
            taglist=['support', 'email']
        )
        msg.send()
        
        # Also send a copy to the user for their records
        confirmation_msg = SendEmail(
            envelop_to=[current_user],
            envelop_from=support_user,
            body=f"""
            <p>Thank you for contacting support. We have received your message and will respond as soon as possible.</p>
            <hr>
            <p><strong>Your message:</strong></p>
            <p><strong>Subject:</strong> {form.subject.data}</p>
            <p>{form.body.data}</p>
            """,
            subject=f"Support Request Received: {form.subject.data}",
            taglist=['support', 'email']
        )
        confirmation_msg.send()
        
        flash(_("Your message has been sent to support. You will receive a response soon."), 'success')
        return redirect(url_for('home_bp.home'))
    
    return render_template("user/support.html", form=form)


@user_bp.route('/support-public', methods=['GET', 'POST'])
def support_public():
    """Support form for non-authenticated users"""
    form = PublicSupportForm()
    
    url = get_url(form)
    
    if form.validate_on_submit():
        # Find or create the support user
        support_user = User.query.filter_by(email=cv('SUPPORT_EMAIL')).first()
        if not support_user:
            # Create support user if it doesn't exist
            support_user = User(
                email=cv('SUPPORT_EMAIL'),
                first_name='Support',
                last_name='Team',
                active=True
            )
            db.session.add(support_user)
            db.session.commit()
        
        # Create or find the sender user
        sender_user = User.query.filter_by(email=form.email.data).first()
        if not sender_user:
            # Create a temporary user for tracking purposes
            sender_user = User(
                email=form.email.data,
                first_name=form.name.data.split()[0] if form.name.data else 'Guest',
                last_name=' '.join(form.name.data.split()[1:]) if form.name.data and len(form.name.data.split()) > 1 else 'User',
                active=False  # Not an active user, just for message tracking
            )
            db.session.add(sender_user)
            db.session.commit()
        
        # Send email to support
        msg = SendEmail(
            envelop_to=[support_user],
            envelop_from=sender_user,
            body=f"""
            <p><strong>Support Request from {form.name.data} ({form.email.data})</strong></p>
            <p><em>Note: This is from a non-authenticated user</em></p>
            <hr>
            <p><strong>Subject:</strong> {form.subject.data}</p>
            <p><strong>Message:</strong></p>
            <p>{form.body.data}</p>
            """,
            subject=f"Support Request: {form.subject.data}",
            taglist=['support', 'email', 'public']
        )
        msg.send()
        
        # Send confirmation to the user
        confirmation_msg = SendEmail(
            envelop_to=[sender_user],
            envelop_from=support_user,
            body=f"""
            <p>Thank you for contacting support. We have received your message and will respond to {form.email.data} as soon as possible.</p>
            <hr>
            <p><strong>Your message:</strong></p>
            <p><strong>Subject:</strong> {form.subject.data}</p>
            <p>{form.body.data}</p>
            """,
            subject=f"Support Request Received: {form.subject.data}",
            taglist=['support', 'email', 'public']
        )
        confirmation_msg.send()
        
        flash(_("Your message has been sent to support. You will receive a response at the email address provided."), 'success')
        return redirect(url_for('home_bp.home'))
    
    return render_template("user/support_public.html", form=form)


@user_bp.route('/delete-account', methods=['GET', 'POST'])
@auth_required()
def delete_account():
    """Allow user to delete their account (GDPR Right to be Forgotten)"""
    
    # Check if user has any active enrollments in trainings
    active_enrollments = TrainingEnroll.query.join(Student).filter(
        Student.user_id == current_user.id
    ).all()
    
    # Add flag to indicate if training has ended (for display purposes)
    current_time = datetime.now(timezone.utc)
    for enrollment in active_enrollments:
        if enrollment.training.trainingevents:
            last_event = enrollment.training.trainingevents[-1]
            # Handle both timezone-aware and naive datetimes
            if last_event.end_time.tzinfo is None:
                # If naive, assume UTC
                enrollment.is_past_training = last_event.end_time.replace(tzinfo=timezone.utc) < current_time
            else:
                enrollment.is_past_training = last_event.end_time < current_time
        else:
            enrollment.is_past_training = False
    
    if request.method == 'POST':
        # Check again to ensure no enrollments exist
        if active_enrollments:
            flash(_("You cannot delete your account while you are enrolled in training courses. Please unenroll from all trainings first."), 'error')
            return redirect(url_for('user_bp.delete_account'))
        
        # Get confirmation token from form
        confirmation = request.form.get('confirmation', '').strip().upper()
        
        if confirmation != 'DELETE':
            flash(_("Please type 'DELETE' to confirm account deletion."), 'error')
            return redirect(url_for('user_bp.delete_account'))
        
        # Store user info for logging before deletion
        user_email = current_user.email
        user_id = current_user.id
        user_fullname = current_user.fullname
        
        try:
            # Log the deletion request
            app.logger.info(f"User account deletion requested: ID={user_id}, Email={user_email}")
            
            # Send notification to support before deleting
            support_email = cv('SUPPORT_EMAIL')
            support_user = User.query.filter_by(email=support_email).first()
            if not support_user:
                # Create support user if it doesn't exist
                support_user = User(
                    email=support_email,
                    first_name='Support',
                    last_name='Team',
                    active=True
                )
                db.session.add(support_user)
                db.session.commit()
            
            # Send notification email to support
            notification_msg = SendEmail(
                envelop_to=[support_user],
                envelop_from=current_user,
                body=f"""
                <p><strong>User Account Deletion Notification</strong></p>
                <hr>
                <p>A user has deleted their account from the system.</p>
                <p><strong>Name:</strong> {user_fullname}</p>
                <p><strong>Email:</strong> {user_email}</p>
                <p><strong>User ID:</strong> {user_id}</p>
                <p><strong>Deletion Time:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                """,
                subject=f"Account Deletion: {user_fullname}",
                taglist=['account-deletion', 'notification']
            )
            notification_msg.send()
            
            # Delete the user (cascade will handle related records)
            user_to_delete = User.query.get(user_id)
            
            # Logout the user first
            logout_user()
            
            # Delete the user account
            db.session.delete(user_to_delete)
            db.session.commit()
            
            flash(_("Your account has been successfully deleted. We're sorry to see you go."), 'success')
            return redirect(url_for('home_bp.home'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error deleting user account: {str(e)}")
            flash(_("An error occurred while deleting your account. Please contact support."), 'error')
            return redirect(url_for('user_bp.delete_account'))
    
    # GET request - show confirmation page
    return render_template("user/delete-account.html",
                          active_enrollments=active_enrollments,
                          enrollment_count=len(active_enrollments))


# ============================================================================
# User Impersonation Routes
# ============================================================================

@user_bp.route('/impersonate/<int:user_id>', methods=['GET', 'POST'])
@auth_required()
def impersonate_user(user_id):
    """Start impersonating a user (admin only)."""

    # Security check: only admins with 2FA can impersonate
    super_user_role = cv('SUPER_USER_ROLE')
    if not current_user.has_role(super_user_role):
        flash(_("You do not have permission to impersonate users."), 'error')
        abort(403)

    if not current_user.tf_primary_method:
        flash(_("Two-factor authentication is required to impersonate users."), 'error')
        return redirect(url_for('security.two_factor_setup'))

    # For GET requests, show confirmation page
    # For POST requests, perform the impersonation
    if request.method == 'GET':
        # Get the target user for confirmation
        target_user = User.query.get(user_id)
        if not target_user:
            flash(_("User not found."), 'error')
            return redirect(request.referrer or url_for('admin.index'))

        # Check if we can impersonate
        can_impersonate_user, error_msg = can_impersonate(current_user._get_current_object(), target_user)
        if not can_impersonate_user:
            flash(error_msg, 'error')
            return redirect(request.referrer or url_for('admin.index'))

        # Show confirmation page
        return render_template('user/impersonate_confirm.html', target_user=target_user)

    # POST request - perform impersonation
    success, message = start_impersonation(user_id)

    if success:
        flash(message, 'success')
        return redirect(url_for('user_bp.index'))
    else:
        flash(message, 'error')
        return redirect(request.referrer or url_for('home_bp.home'))


@user_bp.route('/stop-impersonate', methods=['POST', 'GET'])
@auth_required()
def stop_impersonate():
    """Stop impersonating and return to admin account."""

    # Stop impersonation
    success, message = stop_impersonation()

    if success:
        flash(message, 'info')
    else:
        flash(message, 'error')

    # Redirect to admin area
    return redirect(url_for('admin.index'))


# ============================================================================
# WebAuthn / Biometric Authentication Routes
# ============================================================================

@user_bp.route('/security-keys', methods=['GET'])
@auth_required()
def security_keys():
    """Manage WebAuthn security keys and biometric authentication."""

    # Get all registered WebAuthn credentials for the current user
    credentials = WebAuthn.query.filter_by(user_id=current_user.id).all()

    return render_template("user/security-keys.html",
                          credentials=credentials,
                          page_name=_l("Security Keys & Biometrics"))


@user_bp.route('/security-keys/delete/<int:credential_id>', methods=['POST'])
@auth_required()
def delete_security_key(credential_id):
    """Delete a WebAuthn credential."""

    credential = WebAuthn.query.filter_by(
        id=credential_id,
        user_id=current_user.id
    ).first()

    if not credential:
        flash(_("Security key not found."), 'error')
        return redirect(url_for('user_bp.security_keys'))

    # Store credential name for flash message
    credential_name = credential.name or "Unnamed credential"

    # Delete the credential
    db.session.delete(credential)
    db.session.commit()

    flash(_("Security key '%(name)s' has been removed.", name=credential_name), 'success')
    return redirect(url_for('user_bp.security_keys'))


