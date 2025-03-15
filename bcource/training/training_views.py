
from flask import Blueprint
from bcource.admin.admin_views import AuthModelView
from bcource import db, table_admin
from bcource.training.models import Practice
from sqlalchemy.orm import configure_mappers

# Blueprint Configuration
training_bp = Blueprint(
    'training_bp', __name__,
    url_prefix="/training",
    template_folder='templates',
    static_folder='static',
    static_url_path='/training/static'
)

from .models import Location, Practice, Trainer
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

table_admin.add_view(LocationAdmin(Location, db.session, category='Training'))
table_admin.add_view(PracticeAdmin(Practice, db.session, category='Training'))
table_admin.add_view(TrainerAdmin(Trainer, db.session, category='Training'))

