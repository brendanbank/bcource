from bcource import db
from sqlalchemy import Integer, String, Double,Date, ForeignKey, Table, Column, Text, TIMESTAMP, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr, backref
from sqlalchemy.sql import func
import datetime


class Message(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    subject: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str] = mapped_column((Text()), nullable=False)
    sent_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                        server_default=func.now())
    envelop_to: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    envelop_from: Mapped["User"] = relationship(backref="sent_messages")

    created_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    @classmethod
    def create_message(cls, envelop_from, envelop_to, subject, message):
        message = cls(envelop_to=envelop_to, envelop_from=envelop_from, subject=subject, message=message)
        return(message)
        