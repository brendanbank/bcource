from bcource import db, security
from bcource.models import Content, Message
from flask_mailman import EmailMessage
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from bcource.helpers import db_datetime
from bcource.helpers import config_value as cv
import datetime as dt
import zoneinfo
import logging

logger = logging.getLogger(__name__)


def cleanhtml(raw_html):
    # cleantext = re.sub(CLEANR, '', raw_html)
    cleantext = BeautifulSoup(raw_html, "html.parser")
    return cleantext.getText()

class SystemMessage(object):
    
    def __init__(self, envelop_to=None, 
                 envelop_from=None, 
                 taglist=None, 
                 CONTENT_TAG=None,
                 body=None,
                 subject=None,
                 **kwargs):
        

        if not envelop_to:
            raise Exception('envelop_to cannot be None')
        
        if not envelop_from:
            envelop_from = security.datastore.find_user(email=cv('SYSTEM_USER'))
        
        if not taglist:
            self.taglist = []
        else:
            self.taglist = taglist
        
        if hasattr(self.__class__, "message_tag") and not self.__class__.message_tag in self.taglist and not taglist:
            self.taglist.append(self.__class__.message_tag)
                        
        self.kwargs=kwargs
        
        if body and subject:
            self.body = body
            self.subject = subject
            
        else:
        
            if not CONTENT_TAG:
                self.CONTENT_TAG = self.__class__.__name__
            else:
                self.CONTENT_TAG = CONTENT_TAG
                
            self.body = Content.get_tag(self.CONTENT_TAG, **self.kwargs)
            self.subject = Content.get_subject(self.CONTENT_TAG, **self.kwargs)
            
        if not isinstance(envelop_to, list):
            envelop_to = [envelop_to]

        if isinstance(envelop_from, list):
            envelop_from = envelop_from[0]

        self.envelop_from = envelop_from
        self.envelop_to = envelop_to
        
        
    def render_subject(self):
        return cleanhtml(self.subject)
                
    def render_body(self):
        return self.body
        
    def send(self):
        Message.create_db_message(db_session=db.session,
                                  envelop_from=self.envelop_from,
                                  envelop_to=self.envelop_to,
                                  body=self.render_body(),
                                  subject=self.render_subject(),
                                  tags=self.taglist)


class SendEmail(SystemMessage):
    message_tag = "email"
    
    def send(self):
        
        if not SendEmail.message_tag in self.taglist:
            self.taglist.append(SendEmail.message_tag)

        
        envelop_from_system = security.datastore.find_user(email=cv('SYSTEM_USER'))
        email_from = f'{envelop_from_system.fullname} <{envelop_from_system.email}>'
        
        for user in self.envelop_to:
            email_str = f'{user.fullname} <{user.email}>'
            msg = EmailMessage(subject=self.render_subject(), 
                               body=self.email_render_body(),
                               from_email=email_from,
                               to=[email_str]
                               )
            
            msg.content_subtype = "html"
            self.process_attachment(msg)
        
            logging.info (f'Send message ({self.CONTENT_TAG}) to {user} <{user.email}>')

            msg.send()
        
        super().send()

    def process_attachment(self, msg):
        return(msg)
    
    def email_render_body(self):
        if self.envelop_from == security.datastore.find_user(email=cv('SYSTEM_USER')):
            return self.body
        
        return f'{self.envelop_from} wrote:<p>{self.body}'

class EmailStudentWelcomeMessage(SendEmail):
    pass

class EmailStudentApplicationToBeReviewed(SystemMessage):
    pass

class EmailStudentCreated(SendEmail):
    pass


class EmailStudentEnrolledInTrainingWaitlist(SendEmail):
    message_tag = "wait list"
    
    def process_attachment(self, msg):
        if not 'enrollment' in self.kwargs:
            raise Exception(f"'enrollment' not present into kwargs")

        enrollment = self.kwargs['enrollment']
        if not enrollment:
            raise Exception(f"'enrollment' cannot be Null")
        
        user = enrollment.student.user
        training = enrollment.training

        cal = Calendar()
        cal.add("prodid", "-//Gnarst B.V.//Bcourse//EN")
        cal.add("version", "2.0")
        cal.add('summary', training.name)
        cal.add('method', "REQUEST")


        for db_event in training.trainingevents:

            event = Event()
            event.add('dtstart', db_datetime(db_event.start_time))
            event.add('dtend', db_datetime(db_event.end_time))
            event.add('dtstamp', dt.datetime.now(tz=zoneinfo.ZoneInfo('Europe/Amsterdam')))
            event.add('uid', enrollment.uuid)
            event.add('SEQUENCE', enrollment.sequence_next)
            event.add('status', "TENTATIVE")
            #event.add(f'ORGANIZER;CN="{self.envelop_from}"', f'mailto:noreply@bgwlan.nl')
            event.add(f'ATTENDEE;ROLE=REQ-PARTICIPANT;CN="{user.fullname}"', f'mailto:{user.email}')
            event.add('location', db_event.location.ical_adress)
            event.add('summary', f'{training.name} (Waiting List)')
            cal.add_component(event)
            
        cal.to_ical()
        
        msg.attach(f'{training.name}.ics', cal.to_ical(), 'text/calendar')

class EmailStudentEnrolledWaitlist(SendEmail):
    message_tag = "wait list"

class EmailStudentEnrolledInTraining(SendEmail):
    message_tag = "enrolled"
    
    def process_attachment(self, msg):
        if not 'enrollment' in self.kwargs:
            raise Exception(f"'enrollment' not present into kwargs")

        enrollment = self.kwargs['enrollment']
        if not enrollment:
            raise Exception(f"'enrollment' cannot be Null")
        
        user = enrollment.student.user
        training = enrollment.training

        cal = Calendar()
        cal.add("prodid", "-//Gnarst B.V.//Bcourse//EN")
        cal.add("version", "2.0")
        cal.add('summary', training.name)
        cal.add('method', "REQUEST")


        for db_event in training.trainingevents:

            event = Event()
            event.add('dtstart', db_datetime(db_event.start_time))
            event.add('dtend', db_datetime(db_event.end_time))
            event.add('dtstamp', dt.datetime.now(tz=zoneinfo.ZoneInfo('Europe/Amsterdam')))
            event.add('uid', enrollment.uuid)
            event.add('SEQUENCE', enrollment.sequence_next)
            event.add('status', "CONFIRMED")
            #event.add(f'ORGANIZER;CN="{self.envelop_from}"', f'mailto:noreply@bgwlan.nl')
            event.add(f'ATTENDEE;ROLE=REQ-PARTICIPANT;CN="{user.fullname}"', f'mailto:{user.email}')
            event.add('location', db_event.location.ical_adress)
            event.add('summary', training.name)
            cal.add_component(event)
            
        cal.to_ical()
        
        msg.attach(f'{training.name}.ics', cal.to_ical(), 'text/calendar')
        
class EmailStudentDerolledInTraining(SendEmail):
    message_tag = "derolled"

    def process_attachment(self, msg):

        if not 'enrollment' in self.kwargs:
            raise Exception(f"'enrollment' not present into kwargs")

        enrollment = self.kwargs['enrollment']
        if not enrollment:
            raise Exception(f"'enrollment' cannot be Null")
        
        user = enrollment.student.user
        training = enrollment.training
        
        cal = Calendar()
        cal.add("prodid", "-//Gnarst B.V.//Bcourse//EN")
        cal.add("version", "2.0")
        cal.add('summary', training.name)
        cal.add('method', "CANCEL")
        
        for db_event in training.trainingevents:
            
            uuid = enrollment.uuid
            
            event = Event()
            event.add('dtstart', db_datetime(db_event.start_time))
            event.add('dtend', db_datetime(db_event.end_time))
            event.add('dtstamp', dt.datetime.now(tz=zoneinfo.ZoneInfo('Europe/Amsterdam')))
            event.add('uid', uuid)
            event.add('SEQUENCE', enrollment.sequence_next)
            event.add('status', "CANCELLED")
            #event.add(f'ORGANIZER;CN="{self.envelop_from}"', f'mailto:noreply@bgwlan.nl')
            event.add(f'ATTENDEE;ROLE=REQ-PARTICIPANT;CN="{user.fullname}"', f'mailto:{user.email}')
            event.add('location', db_event.location.ical_adress)
            event.add('summary', f"CANCELLED: {enrollment.training.name}")
            cal.add_component(event)
            
        cal.to_ical()
        
        msg.attach(f'{enrollment.training.name} canceled.ics', cal.to_ical(), 'text/calendar')

class EmailStudentStatusActive(SendEmail):
    message_tag = "active"

class EmailStudentEnrolled(SystemMessage):
    message_tag = "enrolled"

# message to trainers to notify that the student has derolled
class EmailStudentDerolled(SystemMessage):
    message_tag = "derolled"

class EmailStudentEnrolledInTrainingInviteAccepted(EmailStudentEnrolledInTraining):
    message_tag = "enrolled"

class EmailStudentEnrolledInTrainingInvited(SendEmail):
    message_tag = "invited"

class EmailStudentEnrolledInTrainingDeInvited(SendEmail):
    message_tag = "devited"

class EmailReminders():
    message_tag = "reminder"
    pass