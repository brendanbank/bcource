from datetime import datetime, timedelta
from bcource.models import AutomationClasses, BeforeAfterEnum, AutomationSchedule,\
    TrainingEnroll
from flask_apscheduler import APScheduler
from bcource import db
from bcource.models import Training, TrainingEvent
from bcource.automation.automation_base import get_registered_automation_classes, get_automation_class
import datetime
import logging
from bcource.helpers import db_datetime_str
from bcource.automation.scheduler import app_scheduler

logger = logging.getLogger(__name__)

                    
    
def report_active_jobs():
    renew_automations()
    logger.info("Reporting active ...")
    all_jobs = app_scheduler.get_jobs()
    for jobs in all_jobs:
        logger.info(f'scheduled job: {jobs.id} {jobs}')
        
def renew_automations():
    
    with app_scheduler.flask_app.app_context():        
        job = app_scheduler.add_job(func=report_active_jobs,
                              trigger='interval', 
                              minutes=1,
                              id='report_active_jobs_id', 
                              replace_existing=True)
    
        logger.info(f'added job {job}')

        current_job_ids = {job.id for job in app_scheduler.get_jobs()}
        
        new_jobs_ids = set()
        
        automations = AutomationSchedule().query.filter(
            AutomationSchedule.active == True).all()
        
        all_jobs = []
        for automation in automations:
            logger.info(f'check for jobs in {automation.automation_class}')
            automationobj = get_automation_class (automation.automation_class.class_name)
            if not automationobj:
                logging.critical(f'class_name: {automation.automation_class.class_name} does not exists')
                continue
            
            cls = automationobj['class']
            
            new_jobs_ids.update(cls.create_jobs(automation))     
        
        remove_jobs_list = current_job_ids - new_jobs_ids

        
        for job_id in remove_jobs_list:
            if job_id == "report_active_jobs_id":
                continue
            app_scheduler.remove_job(job_id)
            
def init_app_scheduler(app):
    app_scheduler.flask_app = app
    #app_scheduler.remove_all_jobs()

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
    report_active_jobs()


