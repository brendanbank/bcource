import datetime
from typing import List
from sqlalchemy.dialects.mysql import LONGTEXT

from sqlalchemy import Integer, String, Double,Date, ForeignKey, Table, Column, Text, TIMESTAMP, Boolean, DateTime, UniqueConstraint, Interval,  and_
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr, backref
from sqlalchemy.sql import func
from flask_security.models import sqla as sqla
from bcource import db, security
from flask_security import hash_password, RoleMixin
from flask import render_template_string
from bcource.helpers import config_value as cv
from bcource.helpers import genpwd
from flask import current_app, session
from sqlalchemy import or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import orm
import nh3
from enum import Enum
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)

from uuid import uuid4

policy_association = Table(
    "training_policies",
    db.Model.metadata,
    Column("policy_id", ForeignKey("policy.id", ondelete="CASCADE"), primary_key=True),
    Column("trainingtype_id", ForeignKey("training_type.id", ondelete="CASCADE"), primary_key=True),
)

class Practice(db.Model):
    
    CONFIG = 'DEFAULT_PRACTICE'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    shortname: Mapped[str] = mapped_column(String(256), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=True)
    street: Mapped[str] = mapped_column(String(256), nullable=True)
    address_line2: Mapped[str] = mapped_column(String(256), nullable=True)
    house_number: Mapped[str] = mapped_column(String(20), nullable=True)
    house_number_extention: Mapped[str] = mapped_column(String(20), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(16), nullable=True)
    city: Mapped[str] = mapped_column(String(256), nullable=True)
    state: Mapped[str] = mapped_column(String(256), nullable=True)
    country: Mapped[str] = mapped_column(String(256), nullable=True)
    
    def __str__(self):
        return self.name

    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    @classmethod
    def default_row(cls, practice=None):

        obj = None
        
        if (practice == None and session and session.get('practice')):
            try:
                practice_id = int(session.get('practice'))
                obj = cls().query.get(practice_id)
            except:
                None
                    
        if obj == None:
            if practice == None:
                practice = cv('DEFAULT_PRACTICE_SHORTNAME')
                
            obj = cls().query.filter(cls.shortname==practice).first()
        
        if not obj:
            obj = cls(name=cv('DEFAULT_PRACTICE'),
                      shortname=cv('DEFAULT_PRACTICE_SHORTNAME'))
            db.session.add(obj)
        db.session.commit()
        return(obj)

class GetAll(object):
    @classmethod
    def get_all(cls, practice=None):
        if not practice:
            practice = Practice.default_row().shortname
            
        return cls().query.join(Practice).filter(
                                    Practice.shortname==practice
                                    ).order_by(cls.name).all()

class TrainingType(db.Model, GetAll):
    
    CONFIG='DEFAULT_TRAINING_TYPE'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=True)

    practice_id: Mapped[int] = mapped_column(ForeignKey("practice.id"))
    practice: Mapped["Practice"] = relationship(backref="trainingtypes")
    
    def __str__(self):
        return self.name
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    policies: Mapped[List["Policy"]] =  relationship(
        secondary=policy_association, back_populates="trainingtypes"
    )
    
    @classmethod
    def default_row(cls):
        
        obj = cls().query.filter(cls.name==cv('DEFAULT_TRAINING_TYPE')).first()
        
        if not obj:
            obj = cls(name=cv('DEFAULT_TRAINING_TYPE'),
                            practice=Practice.default_row())

            db.session.add(obj)
        db.session.commit()
        return(obj)

training_trainers_association = Table(
    "training_trainers",
    db.Model.metadata,
    Column("training_id", ForeignKey("training.id", ondelete="CASCADE"), primary_key=True),
    Column("trainer_id", ForeignKey("trainer.id", ondelete="CASCADE"), primary_key=True),
)

class TrainingEvent(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)

    start_time: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True))
    end_time: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True))
    
    training_id: Mapped[int] = mapped_column(ForeignKey("training.id"), nullable=True)

    location_id: Mapped[int] = mapped_column(ForeignKey("location.id"))
    
    location: Mapped["Location"] = relationship(backref="locations")


    
    def __str__(self):
        return f'{self.start_time}/{self.location}'

    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )


class Policy(db.Model):
    CONFIG='DEFAULT_TRAINING_POLICY'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    policy: Mapped[str] = mapped_column(Text(), nullable=True)
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    practice_id: Mapped[int] = mapped_column(ForeignKey("practice.id"))
    practice: Mapped["Practice"] = relationship(backref="policies")

    trainingtypes: Mapped[List["TrainingType"]] =  relationship(
        secondary=policy_association, back_populates="policies"
    )

    def __str__(self):
        return f'{self.practice} / {self.name}'
    
    @classmethod
    def default_row(cls):
        
        obj = cls().query.filter(cls.name==cv('DEFAULT_TRAINING_POLICY')).first()
        
        if not obj:
            obj = cls(name=cv('DEFAULT_TRAINING_POLICY'),
                            practice=Practice.default_row())

            db.session.add(obj)
        db.session.commit()
        return(obj)

    def __repr__(self)->str:
        return f'<{self.__class__.__name__} name = "{self.name}" practice="{self.practice}>'


class TrainingEnroll(db.Model):
    
    
    def __init__(self, **kwargs):
        if 'uuid' not in kwargs:
            kwargs['uuid'] = uuid4()
        super().__init__(**kwargs)

    enrole_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), 
                                                                nullable=True, 
                                                                server_default=func.now())
    
    invite_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), 
                                                                nullable=True)

    ical_sequence: Mapped[int] = mapped_column(Integer(), nullable=True)


    __table_args__ = (db.UniqueConstraint("student_id", "training_id"),)

    status: Mapped[str] = mapped_column(String(256), nullable=False)

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), primary_key=True)
    student: Mapped["Student"] = relationship(backref=backref("studentenrollments"))

    training_id: Mapped[int] = mapped_column(ForeignKey("training.id"), primary_key=True)
    training: Mapped["Training"] = relationship(backref=backref("trainingenrollments"))

    uuid: Mapped[str] = mapped_column(String(256), default=uuid4)

    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    @hybrid_property
    def sequence_next(self):
        if self.ical_sequence == None:
            self.ical_sequence = 1
        else:
            self.ical_sequence += 1
        return self.ical_sequence
 
    def __repr__(self)->str:
        return f'<{self.__class__.__name__} student = "{self.student}" training="{self.training} status="{self.status}">'

class Training(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    
    trainingtype_id: Mapped[int] = mapped_column(ForeignKey("training_type.id"), nullable=False)
    trainingtype: Mapped["TrainingType"] = relationship(backref="trainings")
    
    practice_id: Mapped[int] = mapped_column(ForeignKey("practice.id"))
    practice: Mapped["Practice"] = relationship(backref="trainings")
    
    max_participants: Mapped[int] = mapped_column(Integer(), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean(), default=False)
    apply_policies: Mapped[bool] = mapped_column(Boolean(), default=True)

    trainers: Mapped[List["Trainer"]] =  relationship(
        secondary=training_trainers_association, back_populates="trainings", 
    )
    
    trainingevents: Mapped[List["TrainingEvent"]] = relationship(backref="training", cascade="all, delete", order_by='TrainingEvent.start_time.asc()')


    # reminders: Mapped[List["Reminders"]] =  relationship(
    #     secondary=training_reminders_association, back_populates="trainings", 
    # )

    def __init__(self):
        self._spots_enrolled = None
        self._spots_waitlist = None
        self._spots_avalablie = None
        self._spots_waitlist_count = None
        self.student_allowed = {}
        self._user_enrollment = None
        self.in_policy = None

    @orm.reconstructor
    def init_on_load(self):
        self._spots_enrolled = None
        self._spots_avalablie = None
        self._spots_waitlist = None
        self._spots_waitlist_count = None
        self.student_allowed = {}
        self._user_enrollment = None
        self.in_policy = None
        
    

    def _cal_enrollments(self):
        if self._spots_enrolled == None:
            self._spots_enrolled = TrainingEnroll.query.join(Training).filter(
                                TrainingEnroll.training_id==self.id, or_(TrainingEnroll.status == 'enrolled', 
                                                                         TrainingEnroll.status == 'waitlist-invited')
                                ).count()

        if self._spots_waitlist == None:                   
            self._spots_waitlist = TrainingEnroll.query.join(Training).join(Student).filter(
                            TrainingEnroll.training_id==self.id, 
                            TrainingEnroll.status.in_(['waitlist'])
                        ).order_by(TrainingEnroll.enrole_date).all()  
                                                
        self._spots_waitlist_count = len(self._spots_waitlist)
                
        spots_avalablie = self.max_participants - self._spots_enrolled
        self._spots_avalablie = spots_avalablie
        
        i=0
        while i < spots_avalablie and i < len(self._spots_waitlist):
            enrollment = self._spots_waitlist[i]
            i += 1
            self.student_allowed[enrollment.student.id]=enrollment
            
        logger.info(f'Training: "{self}" _spots_enrolled: {self._spots_enrolled} _spots_waitlist: {self._spots_waitlist} _student_allowed: {self.student_allowed} _spots_avalablie: {self._spots_avalablie}'  )
        
        
    def waitlist_enrollments_eligeble(self):
        self._cal_enrollments()
        return self.student_allowed.values()
    
    def wait_list_spot_availabled(self, student):
        self._cal_enrollments()
        
        if student.id in self.student_allowed.keys():
            return True
        else:
            return False
            
    def fill_numbers(self,user):
        self._cal_enrollments()       
        e = self.enrolled(user)
        if e:
            self._user_enrollment = e
            self._user_status = e.status
        else:
            self._user_status = False
            
        

    def __str__(self):
        return self.name
    
    @property
    def trainer_users(self):
        users = []
        for trainer in self.trainers:
            users.append(trainer.user)
        
        return(users)
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    @property
    def trainingenrollments_sorted(self):
        q = TrainingEnroll.query.join(Training).filter(
            TrainingEnroll.training_id==self.id
            ).order_by(TrainingEnroll.enrole_date)
        return q.all()
    
    def enrolled(self,user):
        return TrainingEnroll.query.join(Training).join(Student).join(User).filter(and_(Student.user==user,
                                                                                        Training.id == self.id)).first()
                                                                                        
class Trainer(db.Model):
    
    __table_args__ = (
        UniqueConstraint("user_id", "practice_id", name="practice_user_unique"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    bio: Mapped[str] = mapped_column(Text(), nullable=True)
    
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    
    user: Mapped["User"] = relationship(backref="trainers")

    practice_id: Mapped[int] = mapped_column(ForeignKey("practice.id", ondelete="CASCADE"))
    practice: Mapped["Practice"] = relationship(backref="trainers")
    
    trainings: Mapped[List["Training"]] =  relationship(
        secondary=training_trainers_association, back_populates="trainers"
    )
    
    def __str__(self):
        return f'{self.user.fullname}'
    
    @property
    def name(self):
        return f'{self.user.fullname}'
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )


class Location(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256),  nullable=False)
    directions: Mapped[str] = mapped_column(Text(), default="", nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    street: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    address_line2: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    house_number: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    house_number_extention: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    postal_code: Mapped[str] = mapped_column(String(16), default="", nullable=False)
    city: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    state: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    country: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    latitude: Mapped[str] = mapped_column(Double,  nullable=True)
    longitude: Mapped[str] = mapped_column(Double,  nullable=True)
    
    practice_id: Mapped[int] = mapped_column(ForeignKey("practice.id", ondelete="CASCADE"))
    practice: Mapped["Practice"] = relationship(backref="locations")

    def __str__(self):
        return f'{self.name}, {self.street} {self.house_number}{self.house_number_extention}, {self.city}'

    @property
    def ical_adress(self):
        return f'{self.street} {self.house_number}{self.house_number_extention}, {self.city}, {self.postal_code},{self.country}'

    @property
    def ical_venue(self):
        return f'{self.name}\n{self.street} {self.house_number}{self.house_number_extention}\n{self.city}\n{self.postal_code}\n{self.country}'

    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    @classmethod
    def default_row(cls):
        
        obj = cls().query.filter(cls.name==cv('LOCATION_NAME')).first()
        
        if not obj:
            obj = cls(name=cv('LOCATION_NAME'),
                            street=cv('LOCATION_STREET'),
                            house_number=cv('LOCATION_HN'),
                            city=cv('LOCATION_CITY'),
                            postal_code=cv('LOCATION_CITY'),
                            practice=Practice.default_row())

            db.session.add(obj)
        db.session.commit()
        return(obj)


class StudentStatus(db.Model, GetAll):
    CONFIG = 'DEFAULT_STUDENT_STATUS'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=True)
    
    practice_id: Mapped[int] = mapped_column(ForeignKey("practice.id"))
    practice: Mapped["Practice"] = relationship(backref="studentstatuses")

    
    def __str__(self):
        return self.name
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

                                    
    @classmethod
    def default_row(cls):
        
        obj = cls().query.filter(cls.name==cv('DEFAULT_STUDENT_STATUS')).first()
        
        if not obj:
            obj = cls(name=cv('DEFAULT_STUDENT_STATUS'),
                            practice=Practice.default_row())

            db.session.add(obj)
        db.session.commit()
        return(obj)

class StudentType(db.Model, GetAll):
    CONFIG = 'DEFAULT_STUDENT_TYPE'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=True)
    
    def __str__(self):
        return self.name
    
    practice_id: Mapped[int] = mapped_column(ForeignKey("practice.id"))
    practice: Mapped["Practice"] = relationship(backref="studenttypes")

    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    

    @classmethod
    def default_row(cls):
        
        obj = cls().query.filter(cls.name==cv('DEFAULT_STUDENT_TYPE')).first()
        
        if not obj:
            obj = cls(name=cv('DEFAULT_STUDENT_TYPE'),
                            practice=Practice.default_row())

            db.session.add(obj)
        db.session.commit()
        return(obj)

class Student(db.Model):
    
    __table_args__ = (
        UniqueConstraint("user_id", "practice_id", name="practice_user_unique"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(backref=backref("students"))
    
    practice_id: Mapped[int] = mapped_column(ForeignKey("practice.id"))
    practice: Mapped["Practice"] = relationship(backref="students")

    studenttype_id: Mapped[int] = mapped_column(ForeignKey(StudentType.id), nullable=False)
    studenttype: Mapped["StudentType"] = relationship(backref="students")

    studentstatus_id: Mapped[int] = mapped_column(ForeignKey(StudentStatus.id), nullable=False)
    studentstatus: Mapped["StudentStatus"] = relationship(backref="students")


    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    
    @property
    def fullname (self):
        return self.user.fullname

    @property
    def email (self):
        return self.user.email
    
    @email.setter
    def email (self,string):
        pass
    
    @property
    def phone_number (self):
        return self.user.phone_number
    
    @fullname.setter
    def fullname (self,string):
        pass
    
    def __str__(self):
        return self.user.fullname

class UserMessageAssociation(db.Model):
    __tablename__ = "user_message"
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("message.id", ondelete="CASCADE"), primary_key=True)

    message_deleted: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)  
    message_read: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)    

    message: Mapped["Message"] = relationship(back_populates="envelop_to"
                                              )
    user: Mapped["User"] = relationship(back_populates="messages")


message_tag_association = Table(
    "message_tag_message",
    db.Model.metadata,
    Column("messagetag_id", ForeignKey("message_tag.id", ondelete="CASCADE"), primary_key=True),
    Column("message_id", ForeignKey("message.id", ondelete="CASCADE"), primary_key=True),
)

class MessageTag(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    
    
    messages: Mapped[List["Message"]] =  relationship(
        secondary=message_tag_association, back_populates="tags", 
    )
    hidden: Mapped[bool] = mapped_column(Boolean(), default=False)

    created_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    def __str__(self):
        return self.tag
    
    @classmethod
    def get_tag(cls,tag_name):
        tag = MessageTag().query.filter(MessageTag.tag == tag_name).first()
        if not tag:
            tag=cls()
            tag.tag = tag_name
            db.session.add(tag)
            db.session.commit()
        return (tag)
    
class Message(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    subject: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str] = mapped_column((Text()), nullable=False)
    
    envelop_from_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    envelop_from: Mapped["User"] = relationship(backref=backref("sent_messages", uselist=False), single_parent=True)
    envelop_to: Mapped[List["UserMessageAssociation"]] = relationship(back_populates="message")
    
    in_reply_to_id: Mapped[int] = mapped_column(ForeignKey("message.id"), nullable=True)
    in_reply_to: Mapped["Message"] = relationship(single_parent=True)
    
    created_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    tags: Mapped[List["MessageTag"]] =  relationship(
        secondary=message_tag_association, back_populates="messages", 
    )
    
    @staticmethod
    def shorten(data, text_length=30):
        return (data[:text_length] + '..') if len(data) > text_length else data
            
    
    @classmethod
    def create_db_message(cls, db_session, envelop_from, envelop_to, subject, body, in_reply_to=None, tags=[]):
        tagobjs = []
        for tag in tags:
            tagobjs.append(MessageTag.get_tag(tag))
            
        
        message = cls(envelop_from_id=envelop_from.id,
                      subject=subject, 
                      body=nh3.clean(body))
        # body=body)
        
        if in_reply_to:
            message.in_reply_to = in_reply_to
        
        for user in envelop_to:
            association = UserMessageAssociation()
            association.user = user
            message.envelop_to.append(association)

        for tag in tagobjs:
            message.tags.append(tag)
            
        db_session.add(message)
        db_session.commit()
        return(message)
        
class User(db.Model, sqla.FsUserMixin):
    
    phone_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str] = mapped_column(String(128), nullable=True)
    street: Mapped[str] = mapped_column(String(256), nullable=True)
    gender: Mapped[str] = mapped_column(String(1), nullable=True)
    address_line2: Mapped[str] = mapped_column(String(256), nullable=True)
    house_number: Mapped[str] = mapped_column(String(20), nullable=True)
    house_number_extention: Mapped[str] = mapped_column(String(20), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(16), nullable=True)
    city: Mapped[str] = mapped_column(String(256), nullable=True)
    state: Mapped[str] = mapped_column(String(256), nullable=True)
    country: Mapped[str] = mapped_column(String(256), nullable=True)
    birthday: Mapped[datetime.datetime] = mapped_column(Date(), nullable=True)
    
    messages: Mapped[List["UserMessageAssociation"]] = relationship(back_populates="user")


    @property
    def name(self):
        return self.fullname


    @property
    def fullname(self):
        if not self.first_name or not self.last_name:
            return self.email
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        if not self.first_name or not self.last_name:
            return self.email
        return f'{self.first_name} {self.last_name}'

    @declared_attr
    def webauthn(cls):  # @NoSelf
        return relationship(
            "WebAuthn", back_populates="user", cascade="all, delete"
        )

    def has_role(self, role: str | RoleMixin) -> bool:
        """Returns `True` if the user identifies with the specified role.

        :param role: A role name or `Role` instance"""
        
        if current_app.config['BCOURSE_SUPER_USER_ROLE'] in self.roles:
            return True
        
        has_role = None
        
        if isinstance(role, str):
            has_role = role in (role.name for role in self.roles)
        else:
            has_role = role in self.roles
        
        return (has_role)
        
    def practices (self):
        return (Practice().query.all())

    @property
    def student_from_practice(self):
        
        return Student().query.join(User).join(Practice).filter(and_(
            Practice.shortname==Practice.default_row().shortname,
            Student.user==self)).first()

    @property
    def trainer_from_practice(self):
        return Trainer().query.join(User).join(Practice).filter(and_(
            Practice.shortname==Practice.default_row().shortname,
            Trainer.user==self)).first()

    @property
    def unread_messages(self):
        return len(UserMessageAssociation().query.join(User).filter(and_(UserMessageAssociation.user_id==self.id,
                                                                                    UserMessageAssociation.message_read==None,
                                                                                    UserMessageAssociation.message_deleted==None)).all())
    def accessible_by_permission(self, permission):        
        if self.has_role(current_app.config['BCOURSE_SUPER_USER_ROLE']):
            return (True)

        permissionObj = Permission().query.filter(Permission.name==permission).first()
                
        if not permissionObj:
            permissionObj = Permission(name=permission)
            db.session.add(permissionObj)
            db.session.commit()

        return (
            self.is_active
            and self.is_authenticated
            and self.has_permission(permission)
        )

    def __repr__(self)->str:
        return f'<{self.__class__.__name__} id = {self.id} email="{self.email}">'

permission_role = Table(
    "permission_role",
    db.Model.metadata,
    Column("role_id", ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True),
)

class Permission(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str | None] = mapped_column(String(255))
    # A comma separated list of strings

    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    roles: Mapped[List["Role"]] = relationship(
        secondary=permission_role, back_populates="permissions_items", 
    )

    def __str__(self):
        return(self.name)
    

    @classmethod
    def find_or_create_permission(cls,permission):
        if isinstance(permission, cls):
            return permission
        p = db.session.query(cls).filter(cls.name==permission).first()
        if not p:
            p=cls(name=permission)
            db.session.add(p)
        return(p)


class Role(db.Model, sqla.FsRoleMixin):
    __tablename__ = 'role'
    CONFIG = 'DEFAULT_STUDENT_ROLE'
    
    permissions_items: Mapped[List[Permission]] = relationship(
        secondary=permission_role, back_populates="roles",
    )
    
    def __str__(self):
        return  self.description or self.name
    
    @property
    def permissions(self):
        return [ p.name for p in self.permissions_items ]
    
    @permissions.setter
    def permissions(self,args):
        for permission in args:
            p = Permission.find_or_create_permission(permission)
            if p in self.permissions_items:
                continue
            self.permissions_items.append(p)
        
    def __repr__(self)->str:
        return f'<{self.__class__.__name__} id = {self.id} name="{self.name}">'
    
class WebAuthn(db.Model,sqla.FsWebAuthnMixin):
    credential_id: Mapped[str] = mapped_column(String(1024))
    
    @declared_attr
    def user_id(cls) -> Mapped[int]:  # @NoSelf
        return mapped_column(
            ForeignKey("user.id", ondelete="CASCADE")
        )

class Content(db.Model):
    tag: Mapped[str] = mapped_column(String(256), primary_key=True)
    lang: Mapped[str] = mapped_column(String(16), default="en", primary_key=True)
    text: Mapped[str] = mapped_column(LONGTEXT, nullable=True)
    subject: Mapped[str] = mapped_column(String(256), nullable=True)

    @classmethod
    def get_tag(cls,tag,obj=False,lang="en", **kwargs):
        content = db.session.query(cls).filter(cls.tag==tag, lang==lang).first()
        if not content:
            content=cls(tag=tag,text="")
            db.session.add(content)
            db.session.commit()
        if obj:
            return (content)
        
        if content.text:
            return(render_template_string(content.text, **kwargs))
        return ""

    @classmethod
    def get_subject(cls,tag,obj=False,lang="en", **kwargs):
        
        content = db.session.query(cls).filter(cls.tag==tag, lang==lang).first()
        if not content:
            content=cls(tag=tag,text="")
            db.session.add(content)
            db.session.commit()
            
        elif content.subject == None:
            subject_tag = f'{tag}Subject'
            subject_obj = db.session.query(cls).filter(cls.tag==subject_tag, lang==lang).first()
            if subject_obj:
                content.subject = subject_obj.text
                db.session.delete(subject_obj)
                db.session.commit()
        
        if obj:
            return (content)
        
        if content.subject:
            return(render_template_string(content.subject, **kwargs))
        return ""


    def update(self):
        db.session.commit()


    

class Postalcodes(db.Model):
    __bind_key__ = 'postalcodes' # This is the key from SQLALCHEMY_BINDS

    postcode: Mapped[str] = mapped_column(String(32), primary_key=True)
    huisnummer: Mapped[str] = mapped_column(String(32), primary_key=True)
    straat: Mapped[str] = mapped_column(String(256))
    buurt: Mapped[str] = mapped_column(String(256))
    wijk: Mapped[str] = mapped_column(String(256))
    woonplaats: Mapped[str] = mapped_column(String(256))
    gemeente: Mapped[str] = mapped_column(String(256))
    provincie: Mapped[str] = mapped_column(String(256))
    latitude: Mapped[str] = mapped_column(Double)
    longitude: Mapped[str] = mapped_column(Double)


class UserSettings(db.Model):
    
    #parent: Mapped["Parent"] = relationship(back_populates="child", single_parent=True)
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), unique=True)
    user: Mapped["User"] = relationship(backref=backref("usersettings", uselist=False), single_parent=True)

    # max_participants: Mapped[int] = mapped_column(Integer(), nullable=True)
    
    msg_signal: Mapped[bool] = mapped_column(Boolean(), default=False)
    msg_last_min_spots: Mapped[bool] = mapped_column(Boolean(), default=True)
    registration_complete: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    
    emergency_contact: Mapped[str] = mapped_column(Text(), nullable=True)

    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

# class EmailReminderEvents(Enum):
#     training = "training"
#     account = "account"
#
#
# training_reminders_association = Table(
#     "training_reminders_association",
#     db.Model.metadata,
#     Column("reminder_id", ForeignKey("training.id", ondelete="CASCADE"), primary_key=True),
#     Column("training_id", ForeignKey("reminders.id", ondelete="CASCADE"), primary_key=True),
# )
#

class AutomationClasses(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    module_path = db.Column(db.String(255), nullable=False)
    qualified_name = db.Column(db.String(255), unique=True, nullable=False)
    # is_enabled is now part of the schedule, not the config itself
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

    def __str__(self):
        return f"{self.class_name}"

    def __repr__(self):
        return f"<AutomationConfig {self.class_name}>"

class BeforeAfterEnum(Enum):
    before = "before"
    after = "after"
    
class EventsEnum(Enum):
    first="first"
    last="last"
    all="all"


class AutomationSchedule(db.Model):
    __table_args__ = (db.UniqueConstraint("name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    
    beforeafter: Mapped[BeforeAfterEnum] 
    events: Mapped[EventsEnum]

    interval: Mapped[timedelta] = mapped_column(Interval, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean(), default=True)

    automation_class = db.relationship('AutomationClasses', lazy=True, backref='schedules')
    automation_class_id: Mapped[int] = mapped_column(ForeignKey(AutomationClasses.id, ondelete="CASCADE"), nullable=True)

    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )


def role_student_default():
    return Practice().query.filter(Practice.name==cv('BCOURSE_DEFAULT_STUDENT_ROLE')).first()



class SystemInitValidations():
    pass




def db_init_data (app):
    
    role = security.datastore.find_or_create_role(cv('SUPER_USER_ROLE'))
    student_admin = security.datastore.find_or_create_role('student-admin')
    security.datastore.add_permissions_to_role(role, {cv('SUPER_USER_ROLE')})
    user=security.datastore.find_user(email=cv('ADMIN_USER'))

    practice = Practice.default_row()
    Location.default_row()
    TrainingType.default_row()

    if not user:
        user = security.datastore.create_user(email=cv('ADMIN_USER'),
                                              password=hash_password(cv('ADMIN_PASSWORD')))
        
        user.confirmed_at = security.datetime_factory()
        trainer = Trainer()
        trainer.user = user
        trainer.practice = practice
        db.session.add(trainer)
    
    system_user=security.datastore.find_user(email=cv('SYSTEM_USER'))

    if not (system_user):
        system_user = security.datastore.create_user(email=cv('SYSTEM_USER'),
                                            password=hash_password(genpwd()))
        system_user.first_name = cv('SYSTEM_FIRSTNAME')
        system_user.last_name = cv('SYSTEM_LASTNAME')
        system_user.confirmed_at = security.datetime_factory()

    current_app.config["SYSTEM_USER"] = system_user
        
    security.datastore.add_role_to_user(user, role)
    security.datastore.add_role_to_user(user, student_admin)
    StudentType.default_row()
    StudentStatus.default_row()
    Policy.default_row() 

    
    db.session.commit()
