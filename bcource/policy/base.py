from collections import OrderedDict
from flask_babel import _



class BaseMeta(type):
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


class PolicyBase(object, metaclass=BaseMeta):
    
    def __init__(self, *args, **kwargs):
        self._validation_rules = OrderedDict()
        self.args = args
        self.kwargs = kwargs
        self.status = False
                
        for name, validator in self._unbound_validators.items():
            
            obj = validator.bind(self, name)
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
            validation_rule._post_validate()

        return (self.status)
            
    def __iter__(self):
        """Iterate form fields in creation order."""
        return iter(self._validation_rules.values())

    
