from bcource import db, security
from bcource.models import Content, Message
from flask_mailman import EmailMultiAlternatives
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from bcource.helpers import db_datetime, format_phone_number
from bcource.helpers import config_value as cv
import datetime as dt
import zoneinfo
import logging

logger = logging.getLogger(__name__)


def cleanhtml(raw_html):
    """Convert HTML to plain text with better formatting preservation."""
    soup = BeautifulSoup(raw_html, "html.parser")

    # Add newlines before/after block elements for better readability
    for br in soup.find_all('br'):
        br.replace_with('\n')

    for p in soup.find_all('p'):
        p.insert_before('\n')
        p.insert_after('\n')

    for div in soup.find_all('div'):
        div.insert_after('\n')

    for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        h.insert_before('\n')
        h.insert_after('\n')

    for li in soup.find_all('li'):
        li.insert_before('\n  • ')

    # Get text and clean up excessive whitespace
    text = soup.get_text()

    # Clean up multiple newlines but preserve paragraph structure
    import re
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Max 2 consecutive newlines
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space
    text = text.strip()

    return text

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
            self.CONTENT_TAG = 'mail-a-form'
            
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
        logging.info (f'Send message center-message ({self.CONTENT_TAG}) to {self.envelop_to}')
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
        # If system user has no name, fullname returns email - avoid duplicate email format
        if envelop_from_system.fullname == envelop_from_system.email:
            email_from = envelop_from_system.email
        else:
            email_from = f'{envelop_from_system.fullname} <{envelop_from_system.email}>'

        for user in self.envelop_to:
            # If user has no name, fullname returns email - avoid duplicate email format
            if user.fullname == user.email:
                email_str = user.email
            else:
                email_str = f'{user.fullname} <{user.email}>'

            # Get HTML body
            html_body = self.email_render_body()

            # Generate plain text version from HTML
            text_body = self.email_render_text_body(html_body)

            # Create multipart message with plain text body
            msg = EmailMultiAlternatives(subject=self.render_subject(),
                                         body=text_body,
                                         from_email=email_from,
                                         to=[email_str]
                                         )

            # Attach HTML alternative
            msg.attach_alternative(html_body, "text/html")

            # Add anti-spam headers
            self.add_email_headers(msg, user)

            self.process_attachment(msg)

            logging.info (f'Send e-mailmessage ({self.CONTENT_TAG}) to {user} <{user.email}>')

            msg.send()

        super().send()

    def process_attachment(self, msg):
        return(msg)

    def email_render_body(self):
        return self.body

    def email_render_text_body(self, html_body):
        """Convert HTML body to plain text for multipart email."""
        return cleanhtml(html_body)

    def add_email_headers(self, msg, user):
        """Add headers to improve deliverability and reduce spam score."""
        # List-Unsubscribe header (RFC 8058) - critical for bulk email
        # This allows email clients to show an "unsubscribe" button
        from flask import url_for
        try:
            # Generate unsubscribe URL - points to user account settings
            unsubscribe_url = url_for('user_bp.index', _external=True)
            # Generate unsubscribe email (optional alternative)
            unsubscribe_email = f'mailto:{cv("SYSTEM_USER")}?subject=Unsubscribe'

            msg.extra_headers = {
                'List-Unsubscribe': f'<{unsubscribe_url}>, <{unsubscribe_email}>',
                'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
                # Precedence header helps identify bulk mail
                'Precedence': 'bulk',
                # X-Auto-Response-Suppress prevents out-of-office replies
                'X-Auto-Response-Suppress': 'OOF, AutoReply',
                # X-Priority and Importance headers
                'X-Priority': '3',
                'Importance': 'Normal',
                # X-Mailer identification
                'X-Mailer': 'Bcourse Training System',
                # Custom reference for tracking
                'X-Entity-Ref-ID': f'{self.CONTENT_TAG}',
                # Add recipient for potential personalization tracking
                'X-Recipient-ID': f'{user.email}',
            }
        except Exception:
            # If url_for fails for any reason, fallback without List-Unsubscribe
            msg.extra_headers = {
                'Precedence': 'bulk',
                'X-Auto-Response-Suppress': 'OOF, AutoReply',
                'X-Priority': '3',
                'Importance': 'Normal',
                'X-Mailer': 'Bcourse Training System',
                'X-Entity-Ref-ID': f'{self.CONTENT_TAG}',
                'X-Recipient-ID': f'{user.email}',
            }


class EmailAttendeeListReminder(SendEmail):
    message_tag = "attendee_list_reminder"
    
    def __init__(self, envelop_to=None, envelop_from=None, taglist=None, CONTENT_TAG=None, body=None, subject=None, **kwargs):
        # Generate subject from training name
        training = kwargs.get('training')
        if training and not subject:
            subject = f"Attendee List for {training.name}"
        
        # Set a placeholder body - will be replaced in email_render_body
        if not body:
            body = "Attendee list placeholder"
        
        # Call parent constructor
        super().__init__(envelop_to=envelop_to, envelop_from=envelop_from, taglist=taglist, 
                        CONTENT_TAG=CONTENT_TAG, body=body, subject=subject, **kwargs)
    
    def email_render_body(self):
        # Generate HTML table with student list and phone numbers
        training = self.kwargs.get('training')
        enrollments = self.kwargs.get('enrollments', [])
        
        if not training or not enrollments:
            return "No training or enrollments found."
        
        # Sort enrollments by student's first name and last name
        sorted_enrollments = sorted(enrollments, key=lambda e: (e.student.user.first_name.lower(), e.student.user.last_name.lower()))
        
        # Build HTML table
        html_body = f"""
        <h3>Attendee List for {training.name}</h3>
        <p>Dear Trainer,</p>
        <p>Here is the list of enrolled students for your upcoming training:</p>
        
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 600px;">
            <thead style="background-color: #f0f0f0;">
                <tr>
                    <th style="text-align: left; padding: 8px;">#</th>
                    <th style="text-align: left; padding: 8px;">Name</th>
                    <th style="text-align: left; padding: 8px;">Phone Number</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for idx, enrollment in enumerate(sorted_enrollments, 1):
            student = enrollment.student
            user = student.user
            
            # Format phone number using helper function
            if user.phone_number:
                phone = format_phone_number(user.phone_number, user.country)
            else:
                phone = 'N/A'
            
            # Alternate row colors
            row_color = '#ffffff' if idx % 2 == 0 else '#f9f9f9'
            
            html_body += f"""
                <tr style="background-color: {row_color};">
                    <td style="padding: 8px;">{idx}</td>
                    <td style="padding: 8px 28px 8px 8px;">{user.fullname}</td>
                    <td style="padding: 8px;">{phone}</td>
                </tr>
            """
        
        html_body += """
            </tbody>
        </table>
        
        <p style="margin-top: 20px;">
            <strong>Total Enrolled:</strong> {} student(s)
        </p>
        
        <p>Best regards,<br>
        Bcourse Training System</p>
        """.format(len(sorted_enrollments))
        
        self.body = html_body
        return html_body

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
    
class EmailStudentDerolledInTrainingOutOfPolicy(EmailStudentDerolledInTraining):
    message_tag = "policy"
    
class EmailStudentDerolledInTrainingOutOfPolicyTrainer(SendEmail):
    message_tag = "policy"

    
class EmailStudentEnrolledInTrainingInvited(SendEmail):
    message_tag = "invited"

class EmailStudentEnrolledInTrainingDeInvited(SendEmail):
    message_tag = "devited"

class EmailReminders():
    message_tag = "reminder"
    pass