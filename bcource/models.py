import datetime
from typing import List

from sqlalchemy import Integer, String, Double,Date, ForeignKey, Table, Column, Text, TIMESTAMP, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr, backref
from sqlalchemy.sql import func
from flask_admin.contrib.sqla import ModelView
from flask_security.models import sqla as sqla
from flask_security import naive_utcnow
from bcource import db


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
    Column("studen_id", ForeignKey("student.id", ondelete="CASCADE"), primary_key=True),
)


class Practice(db.Model):
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
        secondary=student_association, back_populates="practices"
    )
    
    def __str__(self):
        return self.name

    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=naive_utcnow,
    )

class TrainingType(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=True)
    
    def __str__(self):
        return self.name
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=naive_utcnow,
    )


training_trainers_association = Table(
    "training_trainers",
    db.Model.metadata,
    Column("training_id", ForeignKey("training.id", ondelete="CASCADE"), primary_key=True),
    Column("trainer_id", ForeignKey("trainer.id", ondelete="CASCADE"), primary_key=True),
)

class TrainingEvent(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)

    start_time: Mapped[datetime.datetime] = mapped_column(TIMESTAMP())
    end_time: Mapped[datetime.datetime] = mapped_column(TIMESTAMP())
    
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
        onupdate=naive_utcnow,
    )

class Training(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    
    traningtype_id: Mapped[int] = mapped_column(ForeignKey("training_type.id", ondelete="CASCADE"), nullable=False)
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
        onupdate=naive_utcnow,
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
        onupdate=naive_utcnow,
    )


class Location(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256),  nullable=False)
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
    directions: Mapped[str] = mapped_column(Text(), default="", nullable=False)
    
    practice_id: Mapped[int] = mapped_column(ForeignKey("practice.id", ondelete="CASCADE"))
    practice: Mapped["Practice"] = relationship(backref="locations")

    def __str__(self):
        return f'{self.name}, {self.street} {self.house_number}{self.house_number_extention}, {self.city}'
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=naive_utcnow,
    )


class StudentType(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=False)
    
    def __str__(self):
        return self.name
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=naive_utcnow,
    )


class Student(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)

    studenttype_id: Mapped[int] = mapped_column(ForeignKey(StudentType.id, ondelete="CASCADE"), nullable=False)
    studenttype: Mapped["StudentType"] = relationship(backref="students")

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(backref=backref("student", uselist=False), single_parent=True)
    
    practices: Mapped[List["Practice"]] =  relationship(  #@UndefinedVariable
        secondary=student_association, back_populates="students"
    )
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=naive_utcnow,
    )




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
        onupdate=naive_utcnow,
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
    
    permissions_items: Mapped[List[Permission]] = relationship(
        secondary=permission_role, back_populates="roles",
    )
    
    def __str__(self):
        return  self.description if self.description else self.name
    
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
        onupdate=naive_utcnow,
    )

