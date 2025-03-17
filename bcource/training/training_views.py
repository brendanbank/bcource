from flask import render_template, current_app, g, flash
from flask_babel import _
from flask import Blueprint, abort
from flask_security import permissions_required
from bcource import db
from flask_security import roles_required, current_user
from bcource.helpers import has_role
from bcource.training.helper import make_table_header
from bcource.training.models import Training, Practice
from bcource.training.training_forms import TrainingForm, EventForm
from flask.globals import request
import json

# Blueprint Configuration
training_bp = Blueprint(
    'training_bp', __name__,
    url_prefix="/training",
    template_folder='templates',
    static_folder='static',
    static_url_path='static'
)

def has_trainer_role():
    has_role(["trainer"])

training_bp.before_request(has_trainer_role)


def create_training_event_dict(form_dict):
    i=0
    loop = True
    fields = ['event_id', 'event_location_id', 'event_start_time', 'event_end_time']
    event_array=[]
    
    while loop:
        field_dict = {}
        for field in fields:
            f = f'{field}_{i}'
            if not f in form_dict:
                loop = False
                break
            field_dict[field] = form_dict[f]
        
        if loop != False:
            event_array.append(field_dict)
        
        i += 1
    return (event_array)
    

@training_bp.route('/edit/<int:id>',methods=['GET', 'POST'])
def edit(id):
    
    training=Training().query.filter(Training.id==id).first()
    
    if not training:
        abort(403)
        
    
    form = TrainingForm(obj=training)
    if form.is_submitted():
        print (request.form)
    
    eventform = EventForm()
    eventform.event_location.query=training.practice.locations
    
    form.trainers.query=training.practice.trainers
    events = []
    for event in training.trainingevents:
        events.append({'id': event.id,
                       'start_time': event.start_time.isoformat(),
                       'end_time': event.end_time.isoformat(),
                       'location_id': event.location_id,
                       'location': str(event.location),
                       })        
    
    if form.validate_on_submit():
        
        event_array = create_training_event_dict(request.form)
        print (event_array)
        
        form.populate_obj(training)
        db.session.commit()
        flash(_('Training details are successfully saved!'))
    
    return render_template("training/training.html", form=form, eventform=eventform, events=json.dumps(events))

@training_bp.route('/')
def index():
    
    trainings = Training().query.all()

    training_headers = make_table_header([_('Name'), _('Practice'), _('Training Type'), _('Trainers'), _('Date/Location')])
    return render_template("training/trainings.html", headers=training_headers, trainings=trainings)
