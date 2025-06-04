from flask import (Blueprint, render_template, jsonify, abort, send_from_directory, g, 
                   flash, url_for, redirect, render_template_string, request)
from flask_babel import lazy_gettext as _l
from flask_babel import _
from flask_security import current_user
from bcource import menu_structure
from bcource.helpers import admin_has_role
from bcource.models import User, Student, Practice, Training, TrainingType, TrainingEvent
from sqlalchemy import or_, and_

my_training = menu_structure.add_menu(_l('Training Scheduler'))
my_training.add_menu(_l('Schedule Training'), 'scheduler_bp.index')
my_training.add_menu(_l('My schedule'), 'training_bp.index')


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
        flash(_("Student does not have status active!"), 'error')
        abort(403)

scheduler_bp.before_request(has_student_role)


def make_filters():
    filters = []
    filters.append(('trainingtype', 'Training Type', 
                    TrainingType.get_all()))
    
    return(filters)

def process_filters():
    filters_checked = {}
    
    try:
        filters_checked.update( {'trainingtype': [int(i) for i in request.args.getlist('trainingtype')]} )

    except Exception as e:
        print (f'process_filters: url args not integer {request.args}: error {e}')
        
    return(filters_checked)


def training_query():
    selected_filters=process_filters()
    if not selected_filters:
        return Training().query.all()
    
    if not selected_filters.get('trainingtype'):
        
        q = Training().query.join(TrainingEvent).join(Practice).filter(
                        Practice.shortname==Practice.default_row().shortname
                        ).order_by(TrainingEvent.start_time)
        return q.all()
                                   

                        
                        
    q =  Training().query.join(Practice).filter(and_(
                Practice.shortname==Practice.default_row().shortname), or_( 
        Training.traningtype_id.in_(selected_filters.get('trainingtype')), 
        ))
        
    return q.all()


@scheduler_bp.route('/training', methods=['GET'])
def index():

    clear = request.args.getlist('submit')
    if clear and clear[0]=='clear':
        return redirect(url_for('scheduler_bp.index'))

    return render_template("scheduler/scheduler.html", training=training_query(), filters=make_filters(), filters_checked=process_filters())

@scheduler_bp.route('/search',methods=['GET'])
def search():
    results = {}
    results.update({"results": []})

    query_term = request.args.get('q')
    
    r = []
    
    if query_term:
        r = Training().query.join(Practice).filter(and_(
                Practice.shortname==Practice.default_row().shortname, Training.active==True), or_( 
            Training.name.ilike(f'%{query_term}%'))).order_by(Training.name).all()
    else:
    
        r = Training().query.join(Practice).filter(and_(
            Practice.shortname==Practice.default_row().shortname, Training.active==True)).order_by(Training.name).all()
        
    for training in r:
        results["results"].append({"id": training.id,  "text":  training.name})
    return jsonify(results)
