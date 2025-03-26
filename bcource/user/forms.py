from flask_wtf import FlaskForm, RecaptchaField

from ..myformfields import (MyStringField, MySubmitField, MyPasswordField, MyHiddenField, 
                            MyEmailField, MyTelField, MyDateField, MySelectField, MyBooleanField, MyTextAreaField)

import wtforms.validators as validators
from flask_babel import lazy_gettext as _l
    

class UserSettingsForm(FlaskForm):
    form_description = _l("Update account settings")
    formclass =  "col-md-12"
    hrfields = { 
    }
    
    msg_signal  = MyBooleanField(
        _l('Enable Signal Messaging App'),
        divclass = "col-md-12",
        default=True,
        render_kw={"class": "form-check-input"})
    
    msg_last_min_spots  = MyBooleanField(
        _l('Send me a message when last minute training spots open.'),
        divclass = "col-md-12",
        default=True,
        render_kw={"class": "form-check-input"})

    emergency_contact  = MyTextAreaField(
        _l('My emergency contact:'),
        divclass = "col-md-12",
        render_kw={"class": "position-relative form-control"})

    
    url  = MyHiddenField('url')
    
    # submit = MySubmitField(_l('Submit'), 
    #         render_kw={"class_": "btn btn btn-primary position-relative form-control mt-1", 
    #                    "autocomplete": "country"},
    #         divclass="col-md-12")

class AccountDetailsForm(FlaskForm):
    form_description = _l("Update account details")
    formclass =  "col-md-12"
    hrfields = { 
        "firstname": "",
        "submit": "",
        "postal_code": ""
    }

    first_name = MyStringField(
        _l('Firstname'),
        [validators.DataRequired()],
        divclass = "col-md-6 mt-1",
        render_kw={"class": "position-relative form-control", "autocomplete": "given-name"})

    last_name = MyStringField(
        _l('Lastname'),
        [validators.DataRequired()],
        divclass = "col-md-6 mt-1",
        render_kw={"class": "position-relative form-control", "autocomplete": "family-name"})

    # email = MyEmailField(
    #     _l('E-mail Address'),
    #     [validators.Email(message=_l('Not a valid email address.')),
    #      validators.DataRequired()],
    #     divclass = "col-md-6 mt-1",
    #     render_kw={"class": "position-relative form-control", "autocomplete": "off"})

    phone_number = MyTelField(_l('Mobile Phone'),
                           [validators.DataRequired()],
                           divclass = "col-md-6 pt-1",
                           render_kw={"class": "phone_number position-relative form-control", "autocomplete": "tel"})
           
    birthday = MyDateField(_l('Birth day'),
                           [validators.DataRequired()],
                           divclass = "col-md-4 mt-1",
                           render_kw={"class": "position-relative form-control"})     

    gender = MySelectField(_l('Gender'),
                           [validators.DataRequired()],
                           choices=(("", _l("Choose")),("F", _l("Female")), ("M", _l("Male")), ("O",_l("Other"))),
                           divclass = "col-md-4 mt-1",
                           render_kw={"class": "position-relative form-control form-select"})     
                                         
    postal_code = MyStringField(
        _l('Postal Code'),
        [validators.DataRequired()],
        divclass = "col-md-4 mt-1",
        render_kw={"class": "position-relative form-control", "autocomplete": "postal-code"})


    house_number = MyStringField(
        _l('Number'),
        [validators.DataRequired()],
        divclass = "col-md-4 mt-1",
        render_kw={"class": "position-relative form-control", "autocomplete": "address-level4"})

    house_number_extention = MyStringField(
        _l('Ext.'),
        divclass = "col-md-4 mt-1",
        render_kw={"class": "position-relative form-control"})

    street = MyStringField(
        _l('Street'),
        [validators.DataRequired()],
        divclass = "col-md-12 mt-1",
        render_kw={"class": "position-relative form-control", "autocomplete": "address-line1"})

    address_line2 = MyStringField(
        _l('Street line 2'),
        divclass = "col-md-12 mt-1",
        render_kw={"class": "position-relative form-control"})


    city = MyStringField(
        _l('City'),
        [validators.DataRequired()],
        divclass = "col-md-6 mt-1",
        render_kw={"class": "position-relative form-control", "autocomplete": "address-line2"})

    country = MyStringField(
        _l('Country'), 
        [validators.DataRequired(), validators.Length(min=2,max=2)],
        default="NL",
        divclass = "col-md-2 mt-1",
        render_kw={"class": "position-relative form-control", "autocomplete": "country"})

    url  = MyHiddenField('url')
    
    