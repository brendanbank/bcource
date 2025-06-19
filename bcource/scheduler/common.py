from flask import flash, redirect
from datetime  import datetime
import pytz
from bcource.models import Training, TrainingEnroll, TrainingEvent
from sqlalchemy import and_
from bcource import db
import bcource.messages as system_msg
from flask_babel import lazy_gettext as _l
from flask_babel import _


def derole_common(redirect_url, form, training, user):
    training_enroll = training.enrolled(user)
    
    if not training_enroll:
        flash(_("You are not enrolled for this training: ") + training.name + ".",'error')
        return redirect(redirect_url)

    time_now = datetime.now(tz=pytz.timezone('UTC'))

    q = Training().query.join(TrainingEnroll).join(TrainingEvent).filter(
        and_(~Training.trainingevents.any(TrainingEvent.start_time < time_now),
             Training.id == training.id)).first()
    if not q:
        flash(_("You cannot deroll %(fullname)s from this training. %(trainingname)s has already started: ", 
                fullname=user.fullname, trainingname=training.name), 'error')
        return redirect(redirect_url)

    a = form.is_submitted()
    
    print (a)
    
    if form.validate_on_submit():
        db.session.delete(training_enroll)        
        db.session.commit()
        
        system_msg.EmailStudentDerolled(envelop_to=training.trainer_users, user=user, training=training).send()
        system_msg.EmailStudentDerolledInTraining(envelop_to=user, training=training, user=user, uuid=training_enroll.uuid).send()
        flash(_("%(username)s successfully removed from the training: ", username=user.fullname) + training.name + ".")
        return redirect(redirect_url)
    
    flash(_("%(username)s failed removed from the training: ", username=user.fullname) + training.name + ".", 'error')
    
    return redirect(redirect_url)


