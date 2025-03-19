from flask_babel import _
from flask_babel import lazy_gettext as _l
from bcource.validator import ValidatorBase, SettingRequired

class UserProfileChecks(ValidatorBase):
    full_name = SettingRequired(_l("Full Name"), variables=['first_name', 'last_name'],
                                bp_url='user_bp.update',
                                link_class="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover")

    phone_number = SettingRequired(_l("Phone Number"), 
                                   bp_url='user_bp.update',
                                link_class="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover")
    
    full_name = SettingRequired(_l("Full Name"), variables=['first_name', 'last_name'],
                                bp_url='user_bp.update',
                                link_class="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover")
    
    emergency_contact = SettingRequired(_l("Emergency Contact"), variables=['usersettings.emergency_contact'],
                                bp_url='user_bp.settings',
                                link_class="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover")
