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
import logging
logger = logging.getLogger(__name__)


def deinvite_from_waitlist(enrollment: TrainingEnroll):
    
    enrollment.status="waitlist-invite-expired"
    enrollment.invite_date = datetime.utcnow()
    
    system_msg.EmailStudentEnrolledInTrainingDeInvited(envelop_to=enrollment.student.user, 
                                                  enrollment=enrollment).send()
    
    # Notify trainers that the user's invitation has expired
    system_msg.SystemMessage(
        envelop_to=enrollment.training.trainer_users,
        body=f"<p>The waitlist invitation for {enrollment.student.user.fullname} has expired for training: {enrollment.training.name}</p>",
        subject=f"Waitlist Invitation Expired - {enrollment.training.name}",
        taglist=['waitlist', 'expired']
    ).send()

    db.session.commit()
    
    logger.info(f'deinvited user: {enrollment.student.user} from training: {enrollment.training}')
    return (True)


def invite_from_waitlist(enrollment: TrainingEnroll):
    
    enrollment.status="waitlist-invited"
    enrollment.invite_date = datetime.utcnow()
    
    system_msg.EmailStudentEnrolledInTrainingInvited(envelop_to=enrollment.student.user, 
                                                  enrollment=enrollment).send()
    
    # Notify trainers that a user has been invited from the waitlist
    system_msg.SystemMessage(
        envelop_to=enrollment.training.trainer_users,
        body=f"<p>{enrollment.student.user.fullname} has been invited from the waitlist for training: {enrollment.training.name}</p>",
        subject=f"Waitlist Invitation Sent - {enrollment.training.name}",
        taglist=['waitlist', 'invited']
    ).send()

    db.session.commit()
    logger.info(f'invited user: {enrollment.student.user} from training: {enrollment.training}')

    return (True)


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
    
    # Notify trainers that the student has accepted the waitlist invitation
    system_msg.SystemMessage(
        envelop_to=enrollment.training.trainer_users,
        body=f"<p>{enrollment.student.user.fullname} has accepted the waitlist invitation and is now enrolled in training: {enrollment.training.name}</p>",
        subject=f"Waitlist Invitation Accepted - {enrollment.training.name}",
        taglist=['waitlist', 'enrolled', 'accepted']
    ).send()
    
    db.session.commit()
        
    flash(_("You have successfully enrolled into training %(trainingname)s!", trainingname=enrollment.training.name))

def enroll_common(training, user):
    enrolled_user = training.enrolled(user)
    
    if enrolled_user \
        and enrolled_user.status != "waitlist-invite-expired" \
            and enrolled_user.status != "waitlist-declined" \
                and enrolled_user.status != 'force-off-waitlist':
        
        flash(_("%(fullname)s has already enrolled for this training: %(trainingname)s", 
                fullname=user.fullname,trainingname=training.name ),'error')
        return False
    
    # Check if training has already started
    time_now = datetime.now(tz=pytz.timezone('UTC'))
    q = Training().query.join(TrainingEnroll).join(TrainingEvent).filter(
        and_(~Training.trainingevents.any(TrainingEvent.start_time < time_now),
             Training.id == training.id)).first()
    if not q:
        flash(_("You cannot enroll %(fullname)s in this training. %(trainingname)s has already started.", 
                fullname=user.fullname, trainingname=training.name), 'error')
        return False
    
    training.fill_numbers(user)
    
    waitlist = training._spots_enrolled >= training.max_participants
    
    if enrolled_user:
        enroll = enrolled_user
    else:
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
    
    if waitlist and enroll.status != 'force-off-waitlist':
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
        a = system_msg.EmailStudentEnrolledInTraining(envelop_to=user, 
                                                  enrollment=enroll)
        a.send()
                                                  
        system_msg.EmailStudentEnrolled(envelop_to=training.trainer_users, enrollment=enroll).send()

        db.session.commit()

    return True
    


def deroll_common(training, user, admin=False):
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
    
    if admin==False: # only run if the a student is derolling (not via the admin screen)
        waitlist_enrollments_eligeble = training.waitlist_enrollments_eligeble()
        for enrollment in waitlist_enrollments_eligeble:
            invite_from_waitlist(enrollment)
    
    
    return True

