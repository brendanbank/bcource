# This will be our central registry for automation classes
_automation_classes = {}

from datetime import datetime, timedelta
from bcource.models import AutomationClasses, BeforeAfterEnum, AutomationSchedule
from flask_apscheduler import APScheduler
from bcource import db
from bcource.models import Training, TrainingEvent
import datetime
from bcource.helpers import db_datetime_str
from bcource.automation.scheduler import app_scheduler

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

def _execute_automation_task_job(id: int, classname: str, *args, **kwargs):    
    

    with app_scheduler.flask_app.app_context(): 
        cls = get_automation_class(classname)
        if cls:
            obj = cls.get('class', None)(id)
        else:
            logging.info (f'{__name__}: cannot find classname: {classname}')
            return 
        
        obj.execute()


class BaseAutomationTask:
    """A base class for automation tasks, defining common interface."""

    misfire_grace_time = 1
    max_instances = 1
    replace_existing = True
    
    def __init__(self, *args, **kwags):
        self.args = args
        self.kwags = kwags
        logger.warning (f'Started {self.__class__.__name__} args: {args} kvargs: {kwags}' )

    @classmethod
    def query(cls):
        """This method should be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement the 'query' method.")
    
    @classmethod
    def _get_id(cls,item):
        return item.id
    
    @classmethod
    def _create_job(cls, automation, item, event_dt):
        when = cls._when(automation, event_dt)
        
        str_id = f"{cls.__name__}/{cls._get_id(item)}/{app_scheduler.flask_app.config.get('ENVIRONMENT')}"
        
        
        job = app_scheduler.add_job(
            id=str_id,
            func=_execute_automation_task_job,
            trigger='date',
            args=(cls._get_id(item), automation.automation_class.class_name),
            misfire_grace_time=cls.misfire_grace_time,
            run_date=when,
            replace_existing=cls.replace_existing,
            max_instances=cls.max_instances # Ensure only one refresh job runs at a time
        )
        
        return (job)
    
    @classmethod
    def create_job(cls, item, automation):
        logger.info (f'create_job {cls.__name__} for {item.__class__.__name__} {item}')
        event_dt = cls.get_event_dt(item)
        return cls._create_job(automation, item, event_dt)
        
    @classmethod
    def create_jobs(cls, automation):
        logger.info (f'start {cls.__name__}')
        
        items = cls.query()
        jobs = set()

        for item in items:
            job = cls.create_job(item, automation)
            if job:
                jobs.add(job.id)
                
        return (jobs)

    @classmethod
    def get_event_dt(cls, item):
        """This method should be overridden by subclasses."""
        raise NotImplementedError(f"Subclasse {cls.__name__} must implement the 'get_event_dt' method.")

    def execute(self):
        """This method should be overridden by subclasses."""
        raise NotImplementedError(f"Subclasse {cls.__name__} must implement the 'execute' method.")


    def setup(self):
        """Optional setup method."""
        pass

    def teardown(self):
        """Optional teardown method."""
        pass
        

    @classmethod
    def _when(cls, automation, event_dt):
        
        dt_delta = automation.interval
        if automation.beforeafter == BeforeAfterEnum.before:
            when = event_dt - dt_delta
        elif automation.beforeafter == BeforeAfterEnum.after:
            when = event_dt + dt_delta
        else:
            when = event_dt
                
        if when < datetime.datetime.utcnow():
            logger.warning(f"job is scheduler in the past: {db_datetime_str(when)} task will be probably be ignored event_dt: {event_dt}")
            # if app_scheduler.flask_app.config.get('ENVIRONMENT') == "DEVELOPMENT":
            #     when = datetime.datetime.utcnow() + timedelta(seconds=1)
                
        return when
    
    
    
    