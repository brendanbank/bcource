from bcource.automation.automation_base import BaseAutomationTask, register_automation
from bcource.models import Training, TrainingEvent, TrainingEnroll, Student,\
    Practice, User, UserSettings
from bcource.messages import SendEmail, EmailStudentEnrolledInTraining
from datetime import datetime
from bcource.students.common import deinvite_from_waitlist, invite_from_waitlist
import logging
from bcource import db

logger = logging.getLogger(__name__)

class EmailReminder(SendEmail):
    message_tag = "reminder"

class EmailReminderIcal(EmailStudentEnrolledInTraining):
    message_tag = "reminder"
    

class Reminder(BaseAutomationTask):
    def __init__(self,  *args, **kwargs):
        super().__init__( *args, **kwargs)
        logger.warning (f'Reminder Class: {self.__class__.__name__}')
        self.template_kw= {}

    @staticmethod
    def query():
        return Training().query.join(Training.trainingevents).filter(TrainingEvent.start_time > datetime.utcnow(), Training.active==True).all()
    
    @staticmethod
    def get_event_dt(item):
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
    
    @staticmethod
    def query():
        return TrainingEnroll().query.filter(TrainingEnroll.status =="waitlist-invited").all()

    @staticmethod
    def get_event_dt(item):
        return item.invite_date
    
    @staticmethod
    def _get_id(item):
        return item.uuid


@register_automation(
    description="StudentOpenSpotReminder."
)
class StudentOpenSpotReminder(Reminder):
    def __init__(self, *args, **kwargs):  # @ReservedAssignment
        super().__init__(*args, **kwargs)
        self.to = []
        self.training = Training().query.get(self.id)
        if not self.training:
            logger.warning(f"traiing with id {self.id} is not found")
            return

        students_in_training = [enrollment.student.id for enrollment in self.training.trainingenrollments ]
        
        self.training._cal_enrollments()
        if self.training._spots_avalablie > 0:
            
            self.to = Student().query.join(Practice).join(User).join(UserSettings).filter(
                Practice.shortname==Practice.default_row().shortname,
                UserSettings.msg_last_min_spots == True,
                ~Student.id.in_(students_in_training)).all()                
        else:
            logging.warning(f"traing  {self.training} has no open spots")
            self.to = []
                 
        self.template_kw['training'] = self.training

    def execute(self):
        self.training.apply_policies = False
        db.session.commit()
        
        for student in self.to:
            user = student.user
            self.template_kw['user'] = user
            self.template_kw['training'] = self.training
            msg = EmailReminder(envelop_to=[user], CONTENT_TAG=self.automation_name, taglist=['reminder', 'openspot'], **self.template_kw)
            msg.send()


