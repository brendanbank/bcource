from flask import Blueprint, render_template, abort, redirect, url_for, flash, request, jsonify
from flask_security import current_user, naive_utcnow
from flask import current_app as app
from bcource.helpers import admin_has_role, has_trainer_role, get_url, add_url_argument

from bcource import menu_structure, db
from bcource.models import (Student, StudentStatus, StudentType, User, Practice, 
                            Role, Trainer, UserMessageAssociation, UserSettings, TrainingType, Training, TrainingEnroll, TrainingEvent)
from bcource.students.student_forms import StudentForm, UserStudentForm, UserDeleteForm, UserDerollForm, UserBackForm
from sqlalchemy import or_, and_, not_
import bcource.messages as bmsg 
from datetime import datetime 
import uuid, pytz

from sqlalchemy.orm import joinedload
from bcource.students.common import deroll_common, enroll_common
from bcource.training.training_forms import TrainingDerollForm, TrainingEnrollForm
from bcource.filters import Filters
from flask_babel import lazy_gettext as _l
from flask_babel import _
from bcource.helper_app_context import b_pagination

# Blueprint Configuration
students_bp = Blueprint(
    'students_bp', __name__,
    url_prefix="/students",
    template_folder='templates',
    static_folder='static'
)

students_bp.before_request(has_trainer_role)

main_menu = menu_structure.add_menu('Training Administration', role='trainer')
main_menu.add_menu('User Administration', 'students_bp.index', role='trainer')


def make_filters():
    
    
    filters = Filters("Student Filters")

    
    studentstatus_filter = filters.new_filter("studentstatus", _("Status"))
    for status_type in StudentStatus.get_all():
        studentstatus_filter.add_filter_item( status_type.id, status_type.name)

    studenttype_filter = filters.new_filter("studenttype", _("Type"))
    for student_type in StudentType.get_all():
        studenttype_filter.add_filter_item( student_type.id, student_type.name)

    return(filters)


def students_query(filters, search_on_id=None):
    
    orphan_users()


    if search_on_id:
        q = Student().query.filter(Student.id == search_on_id)
        
        t = q.first()
        
        student_filter = filters.new_filter("id", _("Student"))
        student_filter.add_filter_item( search_on_id, t.fullname)
        filters.filers_checked = True
        filters.show = True
        filters.get_filter("id").get_item(search_on_id).checked = True
        

    else:
        q = Student().query
    
    if filters.get_items_checked('studenttype'):
        studenttype = StudentType().query.join(Practice, Practice.id==StudentType.practice_id).filter(
                                    StudentType.id.in_(filters.get_items_checked('studenttype')
                               )).subquery()
        
        q = q.join(studenttype)
        
    if filters.get_items_checked('studentstatus'):
        studentstatus = StudentStatus().query.join(Practice, Practice.id==StudentStatus.practice_id).filter(
                                    StudentStatus.id.in_(filters.get_items_checked('studentstatus')
                               )).subquery()
        
        q = q.join(studentstatus)

    q = q.join(User).join(Practice, Practice.id==Student.practice_id).filter(and_(
                        Practice.shortname==Practice.default_row().shortname)).order_by(User.first_name, User.last_name, User.email)
    return q

# if there are any users that do not have a student record add them.
def orphan_users():
    orphan_user_list = db.session.query(User).filter(~User.students.any()).all() #@UndefinedVariable
    
    studenttype = StudentType.default_row() #@UndefinedVariable
    studentstatus = StudentStatus.default_row() #@UndefinedVariable
    practice = Practice.default_row() #@UndefinedVariable
    
    for user in orphan_user_list:
        if user.email == "do-not-reply@bgwlan.nl" or user.email == "not-reply@bcourse.nl":
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
        return redirect(url_for('students_bp.index', show=request.args.getlist('show')))

    delete_form = UserDeleteForm()
    search_on_id = request.args.get('id')

    filters = make_filters().process_filters()
    students_select = students_query(filters, search_on_id)

    url = get_url(default='students_bp.index')
    
    
    students_pagination = b_pagination(students_select)

        
    return render_template("students/students.html", 
                           students=students_pagination.items, 
                           filters=filters, 
                           page_name=_("User Overview"),
                           pagination=students_pagination,
                           delete_form=delete_form,
                           )


@students_bp.route('/email-selection', methods=['GET'])
def email_selection():
    filters = make_filters().process_filters()
    students_select = students_query(filters)
    user_ids = [str(s.user_id) for s in students_select.all()
                 if not s.user.email.startswith('do-not-reply')]

    if not user_ids:
        flash(_('No students match the current filters.'), 'error')
        return redirect(url_for('students_bp.index'))

    return redirect(url_for('user_bp.message',
                            user_ids=','.join(user_ids),
                            first_url=request.url))


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

    if user.student_from_practice.studentenrollments:
        flash(_('You cannot delete user <span class="fw-bold" style="white-space:nowrap;">%s</span>. The user is still enrolled in one or more trainings.<br>' % user.email), "error")
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


@students_bp.route('/student-trainings/deroll/<int:user_id>/<int:training_id>',methods=['GET', 'POST'])
def deroll(user_id,training_id):
    
    training = Training().query.get(training_id)
    user = User().query.get(user_id)
    url = get_url()
    deroll_common(training, user, admin=True)
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

        db.session.commit()
        flash(_('Student %s has been updated' % student.fullname))
        
        if student.studentstatus.name == "active":
            bmsg.EmailStudentStatusActive(envelop_to=student.user,
                    user=student.user, status=student.studentstatus).send()
        
        return redirect(url)
    
    return render_template("students/student.html",  form=form)