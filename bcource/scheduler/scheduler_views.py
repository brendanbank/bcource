from flask import (current_app, Blueprint, render_template, jsonify, abort, 
                   flash, url_for, redirect, request)
from flask_babel import lazy_gettext as _l
from flask_babel import _
from flask_security import current_user, auth_required
from bcource.scheduler.scheduler_forms import SchedulerTrainingEnrollForm
from bcource.training.training_forms import TrainingDerollForm
from bcource import menu_structure, db
from bcource.helpers import admin_has_role, get_url, safe_redirect
from bcource.models import User, Student, Practice, Training, TrainingType, TrainingEvent, TrainingEnroll, Content
from sqlalchemy import or_, and_
import bcource.messages as system_msg
from bcource.students.common import deroll_common, enroll_common, enroll_from_waitlist, invite_from_waitlist
from datetime import datetime
import pytz
from bcource.filters import Filters
from bcource.user.user_status import UserProfileChecks
from bcource.students.student_policies import TrainingBookingPolicy, can_student_book_trainings, CancelationPolicy
from bcource.helper_app_context import b_pagination

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
        from bcource.errors import HTTPExceptionStudentNotActive
        raise (HTTPExceptionStudentNotActive())
    
    if not UserProfileChecks().validate():
        from bcource.errors import HTTPExceptionProfileInComplete
        raise (HTTPExceptionProfileInComplete())


scheduler_bp.before_request(has_student_role)


def make_filters(user=None):

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

    if user:
        user_training_filter = filters.new_filter("my", _("User"))
        user_training_filter.add_filter_item( user.id, user.fullname)
        

    return(filters)

            

def training_query(filters, search_on_id=None, user=None):
    
        
    time_now = datetime.now(tz=pytz.timezone('UTC'))

    q = Training().query
    
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
    
    if user and filters.get_item_is_checked("my",user.id):
        users = TrainingEnroll().query.join(Student).filter(TrainingEnroll.student_id == Student.id, Student.user_id == user.id).subquery()
        q = q.join(users)

    
    q = q.join(Practice, Practice.id==Training.practice_id).filter(and_(
                        Practice.shortname==Practice.default_row().shortname, 
                        Training.active==True)
                        )    
    
    q = q.join(TrainingEvent).order_by(TrainingEvent.start_time.asc())

    return q


def fill_trainings(select_query, per_page=current_app.config['POSTS_PER_PAGE']):
    
    trainings=b_pagination(select_query, per_page=per_page)
    training_types = []
    for t in trainings:
        t.fill_numbers(current_user)
        
        if not t.trainingtype in training_types:
            training_types.append(t.trainingtype)

    
    for trainingtype in training_types:
        results = can_student_book_trainings(current_user.student_from_practice, trainings, trainingtype)
        for training in trainings:
            if training.id in results.keys():
                training.in_policy = results[training.id]

    
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
        return redirect(url_for('scheduler_bp.mytraining', show=request.args.getlist('show')))
    
    deroll_form = TrainingDerollForm()
    deroll_form.url.data = get_url(deroll_form, 'scheduler_bp.index')
    
    search_on_id = request.args.get('id')
    traingingtypes = TrainingType().query.join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname)
                        ).all()
                        
    filters = make_filters(user=current_user).process_filters()
    filters.get_filter("my").get_item(current_user.id).checked = True

    trainings_select = training_query(filters, search_on_id=search_on_id, user=current_user)
    trainings = fill_trainings(trainings_select)
    
    return render_template("scheduler/scheduler.html", pagination=trainings,  
                           filters=filters, 
                           trainingtypes=traingingtypes, 
                           page_name=_l('My Training Schedule'),
                           deroll_form=deroll_form
                           )


"""-----"""

@scheduler_bp.route('/training', methods=['GET'])
@auth_required()
def index():

    clear = request.args.getlist('submit_id')
    if clear and clear[0]=='clear':
        return redirect(url_for('scheduler_bp.index', show=request.args.getlist('show')))
    
    deroll_form = TrainingDerollForm()
    deroll_form.url.data = get_url(deroll_form, 'scheduler_bp.index')
    
    search_on_id = request.args.get('id')
    traingingtypes = TrainingType().query.join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname)
                        ).all()
                        
    filters = make_filters(user=current_user).process_filters()
    trainings_select = training_query(filters, search_on_id=search_on_id, user=current_user)
    trainings = fill_trainings(trainings_select)

    return render_template("scheduler/scheduler.html", pagination=trainings,  
                           filters=filters, 
                           trainingtypes=traingingtypes, 
                           page_name=_l('Training Schedule'),
                           deroll_form=deroll_form
                           )


@scheduler_bp.route('/training/enable/<string:uuid>',methods=['GET', 'POST'])
@auth_required()
def enable(uuid):
    enrollment = TrainingEnroll().query.join(Student).join(User).filter(TrainingEnroll.uuid == uuid, User.id == current_user.id).first()

    url = get_url()
    if not (enrollment):
        flash(_("Cannot find your enrollement!"), 'error')
        return safe_redirect(url)

    enroll_common(enrollment.training, current_user)

    return safe_redirect(url)

@scheduler_bp.route('/training/deroll/<int:id>',methods=['GET', 'POST'])
@auth_required()
def deroll(id):  # @ReservedAssignment
    
    form = TrainingDerollForm()    
    training = Training().query.get(id)
    url = get_url(form)
    
    cancel_policy = CancelationPolicy(training=training, user=current_user)
    cancel_policy.validate()
    
    if form.validate_on_submit() :
        
                                           
        return_acton =  deroll_common(training, current_user)

        if not cancel_policy.status and return_acton:
            enrollment = TrainingEnroll().query.join(Student).filter(TrainingEnroll.student_id == Student.id, Student.user_id == current_user.id).first()

            system_msg.EmailStudentDerolledInTrainingOutOfPolicyTrainer(envelop_to=current_user, training=training, 
                                                                         policy_txt=Content.get_tag('Cancellation Policy'), enrollment=enrollment ).send()
            system_msg.EmailStudentDerolledInTrainingOutOfPolicy(
                envelop_to=current_user, training=training, 
                policy_txt=Content.get_tag('Cancellation Policy'
                                            ),enrollment=enrollment ).send()

        if return_acton:
            return safe_redirect(url)

    return render_template("scheduler/deroll.html", cancel_policy=cancel_policy, training=training, form=form, return_url=url)

@scheduler_bp.route('/training/accept-invite/<string:uuid>',methods=['GET', 'POST'])
@auth_required()
def accept_invite(uuid):
    
    enrollment = TrainingEnroll().query.join(Student).join(User).filter(TrainingEnroll.uuid == uuid, User.id == current_user.id).first()
    
    url = get_url()
    
    if not (enrollment):
        flash(_("Cannot find invitation!"), 'error')
        return safe_redirect(url)

    enroll_from_waitlist(enrollment)

    return safe_redirect(url)

@scheduler_bp.route('/training/decline-invite/<string:uuid>',methods=['GET', 'POST'])
@auth_required()
def decline_invite(uuid):
    
    enrollment = TrainingEnroll().query.join(Student).join(User).filter(TrainingEnroll.uuid == uuid, User.id == current_user.id).first()
    
    url = get_url()
    
    if not (enrollment):
        flash(_("Cannot find invitation! Have Did is expire?"), 'error')
        return safe_redirect(url)

    enrollment.status="waitlist-declined"
    db.session.commit()

    waitlist_enrollments_eligeble = enrollment.training.waitlist_enrollments_eligeble()
    for enrollment in waitlist_enrollments_eligeble:
        invite_from_waitlist(enrollment)

    flash(_("You have declined the invite for training %(trainingname)s!", trainingname=enrollment.training.name), 'error')
    return safe_redirect(url)

@scheduler_bp.route('/training/enroll/<int:id>',methods=['GET', 'POST'])
@auth_required()
def enroll(id):  # @ReservedAssignment
    
    training = Training().query.get(id)
    
    if not training:
        flash(f"cannot find training with id {id}")
        abort (404)
    
    
    form = SchedulerTrainingEnrollForm()    
    url = get_url(form)
    
    policies = TrainingBookingPolicy(training=training,user=current_user)
    
    if not policies.validate():
        for policy in policies:
            if not policy:
                flash (policy, "error")
            return safe_redirect(url)


    if form.validate_on_submit():
        redirect_url = enroll_common(training, current_user)
        if redirect_url:
            return safe_redirect(url)
        
    training.fill_numbers(current_user)
    
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


