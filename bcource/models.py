import datetime

from typing import List, Set
from sqlalchemy import Integer, String, DateTime, Float, Double,Date, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr
from sqlalchemy.sql import func
from flask_admin.contrib.sqla import ModelView
from flask_security.models import sqla as sqla

from . import admin
from . import db


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
    
    status_id: Mapped[int] = mapped_column(ForeignKey("user_status.id"), nullable=True)
    status: Mapped["UserStatus"] = relationship(back_populates="users")

    @declared_attr
    def webauthn(cls):
        return relationship(
            "WebAuthn", back_populates="user", cascade="all, delete"
        )
        
    

class Role(db.Model, sqla.FsRoleMixin):
    __tablename__ = 'role'
    
class WebAuthn(db.Model,sqla.FsWebAuthnMixin):
    credential_id: Mapped[str] = mapped_column(String(1024))
    
    @declared_attr
    def user_id(cls) -> Mapped[int]:
        return mapped_column(
            ForeignKey("user.id", ondelete="CASCADE")
        )
    
class UserStatus(db.Model):
    __tablename__ = "user_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    userstatus: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    userstatus_str: Mapped[str] = mapped_column(String(256), nullable=False)
    users: Mapped[Set["User"]] = relationship(back_populates="status")

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


admin.add_view(ModelView(UserStatus, db.session)) #@UndefinedVariable
admin.add_view(ModelView(User, db.session)) #@UndefinedVariable
admin.add_view(ModelView(Role, db.session)) #@UndefinedVariable
