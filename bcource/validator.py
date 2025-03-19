from collections import OrderedDict
from flask_babel import _
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

class UnboundValidator:
    _unbound_validator = True
    creation_counter = 0

    def __init__(self, validator_class, *args, **kwargs):
        UnboundValidator.creation_counter += 1
        self.creation_counter = UnboundValidator.creation_counter
        self.validator_class = validator_class
        self.args = args
        self.kwargs = kwargs
        
    def bind(self, validator, name, data_obj, *args, **kwargs):
        kw = dict(
            self.kwargs,
            _from_base=True,
            _validator=validator,
            **kwargs,
        )
        
        return self.validator_class(name, data_obj, *self.args, **kw)

    def __repr__(self):
        return "<UnboundField({}, {!r}, {!r})>".format(
            self.validator_class.__name__, self.args, self.kwargs
        )

class ValidatorMeta(type):
    _unbound_validators = None
    _validation_rules = None
    
    def __call__(cls, *args, **kwargs):

        validators = []
        validators_dict = OrderedDict()
        
        if not cls._unbound_validators:
            for name in dir(cls):
                if not name.startswith("_"):
                    unbound_validator = getattr(cls, name)
                    if hasattr(unbound_validator, "_unbound_validator"):
                        validators.append((name, unbound_validator))

            validators.sort(key=lambda x: (x[1].creation_counter, x[0]))
        
            for name, clsobj in validators:
                validators_dict[name] = clsobj
            
            cls._unbound_validators = validators_dict

        return type.__call__(cls, *args, **kwargs)


class ValidatorBase(object, metaclass=ValidatorMeta):
    
    def __init__(self, data_obj, *args, **kwargs):
        self.data_obj = data_obj
        self._validation_rules = OrderedDict()
        self.args = args
        self.kwargs = kwargs
        self.status = False
                
        for name, validator in self._unbound_validators.items():
            
            obj = validator.bind(self, name, data_obj)
            # Set all the fields to attributes so that they obscure the class
            # attributes with the same names.
            self._validation_rules[name] = obj
            setattr(self, name, obj)
            
    def pre_validate(self):
        """ can be sub-classed """
        return(True)
            
    def validate(self):
        
        if not self.pre_validate():
            return (False)
        self.status = True
        
        for validation_rule in self:
            if not validation_rule.validate():
                self.status = False

        return (self.status)
            
    def __iter__(self):
        """Iterate form fields in creation order."""
        return iter(self._validation_rules.values())

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
        
        self.msg_fail = kwargs.get('msg_fail', None) 
        self.msg_pass = kwargs.get('msg_pass', None)
        self.bp_url = kwargs.get('bp_url')
        
        self.fail_icon = kwargs.get('fail_icon', self._icon_fail)
        self.pass_icon = kwargs.get('pass_icon', self._icon_pass)
        self.bp_url = kwargs.get('bp_url')
        
        self._validator = kwargs.get('_validator', None)
                
        self.init_variables()
        
    def __new__(cls, *args, **kwargs):
        if "_from_base" in kwargs:
            return super().__new__(cls)
        else:
            return UnboundValidator(cls, *args, **kwargs)

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
        
        if type(_variables) == list:
            self.variables = _variables
        elif type(_variables) == str:
            self.variables.append(str)
        else:
            self.variables.append(self.name)
            
    def validate(self):
        
        raise NotImplementedError("validate should be implemented by subclass!")
    
    def _get_value(self, variable, obj):
        
        data_value=None
        
        if '.' in variable:
            variable_test = variable.split('.')[0]
            if hasattr(obj, variable_test):
                data_value = self._get_value(".".join(variable.split('.')[1:]),getattr(obj, variable_test))

        else:
            
            data_value = getattr(obj, variable, None)                
        
        return data_value

class FriendlyNameRule(ValidationRule):
    def __init__(self, name, data_obj, friendly_name, *args, **kwargs):
        
        self.name = name
        super().__init__(name, data_obj, *args, **kwargs)
        self.friendly_name = friendly_name or self.name
        
        if not self.msg_fail:
            self.msg_fail = self.friendly_name
        if not self.msg_pass:
            self.msg_pass =  self.friendly_name
    
        print (f'{self!r}')
        

    def __repr__(self):
        return f"<{self.__class__.__name__}, friendly_name: '{self.friendly_name}' msg_fail: '{self.msg_fail} msg_pass: '{self.msg_pass} variables: '{self.variables} {self.args}, {self.kwargs}')>"

class SettingRequired(FriendlyNameRule):
    
    wheight = 10

    def validate(self):
        self.status=True
        if callable(self.data_obj):
            for variable in self.variables:
                data_value = self._get_value(variable,self.data_obj)
                if data_value == None or data_value == "":
                    self.status = False
                
        return (self.status)



class StatusRequired(ValidationRule):
    wheight = 10
    
