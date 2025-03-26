from bcource.policy.base import PolicyBase
from bcource.models import Practice

class PolicyRepo():
    def __init__(self, *args, **kwargs):
        self.args = args
        self._policies = {}
        self._policy_classes = []
        self._types = {}

    def __new__(cls, name=None, repos=None, class_objs=None, *args, **kwargs):
        
        if not name:
            return super().__new__(cls)
        
        repo = repos[0]
        new_cls = type(name, (PolicyBase,), class_objs)
        
        repo._policies[name] = new_cls
        repo._policy_classes.append(new_cls)
        
        
        if "type" in class_objs:
            cls_type = class_objs["type"]
            if cls_type in repo._types:
                repo._types[cls_type].append(new_cls)
            else:
                repo._types[cls_type] = [new_cls]
                    
        return new_cls
    
    def __iter__(self):
        for  policy in self._policy_classes:
            yield  policy
    
    def get_policy_by_type(self, name):
        pass

