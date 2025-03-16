from bcource.admin.admin_views import AuthModelView
from bcource import db, table_admin
from .models import Location, Practice, Trainer, Training, TrainingType, TrainingEvent, ClientType, Client
from sqlalchemy.orm import configure_mappers
from wtforms import TextAreaField
from bcource.admin.content import Content
from bcource.admin.helper import TagMixIn

class TrainerAdmin(TagMixIn, AuthModelView):
    permission = "admin-trainer-edit"
    form_columns = ["user", "bio"]
    column_list = ["user"]
    
class PracticeAdmin(AuthModelView):
    permission = "admin-practice-edit"
   
class LocationAdmin(TagMixIn, AuthModelView):
    permission = "admin-location-edit"

    form_columns = ["name",  "practice","phone_number", "street","address_line2",
                    "house_number","house_number_extention", "postal_code",
                    "city","state","country","latitude","longitude"]
    column_list = ["name", "practice", "street", "house_number", "city"]
    
class TrainingAdmin(AuthModelView):
    permission = "admin-training-edit"
    form_columns = ["name", "traningtype", "practice", "trainers", "trainingevents"]
    column_list = ["name", "traningtype", "practice", "trainers", "trainingevents"]


class TrainingTypeAdmin(TagMixIn, AuthModelView):
    permission = "admin-trainingtype-edit"
    form_columns = ["name"]
    column_list = ["name"]
    

class ClientTypeAdmin(AuthModelView):
    permission = "admin-cientType-edit"

class ClientAdmin(AuthModelView):
    permission = "admin-cient-edit"

class TrainingEventAdmin(AuthModelView):
    permission = "admin-trainingevent-edit"

table_admin.add_view(LocationAdmin(Location, db.session, category='Training', tag_field="directions"))
table_admin.add_view(PracticeAdmin(Practice, db.session, category='Training'))
table_admin.add_view(TrainerAdmin(Trainer, db.session, category='Training', tag_field="bio"))
table_admin.add_view(TrainingAdmin(Training, db.session, category='Training'))
table_admin.add_view(TrainingTypeAdmin(TrainingType, db.session, category='Training', tag_field="description"))
table_admin.add_view(TrainingEventAdmin(TrainingEvent, db.session, category='Training'))
table_admin.add_view(ClientTypeAdmin(ClientType, db.session, category='Training'))
table_admin.add_view(ClientAdmin(Client, db.session, category='Training'))

