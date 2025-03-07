from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://bcourse:thomas22@localhost/bcourse"
# initialize the app with the extension
db.init_app(app)

import datetime

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(256),unique=True, nullable=False )
    hashed_password: Mapped[str] = mapped_column(String(256))
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
    
with app.app_context():
    db.create_all()
    
    
    


