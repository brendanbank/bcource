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


def enroll_from_waitlist(enrollment: TrainingEnroll):
    if not enrollment:
        flash(_("enroll: Cannot find invitation!"), 'error')
        return False
    
    if enrollment.status != "waitlist-invited":
        flash(_("enroll: Cannot find invitation!, status is not waitlist-invited"), 'error')
        return False
    
    enrollment.status = "enrolled"
    
    system_msg.EmailStudentEnrolledInTrainingInviteAccepted(envelop_to=enrollment.student.user, 
                                                  enrollment=enrollment).send()
    db.session.commit()
        
    flash(_("You have successfully enrolled into training %(trainingname)s!", trainingname=enrollment.training.name))


    print (enrollment)

def enroll_common(training, user):
    enrolled_user = training.enrolled(user)
    if enrolled_user:
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

    if waitlist:
        system_msg.EmailStudentEnrolledInTrainingWaitlist(envelop_to=user, enrollment=enroll).send()
        system_msg.EmailStudentEnrolledWaitlist(envelop_to=training.trainer_users, enrollment=enroll).send()

    else:
        system_msg.EmailStudentEnrolledInTraining(envelop_to=user, 
                                                  enrollment=enroll).send()
        system_msg.EmailStudentEnrolled(envelop_to=training.trainer_users, enrollment=enroll).send()

        db.session.commit()

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
    
    system_msg.EmailStudentDerolled(envelop_to=training.trainer_users, enrollment=training_enroll).send()
    system_msg.EmailStudentDerolledInTraining(envelop_to=user, enrollment=training_enroll).send()
    flash(_("%(username)s successfully removed from the training: %(trainingname)s", username=user.fullname, 
        trainingname=training.name))

    db.session.delete(training_enroll)        
    db.session.commit()
    
    
    return True

