
from markupsafe import escape
from markupsafe import Markup

def clean_key(key):
    key = key.rstrip("_")
    if key.startswith("data_"):
        key = key.replace("_", "-")
    return key

def html_params(**kwargs):
    params = []
    for k, v in sorted(kwargs.items()):
        k = clean_key(k)
        if v is True:
            params.append(k)
        elif v is False:
            pass
        else:
            params.append(f'{str(k)}="{escape(v)}"')  # noqa: B907
    return " ".join(params)

class UnboundValidationRule:
    _unbound_validator = True
    creation_counter = 0

    def __init__(self, validator_class, *args, **kwargs):
        UnboundValidationRule.creation_counter += 1
        self.creation_counter = UnboundValidationRule.creation_counter
        self.validator_class = validator_class
        self.args = args
        self.kwargs = kwargs
        
    def bind(self, validator, name, *args, **kwargs):
        kw = dict(
            self.kwargs,
            _from_base=True,
            _validator=validator,
            **kwargs,
        )
        
        return self.validator_class(name, *self.args, **kw)

    def __repr__(self):
        return "<UnboundField({}, {!r}, {!r})>".format(
            self.validator_class.__name__, self.args, self.kwargs
        )
class ValidationRule(object):
    _user_validator = True
    _icon_pass = 'text-success bi bi-check-lg'
    _icon_fail = 'text-danger bi bi-exclamation-triangle'

    
    def __init__(self, name, data_obj, *args, **kwargs):
        self.args = args
        self.name = name
        self.data_obj = data_obj
        self.kwargs = kwargs
        self.status = False
        self.data_value = None
        
        self.msg_fail = kwargs.get('msg_fail', None) 
        self.msg_pass = kwargs.get('msg_pass', None)
        
        self.post_validate = kwargs.get('post_validate', None)
        
        self.fail_icon = kwargs.get('fail_icon', self._icon_fail)
        self.pass_icon = kwargs.get('pass_icon', self._icon_pass)
        self.bp_url = kwargs.get('bp_url')
        
        self._validator = kwargs.get('_validator', None)
                
        self.init_variables()
        
    def __new__(cls, *args, **kwargs):
        if "_from_base" in kwargs:
            return super().__new__(cls)
        else:
            return UnboundValidationRule(cls, *args, **kwargs)

    @property
    def icon_fail(self):
        return self._icon_fail

    @property
    def icon_ok(self):
        return self._icon_ok

    def _process(self):
        return (True)

    def __bool__(self):
        return self.status
    
    def __call__(self, **kwargs):
                
        
        if self.status:
            msg = self.msg_pass or self.name
            icon = self._icon(icon_class=self.pass_icon)
        else:
            msg = self.msg_fail or self.name
            icon = self._icon(icon_class=self.fail_icon)
                    
        msg = escape(msg)
        
        if not self.status:
            if kwargs.get('link_href'):
                msg = self._url(msg, **kwargs)
            
            if kwargs.get('link_href'):
                icon = self._url(icon, **kwargs)
            
        return Markup(f'{self._span(msg, icon , **kwargs)}')

    def _icon(self, **kwargs):
        return f'<i {html_params(**self.get_render_kw(kwargs,"icon_"))}></i>'
    
    def _span(self, msg, icon="", **kwargs):
        return f'<span {html_params(**self.get_render_kw(kwargs,"span_"))}>{msg} {icon}</span>'

    def _url(self, msg, **kwargs):
        return f'<a {html_params(**self.get_render_kw(kwargs,"link_"))}>{msg}</a>'

    def get_render_kw(self, render_kw, prefix):
        """
        render_field allows customization of how rendering is done.
        """
        
        kws = {}
        
        other_kw = self.kwargs
                
        if other_kw:
            for k, v in other_kw.items():
                k=clean_key(k)
                if k.startswith(prefix):
                    kws[k.replace(prefix, '')] = v

        for k, v in render_kw.items():
            k=clean_key(k)
            if k.startswith(prefix):
                kws[k.replace(prefix,'')] = v
            

        return(kws)
    
    def __html__(self):
        return self.__call__()
        
    def __str__(self):
        return(self.__call__())
        
    def __repr__(self):
        return f"<{self.__class__.__name__}, {self.args}, {self.kwargs})>"
        
    def init_variables(self):
        self.variables = list()
        
        _variables = self.kwargs.get("variables")
        if not _variables:
            raise ValueError(f'variables is missing from {self.__class__.__name__} for {self.name}')
        
        if type(_variables) == list:
            self.variables = _variables
        elif type(_variables) == str:
            self.variables.append(str)
            
    def validate(self):
        
        raise NotImplementedError("validate should be implemented by subclass!")
    
    def _get_value(self, obj, variable=None):
        data_value=None

        if callable(obj) and obj.__class__.__name__ == "function":
            obj= obj()

        if variable and '.' in variable:

            variable_test = variable.split('.')[0]
            if hasattr(obj, variable_test):
                data_value = self._get_value(getattr(obj, variable_test), ".".join(variable.split('.')[1:]))
                
        else:
            # if array
            if issubclass(obj.__class__, list):
                # if we should look for a specific item in the list
                if hasattr(self,'status_value'):
                    for item in obj:
                        if item == self.status_value:
                            data_value = self.status_value
                            break
                # if the array is not empty consider the rule satisfied
                elif  obj:
                    data_value = True
            else:
                # get the data from the obj
                data_value = getattr(obj, variable, None)       
        
        return data_value

    def _post_validate(self):
        
        if self.post_validate and callable(self.post_validate):
            self.post_validate(self)


class FriendlyNameRule(ValidationRule):
    def __init__(self, name, friendly_name, *args, **kwargs):
        
        self.name = name
        super().__init__(name, *args, **kwargs)
        self.friendly_name = friendly_name or self.name
        
        if not self.msg_fail:
            self.msg_fail = self.friendly_name
        if not self.msg_pass:
            self.msg_pass =  self.friendly_name
    
        

    def __repr__(self):
        return f"<{self.__class__.__name__}, friendly_name: '{self.friendly_name}' msg_fail: '{self.msg_fail} msg_pass: '{self.msg_pass} variables: '{self.variables} {self.args}, {self.kwargs}')>"

class HasData(FriendlyNameRule):
    
    wheight = 10

    def validate(self):
        self.status=True
        if callable(self.data_obj):
            if self.variables:
                for variable in self.variables:
                    data_value = self._get_value(self.data_obj, variable)
                    if data_value == None or data_value == "" or data_value == []:
                        self.status = False
            else:
                data_value = self._get_value(self.data_obj)
                if data_value == None or data_value == "":
                    self.status = False

        else:
            raise ValueError(f'data_obj: {self.data_obj} not callable!')
                
        return (self.status)
    

class DataIs(FriendlyNameRule):
    def __init__(self, name, friendly_name, status_value=None, *args, **kwargs):
        super().__init__(name, friendly_name, *args, **kwargs)
        self.status_value  = status_value
        
    wheight = 10
        
    def validate(self):
        self.status=True
        if callable(self.data_obj):
            
            data_value = self._get_value(self.data_obj, self.variables[0])
            if data_value == None or data_value == "":
                self.status=False
            else:
                self.data_value = data_value
                if self.status_value == self.data_value:
                    self.status=True
                else:
                    self.status=False
        else:
            self.status=False
        
        return (self.status)
        
if __name__ == "__main__":
    pass
        
        
