from flask_wtf import FlaskForm, RecaptchaField
from flask import current_app
from flask_babel import _
from flask import url_for
from flask_babel import lazy_gettext as _l
import wtforms.validators as validators
import bcource.models as models
from wtforms_sqlalchemy.fields import  QuerySelectMultipleField, QuerySelectField, QueryCheckboxField, QueryRadioField

from bcource.myformfields import (MyStringField, MySubmitField, MyPasswordField, MyHiddenField, 
                            MyEmailField, MyTelField, MyDateField, MySelectField, MyTextAreaField,
                            MyQuerySelectMultipleField, MyQuerySelectField, MyDateTimeField, MyDateTimeLocalField,
                            MyIntegerField, MyBooleanField, MySelectMultipleField, MyHiddenIdField)
from bcource.models import Practice, Role





class StudentDeleteForm(FlaskForm):
    id = MyHiddenIdField("id")
    url = MyHiddenField("url")
    
    submit = MySubmitField(_l('Update'), 
            render_kw={"class_": "btn btn-outline-dark position-relative form-control mt-1"},
            divclass="col-md-12")

class StudentForm(FlaskForm):
    form_description = "Student Editor"
    formclass =  "col-md-12"
    hrfields = { 
        "fullname": "",
        "submit": ""
    }
    
    url  = MyHiddenField('url')
    
    id  = MyHiddenField('id')

    email = MyStringField(_l('Email'),
                             # [validators.Disabled()],
                             divclass="col-md-12 mt-1",
                             render_kw={"class": "position-relative form-control", "disabled": True })
    
    studentstatus = MyQuerySelectField(_l("Student status"),
                                       query_factory=lambda: models.StudentStatus().query.join(
                                           Practice
                                           ).filter(
                                               Practice.shortname==Practice.default_row().shortname
                                               ).order_by(models.StudentStatus.name).all(),
                                      divclass="col-md-6 mt-1",
                                      render_kw={"class": "position-relative form-control form-select"})

    studenttype = MyQuerySelectField(_l("Student type"),
                                       query_factory=lambda: models.StudentType().query.join(
                                           Practice
                                           ).filter(Practice.shortname==Practice.default_row().shortname
                                               ).order_by(models.StudentType.name).all(),
                                      divclass="col-md-6 mt-1",
                                      render_kw={"class": "position-relative form-control form-select"})

class UserStudentForm(FlaskForm):
    form_description = "User Editor"
    formclass =  "col-md-12"
    hrfields = { 
        "fullname": "",
        "submit": ""
    }
    
    url  = MyHiddenField('url')
    id  = MyHiddenIdField('id')
    hrfields = { 
        "postal_code": "",
        "active": ""
    }
    email = MyStringField(
        _l('Email'),
        [validators.DataRequired()],
        divclass = "col-md-12 mt-1",
        render_kw={"class": "position-relative form-control", "autocomplete": "given-name"})

    first_name = MyStringField(
        _l('Firstname'),
        [validators.Optional()],
        divclass = "col-md-6 mt-1",
        render_kw={"class": "position-relative form-control", "autocomplete": "given-name"})

    last_name = MyStringField(
        _l('Lastname'),
        [validators.Optional()],
        divclass = "col-md-6 mt-1",
        render_kw={"class": "position-relative form-control", "autocomplete": "family-name"})


    
    phone_number = MyTelField(_l('Mobile Phone'),
                           [validators.DataRequired()],
                           divclass = "col-md-6 pt-1",
                           render_kw={"class": "phone_number position-relative form-control", "autocomplete": "tel"})
           
    birthday = MyDateField(_l('Birth day'),
                           [validators.Optional()],
                           divclass = "col-md-4 mt-1",
                           render_kw={"class": "position-relative form-control"})     

    gender = MySelectField(_l('Gender'),
                           [validators.Optional()],
                           choices=(("", _l("Choose")),("F", _l("Female")), ("M", _l("Male")), ("O",_l("Other"))),
                           divclass = "col-md-12 mt-1",
                           render_kw={"class": "position-relative form-control form-select"})     


    active = MyBooleanField(
        _l('User is enabled'),
        divclass = "col-md-6 mt-2 pt-4 pb-1",
        render_kw={"class": "form-check-input"})

    confirmed_at = MyDateTimeLocalField(_l("User is verified at"),
                                   [validators.Optional()],
                                 divclass = "col-md-6 pb-0",
                                 render_kw={"class": "position-relative form-control"})
    
    roles = MyQuerySelectMultipleField(_l("Roles"),
                                          divclass = "col-md-12 mt-1",
                                          render_kw={"class": "position-relative form-control select2-js"}) #select2-js
    postal_code = MyStringField(
        _l('Postal Code'),
        [validators.Optional()],
        divclass = "col-md-4",
        render_kw={"class": "position-relative form-control", "autocomplete": "postal-code"})


    house_number = MyStringField(
        _l('Number'),
        [validators.Optional()],
        divclass = "col-md-4 mt-1",
        render_kw={"class": "position-relative form-control", "autocomplete": "address-level4"})

    house_number_extention = MyStringField(
        _l('Ext.'),
        divclass = "col-md-4 mt-1",
        render_kw={"class": "position-relative form-control"})

    street = MyStringField(
        _l('Street'),
        [validators.Optional()],
        divclass = "col-md-12 mt-1",
        render_kw={"class": "position-relative form-control", "autocomplete": "address-line1"})

    address_line2 = MyStringField(
        _l('Street line 2'),
        divclass = "col-md-12 mt-1",
        render_kw={"class": "position-relative form-control"})


    city = MyStringField(
        _l('City'),
        [validators.Optional()],
        divclass = "col-md-6 mt-1",
        render_kw={"class": "position-relative form-control", "autocomplete": "address-line2"})

    country = MyStringField(
        _l('Country'), 
        [validators.Optional(), validators.Length(min=2,max=2)],
        default="NL",
        divclass = "col-md-2 mt-1",
        render_kw={"class": "position-relative form-control", "autocomplete": "country"})

class UserDerollForm(FlaskForm):
    url  = MyHiddenField('url')
    
class UserBackForm(FlaskForm):
    url  = MyHiddenField('url')

class UserDeleteForm(FlaskForm):
    id = MyHiddenField("id")
    url = MyHiddenField("url")
    
    submit = MySubmitField(_l('Update'), 
            render_kw={"class_": "btn btn-outline-dark position-relative form-control mt-1"},
            divclass="col-md-12")
