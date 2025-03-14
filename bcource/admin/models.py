import datetime

from typing import List, Set
from sqlalchemy import Integer, String, DateTime, Float, Double,Date, ForeignKey, LargeBinary, Table, Column, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr
from sqlalchemy.sql import func
from flask_admin.contrib.sqla import ModelView
from flask_security.models import sqla as sqla
from flask_security import naive_utcnow

from .. import table_admin
from .. import db

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

    def __str__(self):
        return self.email

    @declared_attr
    def webauthn(cls):
        return relationship(
            "WebAuthn", back_populates="user", cascade="all, delete"
        )
        
permission_role = Table(
    "permission_role",
    db.Model.metadata,
    Column("role_id", ForeignKey("role.id"), primary_key=True),
    Column("permission_id", ForeignKey("permission.id"), primary_key=True),
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
        secondary=permission_role, back_populates="roles", cascade="all, delete",
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
    
class UserStatus(db.Model):
    __tablename__ = "user_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    userstatus: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    users: Mapped[Set["User"]] = relationship(back_populates="status")

