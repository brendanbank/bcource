from flask import render_template, current_app, g, flash, redirect, url_for
from flask_babel import _
from flask import Blueprint, abort
from flask_security import permissions_required
from bcource import db
from flask_security import roles_required, current_user
from bcource.helpers import has_role
from bcource.training.helper import make_table_header
from bcource.models import Training, Practice, TrainingEvent
from bcource.training.training_forms import TrainingForm, EventForm, TrainingDeleteForm
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
            fstrip = field.replace('event_', '')
            field_dict[fstrip] = form_dict[f]
        
        if loop != False:
            if field_dict.get('id') == 'new':
                field_dict['id']= f'new_{i}'
                
            event_array.append(field_dict)
        
        i += 1
        
    return (event_array)

def update_training_events(training, form_events):
    
    current_events = training.trainingevents
    events_dict = {}
    form_dict = {}
    
    for event in current_events:
        events_dict[event.id] = event
    
    for form_event in form_events:
        form_dict[form_event['id']] = form_event
        
    for pk, row in events_dict.items():        
        if str(pk) in form_dict:
            
            row.start_time = form_dict[str(pk)]["start_time"]
            row.end_time = form_dict[str(pk)]["end_time"]
            row.location_id = form_dict[str(pk)]["location_id"]
            del(form_dict[str(pk)])
            
        else:
            db.session.delete(row)
            
    for key, val in form_dict.items():
        print (key,val)
        te = TrainingEvent(training=training,
                           start_time=val["start_time"],
                           end_time=val["end_time"],
                           location_id=val["location_id"],
                           )
        training.trainingevents.append(te)


@training_bp.route('/delete/<int:id>',methods=['GET', 'POST'])
def delete(id):
    training=Training().query.filter(Training.id==id).first()
    if not training:
        abort(404)
    training_name = training.name
        
    form = TrainingDeleteForm()
    if form.validate_on_submit():        
        db.session.delete(training)
        db.session.commit()
        flash(_('Successfully deleted training: %s' % training_name))
    
    return redirect(url_for('training_bp.index'))

@training_bp.route('/edit/<int:id>',methods=['GET', 'POST'])
@training_bp.route('/edit/',methods=['GET', 'POST'])
def edit(id=None):
    practice=Practice().query.filter(Practice.name=="default").first()
    
    training = None
    
    if id != None:
        training=Training().query.filter(Training.id==id).first()
        if not training:
            abort(404)
            
    
    form = TrainingForm(obj=training)
    
    if id == None:
        form.form_description = _("Create Training details")
    else:
        form.form_description = _("Edit Training details")
        
            
    if form.is_submitted():
        print (request.form)
    
    eventform = EventForm()
    eventform.event_location.query=practice.locations
    
    form.trainers.query=practice.trainers
    
    
    if form.validate_on_submit():
        if training == None:
            training=Training()
            training.practice = practice
            db.session.add(training)

        event_array = create_training_event_dict(request.form)
        update_training_events(training, event_array)
                
        form.populate_obj(training)   
        
        db.session.commit()
        flash(_('Training details are successfully saved!'))
        
        return(redirect(url_for('training_bp.edit', id=training.id)))

    events = []
    if training:
        for event in training.trainingevents:
            events.append({'id': event.id,
                           'start_time': event.start_time.isoformat(),
                           'end_time': event.end_time.isoformat(),
                           'location_id': event.location_id,
                           'location': str(event.location),
                           })        

    return render_template("training/training.html", form=form, eventform=eventform, events=json.dumps(events))

@training_bp.route('/')
def index():
    
    #trainings = Training().query.all()
    #Artist.query.filter(Artist.albums.any(genre_id=genre.id)).all()


    delete_form = TrainingDeleteForm()
    
    trainings = Training().query.filter(~Training.trainingevents.any()).all()
    trainings_with_dates = Training().query.join(Training.trainingevents).order_by(TrainingEvent.start_time).all()
    
    for trainings_with_date in trainings_with_dates:
        trainings.append(trainings_with_date)
        
        
    training_headers = make_table_header([_('Name'), _('Practice'), _('Training Type'), _('Trainers'), _('Date/Location')])
    return render_template("training/trainings.html", headers=training_headers, trainings=trainings, delete_form=delete_form)
