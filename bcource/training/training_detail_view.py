from bcource.training.training_views import training_bp, request, redirect, url_for, abort, flash
from bcource.helpers import get_url
from flask import render_template
from flask_babel import _
from flask_babel import lazy_gettext as _l
from bcource.models import Training, TrainingType, TrainingEvent, TrainingEnroll, Student
from datetime import datetime
from bcource.training.training_forms import TrainingDerollForm
from bcource.filters import Filters
from bcource import db
import bcource.messages as system_msg


def make_filters():


    filters = Filters("Training Filters")
    past_training_filter = filters.new_filter("waitlist", _("Wait List"))
    past_training_filter.add_filter_item( 1, _("Wait List"))

    return (filters)

def enrollement_query(training, filters):

    
    if filters.get_item_is_checked("waitlist","1"):
        return TrainingEnroll().query.join(Training).filter(TrainingEnroll.status.ilike("%waitlist%") ,
                                                         TrainingEnroll.training_id==training.id).order_by(
                                                             TrainingEnroll.enrole_date).order_by(TrainingEnroll.enrole_date).all()
    else:
        return training.trainingenrollments_sorted


@training_bp.route('/training-de-infite/<int:training_id>/<int:student_id>',methods=['GET', 'POST'])
def deinvite(training_id,student_id):        
    training=Training().query.get(training_id)
    if not training:
        flash(_('Training id: %s not found' % training_id), "error")
        abort(404)
        
    student=Student().query.get(student_id)
    if not training:
        flash(_('Training id: %s not found' % training_id), "error")
        abort(404)
    
    url = get_url()
        
    enrollment = TrainingEnroll().query.filter(TrainingEnroll.student == student, TrainingEnroll.training == training).first()
    if enrollment: 
        enrollment.status="waitlist"
        db.session.commit()
        
        flash(_('Student %(fullname)s is de-invited for %(trainingname)s.', 
                fullname=student.fullname, 
                trainingname=training.name))
    else:
        flash(_('Cannot find invite for %(fullname)s for training %(trainingname)s.', 
                fullname=student.fullname, 
                trainingname=training.name), 'error')
    
    return redirect(url)

@training_bp.route('/training-invite/<int:training_id>/<int:student_id>',methods=['GET', 'POST'])
def invite(training_id,student_id):        
    training=Training().query.get(training_id)
    if not training:
        flash(_('Training id: %s not found' % training_id), "error")
        abort(404)
        
    student=Student().query.get(student_id)
    if not training:
        flash(_('Training id: %s not found' % training_id), "error")
        abort(404)
    
    url = get_url()
    
    if not training.wait_list_spot_availabled(student):
        flash(_('Student %(fullname)s cannot be invited for %(trainingname)s.', 
                fullname=student.fullname, 
                trainingname=training.name), "error")
        
        return redirect(url)
    
    enrollment = TrainingEnroll().query.filter(TrainingEnroll.student == student, TrainingEnroll.training == training).first()
    enrollment.status="waitlist-invited"
    
    system_msg.EmailStudentEnrolledInTrainingInvited(envelop_to=enrollment.student.user, 
                                                  enrollment=enrollment).send()

    db.session.rollback()
    
    flash(_('Student %(fullname)s is invited for %(trainingname)s.', 
            fullname=student.fullname, 
            trainingname=training.name))
    
    return redirect(url)
    
    
@training_bp.route('/training-detail/<int:id>',methods=['GET', 'POST'])
def training_detail(id):
    clear = request.args.getlist('submit_id')
    
    if clear and clear[0]=='back':
        return redirect(get_url())


    if clear and clear[0]=='clear':
        return redirect(url_for('training_bp.training_detail', id=id, show=request.args.getlist('show'), url=get_url()))


    
    deroll_form = TrainingDerollForm()
    training = Training().query.get(id)
    filters = make_filters().process_filters()
    
    enrolled = enrollement_query(training, filters)
    url = get_url(deroll_form, default='training_bp.overview_list', back_button=True)
        
    
    return render_template("training/training_detail.html", 
                           return_url=url,
                           page_name=_("Training Overview for %(training_name)s", training_name=training.name),
                           filters=filters, 
                           enrolled=enrolled,
                           training=training)
