from flask import (Blueprint, render_template, jsonify, abort, send_from_directory, g, 
                   flash, url_for, redirect, render_template_string, request)
from flask_babel import lazy_gettext as _l
from flask_babel import _
from flask_security import current_user, auth_required
from bcource.scheduler.scheduler_forms import TrainingEnrollForm, TrainingDerollForm
from bcource import menu_structure, db
from bcource.helpers import admin_has_role, get_url
from bcource.models import User, Student, Practice, Training, TrainingType, TrainingEvent, TrainingEnroll
from sqlalchemy import or_, and_
import bcource.messages as system_msg

from datetime import datetime
import pytz

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

    filters.append(('trainingtype', 'Training Type', 
                    traingingtypes))
    
    filters.append(('my_trainings', 'My Trainings', 
                    [current_user]))

    return(filters)

def process_filters(my_trainings=None):
    filters_checked = {}
    
    try:
        filters_checked.update( {'trainingtype': [int(i) for i in request.args.getlist('trainingtype')]} )
        
        if my_trainings:
            filters_checked.update( {'my_trainings': [current_user.id]} )
        else:
            filters_checked.update( {'my_trainings': [int(i) for i in request.args.getlist('my_trainings')]} )

    except Exception as e:
        print (f'process_filters: url args not integer {request.args}: error {e}')
                
    return(filters_checked)


def training_query(search_on_id=None, my_trainings=None):
    selected_filters=process_filters()
    if not selected_filters:
        return Training().query.all()
    
    time_now = datetime.now(tz=pytz.timezone('UTC'))
    
    if search_on_id:
        q = Training().query.join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname,Training.id==search_on_id))
        return q.all()
    
    
    if not selected_filters.get('trainingtype') and not selected_filters.get('my_trainings') and not my_trainings:
        
        q = Training().query.join(TrainingEvent).join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname, 
                        ~Training.trainingevents.any(TrainingEvent.start_time < time_now),
                        Training.active==True)
                        ).order_by(TrainingEvent.start_time)
        return q.all()
    
    if selected_filters.get('my_trainings') or my_trainings:
        
        if not selected_filters.get('trainingtype'):
            q = Training().query.join(TrainingEnroll).join(TrainingEvent).join(Student).join(Practice, Practice.id==Training.practice_id).filter(
                and_(Student.user_id == current_user.id,
                     TrainingEvent.start_time > time_now)).order_by(TrainingEvent.start_time)
        else:
            q = Training().query.join(TrainingEnroll).join(TrainingEvent).join(Student).join(Practice, Practice.id==Training.practice_id).filter(
                and_(Student.user_id == current_user.id,
                     TrainingEvent.start_time > time_now), or_( 
            Training.traningtype_id.in_(selected_filters.get('trainingtype')), 
            )).order_by(TrainingEvent.start_time)
        
        return q.all()

    q =  Training().query.join(TrainingEvent).join(Practice).filter(and_(
                Practice.shortname==Practice.default_row().shortname,
                ~Training.trainingevents.any(TrainingEvent.start_time < time_now),
                Training.active==True), or_( 
        Training.traningtype_id.in_(selected_filters.get('trainingtype')), 
        )).order_by(TrainingEvent.start_time)
        
    return q.all()


@scheduler_bp.route('/training/mytraining', methods=['GET'])
@auth_required()
def mytraining():

    clear = request.args.getlist('submit_id')
    if clear and clear[0]=='clear':
        return redirect(url_for('scheduler_bp.mytraining'))
    
    search_on_id = request.args.get('id')
    
    traingingtypes = TrainingType().query.join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname)
                        ).all()
                        
    return render_template("scheduler/scheduler.html", training=training_query(search_on_id,my_trainings=True), 
                           trainingtypes=traingingtypes, 
                           filters=make_filters(my_trainings=True), 
                           filters_checked=process_filters(my_trainings=True),
                           page_name=_l('My Training Schedule'))


@scheduler_bp.route('/training', methods=['GET'])
@auth_required()
def index():

    clear = request.args.getlist('submit_id')
    if clear and clear[0]=='clear':
        return redirect(url_for('scheduler_bp.index'))
    
    search_on_id = request.args.get('id')
    traingingtypes = TrainingType().query.join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname)
                        ).all()
    return render_template("scheduler/scheduler.html", training=training_query(search_on_id),  
                           filters=make_filters(), 
                           trainingtypes=traingingtypes, 
                           filters_checked=process_filters(),
                           page_name=_l('Training Schedule'))


@scheduler_bp.route('/training/deroll/<int:id>',methods=['GET', 'POST'])
@auth_required()
def deroll(id):
    
    training = Training().query.get(id)
        
    form = TrainingDerollForm()    
    url = get_url(form)
    
    training_enroll = training.enrolled(current_user)
    
    
        
    if not training_enroll:
        flash(_("You are not enrolled for this training: ") + training.name + ".",'error')
        return redirect(url)
    
    time_now = datetime.now(tz=pytz.timezone('UTC'))
    
    q = Training().query.join(TrainingEnroll).join(TrainingEvent).filter(
        and_(~Training.trainingevents.any(TrainingEvent.start_time < time_now),
             Training.id == training.id)).first()
    if not q:
        flash(_("You cannot remove yourself from a training that has already started: ") + training.name + ".", 'error')
        return redirect(url)
    
    if form.validate_on_submit():
        
        
        db.session.delete(training_enroll)        
        db.session.commit()
        
        system_msg.EmailStudentDerolled(envelop_to=training.trainer_users, user=current_user, training=training).send()
        system_msg.EmailStudentDerolledInTraining(envelop_to=current_user, training=training, user=current_user).send()
        flash(_("You are successfully removed yourself from the training: ") + training.name + ".")
        return redirect(url)
    
    return render_template("scheduler/deroll.html", training=training, form=form)


@scheduler_bp.route('/training/enroll/<int:id>',methods=['GET', 'POST'])
@auth_required()
def enroll(id):
    
    training = Training().query.get(id)
    
    print (training.enrolled(current_user))
    
    form = TrainingEnrollForm()    
    url = get_url(form)
    
        
    if training.enrolled(current_user):
        flash(_("You are already enrolled for this training: ") + training.name + ".",'error')
        return redirect(url)
    
    if form.validate_on_submit():
        
        enroll = TrainingEnroll()

        student = Student().query.join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname, Student.user==current_user)
                        ).first()
        if not student:
            flash(_("enroll: Student Not Found!"), 'error')
            abort(403)
            
        enroll.student = student          
        enroll.training = training
        
        if len(training.trainingenrollments) >= training.max_participants:
            enroll.status = "waitlist"

        else:
            enroll.status = "enrolled"
        
        db.session.add(enroll)

        if len(training.trainingenrollments) >= training.max_participants:
            system_msg.EmailStudentEnrolledInTrainingWaitlist(envelop_to=current_user, training=training, user=current_user).send()
            system_msg.EmailStudentEnrolledWaitlist(envelop_to=training.trainer_users, user=current_user, training=training).send()

        else:
            system_msg.EmailStudentEnrolledInTraining(envelop_to=current_user, training=training, user=current_user).send()
            system_msg.EmailStudentEnrolled(envelop_to=training.trainer_users, user=current_user, training=training).send()
            

        db.session.commit()
        
        if len(training.trainingenrollments) >= training.max_participants:
            flash(_("You have been added to the wait list of training training: ") + training.name + ".")
        else:
            flash(_("You have successfully enrolled into the training: ") + training.name + ".")
        
        return redirect(url)
    
    return render_template("scheduler/enroll.html", training=training, form=form)


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


