from flask import render_template, current_app, g
from flask_babel import _
from flask import Blueprint, abort
from flask_security import permissions_required
from bcource import db
from flask_security import roles_required, current_user
from bcource.helpers import has_role
from bcource.training.helper import make_table_header
from bcource.training.models import Training, Practice
from bcource.training.training_forms import TrainingForm
# Blueprint Configuration
training_bp = Blueprint(
    'training_bp', __name__,
    url_prefix="/training",
    template_folder='templates',
    static_folder='static',
    static_url_path='/training'
)

def has_trainingr_role():
    has_role(["trainer"])

        
    
training_bp.before_request(has_trainingr_role)

@training_bp.route('/edit/<int:id>',methods=['GET', 'POST'])
def edit(id):
    
    training=Training().query.filter(Training.id==id).first()
    
    if not training:
        abort(403)    
    
    form = TrainingForm(obj=training)
    
    form.trainers.query=training.practice.trainers
    
    return render_template("training/training.html", form=form)

@training_bp.route('/')
def index():
    
    trainings = Training().query.all()

    training_headers = make_table_header([_('Name'), _('Practice'), _('Training Type'), _('Trainers'), _('Date/Location')])
    return render_template("training/trainings.html", headers=training_headers, trainings=trainings)
