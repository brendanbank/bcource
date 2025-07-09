from bcource.automation.automation_base import BaseAutomationTask, register_automation
from bcource.models import Training, TrainingEvent, TrainingEnroll
from bcource.messages import SendEmail, EmailStudentEnrolledInTraining
from datetime import datetime
import logging
from bcource.students.common import deinvite_from_waitlist, invite_from_waitlist

logger = logging.getLogger(__name__)

class EmailReminder(SendEmail):
    message_tag = "reminder"

class EmailReminderIcal(EmailStudentEnrolledInTraining):
    message_tag = "reminder"
    

class Reminder(BaseAutomationTask):
    def __init__(self, id, automation_name, *args, **kwargs):
        super().__init__(id, automation_name, *args, **kwargs)
        logger.warning (f'Reminder Class: {self.__class__.__name__}')
        self.template_kw= {}

    @classmethod
    def query(cls):
        return Training().query.join(Training.trainingevents).filter(TrainingEvent.start_time > datetime.utcnow(), Training.active==True).all()
    
    @classmethod
    def get_event_dt(cls, item):
        return item.trainingevents[0].start_time
                
@register_automation(
    description="Class to handle sending reminder to students."
)
class StudentReminderTask(Reminder):
    def __init__(self, id, automation_name, *args, **kwargs):  # @ReservedAssignment
        super().__init__(id, automation_name, *args, **kwargs)
        self.to = []
        self.enrollments = TrainingEnroll().query.join(Training).filter(TrainingEnroll.status=="enrolled", Training.id == id).all()
        if not self.enrollments:
            logger.warning(f"No enrollments in training with id {id}")
            return
        self.to = [ enrollment.student.user for enrollment in self.enrollments ]
        self.template_kw['training'] = Training().query.get(id)

    def execute(self):
        for enrollment in self.enrollments:
            self.template_kw['user'] = enrollment.student.user
            self.template_kw['enrollment'] = enrollment
            a = EmailReminderIcal(envelop_to=[enrollment.student.user], CONTENT_TAG=self.automation_name, taglist=['reminder'], **self.template_kw)
            a.send()

@register_automation(
    description="Class to handle sending reminders to trainers."
)
class TrainerReminderTask(Reminder):
    def __init__(self, id, automation_name, *args, **kwargs):  # @ReservedAssignment
        super().__init__(id, automation_name,*args, **kwargs)
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
            a = EmailReminder(envelop_to=[user], CONTENT_TAG=self.automation_name, taglist=['reminder'], **self.template_kw)
            a.send()

@register_automation(
    description="Automatic Waitlist."
)
class AutomaticWaitList(BaseAutomationTask):
    misfire_grace_time = 3600
    def __init__(self, id, automation_name, *args, **kwargs):  # @ReservedAssignment
        super().__init__(id, automation_name, *args, **kwargs)
        self.id = id
        
    def execute(self):
        enrollment = TrainingEnroll().query.filter(TrainingEnroll.uuid == self.id).first()
        if enrollment.status != "waitlist-invited":
            logging.warn(f'{enrollment} enrollment.status: {enrollment.status} is not waitlist-invited, stop automation')
        else:
            deinvite = deinvite_from_waitlist(enrollment)
            
        waitlist_enrollments_eligeble = enrollment.training.waitlist_enrollments_eligeble()
        for enrollment in waitlist_enrollments_eligeble:
            invite_from_waitlist(enrollment)

        return(True)
    
    @classmethod
    def query(cls):
        return TrainingEnroll().query.filter(TrainingEnroll.status =="waitlist-invited").all()

    @classmethod
    def get_event_dt(cls, item):
        return item.invite_date
    
    @classmethod
    def _get_id(cls,item):
        return item.uuid


