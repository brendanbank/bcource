from bcource.students.students_views import students_bp
from flask import redirect, request, url_for, render_template
from datetime import datetime
import pytz
from bcource.models import Training, Practice, TrainingType, TrainingEnroll, TrainingEvent, Student, User
from sqlalchemy import not_, and_, or_
from flask_babel import lazy_gettext as _l
from flask_babel import _
from bcource.helpers import get_url
from bcource.training.training_forms import TrainingDerollForm, TrainingEnrollForm
from sqlalchemy.orm import joinedload
from bcource.filters import Filters


def scheduler_process_filters(my_trainings=None):
    filters_checked = {}
    
    try:
        filters_checked.update( {'trainingtype': [int(i) for i in request.args.getlist('trainingtype')]} )
        filters_checked.update( {'training_filter': [int(i) for i in request.args.getlist('training_filter')]} )

    except Exception as e:
        print (f'process_filters: url args not integer {request.args}: error {e}')
                
    return(filters_checked)


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


    return(filters)

def training_query(filters, user,search_on_id=None):
    
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

    if user:
        users = TrainingEnroll().query.join(Student).filter(TrainingEnroll.student_id == Student.id, Student.user_id == user.id).subquery()
        q = q.join(users)
        
    if filters.get_item_is_checked("period","1"):
        future = TrainingEvent().query.filter(TrainingEvent.start_time < time_now
                        ).order_by(TrainingEvent.start_time).subquery()
    else:
        future = TrainingEvent().query.filter(TrainingEvent.start_time > time_now
                        ).order_by(TrainingEvent.start_time).subquery()

    if  filters.get_items_checked('training_type'):

        items_checked = filters.get_items_checked('training_type')
        trainingtypes = TrainingType().query.join(Practice, Practice.id==TrainingType.practice_id).filter(Practice.shortname==Practice.default_row().shortname, 
                                                                   TrainingType.id.in_(items_checked)).subquery()
        q = q.join(trainingtypes)    


    q = q.join(future)
    
    q = q.join(TrainingEvent).order_by(TrainingEvent.start_time)
    trainings = q.all()
    for t in trainings:
        t.fill_numbers(user)
        
    return trainings


@students_bp.route('/student-trainings/<int:id>', methods=['GET', 'POST'])
def student_training(id):

    clear = request.args.getlist('submit_id')

    if clear and clear[0]=='clear':
        return redirect(url_for('students_bp.student_training', id=id, show=request.args.getlist('show'), url=get_url()))

    if clear and clear[0]=='back':
        return redirect(get_url())

    user = User().query.get(id)
    
    
    deroll_form = TrainingDerollForm()
    url = get_url(deroll_form, default='training_bp.overview_list', back_button=True)
    
    if not deroll_form.first_url.data:
        deroll_form.first_url.data = url
        
    filters = make_filters().process_filters()
    
    search_on_id = request.args.get('id')

    
    traingingtypes = TrainingType().query.join(Practice).filter(and_(
                        Practice.shortname==Practice.default_row().shortname)
                        ).all()
                        
    return render_template("students/student-training.html", training=training_query(filters,user,search_on_id), 
                           trainingtypes=traingingtypes, 
                           filters=filters, 
                           page_name=_l('Training Schedule'),
                           user=user,
                           deroll_form=deroll_form,
                           return_url=url
                           )

