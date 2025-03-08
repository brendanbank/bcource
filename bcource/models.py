import datetime

from sqlalchemy import Integer, String, DateTime, Float, Double
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from . import db

class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(256),unique=True, nullable=False )
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False )
    mobile_phone_number: Mapped[str] = mapped_column(String(32))
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    street: Mapped[str] = mapped_column(String(256), nullable=False)
    address_line2: Mapped[str] = mapped_column(String(256))
    house_number: Mapped[str] = mapped_column(String(20), nullable=False)
    house_number_extention: Mapped[str] = mapped_column(String(20))
    postal_code: Mapped[str] = mapped_column(String(16), nullable=False)
    city: Mapped[str] = mapped_column(String(256), nullable=False)
    state: Mapped[str] = mapped_column(String(256))
    country: Mapped[str] = mapped_column(String(256), nullable=False)
    
    created_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

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
