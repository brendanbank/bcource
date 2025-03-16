
from flask import Blueprint
from bcource.admin.admin_views import AuthModelView
from bcource import db, table_admin
from .models import Location, Practice, Trainer, Training, TrainingType, TrainingEvent, ClientType, Client
from sqlalchemy.orm import configure_mappers

# Blueprint Configuration
training_bp = Blueprint(
    'training_bp', __name__,
    url_prefix="/training",
    template_folder='templates',
    static_folder='static',
    static_url_path='/training/static'
)

class TrainerAdmin(AuthModelView):
    permission = "admin-trainer-edit"
    form_columns = ["user", "bio"]
    column_list = ["user"]
    
class PracticeAdmin(AuthModelView):
    permission = "admin-practice-edit"
    
class LocationAdmin(AuthModelView):
    permission = "admin-location-edit"

    form_columns = ["name",  "practice","phone_number", "street","address_line2",
                    "house_number","house_number_extention", "postal_code",
                    "city","state","country","latitude","longitude","directions"]
    column_list = ["name", "practice", "street", "house_number", "city"]
    
class TrainingAdmin(AuthModelView):
    permission = "admin-training-edit"
    form_columns = ["name", "traningtype", "practice", "trainers", "trainingevents"]
    column_list = ["name", "traningtype", "practice", "trainers", "trainingevents"]

class TrainingTypeAdmin(AuthModelView):
    permission = "admin-trainingtype-edit"
    form_columns = ["name"]
    column_list = ["name"]

class ClientTypeAdmin(AuthModelView):
    permission = "admin-cientType-edit"

class ClientAdmin(AuthModelView):
    permission = "admin-cient-edit"

class TrainingEventAdmin(AuthModelView):
    permission = "admin-trainingevent-edit"

table_admin.add_view(LocationAdmin(Location, db.session, category='Training'))
table_admin.add_view(PracticeAdmin(Practice, db.session, category='Training'))
table_admin.add_view(TrainerAdmin(Trainer, db.session, category='Training'))
table_admin.add_view(TrainingAdmin(Training, db.session, category='Training'))
table_admin.add_view(TrainingTypeAdmin(TrainingType, db.session, category='Training'))
table_admin.add_view(TrainingEventAdmin(TrainingEvent, db.session, category='Training'))
table_admin.add_view(ClientTypeAdmin(ClientType, db.session, category='Training'))
table_admin.add_view(ClientAdmin(Client, db.session, category='Training'))

