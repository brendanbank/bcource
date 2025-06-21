from flask import (Blueprint, render_template, jsonify, abort, send_from_directory, g, 
                   flash, url_for, redirect, render_template_string, request)
from flask_babel import lazy_gettext as _l
from flask_babel import _
from flask_security import current_user, auth_required
from bcource.scheduler.scheduler_forms import SchedulerTrainingEnrollForm
from bcource.training.training_forms import TrainingDerollForm, TrainingEnrollForm
from bcource import menu_structure, db
from bcource.helpers import admin_has_role, get_url
from bcource.models import User, Student, Practice, Training, TrainingType, TrainingEvent, TrainingEnroll
from sqlalchemy import or_, and_
import bcource.messages as system_msg
from bcource.students.common import deroll_common, enroll_common
from sqlalchemy.orm import joinedload

from datetime import datetime
import pytz
from alembic.command import current

# Blueprint Configuration
scheduler_bp = Blueprint(
    'scheduler_bp', __name__,
    url_prefix="/scheduler",
    template_folder='templates',
    static_folder='static'
)


def has_student_role():
    admin_has_role(["student"])
    
    q = Student().query.join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname, Student.user==current_user)
                        ).first()
                        
    if not q or not q.studentstatus or  q.studentstatus.name != "active":
        flash(_("Student does not have an active status!"), 'error')
        flash(_("Please check with the Student Administrators to have your status changed to active."), 'error')
        abort(403)

scheduler_bp.before_request(has_student_role)

class Filter():
    def __init__(self, id, name):
        self.name = name
        self.id = id
    
    def __str__(self):
        return self.name

training_filter_obj = [Filter(1,"Past Trainings")]


def make_filters(my_trainings=None):

    filters = []
    
    time_now = datetime.now(tz=pytz.timezone('UTC'))
    if my_trainings:
        
        traingingtypes = TrainingType().query.join(Training).join(TrainingEvent).join(Practice, Practice.id==Training.practice_id).filter(and_(
                        Practice.shortname==Practice.default_row().shortname,
                        TrainingEvent.start_time > time_now
                        )).all()
    else:
        traingingtypes = TrainingType().query.join(Training).join(TrainingEvent).join(Practice, Practice.id==Training.practice_id).filter(and_(
                        Practice.shortname==Practice.default_row().shortname,
                        ~Training.trainingevents.any(TrainingEvent.start_time < time_now)
                        )).all()
    filters.append(('training_filter', 'Training Filter', 
                    training_filter_obj))

    filters.append(('trainingtype', 'Training Type', 
                    traingingtypes))
    
    filters.append(('my_trainings', 'My Trainings', 
                    [current_user]))

    return(filters)

def process_filters(my_trainings=None):
    filters_checked = {}
    
    try:
        filters_checked.update( {'trainingtype': [int(i) for i in request.args.getlist('trainingtype')]} )
        filters_checked.update( {'training_filter': [int(i) for i in request.args.getlist('training_filter')]} )
        if my_trainings:
            filters_checked.update( {'my_trainings': [current_user.id]} )
        else:
            filters_checked.update( {'my_trainings': [int(i) for i in request.args.getlist('my_trainings')]} )

    except Exception as e:
        print (f'process_filters: url args not integer {request.args}: error {e}')
                
    return(filters_checked)


def training_query(search_on_id=None, my_trainings=None):
    selected_filters=process_filters()
    
    time_now = datetime.now(tz=pytz.timezone('UTC'))

    
    # # past trainings
    if request.args.get('training_filter') == "1":
        future = TrainingEvent().query.filter(TrainingEvent.start_time < time_now
                        ).order_by(TrainingEvent.start_time).subquery()
    else:
        future = TrainingEvent().query.filter(TrainingEvent.start_time > time_now
                        ).order_by(TrainingEvent.start_time).subquery()    

    if search_on_id:
        q = Training().query.join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname,Training.id==search_on_id))
    
    elif not selected_filters.get('trainingtype') and not selected_filters.get('my_trainings') and not my_trainings:
        
        q = Training().query.join(future).join(TrainingEvent).options(joinedload(Training.trainingevents)).join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname, 
                        Training.active==True)
                        ).order_by(TrainingEvent.start_time)
    
    elif selected_filters.get('my_trainings') or my_trainings:
        
        if not selected_filters.get('trainingtype'):
            q = Training().query.join(future).join(TrainingEnroll).join(TrainingEvent).options(joinedload(Training.trainingevents)).join(Student).join(Practice, Practice.id==Training.practice_id).filter(
                and_(Student.user_id == current_user.id))
        else:
            q = Training().query.join(future).join(TrainingEnroll).join(TrainingEvent).options(joinedload(Training.trainingevents)).join(Student).join(Practice, Practice.id==Training.practice_id).filter(
                and_(Student.user_id == current_user.id), or_( 
            Training.traningtype_id.in_(selected_filters.get('trainingtype')), 
            )).order_by(TrainingEvent.start_time)
        

    else:
        q =  Training().query.join(future).join(TrainingEvent).options(joinedload(Training.trainingevents)).join(Practice).filter(and_(
                    Practice.shortname==Practice.default_row().shortname,
                    ~Training.trainingevents.any(TrainingEvent.start_time < time_now),
                    Training.active==True), or_( 
            Training.traningtype_id.in_(selected_filters.get('trainingtype')), 
            )).order_by(TrainingEvent.start_time)
    
    
    trainings = q.all()
    for t in trainings:
        t.fill_numbers(current_user)
        
    return trainings


@scheduler_bp.route('/training/cancelation-policy', methods=['GET'])
@auth_required()
def cancellation():
    return render_template("scheduler/cancellation_policy.html")

@scheduler_bp.route('/training/mytraining', methods=['GET'])
@auth_required()
def mytraining():

    clear = request.args.getlist('submit_id')
    if clear and clear[0]=='clear':
        return redirect(url_for('scheduler_bp.mytraining'))

    deroll_form = TrainingDerollForm()
    deroll_form.url.data = get_url(deroll_form, 'scheduler_bp.index')

    search_on_id = request.args.get('id')
    traingingtypes = TrainingType().query.join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname)
                        ).all()
                        
    return render_template("scheduler/scheduler.html", training=training_query(search_on_id,my_trainings=True), 
                           trainingtypes=traingingtypes, 
                           filters=make_filters(my_trainings=True), 
                           filters_checked=process_filters(my_trainings=True),
                           page_name=_l('My Training Schedule'),
                           deroll_form=deroll_form

                           )


@scheduler_bp.route('/training', methods=['GET'])
@auth_required()
def index():

    clear = request.args.getlist('submit_id')
    if clear and clear[0]=='clear':
        return redirect(url_for('scheduler_bp.index'))
    
    deroll_form = TrainingDerollForm()
    deroll_form.url.data = get_url(deroll_form, 'scheduler_bp.index')
    
    search_on_id = request.args.get('id')
    traingingtypes = TrainingType().query.join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname)
                        ).all()
    return render_template("scheduler/scheduler.html", training=training_query(search_on_id),  
                           filters=make_filters(), 
                           trainingtypes=traingingtypes, 
                           filters_checked=process_filters(),
                           page_name=_l('Training Schedule'),
                           deroll_form=deroll_form
                           )




@scheduler_bp.route('/training/deroll/<int:id>',methods=['GET', 'POST'])
@auth_required()
def deroll(id):
    
    form = TrainingDerollForm()    
    training = Training().query.get(id)
    url = get_url(form)

    if form.validate_on_submit():
        return_acton =  deroll_common(training, current_user)
        if return_acton:
            return redirect(url)

    return render_template("scheduler/deroll.html", training=training, form=form, return_url=url)


@scheduler_bp.route('/training/enroll/<int:id>',methods=['GET', 'POST'])
@auth_required()
def enroll(id):
    
    training = Training().query.get(id)
    
    print (training.enrolled(current_user))
    
    form = SchedulerTrainingEnrollForm()    
    url = get_url(form)
    
    if form.validate_on_submit():
        redirect_url = enroll_common(training, current_user)  
        if redirect_url:
            return redirect(url)
        
    return render_template("scheduler/enroll.html", training=training, form=form, return_url=url)


@scheduler_bp.route('/search',methods=['GET'])
@auth_required()
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
                ~Training.trainingevents.any(TrainingEvent.start_time < time_now)
                ), or_( 
            Training.name.ilike(f'%{query_term}%'))).order_by(TrainingEvent.start_time).all()
    else:
    

        r = Training().query.join(TrainingEvent).join(Practice).filter(and_(
            Practice.shortname==Practice.default_row().shortname,
            Training.active==True, 
            ~Training.trainingevents.any(TrainingEvent.start_time < time_now),
            )).order_by(TrainingEvent.start_time).all()
        
    for training in r:
        results["results"].append({"id": training.id,  "text":  training.name})
    return jsonify(results)

my_training = menu_structure.add_menu(_l('Training Scheduler'), role='student')
my_training.add_menu(_l('Schedule Training'), 'scheduler_bp.index', role='student')
my_training.add_menu(_l('My schedule'), 'scheduler_bp.mytraining', role='student' )


