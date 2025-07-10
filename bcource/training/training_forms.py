from flask_wtf import FlaskForm, RecaptchaField

from bcource.myformfields import (MyStringField, MySubmitField, MyPasswordField, MyHiddenField, 
                            MyEmailField, MyTelField, MyDateField, MySelectField, MyTextAreaField,
                            MyQuerySelectMultipleField, MyQuerySelectField, MyDateTimeField, MyDateTimeLocalField,
                            MyIntegerField, MyBooleanField)

import wtforms.validators as validators
from wtforms.fields import IntegerField
from wtforms import DateTimeField

from flask_babel import lazy_gettext as _l
from bcource.models import TrainingType

def training_types():
    return TrainingType.get_all()

# def cancellation_types ():
#     return TrainingPolicy().query.order_by(TrainingPolicy.name).all()



class TrainingDerollForm(FlaskForm):
    url  = MyHiddenField('url')
    first_url  = MyHiddenField('first_url')

class TrainingEnrollForm(TrainingDerollForm):
    pass

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
    url = MyHiddenField("url")
    
    submit = MySubmitField(_l('Update'), 
            render_kw={"class_": "btn btn-outline-dark position-relative form-control mt-1"},
            divclass="col-md-12")

class TrainingForm(FlaskForm):
    form_description = _l("Training details")
    formclass =  "col-md-9"
    last_field = "submit"
    hrfields = { 
        "id": "",
        "submit": ""
    }

    # id = MyHiddenField("id")

    url = MyHiddenField()
    
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
        _l('Open for bookings.'),
        divclass = "col-md-4 mt-2 pt-4 ",
        render_kw={"class": "form-check-input"})

    trainingtype = MyQuerySelectField(_l("Training type"),
                                      [validators.DataRequired()],
                                      divclass = "col-md-6 mt-1",
                                      render_kw={"class": "position-relative form-control form-select select2-js"}, #select2-js
                                      query_factory=training_types)
    
    apply_policies = MyBooleanField(
        _l('Apply Policies.'),
        divclass = "col-md-6 mt-2 pt-4 ",
        render_kw={"class": "form-check-input"})


    trainers = MyQuerySelectMultipleField(_l("Trainers"),
                                          divclass = "col-md-12 mt-1",
                                          render_kw={"class": "position-relative form-control select2-js"}) #select2-js

    submit = MySubmitField(_l('Update'), 
            render_kw={"class_": "btn btn-outline-dark position-relative form-control mt-1"},
            divclass="col-md-3 position-relative text-center")
    
    close = MySubmitField(_l('Close'), 
            render_kw={"class_": "btn btn-outline-dark position-relative form-control mt-1 align-self-start"},
            divclass="col-md-3 position-relative text-center")

