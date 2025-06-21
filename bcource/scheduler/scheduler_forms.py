
from flask_wtf import FlaskForm, RecaptchaField

from ..myformfields import (MyStringField, MySubmitField, MyPasswordField, MyHiddenField, 
                            MyEmailField, MyTelField, MyDateField, MySelectField, MyBooleanField, MyTextAreaField, 
                            MyQuerySelectMultipleField, MyQuerySelectField)

import wtforms.validators as validators
from flask_babel import lazy_gettext as _l
import bcource.models as models


class SchedulerTrainingEnrollForm(FlaskForm):
    approve_tandc  = MyBooleanField(
        _l('Accept Bcourse Terms and Conditions and Cancellation Policy'),
        [validators.DataRequired(message='You must accept the Terms and Conditions before enrolling into this training')],
        divclass = "col-md-12",
        default=False,
        render_kw={"class": "form-check-input"})
    
    #'onClick':"document.getElementById('TrainingEnroll').submit();

    url  = MyHiddenField('url')
