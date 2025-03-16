import datetime
from typing import List

from sqlalchemy import Integer, String, DateTime, Float, Double,Date, ForeignKey, LargeBinary, Table, Column, Text
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
    
    def __str__(self):
        return self.name

    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=naive_utcnow,
    )

class TrainingType(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    
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

    start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime.datetime] = mapped_column(DateTime())
    
    training_id: Mapped[int] = mapped_column(ForeignKey("training.id", ondelete="CASCADE"), nullable=True)
    training: Mapped["Training"] = relationship(backref=backref("trainingevents", cascade="all, delete-orphan"))

    location_id: Mapped[int] = mapped_column(ForeignKey("location.id"))
    location: Mapped["Location"] = relationship(backref="trainingevents")

    def __str__(self):
        return f'{self.start_time}/{self.location})'

    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=naive_utcnow,
    )

class Training(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=True)
    
    traningtype_id: Mapped[int] = mapped_column(ForeignKey("training_type.id", ondelete="CASCADE"), nullable=False)
    traningtype: Mapped["TrainingType"] = relationship(backref="trainings")
    
    practice_id: Mapped[int] = mapped_column(ForeignKey("practice.id"))
    practice: Mapped["Practice"] = relationship(backref="trainings")

    trainers: Mapped[List["Trainer"]] =  relationship(
        secondary=training_trainers_association, back_populates="trainings"
    )
    
    # trainingevents: Mapped["TrainingEvent"] = relationship()
    
    def __str__(self):
        return self.name
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=naive_utcnow,
    )



class ClientType(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=False)
    
    def __str__(self):
        return self.name
    
    update_datetime: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=naive_utcnow,
    )


class Client(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)

    clienttype_id: Mapped[int] = mapped_column(ForeignKey(ClientType.id, ondelete="CASCADE"), nullable=False)
    clienttype: Mapped["ClientType"] = relationship(backref="clients")

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(uselist=False,backref="client")
    
    practice_id: Mapped[int] = mapped_column(ForeignKey("practice.id"))
    practice: Mapped["Practice"] = relationship(backref="clients")


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
        return f'{self.user}'
    
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
