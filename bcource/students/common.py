from flask import flash, redirect, abort
from datetime  import datetime
import pytz
from bcource.models import Training, TrainingEnroll, TrainingEvent, Student, Practice
from sqlalchemy import and_
from bcource import db
import bcource.messages as system_msg
from flask_babel import lazy_gettext as _l
from flask_babel import _
from bcource.helpers import add_url_argument


def enroll_common(training, user):
        
    if training.enrolled(user):
        flash(_("%(fullname)s has already enrolled for this training: %(trainingname)s", 
                fullname=user.fullname,trainingname=training.name ),'error')
        return False
    
    waitlist = len(training.trainingenrollments) >= training.max_participants
    enroll = TrainingEnroll()

    student = Student().query.join(Practice).filter(and_(
                    Practice.shortname==Practice.default_row().shortname, Student.user==user)
                    ).first()
    if not student:
        flash(_("enroll: Student Not Found!"), 'error')
        return False

    if not student.studentstatus.name == 'active':
        flash(_("enroll: Student is not active!"), 'error')
        return False

    fullname = user.fullname 
    trainingname= training.name # prevent warnings 

    enroll.student = student          
    enroll.training = training
    
    if waitlist:
        enroll.status = "waitlist"
        flash(_("%(fullname)s has been added to the wait list of training training: %(trainingname)s", 
                fullname=user.fullname, trainingname=training.name ))

    else:
        enroll.status = "enrolled"
        flash(_("%(fullname)s has successfully enrolled into the training: %(trainingname)s", 
                fullname=fullname,trainingname=trainingname ))

    
    db.session.add(enroll)
    db.session.commit()

    if len(training.trainingenrollments) >= training.max_participants:
        system_msg.EmailStudentEnrolledInTrainingWaitlist(envelop_to=user, training=training, user=user).send()
        system_msg.EmailStudentEnrolledWaitlist(envelop_to=training.trainer_users, user=user, training=training).send()

    else:
        system_msg.EmailStudentEnrolledInTraining(envelop_to=user, 
                                                  training=training, 
                                                  user=user, 
                                                  uuid=enroll.uuid).send()
        system_msg.EmailStudentEnrolled(envelop_to=training.trainer_users, user=user, training=training).send()

    return True
    


def deroll_common(training, user):
    training_enroll = training.enrolled(user)
            
    if not training_enroll:
        flash(_("%(fullname)s is not enrolled in training : %(trainingname)s", fullname=user.fullname, 
                trainingname=training.name),'error')
        return False

    time_now = datetime.now(tz=pytz.timezone('UTC'))

    q = Training().query.join(TrainingEnroll).join(TrainingEvent).filter(
        and_(~Training.trainingevents.any(TrainingEvent.start_time < time_now),
             Training.id == training.id)).first()
    if not q:
        flash(_("You cannot deroll %(fullname)s from this training. %(trainingname)s has already started: ", 
                fullname=user.fullname, trainingname=training.name), 'error')
        return False
    
    db.session.delete(training_enroll)        
    db.session.commit()
    
    system_msg.EmailStudentDerolled(envelop_to=training.trainer_users, user=user, training=training).send()
    system_msg.EmailStudentDerolledInTraining(envelop_to=user, training=training, user=user, uuid=training_enroll.uuid).send()
    flash(_("%(username)s successfully removed from the training: %(trainingname)s", username=user.fullname, 
        trainingname=training.name))
    
    return True

