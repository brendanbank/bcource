# # your_flask_app/run_scheduler.py
#
# import os
# import sys
# import logging
#
# # Add the parent directory of your_flask_app to the Python path
# # so that imports like `from your_flask_app.config import Config` work
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#
# from bcource import create_app, db # Import your app factory
# from bcource.auto.automation import init_app_scheduler, app_scheduler
#
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
# if __name__ == '__main__':
#     logger.info("Starting dedicated APScheduler process...")
#
#     # Create a *separate* Flask app instance just for the scheduler
#     # This provides the necessary app context for DB operations within jobs
#     app = create_app() # Your factory will do initial DB setup etc.
#     with app.app_context():
#
#         init_app_scheduler(app, db)
#         app_scheduler.start()
#
#
#         while True:
#             import time
#             time.sleep(1) # Sleep for 5 minutes, or use a more sophisticated loop

import click
from flask import Flask, current_app as app
from datetime import datetime
import time
from bcource import db
from bcource.auto.automation import init_app_scheduler

@app.cli.command("run-scheduler")
def run_scheduler():
    print ("Hello World!")
    init_app_scheduler(app, db)
    while True:
        print (".")
        time.sleep(1)