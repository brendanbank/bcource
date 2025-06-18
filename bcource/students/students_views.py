from flask import Blueprint, render_template, abort, redirect, url_for, flash, request, jsonify
from flask_babel import _
from flask_security import current_user
from flask import current_app as app
from bcource.helpers import admin_has_role
from bcource import menu_structure, db
from bcource.models import Student, StudentStatus, StudentType, User, Practice
from bcource.students.student_forms import StudentForm, UserStudentForm
from bcource.helpers import get_url
from sqlalchemy import or_, and_, not_
import bcource.messages as bmsg 
import datetime

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
main_menu.add_menu('Student Administration', 'students_bp.index', role='trainer')

def make_filters():
    filters = []
    filters.append(('studentstatus', 'Student Status', 
                    StudentStatus.get_all()))
    
    filters.append(('studenttype', 'Student Type', 
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

def students_query():
    orphan_users()

    selected_filters=process_filters()
    if not selected_filters:
        return Student().query.order_by(User.email).all()
    
    if not selected_filters.get('studentstatus') and not selected_filters.get('studenttype'):
        
        q = Student().query.join(Practice).join(User).filter(
                        Practice.shortname==Practice.default_row().shortname
                        ).order_by(User.first_name, User.last_name, User.email)
        return q.all()
                                   

                        
                        
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
    clear = request.args.getlist('submit')
    if clear and clear[0]=='clear':
        return redirect(url_for('students_bp.index'))
    
    students = students_query()
    
    return render_template("students/students.html", students=students, filters=make_filters(), filters_checked=process_filters())

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

@students_bp.route('/user-edit/<int:id>',methods=['GET', 'POST'])
def edit_user(id):
    
    user = User().query.get(id)

    
    if not user:
        flash(_('Student not found!'))
        abort(404)
            
    form = UserStudentForm(obj=user)
    
    url = get_url(form, default='students_bp.index')
    
    print (request.form)
        
    if  form.validate_on_submit():
            
        form.populate_obj(user)

        db.session.commit()
        flash(_('User %s has been updated' % user.fullname))
                
        return redirect(url)
    
    return render_template("students/student.html", form=form)


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
    
    return render_template("students/student.html", form=form)