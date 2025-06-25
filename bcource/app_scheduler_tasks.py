from bcource import app_scheduler, db
from flask import current_app
from bcource.models import Training

# # interval example
# @app_scheduler.task('interval', id='do_job_1', seconds=3, misfire_grace_time=900)
# def job1():
#     print('Job 1 executed')
#     with app_scheduler.app.app_context():
#         trainings = Training().query.all()
#         print (trainings)
    