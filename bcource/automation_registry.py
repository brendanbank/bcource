# This will be our central registry for automation classes
import bcource
_automation_classes = {}
from datetime import datetime, timedelta
from bcource.models import AutomationClasses, TypeEnum, BeforeAfterEnum, AutomationSchedule

from bcource import db, app_scheduler

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
        print (f'Started {self.__class__.__name__} args: {args} kvargs: {kwags}' )


    def execute(self):
        """This method should be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement the 'execute' method.")

    def setup(self):
        """Optional setup method."""
        pass

    def teardown(self):
        """Optional teardown method."""
        pass
        

def create_tasks(id: int, event_dt: datetime, type: TypeEnum, **kwargs):
    #print (id, event_dt, type)
    task_schedules = AutomationSchedule().query.filter(AutomationSchedule.type==type).all()
        
    for task in task_schedules:
        
        dt_delta = task.interval
        
        if task.beforeafter == BeforeAfterEnum.before:
            when = event_dt - dt_delta
        elif task.beforeafter == BeforeAfterEnum.after:
            when = event_dt + dt_delta
        else:
            when = event_dt
            
        str_id = f'{task.name}_{id}'
        
        
        app_scheduler.add_job(
            id=str_id,
            func=_execute_automation_task_job,
            trigger='date',
            args=(id,task.name, task.automation_class.class_name),
            kwargs=kwargs,
            run_date=when,
            replace_existing=True,
            max_instances=1 # Ensure only one refresh job runs at a time
        )
        
        
    

def _execute_automation_task_job(id: int, name, classname, *args, **kwargs):    
    
    with app_scheduler.app.app_context(): 
        cls = get_automation_class(classname)
        b = cls.get('class', None)(id)
        print (b)
    
    
    # b = cls()

def echo_schedule(*args, **kwargs):
    print (f"Test echo {args} {kwargs}")

def init_scheduler(app_scheduler, db):
    
    now = datetime.utcnow()
    
    then = now + timedelta(seconds=5)
    
    app_scheduler.add_job(
        id='db_refresh_job',
        func=echo_schedule,
        trigger='date',
        kwargs={"a": "a"},
        run_date=then,
        replace_existing=True,
        max_instances=1 # Ensure only one refresh job runs at a time
    )

    # Optional: Populate AutomationConfig table with registered classes on first run

    for class_name, details in get_registered_automation_classes().items():
        existing_config = AutomationClasses().query.filter_by(class_name=class_name).first()
        if not existing_config:
            new_config = AutomationClasses(
                class_name=class_name,
                description=details['description'],
                module_path=details['module'],
                qualified_name=details['qualified_name']
            )
            db.session.add(new_config)
            print(f"Registered new automation class in DB: {class_name}")
    db.session.commit()


    from bcource.app_scheduler_tasks import ReminderTask

    create_tasks(3, datetime.utcnow(), TypeEnum.training)
    