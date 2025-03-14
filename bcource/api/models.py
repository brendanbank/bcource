
from sqlalchemy import String, Double
from sqlalchemy.orm import Mapped, mapped_column

from bcource import db

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
