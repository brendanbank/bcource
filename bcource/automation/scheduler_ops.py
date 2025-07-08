from datetime import datetime, timedelta
from bcource.models import AutomationClasses, TypeEnum, BeforeAfterEnum, AutomationSchedule
from flask_apscheduler import APScheduler
from bcource import db
from bcource.models import Training, TrainingEvent
from bcource.automation.automation_base import get_registered_automation_classes, get_automation_class
import datetime
import logging
from bcource.helpers import db_datetime_str

logger = logging.getLogger(__name__)

app_scheduler = None

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
            when = datetime.datetime.utcnow()
            
        if when < datetime.datetime.utcnow():
            logger.warning(f"job is scheduler in the past: {db_datetime_str(when)} ignoring task with type: {type} id: {id}")
            continue
            
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
                
        logging.warning(f'added job: {job}')
        
        
        
def _execute_automation_task_job(id: int, name: str, classname: str, *args, **kwargs):    
    

    with app_scheduler.flask_app.app_context(): 
        cls = get_automation_class(classname)
        if cls:
            obj = cls.get('class', None)(id)
        else:
            logging.info (f'{__name__}: cannot find classname: {classname}')
            return 
        
        obj.execute()
    
def report_active_jobs():
    logger.info("Reporting active ...")
    all_jobs = app_scheduler.get_jobs()
    for jobs in all_jobs:
        logger.info(f'scheduled job: {jobs.id} {jobs}')
        
def renew_automations():
    
    app_scheduler.remove_all_jobs()
    with app_scheduler.flask_app.app_context():        
        job = app_scheduler.add_job(func=report_active_jobs,
                              trigger='interval', 
                              minutes=1,
                              id='report_active_jobs_id', 
                              replace_existing=True)
    
        logger.info(f'added job {job}')
        # training automations
        trainings = Training().query.join(Training.trainingevents).filter(TrainingEvent.start_time > datetime.datetime.utcnow(), Training.active==True).all()
        
        for training in trainings:
            logger.info (f'renew: {training}')
            first_training_event_dt = training.trainingevents[0].start_time
            create_app_scheduler_tasks(training.id, first_training_event_dt, TypeEnum.training)
        

def init_app_scheduler(app, scheduler):
    global app_scheduler
    app_scheduler = scheduler
    app_scheduler.flask_app = app
    app_scheduler.remove_all_jobs()

    import bcource.automation.automation_tasks
    
    with app_scheduler.flask_app.app_context():
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
                logging.info(f"Registered new automation class in DB: {class_name}")
        
        
        orphan_classes = AutomationClasses().query.filter(~AutomationClasses.class_name.in_(get_registered_automation_classes().keys())).all()
        if orphan_classes:
            raise SystemError(f'AutomationClasses exists delete them manually if needed: {orphan_classes}')
        
        db.session.commit()

    
    ## renew automations for all trainings
    renew_automations()
    report_active_jobs()


