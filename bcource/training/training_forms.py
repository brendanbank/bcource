from flask_wtf import FlaskForm, RecaptchaField

from bcource.myformfields import (MyStringField, MySubmitField, MyPasswordField, MyHiddenField, 
                            MyEmailField, MyTelField, MyDateField, MySelectField, MyTextAreaField,
                            MyQuerySelectMultipleField, MyQuerySelectField, MyDateTimeField, MyDateTimeLocalField)

import wtforms.validators as validators
from wtforms.fields import IntegerField

from flask_babel import lazy_gettext as _l
from bcource.training.models import TrainingType

def training_types():
    return TrainingType().query.all()


from wtforms import DateTimeField

class EventForm(FlaskForm):
    form_description = "Event Editor"


    event_start_time = MyDateTimeLocalField(_l("Start Time"),
                                 [validators.DataRequired()],
                                 divclass = "col-md-6",
                                 render_kw={"class": "position-relative form-control"})
    
    event_end_time = MyDateTimeLocalField(_l("End Time"),
                                 [validators.DataRequired()],
                                 divclass = "col-md-6",
                                 render_kw={"class": "position-relative form-control"})
    

    event_location = MyQuerySelectField(_l("Training type"),
                                      [validators.DataRequired()],
                                      divclass = "col-md-6 mt-1",
                                      render_kw={"class": "position-relative form-control form-select"})


    
class TrainingForm(FlaskForm):
    form_description = _l("Training details")
    formclass =  "col-md-8   "
    last_field = "submit"
    hrfields = { 
        "id": "",
        "submit": ""
    }

    id = MyHiddenField("id")

    name = MyStringField(
        _l('Training Name'),
        [validators.DataRequired()],
        divclass = "col-md-6 mt-1",
        render_kw={"class": "position-relative form-control"})
    
    trainingtype = MyQuerySelectField(_l("Training type"),
                                      [validators.DataRequired()],
                                      divclass = "col-md-6 mt-1",
                                      render_kw={"class": "position-relative form-control form-select"},
                                      query_factory=training_types)
    
    trainers = MyQuerySelectMultipleField(_l("Trainers"),
                                          divclass = "col-md-12 mt-1",
                                          render_kw={"class": "position-relative form-control select2-js"})

    submit = MySubmitField(_l('Update'), 
            render_kw={"class_": "btn btn-outline-dark position-relative form-control mt-1"},
            divclass="col-md-12")
