from bcource.automation import BaseAutomationTask, register_automation
from bcource.models import TypeEnum, Training, TrainingEvent, TrainingEnroll,\
    Content
from bcource.messages import SendEmail, EmailStudentEnrolledInTraining
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

class EmailReminder(SendEmail):
    message_tag = "reminder"

class EmailReminderIcal(EmailStudentEnrolledInTraining):
    message_tag = "reminder"
    

class Reminder(BaseAutomationTask):
    def __init__(self, *args, **kwargs):
        logger.warning (f'Reminder Class: {self.__class__.__name__}')
        self.template_kw= {}
        
                
@register_automation(
    description="Class to handle sending reminder to students."
)
class StudentReminderTask(Reminder):
    def __init__(self, id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.to = []
        self.enrollments = TrainingEnroll().query.join(Training).filter(TrainingEnroll.status=="enrolled", Training.id == id).all()
        if not self.enrollments:
            logger.warning(f"traiing with id {id} is not found")
            return
        self.to = [ enrollment.student.user for enrollment in self.enrollments ]
        self.template_kw['training'] = Training().query.get(id)

    def execute(self):
        for enrollment in self.enrollments:
            self.template_kw['user'] = enrollment.student.user
            self.template_kw['enrollment'] = enrollment
            a = EmailReminderIcal(envelop_to=[enrollment.student.user], CONTENT_TAG=self.__class__.__name__, taglist=['reminder'], **self.template_kw)
            a.send()

@register_automation(
    description="Class to handle sending reminders to trainers."
)
class TrainerReminderTask(Reminder):
    def __init__(self, id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.to = []
        self.training = Training().query.get(id)
        if not self.training:
            logger.warning(f"traiing with id {id} is not found")
            return

        self.to = self.training.trainer_users
        self.template_kw['training'] = self.training

    def execute(self):
        for user in self.training.trainer_users:
            self.template_kw['user'] = user
            self.template_kw['training'] = self.training
            a = EmailReminder(envelop_to=[user], CONTENT_TAG=self.__class__.__name__, taglist=['reminder'], **self.template_kw)
            a.send()


