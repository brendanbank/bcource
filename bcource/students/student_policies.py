from flask_babel import _
from flask_babel import lazy_gettext as _l
from bcource.policy import PolicyBase, HasData, DataIs
from flask_security import current_user
from bcource.models import Student, StudentStatus, StudentType, Practice, Role, User, Training, Student, TrainingEnroll,\
    TrainingEvent, TrainingType
from bcource import db
from os import environ
from bcource.policy import PolicyBase, ValidationRule
from datetime import datetime, timedelta
import bisect

BOOKWINDOW_ONE_WEEK = timedelta(days=7)
BOOKWINDOW_FOUR_WEEKS = timedelta(days=28)
MAX_BOOKINGS = 3 # max + 1!!!

BOOK_WINDOW_VIOLATION_TXT = "You cannot book <strong>%(trainingname)s</strong> as you can only book 2 sessions in a %(time_window_duration)s day period!"

class Bookwindow(ValidationRule):
    def validate(self):
        user = self._validator.kwargs.get('user')
        training = self._validator.kwargs.get('training')
        
        timedelta_before = self._validator.kwargs.get('timedelta_before', BOOKWINDOW_ONE_WEEK)

        time_window_duration = self._validator.kwargs.get('days', BOOKWINDOW_FOUR_WEEKS)
        
        if not user or not training:
            raise(ValueError(f'kwargs "user" or "training" missing in {self._validator.__class__.__name__}'))
        
        student = user.student_from_practice
        if not student:
            self.msg_fail = _("User does not have Student role!")
            self.status = False
            return self.status
        
        if not training.active:
            self.status = True
            return self.status
        
        if training.enrolled(user):
            self.status = True
            return self.status
        

        
        if not check_book_window(training, student, time_window_duration, timedelta_before):
            
            self.msg_fail = _l(BOOK_WINDOW_VIOLATION_TXT, 
                          time_window_duration=round(time_window_duration.total_seconds() / 3600 / 24)    , trainingname=training.name , trainingtype=training.traningtype)
            self.status = False
            return self.status
        else:
            self.status = True
                
        return self.status
        
class TrainingBookingPolicy(PolicyBase):
    book_window = Bookwindow(_l('Check if the student is satisfying all policies to book this training.'))


def check_book_window(training, student, time_window_duration, timedelta_before):
    
    
    q = TrainingEvent().query.join(Training).join(TrainingEnroll).join(TrainingType).filter(
        Training.traningtype_id == training.traningtype_id,
        Training.active == True,
        TrainingEnroll.student_id == student.id,
        TrainingEvent.start_time > (training.trainingevents[0].start_time - time_window_duration),
        TrainingEvent.start_time < (training.trainingevents[0].start_time + time_window_duration),
        
        ).order_by(TrainingEvent.start_time)
        
    events= q.all()
    
    if not events:
        return(True)
        
    existing_bookings_dates = [ d.start_time for d in q.all()]
    
    new_training_date = training.trainingevents[0].start_time
    
    # 5 days before start of the training ignore the rule
    if timedelta_before != None:
        if  (new_training_date - datetime.utcnow()) < timedelta_before:
            return (True)

        
    potential_date_obj = new_training_date
    
    # has already booked!
    if potential_date_obj in existing_bookings_dates:
        return True
        
    # Create a mutable copy of existing bookings for modification
    temp_all_dates = list(existing_bookings_dates)
    
    # Find the correct insertion point for the new date
    insert_idx = bisect.bisect_left(temp_all_dates, potential_date_obj)
    
    # Temporarily add the potential date
    temp_all_dates.insert(insert_idx, potential_date_obj)
    
    # Check only around the newly inserted date's index
    would_not_exceed = _check_violation_around_index(temp_all_dates, insert_idx, MAX_BOOKINGS, time_window_duration)
    
    
    return would_not_exceed

def can_student_book_trainings(student, trainings, training_type, time_window_duration=BOOKWINDOW_FOUR_WEEKS):
    """
    Compares a list of potential new training sessions against a student's
    existing bookings to determine which ones can be booked.

    Args:
        student (Student obj): The student.
        potential_trainings (list of dict/object): A list where each item represents
                                                    a potential training. Each item
                                                    must have a 'date' attribute/key
                                                    (e.g., training_id, date, name).
                                                    The date should be datetime.date object.
                                                    Example: [{'id': 101, 'date': datetime(2025,8,1).date(), 'name': 'Intro SQL'}]

        training_type (TrainingType obj): The TrainingType.
        time_window_duration: time delta 

    Returns:
        dict: A dictionary where keys are potential training IDs/identifiers,
              and values are dictionaries with 'can_book' (bool) and 'message' (str).
    """

    # 1. Get existing bookings once, and sort them
    

    ids = [t.id for t in trainings ]

    existing_bookings_dates = TrainingEvent().query.with_entities(TrainingEvent.start_time).join(Training).join(TrainingEnroll).join(TrainingType).filter(
            Training.traningtype_id == training_type.id,
            Training.id.in_(ids),
            Training.active == True,
            TrainingEnroll.student_id == student.id,
            # TrainingEvent.start_time > datetime.utcnow(), # only future trainings
        ).distinct().order_by(TrainingEvent.start_time).all()

    existing_bookings_dates = [ b.start_time for b in existing_bookings_dates ]  
    
      
    potential_trainings = Training().query.with_entities(Training.id, Training.name, TrainingEvent.start_time).join(TrainingEvent).join(TrainingType).filter(
        Training.traningtype_id == training_type.id,
            Training.id.in_(ids),
        # TrainingEvent.start_time > datetime.utcnow(), # only future trainings
        ).all()

    potential_trainings = Training().query.with_entities(Training.id, Training.name, TrainingEvent.start_time).join(TrainingEvent).join(TrainingType).filter(
        Training.traningtype_id == training_type.id,
            Training.id.in_(ids),
        # TrainingEvent.start_time > datetime.utcnow(), # only future trainings
        ).all()

    
    results = {}

    for training in potential_trainings:
    #     # Assuming training object has a 'date' attribute or 'date' key
        
        policy_obj = TrainingBookingPolicy(student.user, training)
        
        
        potential_date_obj = training.start_time

        # no bookings yet this training is already booked.
        if not existing_bookings_dates or potential_date_obj in existing_bookings_dates:
            policy_obj.book_window.status = policy_obj.status = True
            policy_obj.book_window.msg_fail = ''
            results[training.id] = policy_obj
            continue
                    
        # Create a mutable copy of existing bookings for modification
        temp_all_dates = list(existing_bookings_dates)
        
        # Find the correct insertion point for the new date
        insert_idx = bisect.bisect_left(temp_all_dates, potential_date_obj)
        
        # Temporarily add the potential date
        temp_all_dates.insert(insert_idx, potential_date_obj)
        
        
        # Check only around the newly inserted date's index
        would_not_exceed = _check_violation_around_index(temp_all_dates, insert_idx, MAX_BOOKINGS, time_window_duration)
        #
        # Store the result
        if not would_not_exceed:
            policy_obj.book_window.status = policy_obj.status = False
            policy_obj.book_window.msg_fail = _l(BOOK_WINDOW_VIOLATION_TXT, 
                          time_window_duration=round(time_window_duration.total_seconds() / 3600 / 24),
                          trainingname=training.name ,
                          trainingtype=training_type.name)
            
            results[training.id] = policy_obj

        else:
            policy_obj.book_window.status = policy_obj.status = True
            policy_obj.book_window.msg_fail = ''
            results[training.id] = policy_obj

        
        # IMPORTANT: Remove the temporarily added date before the next iteration
        # This restores existing_bookings_dates for the next check without re-fetching
        temp_all_dates.pop(insert_idx)
        
    return (results)


def _check_violation_around_index(sorted_dates, check_idx, max_bookings, time_window_days):
    """
    Checks if a violation occurs in any window of 'max_bookings' around a specific index.
    This is an internal helper for the optimized function.

    Args:
        sorted_dates (list of datetime.date): A sorted list of dates.
        check_idx (int): The index of the date around which to check windows.
        max_bookings (int): The maximum number of bookings allowed within the window.
                            A violation occurs if max_bookings are found within the window.
        time_window_days (int): The size of the time window in days.

    Returns:
        bool: False if a violation is found (i.e., 'max_bookings' are found within
              'time_window_days' for any window involving check_idx), True otherwise.
    """
    n = len(sorted_dates)
    if n < max_bookings:
        return True # Not enough bookings to even form a violating window

    # The 'check_idx' (the new booking) could be any position within a 'max_bookings' size window.
    # We need to iterate through all possible start indices 'j' for a window of 'max_bookings'
    # such that 'check_idx' falls within [j, j + max_bookings - 1].

    # The earliest possible start of a window that includes check_idx: check_idx - (max_bookings - 1)
    # The latest possible start of a window that includes check_idx: check_idx
    
    start_search_idx = max(0, check_idx - (max_bookings - 1))
    end_search_idx = min(n - max_bookings, check_idx) # Ensure window doesn't go out of bounds

    for j in range(start_search_idx, end_search_idx + 1):
        # Current window starts at sorted_dates[j] and ends at sorted_dates[j + max_bookings - 1]
        start_date_in_window = sorted_dates[j]
        end_date_in_window = sorted_dates[j + max_bookings - 1]

        if (end_date_in_window - start_date_in_window) < time_window_days:
            return False # Violation found

    return True

