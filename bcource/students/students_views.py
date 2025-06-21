from flask import Blueprint, render_template, abort, redirect, url_for, flash, request, jsonify
from flask_babel import _
from flask_security import current_user, naive_utcnow
from flask import current_app as app
from bcource.helpers import admin_has_role
from bcource import menu_structure, db
from bcource.models import (Student, StudentStatus, StudentType, User, Practice, 
                            Role, Trainer, UserMessageAssociation, UserSettings, TrainingType, Training, TrainingEnroll, TrainingEvent)
from bcource.students.student_forms import StudentForm, UserStudentForm, UserDeleteForm, UserDerollForm, UserBackForm
from bcource.helpers import get_url
from sqlalchemy import or_, and_, not_
import bcource.messages as bmsg 
from datetime import datetime 
import uuid, pytz
from flask_babel import lazy_gettext as _l
from sqlalchemy.orm import joinedload
from bcource.students.common import deroll_common, enroll_common
from bcource.training.training_forms import TrainingDerollForm, TrainingEnrollForm

# Blueprint Configuration
students_bp = Blueprint(
    'students_bp', __name__,
    url_prefix="/students",
    template_folder='templates',
    static_folder='static'
)

def has_trainer_role():
    admin_has_role(["trainer"])

students_bp.before_request(has_trainer_role)

main_menu = menu_structure.add_menu('Training Administration', role='trainer')
main_menu.add_menu('User Administration', 'students_bp.index', role='trainer')


def make_filters():
    filters = []
    filters.append(('studentstatus', 'User Status', 
                    StudentStatus.get_all()))
    
    filters.append(('studenttype', 'User Type', 
                    StudentType.get_all()))
    return(filters)

def process_filters():
    filters_checked = {}
    
    try:
        filters_checked.update( {'studentstatus': [int(i) for i in request.args.getlist('studentstatus')]} )
        filters_checked.update( {'studenttype': [int(i) for i in request.args.getlist('studenttype')]} )

    except Exception as e:
        print (f'process_filters: url args not integer {request.args}: error {e}')
        
    return(filters_checked)

def students_query(search_on_id=None):
    orphan_users()

    print (search_on_id)
    selected_filters=process_filters()


    if search_on_id:
        q = Student().query.join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname,Student.id==search_on_id))
        
    elif not selected_filters:
        q = Student().query.join(User).order_by(User.email)
    
    elif not selected_filters.get('studentstatus') and not selected_filters.get('studenttype'):
        
        q = Student().query.join(Practice).join(User).filter(
                        Practice.shortname==Practice.default_row().shortname
                        ).order_by(User.email)
                                   
    else:
        q =  Student().query.join(User).join(Practice).filter(and_(
                    Practice.shortname==Practice.default_row().shortname), or_( 
            Student.studentstatus_id.in_(selected_filters.get('studentstatus')), 
            Student.studenttype_id.in_(selected_filters.get('studenttype')))).order_by(User.email)
        
    return q.all()

# if there are any users that do not have a student record add them.
def orphan_users():
    orphan_user_list = db.session.query(User).filter(~User.students.any()).all() #@UndefinedVariable
    print (orphan_user_list)
    
    studenttype = StudentType.default_row() #@UndefinedVariable
    studentstatus = StudentStatus.default_row() #@UndefinedVariable
    practice = Practice.default_row() #@UndefinedVariable
    
    for user in orphan_user_list:
        if user.email == "do-not-reply@bgwlan.nl":
            continue    
            
        student=Student(user=user, 
                        studentstatus=studentstatus,
                        studenttype=studenttype,
                        practice=practice)
        
        db.session.add(student)
        
    db.session.commit()



@students_bp.route('/', methods=['GET'])
def index():
    clear = request.args.getlist('submit_id')
    if clear and clear[0]=='clear':
        return redirect(url_for('students_bp.index'))
    
    delete_form = UserDeleteForm()
    search_on_id = request.args.get('id')

    students = students_query(search_on_id)
    
    return render_template("students/students.html", 
                           students=students, 
                           filters=make_filters(), 
                           filters_checked=process_filters(),
                           page_name=_("User Overview"),
                           delete_form=delete_form)


@students_bp.route('/search',methods=['GET'])
def search():
    results = {}
    results.update({"results": []})

    query_term = request.args.get('q')
    r = []
    
    if query_term:
        r = Student().query.join(Student.user).join(Practice).filter(and_(
                Practice.shortname==Practice.default_row().shortname), or_( 
            User.first_name.ilike(f'%{query_term}%'), 
            User.last_name.ilike(f'%{query_term}%'),
            User.email.ilike(f'%{query_term}%'))).order_by(User.first_name, User.last_name).all()
    else:
        r = Student().query.join(Student.user).join(Practice).filter(
            Practice.shortname==Practice.default_row().shortname).order_by(User.first_name, User.last_name).all()
        
    for student in r:
        results["results"].append({"id": student.id,  "text":  student.fullname})
    return jsonify(results)

@students_bp.route('/delete-user/<int:id>',methods=['GET', 'POST'])
def delete(id):
    user=User().query.filter(User.id==id).first()
    if not user:
        abort(404)
    
    url = get_url()
    if user.id == current_user.id:
        flash(_('You cannot delete yourself!'), "error")
        return redirect(url)
    
    if user.trainers:
        flash(_('You cannot delete user <span class="fw-bold" style="white-space:nowrap;">%s</span>. First delete the trainer record.<br>' % user.email), "error")
        return redirect(url)
    
    for student in user.students:
        db.session.delete(student)

    UserMessageAssociation().query.filter(UserMessageAssociation.user_id == user.id).delete()
    UserSettings().query.filter(UserSettings.user_id == user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    flash(_('Successfully deleted training: %s' % user))
    
    return redirect(url)


@students_bp.route('/user-edit/<int:id>',methods=['GET', 'POST'])
@students_bp.route('/user-edit/',methods=['GET', 'POST'])
def edit_user(id=None):
    
    if id:
        user = User().query.get(id)
        if not user:
            flash(_('Student not found!'))
            abort(404)
    else:
        user = User()
        
            
    form = UserStudentForm(obj=user)
    if id == None:
        form.form_description = _("Create User")
    else:
        form.form_description = _("Edit User")

    
    url = get_url(form, default='students_bp.index')
    if user.id == current_user.id:
        flash(_('You cannot edit yourself here! Go to the Account Details menu to edit your own details.'), "error")
        return redirect (url)


    if admin_has_role('db-admin'):
        form.roles.query=Role().query.all()
    else:
        form.roles.query=Role().query.filter(Role.name != "db-admin").all()
    
    if  form.validate_on_submit():
            
        form.populate_obj(user)
        if not id:
            user.fs_uniquifier = uuid.uuid4().hex
            user.confirmed_at = naive_utcnow()

            db.session.add(user)

        is_trainer = Trainer().query.filter(Trainer.user_id == user.id).first()

        if user.has_role('trainer') and not is_trainer:
            trainer = Trainer()
            trainer.user_id = user.id
            trainer.practice = Practice.default_row()
            db.session.add(trainer)
        elif not user.has_role('trainer') and is_trainer and is_trainer.trainings:
            flash(_('User %s has the role trainer removed but still has trainings assigned.' % user.fullname), 'error')
            return render_template("students/student.html",  form=form)

        elif not user.has_role('trainer') and is_trainer:
            db.session.delete(is_trainer)
        
            
        db.session.commit()
        flash(_('User %s has been updated' % user.fullname))
                
        return redirect(url)
    
    return render_template("students/student.html", form=form)

def scheduler_process_filters(my_trainings=None):
    filters_checked = {}
    
    try:
        filters_checked.update( {'trainingtype': [int(i) for i in request.args.getlist('trainingtype')]} )
        filters_checked.update( {'training_filter': [int(i) for i in request.args.getlist('training_filter')]} )

    except Exception as e:
        print (f'process_filters: url args not integer {request.args}: error {e}')
                
    return(filters_checked)

class Filter():
    def __init__(self, id, name):
        self.name = name
        self.id = id
    
    def __str__(self):
        return self.name

training_filter_obj = [Filter(1,"Past Trainings")]

def scheduler_make_filters():

    filters = []
    
    time_now = datetime.now(tz=pytz.timezone('UTC'))
    traingingtypes = TrainingType().query.join(Training).join(TrainingEvent).join(Practice, Practice.id==Training.practice_id).filter(and_(
                    Practice.shortname==Practice.default_row().shortname,
                    )).all()
    filters.append(('training_filter', 'Training Filter', 
                    training_filter_obj))

    filters.append(('trainingtype', 'Training Type', 
                    traingingtypes))
    

    return(filters)

def user_training_query(user,search_on_id=None):
    selected_filters=scheduler_process_filters()
    
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
                        Practice.shortname==Practice.default_row().shortname,
                        Training.id==search_on_id,
                        Student.user_id == user.id))
    
        
    elif not selected_filters.get('trainingtype'):
        q = Training().query.join(future).join(TrainingEnroll).join(TrainingEvent).options(joinedload(Training.trainingevents)).join(Student).join(Practice, Practice.id==Training.practice_id).filter(
            and_(Student.user_id == user.id)).order_by(TrainingEvent.start_time)
        print ("here 3")
    elif selected_filters.get('trainingtype'):
        q = Training().query.join(future).join(TrainingEnroll).join(TrainingEvent).options(joinedload(Training.trainingevents)).join(Student).join(Practice, Practice.id==Training.practice_id).filter(
            and_(Student.user_id == user.id,
                 Training.traningtype_id.in_(selected_filters.get('trainingtype')), 
        )).order_by(TrainingEvent.start_time)
        print ("here 2")
    else:
        q =  Training().query.join(future).join(TrainingEvent).options(joinedload(Training.trainingevents)).join(Practice).filter(and_(
                    Practice.shortname==Practice.default_row().shortname,
                    ~Training.trainingevents.any(TrainingEvent.start_time < time_now),
                    Training.active==True), or_( 
            Training.traningtype_id.in_(selected_filters.get('trainingtype')), 
            )).order_by(TrainingEvent.start_time)
        print ("here 1")
    
    
    trainings = q.all()
    for t in trainings:
        t.fill_numbers(user)
        
    return trainings

@students_bp.route('/student-trainings/deroll/<int:user_id>/<int:training_id>',methods=['GET', 'POST'])
def deroll(user_id,training_id):
    
    training = Training().query.get(training_id)
    user = User().query.get(user_id)
    url = get_url()
    print (url)
    deroll_common(training, user)
    return redirect(url)

    
@students_bp.route('/student-trainings/enroll/<int:training_id>',methods=['GET', 'POST'])
def enroll(training_id):
    
    student_id = request.args.get('student_id')
    if not student_id:
        flash(_('Could get student from query!'), 'error')
        return redirect(get_url())
    
    training = Training().query.get(training_id)
    user = User().query.join(Student).filter(Student.id==student_id).first()
    if not user:
        flash(_('Could get user from query!'), 'error')
        return redirect(get_url())
    
    url = get_url()
    
    return_acton =  enroll_common(training, user)
    
    return redirect(url)


@students_bp.route('/student-trainings/<int:id>', methods=['GET', 'POST'])
def student_training(id):

    clear = request.args.getlist('submit_id')
    if clear and clear[0]=='clear':
        return redirect(url_for('students_bp.student_training', id=id))

    if clear and clear[0]=='back':
        return redirect(get_url())

    user = User().query.get(id)
    
    
    deroll_form = TrainingDerollForm()
    url = get_url(deroll_form, default='training_bp.overview_list', back_button=True)
    if not deroll_form.first_url.data:
        deroll_form.first_url.data = url
    
    traingingtypes = TrainingType().query.join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname)
                        ).all()
                        
    return render_template("students/student-training.html", training=user_training_query(user), 
                           trainingtypes=traingingtypes, 
                           filters=scheduler_make_filters(), 
                           filters_checked=scheduler_process_filters(my_trainings=True),
                           page_name=_l('Training Schedule'),
                           user=user,
                           deroll_form=deroll_form,
                           return_url=url
                           )


@students_bp.route('/student-edit/<int:id>',methods=['GET', 'POST'])
def student(id):
    student = Student().query.get(id)
    
    if not student:
        flash(_('Student not found!'))
        abort(404)
            
    form = StudentForm(obj=student)
    
    
    url = get_url(form, default='students_bp.index')
    
    if request.form.get("submit") == 'close':
        return redirect(url)
    
    
    if  form.validate_on_submit():
        form.populate_obj(student)
        print (db.session.is_modified(student))

        db.session.commit()
        flash(_('Student %s has been updated' % student.fullname))
        
        if student.studentstatus.name == "active":
            bmsg.EmailStudentStatusActive(envelop_to=student.user,
                    user=student.user, status=student.studentstatus).send()
        
        return redirect(url)
    
    return render_template("students/student.html",  form=form)