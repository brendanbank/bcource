from flask_security.models.sqla import FsModels
from sqlalchemy import ForeignKey, Table, Column
from flask import current_app as app, flash, session
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user, login_user as flask_security_login_user
from flask import url_for, current_app, request, abort, redirect
from flask_principal import Identity, Permission, RoleNeed, identity_changed
from collections import OrderedDict
import pytz
import string
import secrets
import phonenumbers
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, urlencode
from flask_babel import _
from flask_babel import lazy_gettext as _l
import nh3
from jinja2.filters import do_mark_safe
from datetime import timedelta, datetime
from copy import deepcopy



def is_safe_url(target):
    """Validate that redirect target is safe (same host or relative)."""
    target = target.replace('\\', '/')
    test_url = urlparse(urljoin(request.host_url, target))
    ref_url = urlparse(request.host_url)
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def has_trainer_role():
    admin_has_role(["trainer"])
    if not current_user.tf_primary_method:
        from bcource.errors import HTTPExceptionMustHaveTwoFactorEnabled
        raise(HTTPExceptionMustHaveTwoFactorEnabled())
    
def nh3_save(txt):
    attributes = deepcopy(nh3.ALLOWED_ATTRIBUTES)
    return do_mark_safe(nh3.clean(txt))

def message_date(db_datetime_notz, mobile_date=False):
    dt = db_datetime(db_datetime_notz)
    TZ_NAME = app.config.get('BCOURCE_TZ', 'Europe/Amsterdam')
    TZ = pytz.timezone(TZ_NAME)
    if mobile_date:
         return dt.astimezone(TZ).strftime("%a, %b %d %Y, %H:%M %p %Z")
    elif (datetime.utcnow().astimezone(TZ) - dt.astimezone()) < timedelta(hours=22):
        return dt.astimezone(TZ).strftime("%H:%M")
    else:
        return dt.astimezone(TZ).strftime("%-m/%d")
    
    

def add_url_argument(url, key, value):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    # Add or update the new argument
    query_params[key] = [value] # parse_qs returns lists of values

    new_query_string = urlencode(query_params, doseq=True)

    new_url = urlunparse(parsed_url._replace(query=new_query_string))
    return new_url

def db_datetime(db_datetime_notz):
    
    return db_datetime_notz.replace(tzinfo=pytz.timezone('UTC'))

def ordinal(n):
    return str(n)+("th" if 4<=n%100<=20 else {1:"st",2:"nd",3:"rd"}.get(n%10, "th"))

def db_datetime_str(db_datetime_notz,fmt="%a, %b %-d %Y, %H:%M %p %Z"):
    dt = db_datetime(db_datetime_notz)
    TZ_NAME = app.config.get('BCOURCE_TZ', 'Europe/Amsterdam')
    TZ = pytz.timezone(TZ_NAME)    
    return dt.astimezone(TZ).strftime(fmt).replace("{th}", ordinal(dt.day))

def safe_redirect(url, default='home_bp.home'):
    """Redirect to url only if it's safe (same host), otherwise redirect to default."""
    if url and is_safe_url(url):
        return redirect(url)
    return redirect(url_for(default))

def get_url (form=None,default=None, back_button=False):

    if not default:
        default = 'home_bp.home'

    first_url = None

    if form and form.is_submitted():
        url=form.url.data
    else:
        if request.args.get('first_url'):
            first_url = request.args.get('first_url')
            if back_button:
                url = first_url
            else:
                url = request.referrer
                if not url:
                    url = request.args.get('first_url')
                    if url:
                        add_url_argument(url, 'first_url', first_url)

                else:
                    url = add_url_argument(url, 'first_url', first_url)
        else:
            url = request.args.get('url')


    if url == None:
        if request.referrer:
            url = request.referrer

    for u in ['user_bp.settings', 'user_bp.update']:
        if url_for(u) == url:
            url = url_for(default)
            break
    if form:
        if url:
            form.url.data = url
        else:
            form.url.data=url_for(default)
    if url == None:
        url = url_for(default)

    if not is_safe_url(url):
        url = url_for(default)

    return(url)

def admin_has_role(roles):
    _roles = roles
    if type(roles) == str:
        _roles = [roles]
        
    _roles.append(current_app.config['BCOURSE_SUPER_USER_ROLE'])
    perms = [Permission(RoleNeed(role)) for role in _roles]
    for perm in perms:
        if perm.can():
            return True
    
    abort(403)

class MyFsModels(FsModels):
    
    @classmethod
    def set_db_info(
        cls,
        *,
        base_model,
        user_table_name="user",
        role_table_name="role",
        webauthn_table_name="webauthn",
    ):
        """Initialize Model.
        This MUST be called PRIOR to declaring your User/Role/WebAuthn model in order
        for table name altering to work.

        .. note::
            This should only be used if you are utilizing the sqla data
            models. With your own models you would need similar but slightly
            different code.
        """
        cls.base_model = base_model
        cls.user_table_name = user_table_name
        cls.role_table_name = role_table_name
        cls.webauthn_table_name = webauthn_table_name
        cls.roles_users = Table(
            "roles_users",
            cls.base_model.metadata,
            Column(
                "user_id", ForeignKey(f"{cls.user_table_name}.id", ondelete="CASCADE"), primary_key=True
            ),
            Column(
                "role_id", ForeignKey(f"{cls.role_table_name}.id"), primary_key=True
            ),
        )
        

def config_value(key, app=None, default=None, strict=True):
    app = app or current_app
    key = f"BCOURSE_{key.upper()}"
    # protect against spelling mistakes
    if strict and key not in app.config:
        raise ValueError(f"Key {key} doesn't exist")
    return app.config.get(key, default)


    
def genpwd():
    letters = string.ascii_letters
    digits = string.digits
    special_chars = string.punctuation
    
    alphabet = letters + digits + special_chars
    
    # fix password length
    pwd_length = 16
    while True:
        pwd = ''
        for i in range(pwd_length):
            pwd += ''.join(secrets.choice(alphabet))
    
        break
    
    return (pwd)


def format_email(email):
    return (f'<a href="mailto:{email}" target="_blank" class="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover">{email}</a>')

# Define the country code for which you want local notation
TARGET_LOCAL_COUNTRY_CODE = "NL" # For Netherlands

def format_phone_link(phone_number_str, parsed_number):
    return (f'<a href="tel:{phone_number_str}" class="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover">{parsed_number}</a>')


def format_phone_number(phone_number_str, user_country_code=None):
    """
    Formats a phone number. If the number is from the TARGET_LOCAL_COUNTRY_CODE,
    it's displayed in local (NATIONAL) notation. Otherwise, it's displayed
    in INTERNATIONAL format.

    Args:
        phone_number_str (str): The phone number string.
        user_country_code (str, optional): The 2-letter ISO country code associated with the user
                                           or the number, if available. This helps in parsing
                                           local numbers.
    Returns:
        str: The formatted phone number, or the original string if parsing fails.
    """
    try:
        # Parse the phone number.
        # Provide user_country_code if the number might be local (e.g., "0612345678" for NL)
        # If the number is already in E.164 format (+CC-NNNN...), user_country_code can be None.
        parsed_number = phonenumbers.parse(phone_number_str, user_country_code)

        # Check if the number is valid
        if not phonenumbers.is_valid_number(parsed_number):
            return format_phone_link(phone_number_str, phone_number_str) # Return original if invalid

        # Get the region code (country code) of the parsed number
        region_code = phonenumbers.region_code_for_number(parsed_number)

        if region_code == TARGET_LOCAL_COUNTRY_CODE:
            # If it's a Dutch number, format it in NATIONAL (local) format
            parsed_number =  phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)
            return format_phone_link(phone_number_str, parsed_number)
        
        else:
            # For all other numbers, format them in INTERNATIONAL format
            parsed_number =  phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            return format_phone_link(phone_number_str, parsed_number)

    except phonenumbers.NumberParseException:
        # Handle cases where the number string is not parsable
        return phone_number_str# Return original if invalid


# ============================================================================
# User Impersonation Functions
# ============================================================================

def is_impersonating():
    """Check if the current session is impersonating another user."""
    return '_impersonating_user_id' in session and '_original_user_id' in session


def get_original_user():
    """Get the original admin user when impersonating.

    Returns:
        User object or None if not impersonating
    """
    if not is_impersonating():
        return None

    from bcource.models import User
    original_user_id = session.get('_original_user_id')
    return User.query.get(original_user_id) if original_user_id else None


def get_impersonated_user():
    """Get the user being impersonated.

    Returns:
        User object or None if not impersonating
    """
    if not is_impersonating():
        return None

    from bcource.models import User
    impersonated_user_id = session.get('_impersonating_user_id')
    return User.query.get(impersonated_user_id) if impersonated_user_id else None


def can_impersonate(admin_user, target_user):
    """Check if an admin user can impersonate a target user.

    Args:
        admin_user: The admin user attempting to impersonate
        target_user: The user to be impersonated

    Returns:
        tuple: (bool, str) - (can_impersonate, error_message)
    """
    super_user_role = current_app.config['BCOURSE_SUPER_USER_ROLE']

    # Must be an active admin with super user role
    if not admin_user.is_active or not admin_user.has_role(super_user_role):
        return False, _("Only administrators can impersonate users.")

    # Must have 2FA enabled
    if not admin_user.tf_primary_method:
        return False, _("Two-factor authentication is required to impersonate users.")

    # Cannot impersonate yourself
    if admin_user.id == target_user.id:
        return False, _("You cannot impersonate yourself.")

    # Cannot impersonate other admins (prevent privilege escalation)
    if target_user.has_role(super_user_role):
        return False, _("You cannot impersonate other administrators.")

    # Target user must exist and be active
    if not target_user or not target_user.is_active:
        return False, _("Target user does not exist or is not active.")

    return True, None


def start_impersonation(target_user_id):
    """Start impersonating a user.

    Args:
        target_user_id: The ID of the user to impersonate

    Returns:
        tuple: (bool, str) - (success, message)
    """
    from bcource.models import User

    # Get the target user
    target_user = User.query.get(target_user_id)
    if not target_user:
        return False, _("User not found.")

    # Check if we can impersonate
    can_impersonate_user, error_msg = can_impersonate(current_user._get_current_object(), target_user)
    if not can_impersonate_user:
        return False, error_msg

    # Check if already impersonating
    if is_impersonating():
        return False, _("You are already impersonating a user. Please stop impersonating first.")

    # Store the original user ID BEFORE logging in as target user
    original_user_id = current_user.id
    original_user_email = current_user.email

    # Login as the target user FIRST
    flask_security_login_user(target_user)

    # Then store the impersonation data (after login to ensure session persists)
    session['_original_user_id'] = original_user_id
    session['_impersonating_user_id'] = target_user_id
    session['_impersonation_start_time'] = datetime.utcnow().isoformat()
    session.modified = True  # Force session to be saved

    # Log the impersonation
    app.logger.warning(
        f"IMPERSONATION STARTED: Admin {original_user_email} (ID: {original_user_id}) "
        f"is now impersonating {target_user.email} (ID: {target_user_id})"
    )

    # Notify identity change for Flask-Principal
    identity_changed.send(
        current_app._get_current_object(),
        identity=Identity(target_user_id)
    )

    return True, _("Now viewing as %(name)s", name=target_user.fullname)


def stop_impersonation():
    """Stop impersonating and return to the original admin user.

    Returns:
        tuple: (bool, str) - (success, message)
    """
    if not is_impersonating():
        return False, _("You are not currently impersonating anyone.")

    from bcource.models import User

    # Get the original admin user
    original_user_id = session.get('_original_user_id')
    original_user = User.query.get(original_user_id)

    if not original_user:
        # Clean up session if original user not found
        session.pop('_impersonating_user_id', None)
        session.pop('_original_user_id', None)
        session.pop('_impersonation_start_time', None)
        return False, _("Original user not found. Session cleared.")

    impersonated_user = get_impersonated_user()

    # Log the end of impersonation
    app.logger.warning(
        f"IMPERSONATION STOPPED: Admin {original_user.email} (ID: {original_user_id}) "
        f"stopped impersonating {impersonated_user.email if impersonated_user else 'unknown'} "
        f"(started at {session.get('_impersonation_start_time', 'unknown')})"
    )

    # Clean up session
    session.pop('_impersonating_user_id', None)
    session.pop('_original_user_id', None)
    session.pop('_impersonation_start_time', None)

    # Login back as the original user
    flask_security_login_user(original_user)

    # Notify identity change for Flask-Principal
    identity_changed.send(
        current_app._get_current_object(),
        identity=Identity(original_user_id)
    )

    return True, _("Returned to your admin account.")
