
from wtforms import StringField, SubmitField, PasswordField, HiddenField, EmailField, TelField

def check_divclass (kwargs):
        if "divclass" in kwargs:
            divclass = kwargs["divclass"]
            del(kwargs["divclass"])
            return (divclass)
        return ("")


class MyTelField(TelField):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)            
        super().__init__(*args, **kwargs)

class MyEmailField(EmailField):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)            
        super().__init__(*args, **kwargs)
        
class MyStringField(StringField):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)            
        super().__init__(*args, **kwargs)

class MyPasswordField(PasswordField):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)            
        super().__init__(*args, **kwargs)

class MySubmitField(SubmitField):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)            
        super().__init__(*args, **kwargs)

class MyHiddenField(HiddenField):
    def __init__(self, *args, **kwargs):
        
        self.divclass = check_divclass(kwargs)            
        super().__init__(*args, **kwargs)
