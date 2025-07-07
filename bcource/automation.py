# This will be our central registry for automation classes
_automation_classes = {}

from datetime import datetime, timedelta
from bcource.models import AutomationClasses, TypeEnum, BeforeAfterEnum, AutomationSchedule

from bcource import db, app_scheduler
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
        
def remove_app_scheduler_tasks(id: int, type: TypeEnum, force_now=False, **kwargs):
    task_schedules = AutomationSchedule().query.filter(AutomationSchedule.type==type).all()
    for task in task_schedules:
        
        str_id = f'{task.name}_{id}'
        
        job = app_scheduler.get_job(str_id)
        if job:
            logger.warn(f'remove {job}')
            app_scheduler.remove_job(str_id)
            
def create_app_scheduler_tasks(id: int, event_dt: datetime, type: TypeEnum, force_now=False, **kwargs):
    
    task_schedules = AutomationSchedule().query.filter(AutomationSchedule.type==type).all()
        
    for task in task_schedules:
        
        dt_delta = task.interval
        
        if task.beforeafter == BeforeAfterEnum.before:
            when = event_dt - dt_delta
        elif task.beforeafter == BeforeAfterEnum.after:
            when = event_dt + dt_delta
        else:
            when = event_dt
            
        if force_now:
            when = datetime.utcnow()
            
        str_id = f'{task.name}_{id}'
        
        
        job = app_scheduler.add_job(
            id=str_id,
            func=_execute_automation_task_job,
            trigger='date',
            args=(id,task.name, task.automation_class.class_name),
            kwargs=kwargs,
            misfire_grace_time=300,
            run_date=when,
            replace_existing=True,
            max_instances=1 # Ensure only one refresh job runs at a time
        )
        
        logging.warning(f'{__name__} added task {str_id} for {when} force_now: {force_now}')
        logger.warn(f'added {job}')
        
        
        
def _execute_automation_task_job(id: int, name: str, classname: str, *args, **kwargs):    
    
    with app_scheduler.app.app_context(): 
        cls = get_automation_class(classname)
        if cls:
            obj = cls.get('class', None)(id)
        else:
            print (f'{__name__}: cannot find classname: {classname}')
            return 
        
        obj.execute()
        
    
    
def report_active_jobs():
    logger.info("Reporting active ...")
    
    all_jobs = app_scheduler.get_jobs()
    for jobs in all_jobs:
        logger.info(f'scheduled job: {jobs}')

