"""
Functional tests for enrollment business logic flows.

These tests exercise the real enrollment pipeline against the local MySQL database
(production data copy). They create test data with _FUNCTEST_ / functest_ prefixes
and clean up in tearDown. Email sending is mocked at the lowest level
(flask_mailman.EmailMessage.send) so the full rendering pipeline runs.

Run:
    cd test && ../.venv/bin/python -m unittest test_functional_flows -v
"""

import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
import pytz

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# bcource.students.common triggers imports that access current_app at module
# level, so we must defer those imports until an app context is active.
from bcource import create_app, db


def _import_deferred():
    """Import modules that require an active app context at import time."""
    from bcource.models import (
        Training, TrainingEnroll, TrainingEvent, Student, User,
        Practice, Location, TrainingType, StudentStatus, StudentType,
        Trainer,
    )
    from bcource.students.common import (
        enroll_common, deroll_common, invite_from_waitlist,
        enroll_from_waitlist, deinvite_from_waitlist,
    )
    from flask_security import hash_password

    # Inject into module globals so test classes can use them
    g = globals()
    for name, obj in locals().items():
        if name != 'g':
            g[name] = obj


class FunctionalTestBase(unittest.TestCase):
    """Base class for functional enrollment tests.

    Creates an app context, mocks email sending, and provides helpers
    for creating test users/students/trainings. Cleans up all test
    data in tearDown regardless of test outcome.
    """

    @classmethod
    def setUpClass(cls):
        cls._class_app = create_app()
        with cls._class_app.app_context():
            _import_deferred()

    def setUp(self):
        self.app = self.__class__._class_app
        # Need request context for flash() calls in business logic
        self.ctx = self.app.test_request_context()
        self.ctx.push()

        # Mock the lowest-level email send — everything else runs real
        self.email_patcher = patch('flask_mailman.EmailMessage.send')
        self.mock_email_send = self.email_patcher.start()

        # Mock SMS sending to avoid AWS calls
        self.sms_patcher = patch('bcource.students.common.send_sms', return_value=(True, None))
        self.mock_sms = self.sms_patcher.start()

        # Track test data for cleanup
        self._test_training_ids = []
        self._test_user_emails = []
        self._test_trainer_ids = []
        self._suffix_counter = 0

    def tearDown(self):
        try:
            # Delete in dependency order
            for tid in self._test_training_ids:
                TrainingEnroll.query.filter_by(training_id=tid).delete()
                TrainingEvent.query.filter_by(training_id=tid).delete()
                Training.query.filter_by(id=tid).delete()

            for trainer_id in self._test_trainer_ids:
                Trainer.query.filter_by(id=trainer_id).delete()

            for email in self._test_user_emails:
                user = User.query.filter_by(email=email).first()
                if user:
                    Student.query.filter_by(user_id=user.id).delete()
                    db.session.delete(user)

            db.session.commit()
        except Exception:
            db.session.rollback()
        finally:
            self.sms_patcher.stop()
            self.email_patcher.stop()
            self.ctx.pop()

    def _next_suffix(self):
        self._suffix_counter += 1
        return f'{self._suffix_counter:02d}'

    def create_test_user_and_student(self, suffix=None):
        """Create a User + Student linked to the default practice.

        Returns (user, student).
        """
        if suffix is None:
            suffix = self._next_suffix()

        email = f'functest_{suffix}@test.local'
        self._test_user_emails.append(email)

        from bcource import security
        user = security.datastore.create_user(
            email=email,
            password=hash_password('TestPass123!'),
            first_name=f'FuncFirst{suffix}',
            last_name=f'FuncLast{suffix}',
            active=True,
        )
        db.session.flush()

        practice = Practice.default_row()
        status = StudentStatus.query.filter_by(name='active').first()
        stype = StudentType.query.first()

        student = Student(
            user=user,
            practice=practice,
            studentstatus=status,
            studenttype=stype,
        )
        db.session.add(student)
        db.session.commit()

        return user, student

    def create_test_training(self, max_participants, suffix=None):
        """Create a Training with one future event (30 days out) and a trainer.

        Returns the Training instance.
        """
        if suffix is None:
            suffix = self._next_suffix()

        practice = Practice.default_row()
        ttype = TrainingType.query.filter_by(practice=practice).first()
        location = Location.query.first()

        # Create a trainer user + Trainer record for this training
        trainer_email = f'functest_trainer_{suffix}@test.local'
        self._test_user_emails.append(trainer_email)

        from bcource import security
        trainer_user = security.datastore.create_user(
            email=trainer_email,
            password=hash_password('TestPass123!'),
            first_name=f'Trainer{suffix}',
            last_name=f'FuncTest',
            active=True,
        )
        db.session.flush()

        trainer = Trainer(user=trainer_user, practice=practice)
        db.session.add(trainer)
        db.session.flush()
        self._test_trainer_ids.append(trainer.id)

        training = Training()
        training.name = f'_FUNCTEST_Training{suffix}'
        training.max_participants = max_participants
        training.active = True
        training.apply_policies = True
        training.practice = practice
        training.trainingtype = ttype
        training.trainers.append(trainer)

        db.session.add(training)
        db.session.flush()
        self._test_training_ids.append(training.id)

        future = datetime.now(tz=pytz.UTC) + timedelta(days=30)
        event = TrainingEvent(
            training_id=training.id,
            location=location,
            start_time=future,
            end_time=future + timedelta(hours=2),
        )
        db.session.add(event)
        db.session.commit()

        return training

    def fresh_training(self, training):
        """Re-fetch training from DB to reset cached enrollment counts.

        Must expunge (not just expire) so SQLAlchemy creates a new Python
        object and calls init_on_load, which resets the transient
        _spots_enrolled / _spots_available / etc. attributes to None.
        """
        training_id = training.id
        db.session.expunge(training)
        return db.session.get(Training, training_id)

    def get_enrollment(self, training, user):
        """Get the TrainingEnroll for a user in a training."""
        return TrainingEnroll.query.filter_by(
            training_id=training.id,
        ).join(Student).join(User).filter(User.id == user.id).first()


# ---------------------------------------------------------------------------
# Flow 1: Direct enrollment when spots available
# ---------------------------------------------------------------------------
class TestDirectEnrollment(FunctionalTestBase):

    def test_enroll_direct(self):
        """Student enrolls directly when training has capacity."""
        training = self.create_test_training(max_participants=2)
        user, student = self.create_test_user_and_student()

        result = enroll_common(training, user)

        self.assertTrue(result)
        enrollment = self.get_enrollment(training, user)
        self.assertIsNotNone(enrollment)
        self.assertEqual(enrollment.status, 'enrolled')


# ---------------------------------------------------------------------------
# Flow 2: Waitlist when training is full
# ---------------------------------------------------------------------------
class TestWaitlistWhenFull(FunctionalTestBase):

    def test_second_student_waitlisted(self):
        """Second student goes to waitlist when max_participants=1."""
        training = self.create_test_training(max_participants=1)
        user_a, _ = self.create_test_user_and_student()
        user_b, _ = self.create_test_user_and_student()

        enroll_common(training, user_a)
        training = self.fresh_training(training)
        enroll_common(training, user_b)

        enrollment_a = self.get_enrollment(training, user_a)
        enrollment_b = self.get_enrollment(training, user_b)

        self.assertEqual(enrollment_a.status, 'enrolled')
        self.assertEqual(enrollment_b.status, 'waitlist')


# ---------------------------------------------------------------------------
# Flow 3: Student cancel cascades waitlist invitation
# ---------------------------------------------------------------------------
class TestStudentCancelCascadesWaitlist(FunctionalTestBase):

    def test_cancel_promotes_waitlisted(self):
        """When enrolled student cancels, waitlisted student gets invited."""
        training = self.create_test_training(max_participants=1)
        user_a, _ = self.create_test_user_and_student()
        user_b, _ = self.create_test_user_and_student()

        enroll_common(training, user_a)
        training = self.fresh_training(training)
        enroll_common(training, user_b)

        # Student A cancels (non-admin)
        training = self.fresh_training(training)
        result = deroll_common(training, user_a, admin=False)
        self.assertTrue(result)

        # A's enrollment deleted
        enrollment_a = self.get_enrollment(training, user_a)
        self.assertIsNone(enrollment_a)

        # B promoted to waitlist-invited
        enrollment_b = self.get_enrollment(training, user_b)
        self.assertEqual(enrollment_b.status, 'waitlist-invited')
        self.assertIsNotNone(enrollment_b.invite_date)


# ---------------------------------------------------------------------------
# Flow 4: Admin cancel does NOT cascade
# ---------------------------------------------------------------------------
class TestAdminCancelNoCascade(FunctionalTestBase):

    def test_admin_cancel_no_cascade(self):
        """Admin de-enrollment does not auto-invite waitlisted students."""
        training = self.create_test_training(max_participants=1)
        user_a, _ = self.create_test_user_and_student()
        user_b, _ = self.create_test_user_and_student()

        enroll_common(training, user_a)
        training = self.fresh_training(training)
        enroll_common(training, user_b)

        # Admin cancels A
        training = self.fresh_training(training)
        result = deroll_common(training, user_a, admin=True)
        self.assertTrue(result)

        # A deleted
        enrollment_a = self.get_enrollment(training, user_a)
        self.assertIsNone(enrollment_a)

        # B stays on waitlist — NOT promoted
        enrollment_b = self.get_enrollment(training, user_b)
        self.assertEqual(enrollment_b.status, 'waitlist')


# ---------------------------------------------------------------------------
# Flow 5: Accept waitlist invitation
# ---------------------------------------------------------------------------
class TestAcceptWaitlistInvitation(FunctionalTestBase):

    def test_accept_invitation(self):
        """Student accepts waitlist invitation and becomes enrolled."""
        training = self.create_test_training(max_participants=1)
        user_a, _ = self.create_test_user_and_student()
        user_b, _ = self.create_test_user_and_student()

        enroll_common(training, user_a)
        training = self.fresh_training(training)
        enroll_common(training, user_b)

        # Cancel A → B gets invited
        training = self.fresh_training(training)
        deroll_common(training, user_a, admin=False)

        enrollment_b = self.get_enrollment(training, user_b)
        self.assertEqual(enrollment_b.status, 'waitlist-invited')

        # B accepts
        enroll_from_waitlist(enrollment_b)

        enrollment_b = self.get_enrollment(training, user_b)
        self.assertEqual(enrollment_b.status, 'enrolled')


# ---------------------------------------------------------------------------
# Flow 6: Decline cascades to next student
# ---------------------------------------------------------------------------
class TestDeclineCascadesToNextStudent(FunctionalTestBase):

    def test_decline_cascades(self):
        """When invited student declines, next waitlisted student gets invited."""
        training = self.create_test_training(max_participants=1)
        user_a, _ = self.create_test_user_and_student()
        user_b, _ = self.create_test_user_and_student()
        user_c, _ = self.create_test_user_and_student()

        # A enrolled, B+C waitlisted
        enroll_common(training, user_a)
        training = self.fresh_training(training)
        enroll_common(training, user_b)
        training = self.fresh_training(training)
        enroll_common(training, user_c)

        # Cancel A → B invited
        training = self.fresh_training(training)
        deroll_common(training, user_a, admin=False)

        enrollment_b = self.get_enrollment(training, user_b)
        self.assertEqual(enrollment_b.status, 'waitlist-invited')

        # B declines — simulate the decline + cascade
        enrollment_b.status = 'waitlist-declined'
        db.session.commit()

        # Re-fetch training to recalculate capacity (B declined frees the spot)
        training = self.fresh_training(training)
        waitlist_eligible = training.waitlist_enrollments_eligeble()
        for enrollment in waitlist_eligible:
            invite_from_waitlist(enrollment)

        enrollment_c = self.get_enrollment(training, user_c)
        self.assertEqual(enrollment_c.status, 'waitlist-invited')


# ---------------------------------------------------------------------------
# Flow 7: De-invite from waitlist
# ---------------------------------------------------------------------------
class TestDeinviteFromWaitlist(FunctionalTestBase):

    def test_deinvite(self):
        """Admin de-invites a waitlist-invited student → expired status."""
        training = self.create_test_training(max_participants=1)
        user_a, _ = self.create_test_user_and_student()
        user_b, _ = self.create_test_user_and_student()

        enroll_common(training, user_a)
        training = self.fresh_training(training)
        enroll_common(training, user_b)

        # Cancel A → B invited
        training = self.fresh_training(training)
        deroll_common(training, user_a, admin=False)

        enrollment_b = self.get_enrollment(training, user_b)
        self.assertEqual(enrollment_b.status, 'waitlist-invited')

        # De-invite B
        deinvite_from_waitlist(enrollment_b)

        enrollment_b = self.get_enrollment(training, user_b)
        self.assertEqual(enrollment_b.status, 'waitlist-invite-expired')


# ---------------------------------------------------------------------------
# Flow 8: Force-enroll bypasses capacity
# ---------------------------------------------------------------------------
class TestForceEnrollBypassesCapacity(FunctionalTestBase):

    def test_force_enroll(self):
        """Admin force-enrolls a waitlisted student even when training is full."""
        training = self.create_test_training(max_participants=1)
        user_a, _ = self.create_test_user_and_student()
        user_b, _ = self.create_test_user_and_student()

        enroll_common(training, user_a)
        training = self.fresh_training(training)
        enroll_common(training, user_b)

        enrollment_b = self.get_enrollment(training, user_b)
        self.assertEqual(enrollment_b.status, 'waitlist')

        # Force enroll B
        enrollment_b.status = 'force-off-waitlist'
        db.session.commit()

        training = self.fresh_training(training)
        result = enroll_common(training, user_b)
        self.assertTrue(result)

        enrollment_b = self.get_enrollment(training, user_b)
        self.assertEqual(enrollment_b.status, 'enrolled')

        # Training is now over capacity: 2 enrolled with max=1
        training = self.fresh_training(training)
        training._cal_enrollments()
        self.assertEqual(training._spots_enrolled, 2)


# ---------------------------------------------------------------------------
# Flow 9: Re-enrollment after expired or declined
# ---------------------------------------------------------------------------
class TestReenrollmentAfterExpiredOrDeclined(FunctionalTestBase):

    def test_reenroll_after_expired(self):
        """Student with expired invitation can re-enroll."""
        training = self.create_test_training(max_participants=2)
        user, _ = self.create_test_user_and_student()

        enroll_common(training, user)
        enrollment = self.get_enrollment(training, user)
        enrollment.status = 'waitlist-invite-expired'
        db.session.commit()

        # Re-enroll — should succeed
        training = self.fresh_training(training)
        result = enroll_common(training, user)
        self.assertTrue(result)

        enrollment = self.get_enrollment(training, user)
        self.assertEqual(enrollment.status, 'enrolled')

    def test_reenroll_after_declined(self):
        """Student who declined can re-enroll."""
        training = self.create_test_training(max_participants=2)
        user, _ = self.create_test_user_and_student()

        enroll_common(training, user)
        enrollment = self.get_enrollment(training, user)
        enrollment.status = 'waitlist-declined'
        db.session.commit()

        # Re-enroll — should succeed
        training = self.fresh_training(training)
        result = enroll_common(training, user)
        self.assertTrue(result)

        enrollment = self.get_enrollment(training, user)
        self.assertEqual(enrollment.status, 'enrolled')


# ---------------------------------------------------------------------------
# Flow 10: Capacity calculation
# ---------------------------------------------------------------------------
class TestCapacityCalculation(FunctionalTestBase):

    def test_capacity_counts(self):
        """Enrolled + waitlist-invited count against capacity; plain waitlist does not."""
        training = self.create_test_training(max_participants=3)
        users = []
        for _ in range(5):
            u, _ = self.create_test_user_and_student()
            users.append(u)

        # Enroll first 3 → all enrolled (fills capacity)
        for u in users[:3]:
            enroll_common(training, u)
            training = self.fresh_training(training)

        # Next 2 → waitlist
        for u in users[3:]:
            enroll_common(training, u)
            training = self.fresh_training(training)

        # Verify statuses
        for u in users[:3]:
            e = self.get_enrollment(training, u)
            self.assertEqual(e.status, 'enrolled', f'Expected enrolled for user {u.email}')

        for u in users[3:]:
            e = self.get_enrollment(training, u)
            self.assertEqual(e.status, 'waitlist', f'Expected waitlist for user {u.email}')

        # Now change one enrolled to waitlist-invited to test mixed counting
        # Cancel user[0] to make room, then invite user[3]
        training = self.fresh_training(training)
        deroll_common(training, users[0], admin=False)

        # User[3] should now be waitlist-invited (auto-cascaded)
        e3 = self.get_enrollment(training, users[3])
        self.assertEqual(e3.status, 'waitlist-invited')

        # Recalculate: 2 enrolled + 1 waitlist-invited = 3 against capacity
        training = self.fresh_training(training)
        training._cal_enrollments()

        self.assertEqual(training._spots_enrolled, 3)  # enrolled + waitlist-invited
        self.assertEqual(training._spots_available, 0)
        self.assertEqual(training._spots_waitlist_count, 1)  # only user[4] on plain waitlist


if __name__ == '__main__':
    unittest.main()
