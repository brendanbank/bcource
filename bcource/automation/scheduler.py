import config
import logging

logger = logging.getLogger(__name__)

from pytz import utc

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

app_config = config.Config()

jobstores = {
    'default': SQLAlchemyJobStore(url=app_config.SQLALCHEMY_DATABASE_URI)
}
executors = {
    'default': ThreadPoolExecutor(40),
    'processpool': ProcessPoolExecutor(4)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 1,
    'misfire_grace_time': None
}


class MyBackgroundScheduler(BackgroundScheduler):
    def __init__(self,*args,**kwargs):
        self.flask_app = None
        super().__init__(*args,**kwargs)

app_scheduler = MyBackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)



def start_app_sscheduler():    
    
    app_scheduler.start()
    return (app_scheduler)
    
