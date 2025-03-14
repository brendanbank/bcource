from flask_security import current_user
from .admin.models import User
from flask_babel import _
from flask import flash

#from wtforms import StringField, SubmitField, PasswordField, HiddenField, EmailField, TelField, DateField, SearchField
import wtforms
#wtforms.fields.html5.DateField
def check_divclass (kwargs):
        if "divclass" in kwargs:
            divclass = kwargs["divclass"]
            del(kwargs["divclass"])
            return (divclass)
        return ("")

def render_validation_status(field, form_data, kwargs):
    if len(field.errors) > 0:
        if "class" in kwargs:
            kwargs["class"] = f'{kwargs["class"]} is-invalid'
        else:
            kwargs["class"] = 'is-invalid'
        
    kwargs["aria-describedby"] = f'{field.name}_feedback'


class MixInField(object):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)          
        super().__init__(*args, **kwargs)
    
    def __call__(self, **kwargs):
        if len(self.errors) > 0:
            c = kwargs.pop('class', '') or kwargs.pop('class_', '')
            rkw = self.render_kw.get('class', '')            
            kwargs['class_'] = f'is-invalid {c} {rkw}'
            
        self.render_kw["aria-describedby"] = f'{self.name}_feedback'
        
        return super(MixInField, self).__call__(**kwargs)

            
        

class MyTelField(MixInField, wtforms.TelField):
    def pre_validate(self, form):
        if User().query.filter(User.phone_number==self.data, User.email != current_user.email).first():
            msg = _("Phone number is already used by an other user!")
            flash(msg,'error')
            raise wtforms.ValidationError(msg)

class MyEmailField(MixInField, wtforms.EmailField):
    def pre_validate(self, form):
        if User().query.filter(User.email==self.data, User.email != current_user.email).first():
            msg = _("This email is already used by an other user!")
            flash(msg,'error')
            raise wtforms.ValidationError(msg)
        
class MyStringField(MixInField, wtforms.StringField):
    pass

class MyPasswordField(MixInField, wtforms.PasswordField):
    pass

class MySubmitField(MixInField, wtforms.SubmitField):
    pass

class MyHiddenField(MixInField, wtforms.HiddenField):
    pass

class MyDateField(MixInField, wtforms.DateField):
    pass
        
class MySelectField(MixInField, wtforms.SelectField):
    pass

