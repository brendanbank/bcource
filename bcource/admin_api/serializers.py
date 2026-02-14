from flask_restx import fields
from bcource.admin_api.api import api

# --- Locations ---
location_model = api.model('Location', {
    'id': fields.Integer(readonly=True),
    'name': fields.String(required=True),
    'street': fields.String(),
    'house_number': fields.String(),
    'house_number_extention': fields.String(),
    'postal_code': fields.String(),
    'city': fields.String(),
    'country': fields.String(),
})

# --- Training Types ---
training_type_model = api.model('TrainingType', {
    'id': fields.Integer(readonly=True),
    'name': fields.String(required=True),
    'description': fields.String(),
})

# --- Students ---
student_model = api.model('Student', {
    'id': fields.Integer(readonly=True),
    'fullname': fields.String(attribute=lambda s: s.user.fullname),
    'email': fields.String(attribute=lambda s: s.user.email),
    'phone_number': fields.String(attribute=lambda s: s.user.phone_number),
    'studenttype': fields.String(attribute=lambda s: str(s.studenttype)),
    'studentstatus': fields.String(attribute=lambda s: str(s.studentstatus)),
})

# --- Training Events ---
training_event_model = api.model('TrainingEvent', {
    'id': fields.Integer(readonly=True),
    'start_time': fields.DateTime(required=True),
    'end_time': fields.DateTime(required=True),
    'location_id': fields.Integer(required=True),
    'location_name': fields.String(attribute=lambda e: str(e.location) if e.location else None, readonly=True),
    'training_id': fields.Integer(readonly=True),
})

training_event_input = api.model('TrainingEventInput', {
    'start_time': fields.DateTime(required=True, description='ISO 8601 datetime'),
    'end_time': fields.DateTime(required=True, description='ISO 8601 datetime'),
    'location_id': fields.Integer(required=True),
})

# --- Enrollments ---
enrollment_model = api.model('Enrollment', {
    'student_id': fields.Integer(readonly=True),
    'training_id': fields.Integer(readonly=True),
    'student_name': fields.String(attribute=lambda e: str(e.student)),
    'student_email': fields.String(attribute=lambda e: e.student.user.email),
    'status': fields.String(),
    'enrole_date': fields.DateTime(),
    'invite_date': fields.DateTime(),
    'paid': fields.Boolean(),
})

enrollment_input = api.model('EnrollmentInput', {
    'student_id': fields.Integer(required=True, description='Student ID to enroll. '
                  'Status is determined automatically: enrolled if spots available, waitlist if full.'),
})

enrollment_action_input = api.model('EnrollmentActionInput', {
    'action': fields.String(required=True, description=(
        'invite: waitlist → waitlist-invited (checks spot availability, sends email+SMS). '
        'deinvite: waitlist-invited → waitlist-invite-expired (sends expiry notification). '
        'return-to-waitlist: waitlist-invited → waitlist (no notification, keeps queue position). '
        'force-enroll: waitlist → enrolled (bypasses capacity). '
        'decline: waitlist-invited → waitlist-declined (cascades invitation to next eligible). '
        'toggle-paid: flips the paid flag on the enrollment.'
    )),
})

enrollment_action_result = api.model('EnrollmentActionResult', {
    'student_id': fields.Integer(),
    'training_id': fields.Integer(),
    'status': fields.String(description='New enrollment status after action'),
    'action': fields.String(description='Action that was performed'),
})

bulk_move_input = api.model('BulkMoveInput', {
    'student_ids': fields.List(fields.Integer, required=True),
    'target_training_id': fields.Integer(required=True),
    'operation': fields.String(required=True, description='move or copy'),
    'override_status': fields.String(description='If set, all moved enrollments get this status instead of the source status'),
})

bulk_move_result = api.model('BulkMoveResult', {
    'moved': fields.List(fields.Integer, description='Student IDs successfully processed'),
    'skipped': fields.List(fields.Integer, description='Student IDs skipped (already in target)'),
    'errors': fields.List(fields.String, description='Error messages'),
})

# --- Trainings ---
trainer_model = api.model('Trainer', {
    'id': fields.Integer(readonly=True),
    'name': fields.String(attribute=lambda t: t.user.fullname),
    'email': fields.String(attribute=lambda t: t.user.email),
})

training_summary_model = api.model('TrainingSummary', {
    'id': fields.Integer(readonly=True),
    'name': fields.String(),
    'active': fields.Boolean(),
    'max_participants': fields.Integer(),
    'trainingtype': fields.String(attribute=lambda t: str(t.trainingtype)),
    'trainingtype_id': fields.Integer(),
    'enrollment_count': fields.Integer(
        attribute=lambda t: len([e for e in t.trainingenrollments if e.status in ('enrolled', 'waitlist-invited')])
    ),
    'waitlist_count': fields.Integer(
        attribute=lambda t: len([e for e in t.trainingenrollments if e.status == 'waitlist'])
    ),
    'event_count': fields.Integer(attribute=lambda t: len(t.trainingevents)),
})

def _spots_available(t):
    enrolled = len([e for e in t.trainingenrollments if e.status in ('enrolled', 'waitlist-invited')])
    return max(0, (t.max_participants or 0) - enrolled)

training_detail_model = api.model('TrainingDetail', {
    'id': fields.Integer(readonly=True),
    'name': fields.String(),
    'active': fields.Boolean(),
    'max_participants': fields.Integer(),
    'apply_policies': fields.Boolean(),
    'trainingtype_id': fields.Integer(),
    'trainingtype': fields.String(attribute=lambda t: str(t.trainingtype)),
    'trainers': fields.List(fields.Nested(trainer_model)),
    'events': fields.List(fields.Nested(training_event_model), attribute='trainingevents'),
    'enrollment_count': fields.Integer(
        attribute=lambda t: len([e for e in t.trainingenrollments if e.status in ('enrolled', 'waitlist-invited')]),
        description='Count of enrolled + waitlist-invited (both count against capacity)',
    ),
    'waitlist_count': fields.Integer(
        attribute=lambda t: len([e for e in t.trainingenrollments if e.status == 'waitlist']),
        description='Count of students on waitlist (not yet invited)',
    ),
    'spots_available': fields.Integer(
        attribute=_spots_available,
        description='max_participants minus (enrolled + waitlist-invited)',
    ),
})

training_input = api.model('TrainingInput', {
    'name': fields.String(required=True),
    'trainingtype_id': fields.Integer(required=True),
    'max_participants': fields.Integer(required=True),
    'active': fields.Boolean(default=True),
    'apply_policies': fields.Boolean(default=True),
    'trainer_ids': fields.List(fields.Integer, description='List of trainer IDs to assign'),
    'events': fields.List(fields.Nested(training_event_input), description='Events to create with the training'),
})

training_update_input = api.model('TrainingUpdateInput', {
    'name': fields.String(),
    'trainingtype_id': fields.Integer(),
    'max_participants': fields.Integer(),
    'active': fields.Boolean(),
    'apply_policies': fields.Boolean(),
    'trainer_ids': fields.List(fields.Integer, description='Replace trainer assignments'),
})
