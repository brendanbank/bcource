import datetime
from typing import List

from sqlalchemy import Integer, String, Double,Date, ForeignKey, Table, Column, Text, TIMESTAMP, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr, backref
from sqlalchemy.sql import func
from flask_admin.contrib.sqla import ModelView
from flask_security.models import sqla as sqla
from flask_security import naive_utcnow
from bcource import db, security
from flask_security import hash_password, RoleMixin
from bcource.helpers import config_value as cv
from flask import current_app

class Message(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    subject: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str] = mapped_column((Text()), nullable=False)
    sent_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                        server_default=func.now())
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(backref="sent_messages")

    created_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    
trainers_association = Table(
    "trainers",
    db.Model.metadata,
    Column("practice_id", ForeignKey("practice.id", ondelete="CASCADE"), primary_key=True),
    Column("trainer_id", ForeignKey("trainer.id", ondelete="CASCADE"), primary_key=True),
)

student_association = Table(
    "students",
    db.Model.metadata,
    Column("practice_id", ForeignKey("practice.id", ondelete="CASCADE"), primary_key=True),
    Column("student_id", ForeignKey("student.id", ondelete="CASCADE"), primary_key=True),
)

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
    phone_number: Mapped[str] = mapped_column(String(32), nullable=True)
    street: Mapped[str] = mapped_column(String(256), nullable=True)
    address_line2: Mapped[str] = mapped_column(String(256), nullable=True)
    house_number: Mapped[str] = mapped_column(String(20), nullable=True)
    house_number_extention: Mapped[str] = mapped_column(String(20), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(16), nullable=True)
    city: Mapped[str] = mapped_column(String(256), nullable=True)
    state: Mapped[str] = mapped_column(String(256), nullable=True)
    country: Mapped[str] = mapped_column(String(256), nullable=True)

    trainers: Mapped[List["Trainer"]] =  relationship(
        secondary=trainers_association, back_populates="practices"
    )
    
    students: Mapped[List["Student"]] =  relationship(
        secondary=student_association, back_populates="practice"
    )
    


        
    def __str__(self):
        return self.name

    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    


class TrainingType(db.Model):
    
    CONFIG='DEFAULT_TRAINING_TYPE'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=True)
    
    def __str__(self):
        return self.name
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    policies: Mapped[List["Policy"]] =  relationship(
        secondary=policy_association, back_populates="trainingtypes"
    )


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

    # @property
    # def start_date(self):
    #     return f'{self.start_time}'

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
    trainingtypes: Mapped[List["TrainingType"]] =  relationship(
        secondary=policy_association, back_populates="policies"
    )

    def __str__(self):
        return self.name


class Training(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    
    traningtype_id: Mapped[int] = mapped_column(ForeignKey("training_type.id"), nullable=False)
    traningtype: Mapped["TrainingType"] = relationship(backref="trainings")
    
    practice_id: Mapped[int] = mapped_column(ForeignKey("practice.id"))
    practice: Mapped["Practice"] = relationship(backref="trainings")
    
    max_participants: Mapped[int] = mapped_column(Integer(), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean(), default=False)

    trainers: Mapped[List["Trainer"]] =  relationship(
        secondary=training_trainers_association, back_populates="trainings", 
    )
    
    trainingevents: Mapped[List["TrainingEvent"]] = relationship(backref="training", cascade="all, delete")


    
    def __str__(self):
        return self.name
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )


class Trainer(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    bio: Mapped[str] = mapped_column(Text(), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(uselist=False,backref="trainer")

    practices: Mapped[List["Practice"]] =  relationship(
        secondary=trainers_association, back_populates="trainers"
    )
    
    trainings: Mapped[List["Training"]] =  relationship(
        secondary=training_trainers_association, back_populates="trainers"
    )

    
    def __str__(self):
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

class StudentStatus(db.Model):
    CONFIG = 'DEFAULT_STUDENT_STATUS'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=True)
    
    def __str__(self):
        return self.name
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    @classmethod
    def default(cls):
        return cls().query.filter(
                    cls.name==cv(cls.CONFIG)
                    ).first()

class StudentType(db.Model):
    CONFIG = 'DEFAULT_STUDENT_TYPE'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=True)
    
    def __str__(self):
        return self.name
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )


class Student(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)

    studenttype_id: Mapped[int] = mapped_column(ForeignKey(StudentType.id), nullable=False)
    studenttype: Mapped["StudentType"] = relationship(backref="students")

    studentstatus_id: Mapped[int] = mapped_column(ForeignKey(StudentStatus.id), nullable=False)
    studentstatus: Mapped["StudentStatus"] = relationship(backref="students")

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(backref=backref("student", uselist=False), single_parent=True)

    

    practice: Mapped[List["Practice"]] =  relationship(uselist=False, 
        secondary=student_association, back_populates="students"
    )

    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    @property
    def fullname (self):
        return self.user.fullname
    
    @fullname.setter
    def fullname (self,string):
        pass
    
    def __str__(self):
        return self.user.fullname

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
    
    @property
    def fullname(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return f'{self.first_name} {self.last_name} <{self.email}>'

    @declared_attr
    def webauthn(cls):
        return relationship(
            "WebAuthn", back_populates="user", cascade="all, delete"
        )

    def has_role(self, role: str | RoleMixin) -> bool:
        """Returns `True` if the user identifies with the specified role.

        :param role: A role name or `Role` instance"""
        
        if current_app.config['BCOURSE_SUPER_USER_ROLE'] in self.roles:
            return True
        
        if isinstance(role, str):
            return role in (role.name for role in self.roles)
        else:
            return role in self.roles

        
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
        
    
class WebAuthn(db.Model,sqla.FsWebAuthnMixin):
    credential_id: Mapped[str] = mapped_column(String(1024))
    
    @declared_attr
    def user_id(cls) -> Mapped[int]:
        return mapped_column(
            ForeignKey("user.id", ondelete="CASCADE")
        )

class Content(db.Model):
    tag: Mapped[str] = mapped_column(String(256), primary_key=True)
    lang: Mapped[str] = mapped_column(String(16), default="en", primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=True)

    @classmethod
    def get_tag(cls,tag,lang="en"):
        content = db.session.query(cls).filter(cls.tag==tag, lang==lang).first()
        if not content:
            content=cls(tag=tag,text="")
            db.session.add(content)
            db.session.commit()
        return(content)
    
    def update(self):
        db.session.commit()


    

class Postalcodes(db.Model):
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
    
    emergency_contact: Mapped[str] = mapped_column(Text(), nullable=True)

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
        trainer.practices.append(practice)
        db.session.add(trainer)
        
    security.datastore.add_role_to_user(user, role)
    StudentType.default_row()
    StudentStatus.default_row()
    Policy.default_row() 

    
    db.session.commit()
