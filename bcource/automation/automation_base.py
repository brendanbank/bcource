# This will be our central registry for automation classes
_automation_classes = {}

from datetime import datetime, timedelta
from bcource.models import AutomationClasses, TypeEnum, BeforeAfterEnum, AutomationSchedule
from flask_apscheduler import APScheduler
from bcource import db
from bcource.models import Training, TrainingEvent
import datetime
import logging
logger = logging.getLogger(__name__)

def register_automation(name=None, description=None, enabled=True):
    """
    A decorator to register automation classes.

    Args:
        name (str, optional): The name to register the class under.
                              If None, the class's own name will be used.
        description (str, optional): A brief description of the class/task.
        enabled (bool, optional): Whether the class is initially enabled.
                                   Defaults to True.
    """
    def decorator(cls):
        class_name = name if name is not None else cls.__name__
        if class_name in _automation_classes:
            raise ValueError(f"Automation class '{class_name}' already registered.")

        _automation_classes[class_name] = {
            'class': cls, # Store the class itself
            'description': description,
            'enabled': enabled,
            'module': cls.__module__,
            'qualified_name': f"{cls.__module__}.{cls.__name__}"
        }
        return cls # Return the original class
    return decorator

def get_registered_automation_classes():
    """
    Returns a copy of the dictionary of registered automation classes.
    """
    return _automation_classes.copy()

def get_automation_class(name):
    """
    Retrieves a specific registered automation class by its name.
    """
    return _automation_classes.get(name)


class BaseAutomationTask:
    """A base class for automation tasks, defining common interface."""
    def __init__(self, *args, **kwags):
        self.args = args
        self.kwags = kwags
        logger.warning (f'Started {self.__class__.__name__} args: {args} kvargs: {kwags}' )


    def execute(self):
        """This method should be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement the 'execute' method.")

    def setup(self):
        """Optional setup method."""
        pass

    def teardown(self):
        """Optional teardown method."""
        pass
        
