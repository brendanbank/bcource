from bcource.automation.automation_base import BaseAutomationTask, register_automation
from bcource.models import Training, TrainingEvent, TrainingEnroll, Student,\
    Practice, User, UserSettings
from bcource.messages import SendEmail, EmailStudentEnrolledInTraining, EmailAttendeeListReminder
from datetime import datetime
from bcource.students.common import deinvite_from_waitlist, invite_from_waitlist
import logging
from bcource import db
from bcource.models import BeforeAfterEnum
from bcource.helpers import db_datetime_str
from datetime import timedelta
from bcource.automation.scheduler import app_scheduler

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
        if self.training._spots_available > 0:
            
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


@register_automation(
    description="Remove all students from a training and delete the training."
)
class DeleteTrainingTask(BaseAutomationTask):
    def __init__(self, id, automation_name, *args, **kwargs):  # @ReservedAssignment
        super().__init__(id, automation_name, *args, **kwargs)
        self.training = Training().query.get(id)
        if not self.training:
            logger.warning(f"Training with id {id} is not found")
            return
        
    @staticmethod
    def query():
        # Query trainings that are marked for deletion or have passed their end date
        # This can be customized based on your specific criteria
        return Training().query.join(Training.trainingevents).filter(TrainingEvent.start_time < datetime.utcnow()).all()

#        return Training().query.all()

    @staticmethod
    def _when(automation, event_dt):
        """
        Calculate when a job should be scheduled.
        
        This method calculates the execution time for a job based on:
        - The event datetime
        - The automation interval (before/after)
        - The environment (development vs production)
        
        Args:
            automation: Automation configuration object.
            event_dt (datetime): The event datetime.
        
        Returns:
            datetime: The calculated execution time.
        
        Note:
            - In development mode, jobs execute immediately (1 second delay)
            - Jobs scheduled in the past are logged as warnings
            - The interval is applied before or after the event based on configuration
        """
        dt_delta = automation.interval
        if automation.beforeafter == BeforeAfterEnum.before:
            when = event_dt - dt_delta
        elif automation.beforeafter == BeforeAfterEnum.after:
            when = event_dt + dt_delta
        else:
            when = event_dt
                
        if when < datetime.utcnow():
            logger.warning(f"job is scheduler in the past: {db_datetime_str(when)} task executed immediately: {event_dt}")
            when = datetime.utcnow() + timedelta(seconds=1)

            
        # if app_scheduler.flask_app.config.get('ENVIRONMENT') == "DEVELOPMENT":
        #     when = datetime.utcnow() + timedelta(seconds=1)
                
        return when
        
    
    @staticmethod
    def get_event_dt(item):
        # Return the datetime when the training should be deleted
        # Using the last event's end time as the reference point
        if item.trainingevents:
            return item.trainingevents[-1].end_time
        return datetime.utcnow()
    
    def execute(self):
        if not self.training:
            logger.error(f"Cannot execute DeleteTrainingTask: training with id {self.id} not found")
            return False
        
        training_name = self.training.name
        training_id = self.training.id
        
        try:
            # Get all enrollments for this training
            enrollments = TrainingEnroll().query.filter(TrainingEnroll.training_id == training_id).all()
            
            # Remove all students from the training
            for enrollment in enrollments:
                logger.info(f"Removing student {enrollment.student} from training {training_name}")
                db.session.delete(enrollment)
            
            db.session.commit()
            logger.info(f"Removed {len(enrollments)} student(s) from training {training_name}")
            
            # Delete the training
            db.session.delete(self.training)
            db.session.commit()
            logger.info(f"Successfully deleted training: {training_name} (ID: {training_id})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting training {training_name}: {str(e)}")
            db.session.rollback()
            return False


@register_automation(
    description="Send attendee list reminder to trainers."
)
class SendAttendeeListTask(Reminder):
    def __init__(self, id, automation_name, *args, **kwargs):  # @ReservedAssignment
        super().__init__(id, automation_name, *args, **kwargs)
        self.training = Training().query.get(id)
        if not self.training:
            logger.warning(f"Training with id {id} is not found")
            return

        # Get all enrolled students for this training
        self.enrollments = TrainingEnroll().query.join(Training).filter(
            TrainingEnroll.status == "enrolled", 
            Training.id == id
        ).all()
        
        if not self.enrollments:
            logger.warning(f"No enrolled students found for training with id {id}")
            return

        self.to = self.training.trainer_users
        self.template_kw['training'] = self.training
        self.template_kw['enrollments'] = self.enrollments
        self.template_kw['attendees'] = [enrollment.student for enrollment in self.enrollments]

    def execute(self):
        if not self.training or not self.enrollments:
            logger.error(f"Cannot execute SendAttendeeListTask: training or enrollments not found for id {self.id}")
            return False

        for user in self.training.trainer_users:
            self.template_kw['user'] = user
            self.template_kw['training'] = self.training
            self.template_kw['enrollments'] = self.enrollments
            self.template_kw['attendees'] = [enrollment.student for enrollment in self.enrollments]
            
            a = EmailAttendeeListReminder(
                envelop_to=[user], 
                CONTENT_TAG=self.automation_name, 
                taglist=['reminder', 'attendee_list'], 
                **self.template_kw
            )
            a.send()
            
        logger.info(f"Sent attendee list reminder to {len(self.training.trainer_users)} trainer(s) for training {self.training.name}")
        return True


