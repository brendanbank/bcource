from bcource import db, security
from bcource.models import Content, Message
from flask_mailman import EmailMessage
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from bcource.helpers import db_datetime
from bcource.helpers import config_value as cv
import datetime as dt
import zoneinfo


def cleanhtml(raw_html):
    # cleantext = re.sub(CLEANR, '', raw_html)
    cleantext = BeautifulSoup(raw_html, "html.parser")
    return cleantext.getText()

class SystemMessage(object):
    def __init__(self, envelop_to=None, envelop_from=None, **kwargs):
        if not envelop_to:
            raise Exception('envelop_to cannot be None')
        
        if not envelop_from:
            envelop_from = security.datastore.find_user(email=cv('SYSTEM_USER'))
            
        self.kwargs=kwargs
        self.TAG = self.__class__.__name__
        self.body = Content.get_tag(self.TAG, **self.kwargs)
        self.subject = Content.get_tag(f'{self.TAG}Subject', **self.kwargs)
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
                                  subject=self.render_subject())


class SendEmail(SystemMessage):
    
    def send(self):
        
        email_to = []
        for email_user in self.envelop_to:
            email_to.append(f'{email_user.fullname} <{email_user.email}>')
        
        
        email_from = f'{self.envelop_from.fullname} <{self.envelop_from.email}>'
        
        msg = EmailMessage(self.render_subject(), self.render_body(),email_from , email_to)
        
        msg.content_subtype = "html"
        self.process_attachment(msg)
        
        msg.send()
        
        super().send()

    def process_attachment(self, msg):
        return(msg)

class EmailStudentWelcomeMessage(SendEmail):
    pass

class EmailStudentApplicationToBeReviewed(SystemMessage):
    pass

class EmailStudentCreated(SendEmail):
    pass


class EmailStudentEnrolledInTrainingWaitlist(SendEmail):
    pass

class EmailStudentEnrolledWaitlist(SendEmail):
    pass

class EmailStudentEnrolledInTraining(SendEmail):
    def process_attachment(self, msg):
        if not 'training' in self.kwargs:
            raise Exception(f"'training' not present into kwargs")

        if not 'user' in self.kwargs:
            raise Exception(f"'user' not present into kwargs")
        
        user = self.kwargs['user']

        cal = Calendar()
        cal.add("prodid", "-//bcourse//bcource//EN")
        cal.add("version", "2.0")
        cal.add('summary', self.kwargs['training'].name)

        for db_event in self.kwargs['training'].trainingevents:
            
            uuid = f'bonding_event_id_{db_event.id}@events'

            event = Event()
            event.add('dtstart', db_datetime(db_event.start_time))
            event.add('dtend', db_datetime(db_event.end_time))
            event.add('dtstamp', dt.datetime.now(tz=zoneinfo.ZoneInfo('Europe/Amsterdam')))
            event.add('uid', uuid)
            event.add('SEQUENCE', 0)
            event.add('status', "CONFIRMED")
            #event.add(f'ORGANIZER;CN="{self.envelop_from}"', f'mailto:noreply@bgwlan.nl')
            event.add(f'ATTENDEE;ROLE=REQ-PARTICIPANT;CN="{user.fullname}"', f'mailto:{user.email}')
            event.add('location', db_event.location.ical_adress)
            event.add('summary', self.kwargs['training'].name)
            cal.add_component(event)
            
        cal.to_ical()
        
        msg.attach(f'{self.kwargs["training"].name}.ics', cal.to_ical(), 'text/calendar')
        
class EmailStudentDerolledInTraining(SendEmail):
    def process_attachment(self, msg):
        if not 'training' in self.kwargs:
            raise Exception(f"'training' not present into kwargs")

        if not 'user' in self.kwargs:
            raise Exception(f"'user' not present into kwargs")
        
        user = self.kwargs['user']

        cal = Calendar()
        cal.add("prodid", "-//bcourse//bcource//EN")
        cal.add("version", "2.0")
        cal.add('summary', self.kwargs['training'].name)
        cal.add('method', "CANCEL")
        
        for db_event in self.kwargs['training'].trainingevents:
            
            uuid = f'bonding_event_id_{db_event.id}@events'
            
            event = Event()
            event.add('dtstart', db_datetime(db_event.start_time))
            event.add('dtend', db_datetime(db_event.end_time))
            event.add('dtstamp', dt.datetime.now(tz=zoneinfo.ZoneInfo('Europe/Amsterdam')))
            event.add('uid', uuid)
            event.add('SEQUENCE', 1)
            event.add('status', "CANCELLED")
            #event.add(f'ORGANIZER;CN="{self.envelop_from}"', f'mailto:noreply@bgwlan.nl')
            event.add(f'ATTENDEE;ROLE=REQ-PARTICIPANT;CN="{user.fullname}"', f'mailto:{user.email}')
            event.add('location', db_event.location.ical_adress)
            event.add('summary', f"CANCELLED: {self.kwargs['training'].name}")
            cal.add_component(event)
            
        cal.to_ical()
        
        msg.attach(f'{self.kwargs["training"].name}.ics', cal.to_ical(), 'text/calendar')

class EmailStudentStatusActive(SendEmail):
    pass

class EmailStudentEnrolled(SystemMessage):
    pass

# message to trainers to notify that the student has derolled
class EmailStudentDerolled(SystemMessage):
    pass
