from bcource.training.training_views import training_bp, request, redirect, url_for
from bcource.helpers import get_url
from flask import render_template
from flask_babel import _
from flask_babel import lazy_gettext as _l
from bcource.models import Training, TrainingType, TrainingEvent, TrainingEnroll
from datetime import datetime
from bcource.training.training_forms import TrainingDerollForm

class Filter():
    def __init__(self, id, name):
        self.name = name
        self.id = id
    
    def __str__(self):
        return self.name

training_filter_obj = [Filter(1,"Waitlist")]

def process_filters(my_trainings=None):
    filters_checked = {}
    
    try:
        filters_checked.update( {'training_filter': [int(i) for i in request.args.getlist('training_filter')]} )

    except Exception as e:
        print (f'process_filters: url args not integer {request.args}: error {e}')
                
    return(filters_checked)

def make_filters():

    filters = []
    
    filters.append(('training_filter', 'Training Filter', 
                    training_filter_obj))    

    return(filters)


def enrollement_query(training):

    selected_filters=process_filters()
    
    if selected_filters.get('training_filter'):
        return TrainingEnroll().query.join(Training).filter(TrainingEnroll.status.ilike("%waitlist%") ,
                                                         TrainingEnroll.training_id==training.id).order_by(
                                                             TrainingEnroll.enrole_date).all()
    else:
        return training.trainingenrollments_sorted
    
@training_bp.route('/training-detail/<int:id>',methods=['GET', 'POST'])
def training_detail(id):
    clear = request.args.getlist('submit_id')
    if clear and clear[0]=='back':
        return redirect(get_url())
    
    
    deroll_form = TrainingDerollForm()
    training = Training().query.get(id)
    enrolled = enrollement_query(training)
    url = get_url(deroll_form, default='training_bp.overview_list', back_button=True)      
        
    
    return render_template("training/training_detail.html", 
                           return_url=url,
                           page_name=_("Training Overview for %(training_name)s", training_name=training.name),
                           filters=make_filters(), 
                           filters_checked=process_filters(my_trainings=True),
                           enrolled=enrolled,
                           training=training)
