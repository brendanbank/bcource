from flask_wtf import FlaskForm, RecaptchaField

from ..myformfields import (MyStringField, MySubmitField, MyPasswordField, MyHiddenField, 
                            MyEmailField, MyTelField, MyDateField, MySelectField)

import wtforms.validators as validators
from flask_babel import lazy_gettext as _l

class LoginForm(FlaskForm):
    
    form_description = _l("Login")
    formclass =  "col-md-12"
    
    email = MyStringField(
        _l('E-mail Address'),
        [validators.Email(message=_l('Not a valid email address.')),
         validators.DataRequired()],
        divclass = "col-md-12 mb-2",
        render_kw={"class": "position-relative form-control", "autocomplete": "username"},
    )
    
    password = MyPasswordField(
        _l('Password'),
        [validators.DataRequired(message=_l("Please enter a password."))],
        divclass = "col-md-12 mb-2",
        render_kw={"class": "position-relative form-control", "autocomplete": "current-password"},
        )
    
    submit = MySubmitField(_l('Submit'), render_kw={
            "class_": "btn btn-outline-secondary position-relative form-control"},
            divclass="col-md-12 mt-3 mb-3")
    
    
class AccountDetailsForm(FlaskForm):
    form_description = _l("Update account details")
    formclass =  "col-md-8"
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

    phone_number = MyTelField(_l('Mobile Phone Number'),
                           [validators.DataRequired()],
                           divclass = "col-md-4 mt-1",
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

    submit = MySubmitField(_l('Submit'), 
            render_kw={"class_": "btn btn btn-primary position-relative form-control mt-1", 
                       "autocomplete": "country"},
            divclass="col-md-12")
    
    