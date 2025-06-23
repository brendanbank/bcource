from flask import render_template, current_app, g, flash, redirect, url_for, jsonify
from flask_babel import _
from flask_babel import lazy_gettext as _l
from flask import Blueprint, abort
from flask_security import permissions_required
from bcource import db, menu_structure
from flask_security import roles_required, current_user
from bcource.helpers import admin_has_role, get_url
from bcource.training.helper import make_table_header
from bcource.models import Training, Practice, TrainingEvent, TrainingType, Trainer
from bcource.training.training_forms import TrainingForm, EventForm, TrainingDeleteForm
from flask.globals import request
from sqlalchemy import and_, or_
import json
from datetime import datetime
import pytz
from sqlalchemy.orm import joinedload
from bcource.filters import Filters

# Blueprint Configuration
training_bp = Blueprint(
    'training_bp', __name__,
    url_prefix="/training",
    template_folder='templates',
    static_folder='static',
    static_url_path='static'
)

def has_trainer_role():
    admin_has_role(["trainer"])

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
        
    url = get_url(default='training_bp.overview_list')

    if training.trainingenrollments:
        flash(_('You cannot delete training <span class="fw-bold" style="white-space:nowrap;">%s</span>.<br> It still has students enrolled to it.' % training_name), "error")
        return redirect(url)
    
    db.session.delete(training)
    db.session.commit()
    flash(_('Successfully deleted training: %s' % training_name))
    
    return redirect(url)


@training_bp.route('/edit/<int:id>',methods=['GET', 'POST'])
@training_bp.route('/edit/',methods=['GET', 'POST'])
def edit_training(id=None):
    
    practice=Practice.default_row() #@UndefinedVariable
    
    training = None
    
    if id != None:
        training=Training().query.join(Practice).filter(and_(
            Training.id==id, Practice.shortname==Practice.default_row().shortname)).first()
        if not training:
            return(redirect(get_url()))
            
    
    form = TrainingForm(obj=training)
    
    url = get_url(form, default='training_bp.overview_list')
    
    if form.close.data:
        return(redirect(url))
    
    if id == None:
        form.form_description = _("Create Training details")
    else:
        form.form_description = _("Edit Training details")
    
    eventform = EventForm()
    eventform.event_location.query=practice.locations
    
    form.trainers.query=practice.trainers
    
    
    if form.validate_on_submit():
        if training == None:
            training=Training()
            training.practice = practice
            db.session.add(training)

        event_array = create_training_event_dict(request.form)
        if not event_array:
            flash(_('You cannot save a training without dates!'), 'error')
            db.session.rollback()
            return render_template("training/training.html", 
                                   form=form, 
                                   eventform=eventform, 
                                   events=json.dumps(create_events(training)))
        
        update_training_events(training, event_array)
                
        form.populate_obj(training)   
        
        db.session.commit()
        flash(_('Training details are successfully saved!'))
        
        return(redirect(url))


    return render_template("training/training.html", form=form, eventform=eventform, events=json.dumps(create_events(training)))

def create_events(training):
    events = []
    if training:
        for event in training.trainingevents:
            events.append({'id': event.id,
                           'start_time': event.start_time.isoformat(),
                           'end_time': event.end_time.isoformat(),
                           'location_id': event.location_id,
                           'location': str(event.location),
                           })        
    return (events)
training_admin = menu_structure.add_menu(_l('Training Administration'), role='trainer')
# training_admin.add_menu(_l('Training Editor'), 'training_bp.index', role='trainer')

@training_bp.route('/')
def index():

    delete_form = TrainingDeleteForm()
    
    trainings = Training().query.join(Practice).filter(
        and_(
            Practice.shortname==Practice.default_row().shortname, 
            ~Training.trainingevents.any())
        ).all()
        
    trainings_with_dates = Training().query.join(Training.trainingevents).join(Practice).filter(
        and_(
            Practice.shortname==Practice.default_row().shortname)
        ).order_by(TrainingEvent.start_time).all()
    
    for trainings_with_date in trainings_with_dates:
        trainings.append(trainings_with_date)
        
    training_headers = make_table_header([_('Name'), _('Training Type'), _('Trainers'), _('Date/Location')])
    return render_template("training/trainings.html", headers=training_headers, trainings=trainings, delete_form=delete_form)



def make_filters():

    filters = Filters("Training Filters")
    past_training_filter = filters.new_filter("period", _("Period"))
    past_training_filter.add_filter_item( 1, _("Past Trainings"))

    time_now = datetime.now(tz=pytz.timezone('UTC'))
    training_type_filter = filters.new_filter("training_type", _("Training Types"))
    for training_type in TrainingType().query.join(Training).join(TrainingEvent).join(Practice, Practice.id==Training.practice_id).filter(and_(
                        Practice.shortname==Practice.default_row().shortname,
                        ~Training.trainingevents.any(TrainingEvent.start_time < time_now)
                        )).all():
        training_type_filter.add_filter_item( training_type.id, training_type.name)



    trainer_filter = filters.new_filter("trainers", _("Trainers"))
    for trainer in Practice.default_row().trainers:
        trainer_filter.add_filter_item( trainer.id, trainer)

    return(filters)

def training_query(filters, search_on_id=None):

    q = Training().query
    time_now = datetime.now(tz=pytz.timezone('UTC'))

    if search_on_id:
        q = Training().query.filter(Training.id==search_on_id)
        
        t = q.first()
        
        training_filter = filters.new_filter("selected_training", _("Training"))
        training_filter.add_filter_item( search_on_id, t.name)
        filters.show = True
        filters.filers_checked = True
        filters.get_filter("selected_training").get_item(search_on_id).checked = True
        
    
    if  filters.get_items_checked('training_type'):

        items_checked = filters.get_items_checked('training_type')
        trainingtypes = TrainingType().query.join(Practice, Practice.id==TrainingType.practice_id).filter(Practice.shortname==Practice.default_row().shortname, 
                                                                   TrainingType.id.in_(items_checked)).subquery()
        q = q.join(trainingtypes)    
          
    if filters.get_item_is_checked("period","1"):
        future = TrainingEvent().query.filter(TrainingEvent.start_time < time_now
                        ).order_by(TrainingEvent.start_time).subquery()
    else:
        future = TrainingEvent().query.filter(TrainingEvent.start_time > time_now
                        ).order_by(TrainingEvent.start_time).subquery()
    
    
    q = q.join(future)
    
    if  filters.get_items_checked('trainers'):
    
        items_checked = filters.get_items_checked('trainers')
    
        q = q.join(Training.trainers).filter(Trainer.id.in_(items_checked))
    
    q = q.join(TrainingEvent).order_by(TrainingEvent.start_time)

    trainings = q.all()
    for t in trainings:
        t.fill_numbers(current_user)
        
    return trainings

@training_bp.route('/search',methods=['GET'])
def search():
    results = {}
    results.update({"results": []})

    query_term = request.args.get('q')
    
    r = []
    time_now = datetime.now(tz=pytz.timezone('UTC'))
    
    if query_term:
        r = Training().query.join(TrainingEvent).join(Practice).filter(and_(
                Practice.shortname==Practice.default_row().shortname, 
                Training.active==True,
                ), or_( 
            Training.name.ilike(f'%{query_term}%'))).order_by(TrainingEvent.start_time).all()
    else:
    

        r = Training().query.join(TrainingEvent).join(Practice).filter(and_(
            Practice.shortname==Practice.default_row().shortname,
            Training.active==True, 
            )).order_by(TrainingEvent.start_time).all()
        
    for training in r:
        results["results"].append({"id": training.id,  "text":  training.name})
    
    return jsonify(results)

training_admin.add_menu(_l('Training Overview'), 'training_bp.overview_list', role='trainer')

@training_bp.route('/training-overview')
def overview_list():
    clear = request.args.getlist('submit_id')
    if clear and clear[0]=='clear':
        return redirect(url_for('training_bp.overview_list', show=request.args.getlist('show')))
    
    
    
    search_on_id = request.args.get('id')

    traingingtypes = TrainingType().query.join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname)
                        ).all()
    filters = make_filters().process_filters()
    trainings = training_query(filters,search_on_id)

    delete_form = TrainingDeleteForm()
    
    return render_template("training/overview_list.html", trainings=trainings, 
                           delete_form=delete_form,
                           trainingtypes=traingingtypes ,
                           filters=filters, 
                           page_name=_("Training Overview"))


