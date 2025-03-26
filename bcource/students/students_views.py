from flask import Blueprint, render_template, abort, redirect, url_for
from flask import current_app as app
from bcource.helpers import has_role
from bcource import menu_structure, db
import bcource.models as models
from bcource.students.student_forms import StudentForm

# Blueprint Configuration
students_bp = Blueprint(
    'students_bp', __name__,
    url_prefix="/students",
    template_folder='templates',
    static_folder='static'
)

def has_trainer_role():
    has_role(["trainer"])

students_bp.before_request(has_trainer_role)

main_menu = menu_structure.add_menu('Training Administration', role='trainer')
main_menu.add_menu('Student Administration', 'students_bp.index', role='trainer')

@students_bp.route('/', methods=['GET'])
def index():
    students = models.Student().query.all()
    print (students)
    return render_template("students/students.html", students=students)

@students_bp.route('/edit/<int:id>',methods=['GET', 'POST'])
def student(id):
    print (id)
    student = models.Student().query.get(id)
    if not student:
        abort(404)
    
    form = StudentForm(obj=student)
    
    form.url.data = url_for('students_bp.index')
    
    if form.validate_on_submit():
        form.populate_obj(student)
        db.session.commit()
        return redirect(url_for('students_bp.index'))
    
    return render_template("students/student.html", form=form)

