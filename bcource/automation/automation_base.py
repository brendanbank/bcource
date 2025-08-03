"""
Automation Base Module

This module provides the core framework for creating and managing automated tasks
in the Bcourse application. It includes a registry system for automation classes,
a base class for implementing automation tasks, and job execution infrastructure.

Key Components:
- BaseAutomationTask: Abstract base class for all automation tasks
- register_automation: Decorator for registering automation classes
- _execute_automation_task_job: Job execution function
- Registry system for managing automation classes

Example Usage:
    @register_automation(description="Send reminder emails")
    class ReminderTask(BaseAutomationTask):
        @staticmethod
        def query():
            return Training.query.filter(Training.active == True).all()
        
        @staticmethod
        def get_event_dt(item):
            return item.start_time
        
        def execute(self):
            # Send reminder email logic
            pass
"""

# This will be our central registry for automation classes
_automation_classes = {}

from bcource.models import BeforeAfterEnum
from bcource.helpers import db_datetime_str
from bcource.automation.scheduler import app_scheduler
import datetime
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)

def register_automation(name=None, description=None, enabled=True):
    """
    Decorator to register automation classes in the central registry.
    
    This decorator allows automation classes to be discovered and managed
    by the automation system. Registered classes can be retrieved and
    instantiated by the job execution framework.
    
    Args:
        name (str, optional): The name to register the class under.
                             If None, the class's own name will be used.
        description (str, optional): A brief description of the class/task.
                                   Used for documentation and logging.
        enabled (bool, optional): Whether the class is initially enabled.
                                 Defaults to True.
    
    Returns:
        function: Decorator function that registers the class.
    
    Raises:
        ValueError: If an automation class with the same name is already registered.
    
    Example:
        @register_automation(
            name="student_reminder",
            description="Send reminder emails to enrolled students",
            enabled=True
        )
        class StudentReminderTask(BaseAutomationTask):
            pass
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
    Get all registered automation classes.
    
    Returns:
        dict: A copy of the registered automation classes dictionary.
              Keys are automation names, values are dictionaries containing:
              - 'class': The automation class
              - 'description': Description of the automation
              - 'enabled': Whether the automation is enabled
              - 'module': Module where the class is defined
              - 'qualified_name': Fully qualified class name
    
    Example:
        automations = get_registered_automation_classes()
        for name, info in automations.items():
            print(f"{name}: {info['description']}")
    """
    return _automation_classes.copy()

def get_automation_class(name):
    """
    Get a specific registered automation class by name.
    
    Args:
        name (str): The name of the automation class to retrieve.
    
    Returns:
        dict or None: Dictionary containing automation class information,
                     or None if the class is not found.
    
    Example:
        automation_info = get_automation_class("StudentReminderTask")
        if automation_info:
            cls = automation_info['class']
            description = automation_info['description']
    """
    return _automation_classes.get(name)

def _execute_automation_task_job(id: int, automation_name: str, classname: str, *args, **kwargs):    # @ReservedAssignment
    """
    Execute an automation task job.
    
    This function is called by the scheduler to execute automation tasks.
    It retrieves the automation class from the registry, instantiates it,
    and calls the execute method within the Flask application context.
    
    Args:
        id (int): The ID of the item to process (e.g., training ID).
        automation_name (str): The name of the automation configuration.
        classname (str): The name of the automation class to execute.
        *args: Additional positional arguments passed to the automation class.
        **kwargs: Additional keyword arguments passed to the automation class.
    
    Returns:
        Any: The result of the automation task's execute() method.
    
    Note:
        This function runs within the Flask application context to ensure
        database connections and other Flask services are available.
    """
    with app_scheduler.flask_app.app_context(): 
        cls = get_automation_class(classname)
        if cls:
            try:
                obj = cls.get('class', None)(id, automation_name)
                if obj is None:
                    logging.error(f'{__name__}: Failed to instantiate class {classname}')
                    return False
                return obj.execute()
            except Exception as e:
                logging.error(f'{__name__}: Error executing automation {classname}: {str(e)}')
                return False
        else:
            logging.info (f'{__name__}: cannot find classname: {classname}')
            return True


class BaseAutomationTask:
    """
    Base class for automation tasks.
    
    This abstract class defines the common interface and functionality
    for all automation tasks in the Bcourse application. Subclasses
    must implement the required methods to define their specific behavior.
    
    Attributes:
        misfire_grace_time (int): Seconds to wait before considering job misfired.
        max_instances (int): Maximum number of concurrent instances allowed.
        replace_existing (bool): Whether to replace existing jobs with same ID.
    
    Required Methods:
        - query(): Return items that need processing
        - get_event_dt(item): Return datetime when item should be processed
        - execute(): Execute the automation logic
    
    Optional Methods:
        - setup(): Optional setup before execution
        - teardown(): Optional cleanup after execution
    """
    
    # Job configuration
    misfire_grace_time = 1
    max_instances = 1
    replace_existing = True
    
    def __init__(self, id, automation_name, *args, **kwags):  # @ReservedAssignment
        """
        Initialize the automation task.
        
        Args:
            id (int): The ID of the item to process (e.g., training ID).
            automation_name (str): The name of the automation configuration.
            *args: Additional positional arguments.
            **kwags: Additional keyword arguments.
        """
        self.id = id
        self.automation_name = automation_name
        self.args = args
        self.kwags = kwags
        logger.warning (f'Started {self.__class__.__name__} id: {id} automation_name: {automation_name} args: {args} kvargs: {kwags}' )

    @staticmethod
    def query():
        """
        Return items that need processing.
        
        This method should be overridden by subclasses to define which
        items should be processed by the automation task.
        
        Returns:
            list: List of model instances that need processing.
        
        Raises:
            NotImplementedError: If not implemented by subclass.
        
        Example:
            @staticmethod
            def query():
                return Training.query.filter(Training.active == True).all()
        """
        raise NotImplementedError("Subclasses must implement the 'query' method.")
    
    @staticmethod
    def _get_id(item):
        """
        Get the ID of an item.
        
        Args:
            item: Model instance.
        
        Returns:
            int: The ID of the item.
        """
        return item.id
    
    @classmethod
    def _create_job(cls, automation, item, event_dt):
        """
        Create a job for a specific item.
        
        This method creates a scheduled job for processing a single item.
        The job is scheduled based on the event datetime and automation
        configuration (before/after, interval).
        
        Args:
            automation: Automation configuration object.
            item: Model instance to process.
            event_dt (datetime): The event datetime.
        
        Returns:
            Job: The created scheduler job.
        """
        when = cls._when(automation, event_dt)

        print (f'automation: {automation.name}')
        
        str_id = f"{automation.name}/{cls._get_id(item)}/{app_scheduler.flask_app.config.get('ENVIRONMENT')}"
        
        
        job = app_scheduler.add_job(
            id=str_id,
            func=_execute_automation_task_job,
            trigger='date',
            args=(cls._get_id(item), automation.name, automation.automation_class.class_name),
            misfire_grace_time=cls.misfire_grace_time,
            run_date=when,
            replace_existing=cls.replace_existing,
            max_instances=cls.max_instances # Ensure only one refresh job runs at a time
        )
        
        return (job)
    
    @classmethod
    def create_job(cls, item, automation):
        """
        Create a job for a single item.
        
        Args:
            item: Model instance to process.
            automation: Automation configuration object.
        
        Returns:
            Job: The created scheduler job.
        """
        logger.info (f'create_job {cls.__name__} for {item.__class__.__name__} {item}')
        event_dt = cls.get_event_dt(item)
        return cls._create_job(automation, item, event_dt)
        
    @classmethod
    def create_jobs(cls, automation):
        """
        Create jobs for all items returned by query().
        
        This method queries for all items that need processing and creates
        a job for each one. It's typically used during system initialization
        or when automation rules are updated.
        
        Args:
            automation: Automation configuration object.
        
        Returns:
            set: Set of job IDs that were created.
        """
        logger.info (f'start {cls.__name__}')
        
        items = cls.query()
        jobs = set()

        for item in items:
            job = cls.create_job(item, automation)
            if job:
                jobs.add(job.id)
                
        return (jobs)

    @staticmethod
    def get_event_dt(item):
        """
        Get the datetime when an item should be processed.
        
        This method should be overridden by subclasses to define when
        each item should be processed by the automation task.
        
        Args:
            item: Model instance from query().
        
        Returns:
            datetime: The datetime when the item should be processed.
        
        Raises:
            NotImplementedError: If not implemented by subclass.
        
        Example:
            @staticmethod
            def get_event_dt(item):
                return item.start_time
        """
        raise NotImplementedError(f"Subclasse must implement the 'get_event_dt' method.")

    def execute(self):
        """
        Execute the automation logic.
        
        This method should be overridden by subclasses to implement
        the actual automation logic. It's called by the scheduler
        when the job is executed.
        
        Returns:
            Any: The result of the automation task.
        
        Raises:
            NotImplementedError: If not implemented by subclass.
        
        Note:
            This method has access to:
            - self.id: The ID of the item being processed
            - self.automation_name: The name of the automation
            - self.args: Additional positional arguments
            - self.kwags: Additional keyword arguments
        """
        raise NotImplementedError(f"Subclasse {self.__name__} must implement the 'execute' method.")


    def setup(self):
        """
        Optional setup method called before execution.
        
        Override this method to perform any setup required before
        the automation task executes. This could include:
        - Loading additional data
        - Setting up connections
        - Validating prerequisites
        
        Note:
            This method is called automatically before execute().
        """
        pass

    def teardown(self):
        """
        Optional teardown method called after execution.
        
        Override this method to perform any cleanup required after
        the automation task executes. This could include:
        - Closing connections
        - Cleaning up temporary data
        - Logging completion status
        
        Note:
            This method is called automatically after execute().
        """
        pass
        

    @staticmethod
    def _when(automation, event_dt):
        """
        Calculate when a job should be scheduled.
        
        This method calculates the execution time for a job based on:
        - The event datetime
        - The automation interval (before/after)
        - The environment (development vs production)
        
        Args:
            automation: Automation configuration object.
            event_dt (datetime): The event datetime.
        
        Returns:
            datetime: The calculated execution time.
        
        Note:
            - In development mode, jobs execute immediately (1 second delay)
            - Jobs scheduled in the past are logged as warnings
            - The interval is applied before or after the event based on configuration
        """
        dt_delta = automation.interval
        if automation.beforeafter == BeforeAfterEnum.before:
            when = event_dt - dt_delta
        elif automation.beforeafter == BeforeAfterEnum.after:
            when = event_dt + dt_delta
        else:
            when = event_dt
                
        if when < datetime.datetime.utcnow():
            logger.warning(f"job is scheduler in the past: {db_datetime_str(when)} task will be probably be ignored event_dt: {event_dt}")
            
        if app_scheduler.flask_app.config.get('ENVIRONMENT') == "DEVELOPMENT":
            when = datetime.datetime.utcnow() + timedelta(seconds=1)
                
        return when
    
    
    
    