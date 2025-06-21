from flask_security.models.sqla import FsModels
from sqlalchemy import ForeignKey, Table, Column
from flask import current_app as app
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from flask import url_for, current_app, request, abort, redirect
from flask_principal import Identity, Permission, RoleNeed, identity_changed
from collections import OrderedDict
import pytz
import string
import secrets
import phonenumbers
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

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

def db_datetime_str(db_datetime_notz):
    dt = db_datetime(db_datetime_notz)
    TZ_NAME = app.config.get('BCOURCE_TZ', 'Europe/Amsterdam')
    TZ = pytz.timezone(TZ_NAME)    
    return dt.astimezone(TZ).strftime("%a, %b %d %Y, %H:%M %p %Z")

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
