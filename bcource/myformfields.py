
#from wtforms import StringField, SubmitField, PasswordField, HiddenField, EmailField, TelField, DateField, SearchField
import wtforms
#wtforms.fields.html5.DateField
def check_divclass (kwargs):
        if "divclass" in kwargs:
            divclass = kwargs["divclass"]
            del(kwargs["divclass"])
            return (divclass)
        return ("")


class MyTelField(wtforms.TelField):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)            
        super().__init__(*args, **kwargs)

class MyEmailField(wtforms.EmailField):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)            
        super().__init__(*args, **kwargs)
        
class MyStringField(wtforms.StringField):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)            
        super().__init__(*args, **kwargs)

class MyPasswordField(wtforms.PasswordField):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)            
        super().__init__(*args, **kwargs)

class MySubmitField(wtforms.SubmitField):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)            
        super().__init__(*args, **kwargs)

class MyHiddenField(wtforms.HiddenField):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)            
        super().__init__(*args, **kwargs)

class MyDateField(wtforms.DateField):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)            
        super().__init__(*args, **kwargs)
        
        
class MySelectField(wtforms.SelectField):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)            
        super().__init__(*args, **kwargs)

