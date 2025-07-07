from bcource.automation import BaseAutomationTask, register_automation
from bcource.models import TypeEnum, Training
from datetime import datetime


@register_automation(
    description="Class to handle sending reminders."
)
class ReminderTask(BaseAutomationTask):
    def __init__(self, id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        t = Training().query.get(id)
        print (f'Training: {t}')
        print (f'students: {t.trainingenrollments_sorted}')
        
        
    def setup(self):
        print(f"Setting up DailyReportSender for {self.report_type}...")

    def execute(self):
        print(f"Sending daily {self.report_type} reports from class...")
        # Actual report sending logic here
        return f"Daily {self.report_type} reports sent successfully by class."

    def teardown(self):
        print(f"Tearing down DailyReportSender for {self.report_type}...")
        


