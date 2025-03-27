from bcource.admin.helper import AuthModelView, CkModelView, CKTextAreaField, TagMixIn
from bcource import db, table_admin
from bcource.models import Location, Practice, Trainer, Training, TrainingType, TrainingEvent,\
    Content, Policy
from sqlalchemy.orm import configure_mappers
from wtforms import TextAreaField




class TrainerAdmin(TagMixIn, CkModelView, AuthModelView):
    permission = "admin-trainer-edit"
    form_columns = ["user"]
    column_list = ["user"]
    

    
class PracticeAdmin(AuthModelView):
    permission = "admin-practice-edit"
    
    form_columns = ["name","phone_number","street","address_line2","house_number","house_number_extention",
                    "postal_code","city","state","country","trainers", "locations"]
    column_list = ["name","city", "trainers"]

   
class LocationAdmin(TagMixIn, CkModelView, AuthModelView):
    permission = "admin-location-edit"

    form_columns = ["name",  "practice","phone_number", "street","address_line2",
                    "house_number","house_number_extention", "postal_code",
                    "city","state","country","latitude","longitude"]
    column_list = ["name", "practice", "street", "house_number", "city"]
    
class TrainingAdmin(AuthModelView):
    permission = "admin-training-edit"
    form_columns = ["name", "traningtype", "practice", "trainers", "trainingevents"]
    column_list = ["name", "traningtype", "practice", "trainers", "trainingevents"]
    form_widget_args = {
        'trainingevents':{
            'disabled':True
        }
    }


class TrainingTypeAdmin(TagMixIn, CkModelView, AuthModelView):
    permission = "admin-trainingtype-edit"
    form_columns = ["name", "policies"]
    column_list = ["name"]
    

class ClientTypeAdmin(AuthModelView):
    permission = "admin-cientType-edit"

class ClientAdmin(AuthModelView):
    permission = "admin-cient-edit"

class TrainingEventAdmin(AuthModelView):
    permission = "admin-trainingevent-edit"


class PolicyAdmin(TagMixIn, CkModelView, AuthModelView):
    permission = "admin-policy-edit"
    form_columns = ["name", "trainingtypes"]

    form_widget_args = {
        'trainingtypes':{
            'disabled':True
        }
    }


table_admin.add_view(LocationAdmin(Location, db.session, category='Training', tag_field="directions"))
table_admin.add_view(PracticeAdmin(Practice, db.session, category='Training'))
table_admin.add_view(TrainerAdmin(Trainer, db.session, category='Training', tag_field="bio"))
table_admin.add_view(TrainingAdmin(Training, db.session, category='Training'))
table_admin.add_view(TrainingTypeAdmin(TrainingType, db.session, category='Training', tag_field="description"))
table_admin.add_view(TrainingEventAdmin(TrainingEvent, db.session, category='Training'))
table_admin.add_view(PolicyAdmin(Policy, db.session, category='Training', tag_field="policy"))

