from flask_wtf import FlaskForm, RecaptchaField
from flask_babel import _
from flask_babel import lazy_gettext as _l
import wtforms.validators as validators
import bcource.models as models

from bcource.myformfields import (MyStringField, MySubmitField, MyPasswordField, MyHiddenField, 
                            MyEmailField, MyTelField, MyDateField, MySelectField, MyTextAreaField,
                            MyQuerySelectMultipleField, MyQuerySelectField, MyDateTimeField, MyDateTimeLocalField,
                            MyIntegerField, MyBooleanField)



class StudentForm(FlaskForm):
    form_description = "Student Editor"
    formclass =  "col-md-12"
    hrfields = { 
        "fullname": "",
        "submit": ""
    }
    
    url  = MyHiddenField('url')

    fullname = MyStringField(_l('Fullname'),
                             # [validators.Disabled()],
                             divclass="col-md-12 mt-1",
                             render_kw={"class": "position-relative form-control", "disabled": True })
    
    studentstatus = MyQuerySelectField(_l("Student status"),
                                       query_factory=lambda: models.StudentStatus().query.order_by(models.StudentStatus.name).all(),
                                      divclass="col-md-6 mt-1",
                                      render_kw={"class": "position-relative form-control form-select"})

    studenttype = MyQuerySelectField(_l("Student type"),
                                       query_factory=lambda: models.StudentType().query.order_by(models.StudentType.name).all(),
                                      divclass="col-md-6 mt-1",
                                      render_kw={"class": "position-relative form-control form-select"})

    # submit = MySubmitField(_l('Update'), 
    #         render_kw={"class_": "btn btn-outline-dark position-relative form-control mt-1"},
    #         divclass="col-md-12")


