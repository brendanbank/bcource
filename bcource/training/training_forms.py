from flask_wtf import FlaskForm, RecaptchaField

from bcource.myformfields import (MyStringField, MySubmitField, MyPasswordField, MyHiddenField, 
                            MyEmailField, MyTelField, MyDateField, MySelectField, MyTextAreaField,
                            MyQuerySelectMultipleField, MyQuerySelectField, MyDateTimeField, MyDateTimeLocalField,
                            MyIntegerField, MyBooleanField)

import wtforms.validators as validators
from wtforms.fields import IntegerField

from flask_babel import lazy_gettext as _l
from bcource.models import TrainingType

def training_types():
    return TrainingType().query.order_by(TrainingType.name).all()


from wtforms import DateTimeField

class EventForm(FlaskForm):
    form_description = "Event Editor"


    event_start_time = MyDateTimeLocalField(_l("Start Time"),
                                 divclass = "col-md-6",
                                 render_kw={"class": "position-relative form-control"})
    
    event_end_time = MyDateTimeLocalField(_l("End Time"),
                                 divclass = "col-md-6",
                                 render_kw={"class": "position-relative form-control"})
    

    event_location = MyQuerySelectField(_l("Training type"),
                                      divclass = "col-md-6 mt-1",
                                      render_kw={"class": "position-relative form-control form-select"})



class TrainingDeleteForm(FlaskForm):
    id = MyHiddenField("id")
    submit = MySubmitField(_l('Update'), 
            render_kw={"class_": "btn btn-outline-dark position-relative form-control mt-1"},
            divclass="col-md-12")

class TrainingForm(FlaskForm):
    form_description = _l("Training details")
    formclass =  "col-md-8   "
    last_field = "submit"
    hrfields = { 
        "id": "",
        "submit": ""
    }

    # id = MyHiddenField("id")

    name = MyStringField(
        _l('Training Name'),
        [validators.DataRequired()],
        divclass = "col-md-4 mt-1",
        render_kw={"class": "position-relative form-control"})
    
    max_participants = MyIntegerField(
        _l('Maximum Participants'),
        [validators.DataRequired()],
        divclass = "col-md-4 mt-1",
        render_kw={"class": "position-relative form-control"})

    
    active = MyBooleanField(
        _l('Open for Signup'),
        divclass = "col-md-4 mt-2 pt-4 ",
        render_kw={"class": "form-check-input"})

    traningtype = MyQuerySelectField(_l("Training type"),
                                      [validators.DataRequired()],
                                      divclass = "col-md-4 mt-1",
                                      render_kw={"class": "position-relative form-control form-select"}, #select2-js
                                      query_factory=training_types)
    
    trainers = MyQuerySelectMultipleField(_l("Trainers"),
                                          divclass = "col-md-12 mt-1",
                                          render_kw={"class": "position-relative form-control"}) #select2-js

    submit = MySubmitField(_l('Update'), 
            render_kw={"class_": "btn btn-outline-dark position-relative form-control mt-1"},
            divclass="col-md-12")
