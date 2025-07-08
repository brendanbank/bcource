from datetime import datetime, timedelta
from bcource.models import AutomationClasses, TypeEnum, BeforeAfterEnum, AutomationSchedule
from bcource import db
from bcource.models import Training, TrainingEvent
import config
import datetime
import logging

logger = logging.getLogger(__name__)

from pytz import utc
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor


def start_app_sscheduler():
        
    app_config = config.Config()
    
    print (app_config.SQLALCHEMY_DATABASE_URI)
    
    jobstores = {
        'default': SQLAlchemyJobStore(url=app_config.SQLALCHEMY_DATABASE_URI)
    }
    executors = {
        'default': ThreadPoolExecutor(20),
        'processpool': ProcessPoolExecutor(5)
    }
    job_defaults = {
        'coalesce': True,
        'max_instances': 1
    }

    scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)
    scheduler.start()
    return (scheduler)
    
