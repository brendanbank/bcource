from flask_restx import Resource, abort
from bcource.admin_api.auth import admin_required
from bcource.admin_api.serializers import (
    enrollment_model, enrollment_input, bulk_move_input, bulk_move_result,
    enrollment_action_input, enrollment_action_result,
)
from bcource.admin_api.api import api
from bcource.admin_api.trainings import ns
from bcource.models import Training, TrainingEnroll, Student, User, Practice
from bcource.students.common import (
    invite_from_waitlist, deinvite_from_waitlist,
    enroll_from_waitlist, enroll_common, deroll_common,
)
from bcource import db

enroll_parser = ns.parser()
enroll_parser.add_argument('status', type=str, help='Filter by enrollment status '
                           '(enrolled, waitlist, waitlist-invited, waitlist-invite-expired, '
                           'waitlist-declined)', location='args')


@ns.route('/<int:training_id>/enrollments')
@ns.param('training_id', 'Training ID')
class EnrollmentList(Resource):
    @ns.doc('list_enrollments')
    @ns.expect(enroll_parser)
    @ns.marshal_list_with(enrollment_model)
    @admin_required
    def get(self, training_id):
        """List enrollments for a training.

        Possible status values: enrolled, waitlist, waitlist-invited,
        waitlist-invite-expired, waitlist-declined.
        """
        Training.query.get_or_404(training_id)
        args = enroll_parser.parse_args()

        query = TrainingEnroll.query.filter_by(training_id=training_id)

        if args.get('status'):
            query = query.filter_by(status=args['status'])

        return query.order_by(TrainingEnroll.enrole_date).all()

    @ns.doc('enroll_student')
    @ns.expect(enrollment_input)
    @ns.marshal_with(enrollment_model, code=201)
    @admin_required
    def post(self, training_id):
        """Enroll a student in a training.

        Uses the standard enrollment flow (enroll_common):

        - If spots are available → status=enrolled
        - If training is full → status=waitlist
        - Sends appropriate email/SMS notifications
        - Validates: student must be active, training must not have started,
          student must not already be enrolled (unless expired/declined)

        Note: booking policies (max-2-sessions-4-weeks) are NOT enforced here,
        matching the admin enrollment behaviour in the web UI.
        """
        training = Training.query.get_or_404(training_id)
        data = api.payload

        student = Student.query.get(data['student_id'])
        if not student:
            abort(400, 'Invalid student_id')

        result = enroll_common(training, student.user)

        if not result:
            existing = TrainingEnroll.query.filter_by(
                student_id=data['student_id'],
                training_id=training_id,
            ).first()
            if existing and existing.status not in (
                'waitlist-invite-expired', 'waitlist-declined', 'force-off-waitlist'
            ):
                abort(409, f'Student is already enrolled with status: {existing.status}')
            abort(400, 'Enrollment failed — student may not be active or training may have started')

        enrollment = TrainingEnroll.query.filter_by(
            student_id=data['student_id'],
            training_id=training_id,
        ).first()
        return enrollment, 201


@ns.route('/<int:training_id>/enrollments/<int:student_id>')
@ns.param('training_id', 'Training ID')
@ns.param('student_id', 'Student ID')
class EnrollmentDetail(Resource):
    @ns.doc('get_enrollment')
    @ns.marshal_with(enrollment_model)
    @admin_required
    def get(self, training_id, student_id):
        """Get a single enrollment."""
        enrollment = TrainingEnroll.query.filter_by(
            training_id=training_id,
            student_id=student_id,
        ).first_or_404()
        return enrollment

    @ns.doc('remove_enrollment')
    @admin_required
    def delete(self, training_id, student_id):
        """Remove an enrollment (admin de-enrollment).

        Sends de-enrollment notifications to student and trainers.
        Does NOT automatically cascade waitlist invitations — this is
        intentional for admin operations (matches web UI behaviour where
        deroll_common is called with admin=True).

        Use the 'invite' action to manually invite the next waitlisted student.
        """
        training = Training.query.get_or_404(training_id)
        enrollment = TrainingEnroll.query.filter_by(
            training_id=training_id,
            student_id=student_id,
        ).first_or_404()

        result = deroll_common(training, enrollment.student.user, admin=True)
        if not result:
            abort(400, 'De-enrollment failed — training may have already started')

        return '', 204


@ns.route('/<int:training_id>/enrollments/<int:student_id>/action')
@ns.param('training_id', 'Training ID')
@ns.param('student_id', 'Student ID')
class EnrollmentAction(Resource):
    @ns.doc('enrollment_action')
    @ns.expect(enrollment_action_input)
    @ns.marshal_with(enrollment_action_result)
    @admin_required
    def post(self, training_id, student_id):
        """Perform a status transition on an enrollment.

        Available actions:

        - **invite**: waitlist → waitlist-invited.
          Checks spot availability first. Sends invitation email + SMS + trainer notification.
        - **deinvite**: waitlist-invited → waitlist-invite-expired.
          Sends expiry notification to student and trainers.
        - **return-to-waitlist**: waitlist-invited → waitlist.
          Silently returns student to waitlist without notifications (keeps queue position).
        - **force-enroll**: waitlist → enrolled.
          Bypasses capacity check. Sends enrolled confirmation.
        - **decline**: waitlist-invited → waitlist-declined.
          Cascades: automatically invites next eligible waitlisted student(s).
        - **toggle-paid**: Flips the paid flag on the enrollment (any status).
        """
        training = Training.query.get_or_404(training_id)
        enrollment = TrainingEnroll.query.filter_by(
            training_id=training_id,
            student_id=student_id,
        ).first_or_404()

        data = api.payload
        action = data['action']

        if action == 'invite':
            if enrollment.status != 'waitlist':
                abort(400, f'Cannot invite: current status is {enrollment.status}, must be waitlist')
            # Check spot availability (mirrors training_detail_view.invite)
            if not training.wait_list_spot_available(enrollment.student):
                abort(409, 'No spots available — training is at capacity (enrolled + waitlist-invited)')
            invite_from_waitlist(enrollment)

        elif action == 'deinvite':
            if enrollment.status != 'waitlist-invited':
                abort(400, f'Cannot de-invite: current status is {enrollment.status}, must be waitlist-invited')
            deinvite_from_waitlist(enrollment)

        elif action == 'return-to-waitlist':
            # Mirrors training_detail_view.deinvite — sets back to waitlist silently
            if enrollment.status != 'waitlist-invited':
                abort(400, f'Cannot return to waitlist: current status is {enrollment.status}, must be waitlist-invited')
            enrollment.status = 'waitlist'
            db.session.commit()

        elif action == 'force-enroll':
            if enrollment.status != 'waitlist':
                abort(400, f'Cannot force-enroll: current status is {enrollment.status}, must be waitlist')
            enrollment.status = 'force-off-waitlist'
            db.session.commit()
            result = enroll_common(training, enrollment.student.user)
            if not result:
                abort(500, 'Force-enroll failed unexpectedly')
            enrollment = TrainingEnroll.query.filter_by(
                training_id=training_id,
                student_id=student_id,
            ).first()

        elif action == 'decline':
            if enrollment.status != 'waitlist-invited':
                abort(400, f'Cannot decline: current status is {enrollment.status}, must be waitlist-invited')
            enrollment.status = 'waitlist-declined'
            db.session.commit()
            # Cascade: invite next eligible waitlisted students (mirrors scheduler_views.decline_invite)
            for eligible in training.waitlist_enrollments_eligeble():
                invite_from_waitlist(eligible)

        elif action == 'toggle-paid':
            enrollment.paid = not enrollment.paid
            db.session.commit()

        else:
            abort(400, f'Unknown action: {action}. '
                  'Must be invite, deinvite, return-to-waitlist, force-enroll, decline, or toggle-paid')

        return {
            'student_id': student_id,
            'training_id': training_id,
            'status': enrollment.status,
            'action': action,
        }


@ns.route('/<int:training_id>/enrollments/bulk-move')
@ns.param('training_id', 'Source Training ID')
class EnrollmentBulkMove(Resource):
    @ns.doc('bulk_move_enrollments')
    @ns.expect(bulk_move_input)
    @ns.marshal_with(bulk_move_result)
    @admin_required
    def post(self, training_id):
        """Move or copy enrollments to another training.

        Preserves the enrollment status and paid flag.  Students already
        enrolled in the target training are skipped (reported in the
        skipped list).

        Note: no notifications are sent and no policy checks are performed.
        This is a direct database operation for admin convenience.
        """
        Training.query.get_or_404(training_id)
        data = api.payload

        target_id = data['target_training_id']
        target = Training.query.get(target_id)
        if not target:
            abort(400, 'Invalid target_training_id')

        if target_id == training_id:
            abort(400, 'Source and target training cannot be the same')

        operation = data.get('operation', 'move')
        if operation not in ('move', 'copy'):
            abort(400, 'Operation must be move or copy')

        override_status = data.get('override_status')
        valid_statuses = ('enrolled', 'waitlist', 'waitlist-invited',
                          'waitlist-invite-expired', 'waitlist-declined')
        if override_status and override_status not in valid_statuses:
            abort(400, f'Invalid override_status. Must be one of: {", ".join(valid_statuses)}')

        moved = []
        skipped = []
        errors = []

        for sid in data['student_ids']:
            source_enrollment = TrainingEnroll.query.filter_by(
                training_id=training_id,
                student_id=sid,
            ).first()

            if not source_enrollment:
                errors.append(f'Student {sid} not enrolled in source training')
                continue

            existing = TrainingEnroll.query.filter_by(
                training_id=target_id,
                student_id=sid,
            ).first()

            if existing:
                skipped.append(sid)
                continue

            new_enrollment = TrainingEnroll(
                student_id=sid,
                training_id=target_id,
                status=override_status or source_enrollment.status,
                paid=source_enrollment.paid,
            )
            db.session.add(new_enrollment)

            if operation == 'move':
                db.session.delete(source_enrollment)

            moved.append(sid)

        db.session.commit()
        return {'moved': moved, 'skipped': skipped, 'errors': errors}
