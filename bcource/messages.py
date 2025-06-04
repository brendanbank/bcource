from bcource import db, security
from flask import render_template_string
from flask_security import current_user
from flask_babel import _
from flask_babel import lazy_gettext as _l
from bcource.models import Content, Message

import re
# as per recommendation from @freylis, compile once only
CLEANR = re.compile('<.*?>') 

def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

class BaseMessage(object):
    def __init__(self, envelop_from=None, envelop_to=None):
        self.TAG = self.__class__.__name__
        self.body = Content.get_tag(self.TAG).text
        self.subject = Content.get_tag(f'{self.TAG}Subject').text
        self.envelop_from = envelop_from
        self.envelop_to = envelop_to
        self.subject_render = None
        self.body_render = None
        
    def render_subject(self):
        return render_template_string(cleanhtml(self.subject), user=current_user)
                
    def render_body(self):
        return render_template_string(self.body, user=current_user)
        

    def send(self):
        
        if self.envelop_to == None:
            self.envelop_to = [current_user]
        
        if self.envelop_from == None:
            self.envelop_from = security.datastore.find_or_create_role('student-admin').users[0]

        print (self.envelop_to, self.envelop_from)
        
        Message.create_db_message(db_session=db.session,
                                  envelop_from=self.envelop_from,
                                  envelop_to=self.envelop_to,
                                  body=self.render_body() , 
                                  subject=self.render_subject())

class StudentWelcomeMessage(BaseMessage):
    pass

class StudentApplicationToBeReviewed(BaseMessage):
    pass

class StudentStatusActive(BaseMessage):
    def __init__(self, envelop_to, status):
        self.status = status
        super().__init__(envelop_from=None, envelop_to=envelop_to)

    def render_body(self):
        return render_template_string(self.body, user=current_user, status=self.status)

class StudentCreated(BaseMessage):
    def __init__(self, envelop_from=None, envelop_to=None):
        envelop_to = security.datastore.find_or_create_role('student-admin').users
        super().__init__(envelop_from, envelop_to)
        