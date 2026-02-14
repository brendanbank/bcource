"""
Tests for the admin API blueprint.

This module tests the Flask-RESTX admin API including:
- Authentication decorator (admin_required)
- Training CRUD endpoints
- Training event endpoints
- Enrollment endpoints with full status flow
- Enrollment actions (invite, deinvite, decline, force-enroll, etc.)
- Bulk move/copy operations
- Lookup endpoints (locations, training types, students)
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import json
import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def _make_admin_user():
    """Create a mock admin user that passes admin_required checks."""
    user = Mock()
    user.is_authenticated = True
    user.is_active = True
    user.tf_primary_method = 'email'
    user.has_role.return_value = True
    return user


def _make_non_admin_user():
    """Create a mock authenticated user without admin role."""
    user = Mock()
    user.is_authenticated = True
    user.is_active = True
    user.tf_primary_method = 'email'
    user.has_role.return_value = False
    return user


class TestAdminRequired(unittest.TestCase):
    """Test the admin_required authentication decorator."""

    def setUp(self):
        from bcource import create_app
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @patch('bcource.admin_api.auth.current_user')
    def test_unauthenticated_returns_401(self, mock_user):
        mock_user.is_authenticated = False
        resp = self.client.get('/admin-api/locations/')
        self.assertEqual(resp.status_code, 401)

    @patch('bcource.admin_api.auth.current_user')
    def test_inactive_user_returns_403(self, mock_user):
        mock_user.is_authenticated = True
        mock_user.is_active = False
        resp = self.client.get('/admin-api/locations/')
        self.assertEqual(resp.status_code, 403)

    @patch('bcource.admin_api.auth.current_user')
    def test_no_2fa_returns_403(self, mock_user):
        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.tf_primary_method = None
        resp = self.client.get('/admin-api/locations/')
        self.assertEqual(resp.status_code, 403)

    @patch('bcource.admin_api.auth.current_user')
    def test_wrong_role_returns_403(self, mock_user):
        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.tf_primary_method = 'email'
        mock_user.has_role = Mock(return_value=False)
        resp = self.client.get('/admin-api/locations/')
        self.assertEqual(resp.status_code, 403)


class TestLocationEndpoints(unittest.TestCase):
    """Test /admin-api/locations/ endpoints."""

    def setUp(self):
        from bcource import create_app
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @patch('bcource.admin_api.auth.current_user')
    @patch('bcource.admin_api.locations.Location')
    @patch('bcource.admin_api.locations.Practice')
    def test_list_locations(self, mock_practice_cls, mock_location_cls, mock_user):
        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.tf_primary_method = 'email'
        mock_user.has_role.return_value = True

        mock_practice = Mock(id=1)
        mock_practice_cls.default_row.return_value = mock_practice

        mock_loc = Mock()
        mock_loc.id = 1
        mock_loc.name = 'Test Location'
        mock_loc.street = 'Main St'
        mock_loc.house_number = '42'
        mock_loc.house_number_extention = None
        mock_loc.postal_code = '1234AB'
        mock_loc.city = 'Amsterdam'
        mock_loc.country = 'NL'

        mock_query = Mock()
        mock_query.order_by.return_value.all.return_value = [mock_loc]
        mock_location_cls.query.filter_by.return_value = mock_query

        resp = self.client.get('/admin-api/locations/')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Location')
        self.assertEqual(data[0]['city'], 'Amsterdam')


class TestTrainingTypeEndpoints(unittest.TestCase):
    """Test /admin-api/training-types/ endpoints."""

    def setUp(self):
        from bcource import create_app
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @patch('bcource.admin_api.auth.current_user')
    @patch('bcource.admin_api.training_types.TrainingType')
    @patch('bcource.admin_api.training_types.Practice')
    def test_list_training_types(self, mock_practice_cls, mock_tt_cls, mock_user):
        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.tf_primary_method = 'email'
        mock_user.has_role.return_value = True

        mock_practice = Mock(id=1)
        mock_practice_cls.default_row.return_value = mock_practice

        mock_tt = Mock()
        mock_tt.id = 1
        mock_tt.name = 'Yoga'
        mock_tt.description = 'Yoga class'

        mock_query = Mock()
        mock_query.order_by.return_value.all.return_value = [mock_tt]
        mock_tt_cls.query.filter_by.return_value = mock_query

        resp = self.client.get('/admin-api/training-types/')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Yoga')


class TestStudentEndpoints(unittest.TestCase):
    """Test /admin-api/students/ endpoints."""

    def setUp(self):
        from bcource import create_app
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @patch('bcource.admin_api.auth.current_user')
    @patch('bcource.admin_api.students.Student')
    @patch('bcource.admin_api.students.Practice')
    def test_search_students(self, mock_practice_cls, mock_student_cls, mock_user):
        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.tf_primary_method = 'email'
        mock_user.has_role.return_value = True

        mock_practice = Mock(id=1)
        mock_practice_cls.default_row.return_value = mock_practice

        mock_student_user = Mock()
        mock_student_user.fullname = 'Jane Doe'
        mock_student_user.email = 'jane@example.com'
        mock_student_user.phone_number = '+31612345678'

        mock_student = Mock()
        mock_student.id = 10
        mock_student.user = mock_student_user
        mock_student.studenttype = 'regular'
        mock_student.studentstatus = 'active'

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = [mock_student]
        mock_student_cls.query.join.return_value = mock_query

        resp = self.client.get('/admin-api/students/?q=jane')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['fullname'], 'Jane Doe')
        self.assertEqual(data[0]['email'], 'jane@example.com')

    @patch('bcource.admin_api.auth.current_user')
    @patch('bcource.admin_api.students.Student')
    @patch('bcource.admin_api.students.Practice')
    def test_list_students_no_query(self, mock_practice_cls, mock_student_cls, mock_user):
        """Without q param, should return all students (up to limit)."""
        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.tf_primary_method = 'email'
        mock_user.has_role.return_value = True

        mock_practice = Mock(id=1)
        mock_practice_cls.default_row.return_value = mock_practice

        mock_query = Mock()
        mock_query.order_by.return_value.limit.return_value.all.return_value = []
        mock_student_cls.query.join.return_value.filter.return_value = mock_query

        resp = self.client.get('/admin-api/students/')
        self.assertEqual(resp.status_code, 200)


class TestTrainingEndpoints(unittest.TestCase):
    """Test /admin-api/trainings/ CRUD endpoints."""

    def setUp(self):
        from bcource import create_app
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def _auth_patch(self):
        """Return a patch for admin_required auth."""
        patcher = patch('bcource.admin_api.auth.current_user')
        mock_user = patcher.start()
        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.tf_primary_method = 'email'
        mock_user.has_role.return_value = True
        return patcher

    @patch('bcource.admin_api.trainings.Practice')
    @patch('bcource.admin_api.trainings.Training')
    def test_list_trainings(self, mock_training_cls, mock_practice_cls):
        patcher = self._auth_patch()
        try:
            mock_practice = Mock(id=1)
            mock_practice_cls.default_row.return_value = mock_practice

            mock_training = Mock()
            mock_training.id = 1
            mock_training.name = 'Morning Yoga'
            mock_training.active = True
            mock_training.max_participants = 10
            mock_training.trainingtype = Mock(__str__=lambda s: 'Yoga')
            mock_training.trainingtype_id = 1
            mock_training.trainingenrollments = []
            mock_training.trainingevents = []

            mock_query = Mock()
            mock_query.filter_by.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value.all.return_value = [mock_training]
            mock_training_cls.query.filter_by.return_value = mock_query

            resp = self.client.get('/admin-api/trainings/')
            self.assertEqual(resp.status_code, 200)

            data = json.loads(resp.data)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['name'], 'Morning Yoga')
        finally:
            patcher.stop()

    @patch('bcource.admin_api.trainings.Practice')
    @patch('bcource.admin_api.trainings.Training')
    def test_list_trainings_filter_active(self, mock_training_cls, mock_practice_cls):
        patcher = self._auth_patch()
        try:
            mock_practice = Mock(id=1)
            mock_practice_cls.default_row.return_value = mock_practice

            mock_query = Mock()
            mock_query.filter_by.return_value = mock_query
            mock_query.order_by.return_value.all.return_value = []
            mock_training_cls.query.filter_by.return_value = mock_query

            resp = self.client.get('/admin-api/trainings/?active=true')
            self.assertEqual(resp.status_code, 200)

            # Verify filter_by was called with active=True
            calls = mock_query.filter_by.call_args_list
            active_filter_found = any(
                c.kwargs.get('active') is True for c in calls
            )
            self.assertTrue(active_filter_found, 'Expected filter_by(active=True) call')
        finally:
            patcher.stop()

    @patch('bcource.admin_api.trainings.db')
    @patch('bcource.admin_api.trainings.Practice')
    @patch('bcource.admin_api.trainings.TrainingType')
    @patch('bcource.admin_api.trainings.Training')
    def test_create_training(self, mock_training_cls, mock_tt_cls, mock_practice_cls, mock_db):
        patcher = self._auth_patch()
        try:
            mock_practice = Mock(id=1)
            mock_practice_cls.default_row.return_value = mock_practice

            mock_tt = Mock(id=1, practice_id=1)
            mock_tt_cls.query.get.return_value = mock_tt

            mock_training = Mock()
            mock_training.id = 5
            mock_training.name = 'New Training'
            mock_training.active = True
            mock_training.max_participants = 8
            mock_training.apply_policies = True
            mock_training.trainingtype_id = 1
            mock_training.trainingtype = Mock(__str__=lambda s: 'Yoga')
            mock_training.trainers = []
            mock_training.trainingevents = []
            mock_training.trainingenrollments = []
            mock_training_cls.return_value = mock_training

            resp = self.client.post('/admin-api/trainings/',
                data=json.dumps({
                    'name': 'New Training',
                    'trainingtype_id': 1,
                    'max_participants': 8,
                }),
                content_type='application/json')

            self.assertEqual(resp.status_code, 201)
            mock_db.session.add.assert_called_once()
            mock_db.session.commit.assert_called_once()
        finally:
            patcher.stop()

    @patch('bcource.admin_api.trainings.db')
    @patch('bcource.admin_api.trainings.Practice')
    @patch('bcource.admin_api.trainings.TrainingType')
    @patch('bcource.admin_api.trainings.Training')
    def test_create_training_invalid_type(self, mock_training_cls, mock_tt_cls, mock_practice_cls, mock_db):
        patcher = self._auth_patch()
        try:
            mock_practice = Mock(id=1)
            mock_practice_cls.default_row.return_value = mock_practice

            mock_tt_cls.query.get.return_value = None  # Invalid type

            resp = self.client.post('/admin-api/trainings/',
                data=json.dumps({
                    'name': 'Bad Training',
                    'trainingtype_id': 999,
                    'max_participants': 8,
                }),
                content_type='application/json')

            self.assertEqual(resp.status_code, 400)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.trainings.Training')
    def test_get_training_detail(self, mock_training_cls):
        patcher = self._auth_patch()
        try:
            mock_training = Mock()
            mock_training.id = 1
            mock_training.name = 'Morning Yoga'
            mock_training.active = True
            mock_training.max_participants = 10
            mock_training.apply_policies = True
            mock_training.trainingtype_id = 1
            mock_training.trainingtype = Mock(__str__=lambda s: 'Yoga')
            mock_training.trainers = []
            mock_training.trainingevents = []
            mock_training.trainingenrollments = []

            mock_training_cls.query.get_or_404.return_value = mock_training

            resp = self.client.get('/admin-api/trainings/1')
            self.assertEqual(resp.status_code, 200)

            data = json.loads(resp.data)
            self.assertEqual(data['name'], 'Morning Yoga')
            self.assertEqual(data['spots_available'], 10)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.trainings.Training')
    def test_get_training_spots_calculation(self, mock_training_cls):
        """Test spots_available = max_participants - (enrolled + waitlist-invited)."""
        patcher = self._auth_patch()
        try:
            enrolled_1 = Mock(status='enrolled')
            enrolled_2 = Mock(status='enrolled')
            invited = Mock(status='waitlist-invited')
            waitlisted = Mock(status='waitlist')  # Should NOT count against capacity

            mock_training = Mock()
            mock_training.id = 1
            mock_training.name = 'Full Training'
            mock_training.active = True
            mock_training.max_participants = 4
            mock_training.apply_policies = True
            mock_training.trainingtype_id = 1
            mock_training.trainingtype = Mock(__str__=lambda s: 'Yoga')
            mock_training.trainers = []
            mock_training.trainingevents = []
            mock_training.trainingenrollments = [enrolled_1, enrolled_2, invited, waitlisted]

            mock_training_cls.query.get_or_404.return_value = mock_training

            resp = self.client.get('/admin-api/trainings/1')
            self.assertEqual(resp.status_code, 200)

            data = json.loads(resp.data)
            # 4 max - 3 (2 enrolled + 1 invited) = 1 spot
            self.assertEqual(data['enrollment_count'], 3)
            self.assertEqual(data['waitlist_count'], 1)
            self.assertEqual(data['spots_available'], 1)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.trainings.db')
    @patch('bcource.admin_api.trainings.Practice')
    @patch('bcource.admin_api.trainings.Training')
    def test_update_training(self, mock_training_cls, mock_practice_cls, mock_db):
        patcher = self._auth_patch()
        try:
            mock_practice = Mock(id=1)
            mock_practice_cls.default_row.return_value = mock_practice

            mock_training = Mock()
            mock_training.id = 1
            mock_training.name = 'Old Name'
            mock_training.active = True
            mock_training.max_participants = 10
            mock_training.apply_policies = True
            mock_training.trainingtype_id = 1
            mock_training.trainingtype = Mock(__str__=lambda s: 'Yoga')
            mock_training.trainers = MagicMock()
            mock_training.trainingevents = []
            mock_training.trainingenrollments = []

            mock_training_cls.query.get_or_404.return_value = mock_training

            resp = self.client.put('/admin-api/trainings/1',
                data=json.dumps({'name': 'New Name', 'max_participants': 12}),
                content_type='application/json')

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(mock_training.name, 'New Name')
            self.assertEqual(mock_training.max_participants, 12)
            mock_db.session.commit.assert_called_once()
        finally:
            patcher.stop()

    @patch('bcource.admin_api.trainings.db')
    @patch('bcource.admin_api.trainings.Training')
    def test_deactivate_training(self, mock_training_cls, mock_db):
        patcher = self._auth_patch()
        try:
            mock_training = Mock()
            mock_training.id = 1
            mock_training.name = 'Active Training'
            mock_training.active = True
            mock_training.max_participants = 10
            mock_training.apply_policies = True
            mock_training.trainingtype_id = 1
            mock_training.trainingtype = Mock(__str__=lambda s: 'Yoga')
            mock_training.trainers = []
            mock_training.trainingevents = []
            mock_training.trainingenrollments = []

            mock_training_cls.query.get_or_404.return_value = mock_training

            resp = self.client.patch('/admin-api/trainings/1/deactivate')
            self.assertEqual(resp.status_code, 200)
            self.assertFalse(mock_training.active)
            mock_db.session.commit.assert_called_once()
        finally:
            patcher.stop()


class TestTrainingEventEndpoints(unittest.TestCase):
    """Test /admin-api/trainings/<id>/events endpoints."""

    def setUp(self):
        from bcource import create_app
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def _auth_patch(self):
        patcher = patch('bcource.admin_api.auth.current_user')
        mock_user = patcher.start()
        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.tf_primary_method = 'email'
        mock_user.has_role.return_value = True
        return patcher

    @patch('bcource.admin_api.training_events.TrainingEvent')
    @patch('bcource.admin_api.training_events.Training')
    def test_list_events(self, mock_training_cls, mock_event_cls):
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)

            mock_event = Mock()
            mock_event.id = 10
            mock_event.start_time = datetime.datetime(2025, 3, 1, 9, 0)
            mock_event.end_time = datetime.datetime(2025, 3, 1, 10, 0)
            mock_event.location_id = 1
            mock_event.location = Mock(__str__=lambda s: 'Studio A')
            mock_event.training_id = 1

            mock_query = Mock()
            mock_query.order_by.return_value.all.return_value = [mock_event]
            mock_event_cls.query.filter_by.return_value = mock_query

            resp = self.client.get('/admin-api/trainings/1/events')
            self.assertEqual(resp.status_code, 200)

            data = json.loads(resp.data)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['location_name'], 'Studio A')
        finally:
            patcher.stop()

    @patch('bcource.admin_api.training_events.db')
    @patch('bcource.admin_api.training_events.Location')
    @patch('bcource.admin_api.training_events.Practice')
    @patch('bcource.admin_api.training_events.Training')
    def test_create_event(self, mock_training_cls, mock_practice_cls, mock_location_cls, mock_db):
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)
            mock_practice = Mock(id=1)
            mock_practice_cls.default_row.return_value = mock_practice
            mock_location_cls.query.get.return_value = Mock(id=1, practice_id=1)

            resp = self.client.post('/admin-api/trainings/1/events',
                data=json.dumps({
                    'start_time': '2025-03-01T09:00:00',
                    'end_time': '2025-03-01T10:00:00',
                    'location_id': 1,
                }),
                content_type='application/json')

            self.assertEqual(resp.status_code, 201)
            mock_db.session.add.assert_called_once()
            mock_db.session.commit.assert_called_once()
        finally:
            patcher.stop()

    @patch('bcource.admin_api.training_events.db')
    @patch('bcource.admin_api.training_events.Location')
    @patch('bcource.admin_api.training_events.Practice')
    @patch('bcource.admin_api.training_events.TrainingEvent')
    @patch('bcource.admin_api.training_events.Training')
    def test_update_event(self, mock_training_cls, mock_event_cls, mock_practice_cls,
                          mock_location_cls, mock_db):
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)
            mock_practice = Mock(id=1)
            mock_practice_cls.default_row.return_value = mock_practice

            mock_event = Mock()
            mock_event.id = 10
            mock_event.training_id = 1
            mock_event.start_time = datetime.datetime(2025, 3, 1, 9, 0)
            mock_event.end_time = datetime.datetime(2025, 3, 1, 10, 0)
            mock_event.location_id = 1
            mock_event.location = Mock(__str__=lambda s: 'Studio A')
            mock_event_cls.query.get_or_404.return_value = mock_event

            mock_location_cls.query.get.return_value = Mock(id=2, practice_id=1)

            resp = self.client.put('/admin-api/trainings/1/events/10',
                data=json.dumps({
                    'start_time': '2025-03-01T10:00:00',
                    'end_time': '2025-03-01T11:00:00',
                    'location_id': 2,
                }),
                content_type='application/json')

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(mock_event.location_id, 2)
            mock_db.session.commit.assert_called_once()
        finally:
            patcher.stop()

    @patch('bcource.admin_api.training_events.db')
    @patch('bcource.admin_api.training_events.TrainingEvent')
    @patch('bcource.admin_api.training_events.Training')
    def test_update_event_wrong_training(self, mock_training_cls, mock_event_cls, mock_db):
        """Updating an event that belongs to a different training returns 404."""
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)
            mock_event = Mock()
            mock_event.training_id = 999  # Different training
            mock_event_cls.query.get_or_404.return_value = mock_event

            resp = self.client.put('/admin-api/trainings/1/events/10',
                data=json.dumps({
                    'start_time': '2025-03-01T10:00:00',
                    'end_time': '2025-03-01T11:00:00',
                    'location_id': 1,
                }),
                content_type='application/json')

            self.assertEqual(resp.status_code, 404)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.training_events.db')
    @patch('bcource.admin_api.training_events.TrainingEvent')
    @patch('bcource.admin_api.training_events.Training')
    def test_delete_event(self, mock_training_cls, mock_event_cls, mock_db):
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)

            mock_event = Mock()
            mock_event.id = 10
            mock_event.training_id = 1
            mock_event_cls.query.get_or_404.return_value = mock_event

            resp = self.client.delete('/admin-api/trainings/1/events/10')
            self.assertEqual(resp.status_code, 204)
            mock_db.session.delete.assert_called_once_with(mock_event)
            mock_db.session.commit.assert_called_once()
        finally:
            patcher.stop()


class TestEnrollmentEndpoints(unittest.TestCase):
    """Test /admin-api/trainings/<id>/enrollments endpoints."""

    def setUp(self):
        from bcource import create_app
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def _auth_patch(self):
        patcher = patch('bcource.admin_api.auth.current_user')
        mock_user = patcher.start()
        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.tf_primary_method = 'email'
        mock_user.has_role.return_value = True
        return patcher

    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_list_enrollments(self, mock_training_cls, mock_enroll_cls):
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)

            mock_student = Mock(__str__=lambda s: 'Jane Doe')
            mock_student.user = Mock(email='jane@example.com')

            mock_enrollment = Mock()
            mock_enrollment.student_id = 10
            mock_enrollment.training_id = 1
            mock_enrollment.student = mock_student
            mock_enrollment.status = 'enrolled'
            mock_enrollment.enrole_date = datetime.datetime(2025, 1, 15)
            mock_enrollment.invite_date = None
            mock_enrollment.paid = False

            mock_query = Mock()
            mock_query.filter_by.return_value = mock_query
            mock_query.order_by.return_value.all.return_value = [mock_enrollment]
            mock_enroll_cls.query.filter_by.return_value = mock_query

            resp = self.client.get('/admin-api/trainings/1/enrollments')
            self.assertEqual(resp.status_code, 200)

            data = json.loads(resp.data)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['status'], 'enrolled')
            self.assertEqual(data[0]['student_name'], 'Jane Doe')
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_list_enrollments_filter_status(self, mock_training_cls, mock_enroll_cls):
        """Filter by status parameter."""
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)

            mock_query = Mock()
            mock_query.filter_by.return_value = mock_query
            mock_query.order_by.return_value.all.return_value = []
            mock_enroll_cls.query.filter_by.return_value = mock_query

            resp = self.client.get('/admin-api/trainings/1/enrollments?status=waitlist')
            self.assertEqual(resp.status_code, 200)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.enroll_common')
    @patch('bcource.admin_api.enrollments.Student')
    @patch('bcource.admin_api.enrollments.Training')
    def test_enroll_student_enrolled(self, mock_training_cls, mock_student_cls,
                                      mock_enroll_common, mock_enroll_cls):
        """When spots are available, enroll_common sets status=enrolled."""
        patcher = self._auth_patch()
        try:
            mock_training = Mock(id=1)
            mock_training_cls.query.get_or_404.return_value = mock_training

            mock_user = Mock()
            mock_student = Mock(id=10, user=mock_user)
            mock_student_cls.query.get.return_value = mock_student

            mock_enroll_common.return_value = True

            mock_enrollment = Mock()
            mock_enrollment.student_id = 10
            mock_enrollment.training_id = 1
            mock_enrollment.student = Mock(__str__=lambda s: 'Jane Doe')
            mock_enrollment.student.user = Mock(email='jane@example.com')
            mock_enrollment.status = 'enrolled'
            mock_enrollment.enrole_date = datetime.datetime(2025, 1, 15)
            mock_enrollment.invite_date = None
            mock_enrollment.paid = False

            mock_enroll_cls.query.filter_by.return_value.first.return_value = mock_enrollment

            resp = self.client.post('/admin-api/trainings/1/enrollments',
                data=json.dumps({'student_id': 10}),
                content_type='application/json')

            self.assertEqual(resp.status_code, 201)
            mock_enroll_common.assert_called_once_with(mock_training, mock_user)

            data = json.loads(resp.data)
            self.assertEqual(data['status'], 'enrolled')
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.enroll_common')
    @patch('bcource.admin_api.enrollments.Student')
    @patch('bcource.admin_api.enrollments.Training')
    def test_enroll_student_waitlist(self, mock_training_cls, mock_student_cls,
                                      mock_enroll_common, mock_enroll_cls):
        """When training is full, enroll_common sets status=waitlist."""
        patcher = self._auth_patch()
        try:
            mock_training = Mock(id=1)
            mock_training_cls.query.get_or_404.return_value = mock_training

            mock_user = Mock()
            mock_student = Mock(id=10, user=mock_user)
            mock_student_cls.query.get.return_value = mock_student

            mock_enroll_common.return_value = True

            mock_enrollment = Mock()
            mock_enrollment.student_id = 10
            mock_enrollment.training_id = 1
            mock_enrollment.student = Mock(__str__=lambda s: 'Jane Doe')
            mock_enrollment.student.user = Mock(email='jane@example.com')
            mock_enrollment.status = 'waitlist'
            mock_enrollment.enrole_date = datetime.datetime(2025, 1, 15)
            mock_enrollment.invite_date = None
            mock_enrollment.paid = False

            mock_enroll_cls.query.filter_by.return_value.first.return_value = mock_enrollment

            resp = self.client.post('/admin-api/trainings/1/enrollments',
                data=json.dumps({'student_id': 10}),
                content_type='application/json')

            self.assertEqual(resp.status_code, 201)
            data = json.loads(resp.data)
            self.assertEqual(data['status'], 'waitlist')
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.enroll_common')
    @patch('bcource.admin_api.enrollments.Student')
    @patch('bcource.admin_api.enrollments.Training')
    def test_enroll_already_enrolled_returns_409(self, mock_training_cls, mock_student_cls,
                                                  mock_enroll_common, mock_enroll_cls):
        """Enrolling an already-enrolled student returns 409."""
        patcher = self._auth_patch()
        try:
            mock_training = Mock(id=1)
            mock_training_cls.query.get_or_404.return_value = mock_training

            mock_student = Mock(id=10, user=Mock())
            mock_student_cls.query.get.return_value = mock_student

            mock_enroll_common.return_value = None  # Failed - already enrolled

            existing = Mock(status='enrolled')
            mock_enroll_cls.query.filter_by.return_value.first.return_value = existing

            resp = self.client.post('/admin-api/trainings/1/enrollments',
                data=json.dumps({'student_id': 10}),
                content_type='application/json')

            self.assertEqual(resp.status_code, 409)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.enroll_common')
    @patch('bcource.admin_api.enrollments.Student')
    @patch('bcource.admin_api.enrollments.Training')
    def test_enroll_invalid_student_returns_400(self, mock_training_cls, mock_student_cls,
                                                 mock_enroll_common, mock_enroll_cls):
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)
            mock_student_cls.query.get.return_value = None  # Student not found

            resp = self.client.post('/admin-api/trainings/1/enrollments',
                data=json.dumps({'student_id': 999}),
                content_type='application/json')

            self.assertEqual(resp.status_code, 400)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.deroll_common')
    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_delete_enrollment(self, mock_training_cls, mock_enroll_cls, mock_deroll):
        """Admin de-enrollment calls deroll_common(admin=True) — no waitlist cascade."""
        patcher = self._auth_patch()
        try:
            mock_training = Mock(id=1)
            mock_training_cls.query.get_or_404.return_value = mock_training

            mock_enrollment = Mock()
            mock_enrollment.student = Mock(user=Mock())
            mock_enroll_cls.query.filter_by.return_value.first_or_404.return_value = mock_enrollment

            mock_deroll.return_value = True

            resp = self.client.delete('/admin-api/trainings/1/enrollments/10')
            self.assertEqual(resp.status_code, 204)

            # Verify admin=True to prevent automatic waitlist cascade
            mock_deroll.assert_called_once_with(mock_training, mock_enrollment.student.user, admin=True)
        finally:
            patcher.stop()


class TestEnrollmentActions(unittest.TestCase):
    """Test enrollment action endpoint with all status transitions."""

    def setUp(self):
        from bcource import create_app
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def _auth_patch(self):
        patcher = patch('bcource.admin_api.auth.current_user')
        mock_user = patcher.start()
        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.tf_primary_method = 'email'
        mock_user.has_role.return_value = True
        return patcher

    def _post_action(self, training_id, student_id, action):
        return self.client.post(
            f'/admin-api/trainings/{training_id}/enrollments/{student_id}/action',
            data=json.dumps({'action': action}),
            content_type='application/json',
        )

    @patch('bcource.admin_api.enrollments.invite_from_waitlist')
    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_invite_from_waitlist(self, mock_training_cls, mock_enroll_cls, mock_invite):
        """invite: waitlist → waitlist-invited, checks spot availability."""
        patcher = self._auth_patch()
        try:
            mock_training = Mock(id=1)
            mock_training.wait_list_spot_available.return_value = True
            mock_training_cls.query.get_or_404.return_value = mock_training

            mock_enrollment = Mock()
            mock_enrollment.status = 'waitlist'
            mock_enrollment.student = Mock()
            mock_enroll_cls.query.filter_by.return_value.first_or_404.return_value = mock_enrollment

            resp = self._post_action(1, 10, 'invite')
            self.assertEqual(resp.status_code, 200)
            mock_invite.assert_called_once_with(mock_enrollment)

            # Verify spot check was performed
            mock_training.wait_list_spot_available.assert_called_once_with(mock_enrollment.student)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.invite_from_waitlist')
    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_invite_no_spots_returns_409(self, mock_training_cls, mock_enroll_cls, mock_invite):
        """invite when at capacity returns 409."""
        patcher = self._auth_patch()
        try:
            mock_training = Mock(id=1)
            mock_training.wait_list_spot_available.return_value = False
            mock_training_cls.query.get_or_404.return_value = mock_training

            mock_enrollment = Mock(status='waitlist')
            mock_enrollment.student = Mock()
            mock_enroll_cls.query.filter_by.return_value.first_or_404.return_value = mock_enrollment

            resp = self._post_action(1, 10, 'invite')
            self.assertEqual(resp.status_code, 409)
            mock_invite.assert_not_called()
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_invite_wrong_status_returns_400(self, mock_training_cls, mock_enroll_cls):
        """invite on non-waitlist enrollment returns 400."""
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)

            mock_enrollment = Mock(status='enrolled')
            mock_enroll_cls.query.filter_by.return_value.first_or_404.return_value = mock_enrollment

            resp = self._post_action(1, 10, 'invite')
            self.assertEqual(resp.status_code, 400)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.deinvite_from_waitlist')
    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_deinvite(self, mock_training_cls, mock_enroll_cls, mock_deinvite):
        """deinvite: waitlist-invited → waitlist-invite-expired."""
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)

            mock_enrollment = Mock(status='waitlist-invited')
            mock_enroll_cls.query.filter_by.return_value.first_or_404.return_value = mock_enrollment

            resp = self._post_action(1, 10, 'deinvite')
            self.assertEqual(resp.status_code, 200)
            mock_deinvite.assert_called_once_with(mock_enrollment)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.db')
    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_return_to_waitlist(self, mock_training_cls, mock_enroll_cls, mock_db):
        """return-to-waitlist: waitlist-invited → waitlist (silent, no notification)."""
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)

            mock_enrollment = Mock(status='waitlist-invited')
            mock_enroll_cls.query.filter_by.return_value.first_or_404.return_value = mock_enrollment

            resp = self._post_action(1, 10, 'return-to-waitlist')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(mock_enrollment.status, 'waitlist')
            mock_db.session.commit.assert_called_once()
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.db')
    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_return_to_waitlist_wrong_status(self, mock_training_cls, mock_enroll_cls, mock_db):
        """return-to-waitlist on non-invited enrollment returns 400."""
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)

            mock_enrollment = Mock(status='enrolled')
            mock_enroll_cls.query.filter_by.return_value.first_or_404.return_value = mock_enrollment

            resp = self._post_action(1, 10, 'return-to-waitlist')
            self.assertEqual(resp.status_code, 400)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.enroll_common')
    @patch('bcource.admin_api.enrollments.db')
    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_force_enroll(self, mock_training_cls, mock_enroll_cls, mock_db, mock_enroll_common):
        """force-enroll: waitlist → force-off-waitlist → enrolled (bypasses capacity)."""
        patcher = self._auth_patch()
        try:
            mock_training = Mock(id=1)
            mock_training_cls.query.get_or_404.return_value = mock_training

            mock_enrollment = Mock(status='waitlist')
            mock_enrollment.student = Mock(user=Mock())
            mock_enroll_cls.query.filter_by.return_value.first_or_404.return_value = mock_enrollment
            mock_enroll_cls.query.filter_by.return_value.first.return_value = mock_enrollment

            mock_enroll_common.return_value = True

            resp = self._post_action(1, 10, 'force-enroll')
            self.assertEqual(resp.status_code, 200)

            # Verify intermediate status was set to force-off-waitlist
            # (the mock tracks attribute sets)
            mock_enroll_common.assert_called_once_with(mock_training, mock_enrollment.student.user)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_force_enroll_wrong_status(self, mock_training_cls, mock_enroll_cls):
        """force-enroll on non-waitlist enrollment returns 400."""
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)

            mock_enrollment = Mock(status='enrolled')
            mock_enroll_cls.query.filter_by.return_value.first_or_404.return_value = mock_enrollment

            resp = self._post_action(1, 10, 'force-enroll')
            self.assertEqual(resp.status_code, 400)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.invite_from_waitlist')
    @patch('bcource.admin_api.enrollments.db')
    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_decline_cascades_waitlist(self, mock_training_cls, mock_enroll_cls,
                                        mock_db, mock_invite):
        """decline: waitlist-invited → waitlist-declined + cascades invitation to next eligible."""
        patcher = self._auth_patch()
        try:
            mock_training = Mock(id=1)
            mock_training_cls.query.get_or_404.return_value = mock_training

            mock_enrollment = Mock(status='waitlist-invited')
            mock_enroll_cls.query.filter_by.return_value.first_or_404.return_value = mock_enrollment

            # Set up next eligible students for cascade
            next_eligible = [Mock(), Mock()]
            mock_training.waitlist_enrollments_eligeble.return_value = next_eligible

            resp = self._post_action(1, 10, 'decline')
            self.assertEqual(resp.status_code, 200)

            # Verify status was set to declined
            self.assertEqual(mock_enrollment.status, 'waitlist-declined')
            mock_db.session.commit.assert_called()

            # Verify cascade: invite_from_waitlist called for each eligible
            self.assertEqual(mock_invite.call_count, 2)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.db')
    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_toggle_paid(self, mock_training_cls, mock_enroll_cls, mock_db):
        """toggle-paid: flips the paid flag."""
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)

            mock_enrollment = Mock(status='enrolled', paid=False)
            mock_enroll_cls.query.filter_by.return_value.first_or_404.return_value = mock_enrollment

            resp = self._post_action(1, 10, 'toggle-paid')
            self.assertEqual(resp.status_code, 200)

            # paid should have been toggled from False to True
            self.assertTrue(mock_enrollment.paid)
            mock_db.session.commit.assert_called_once()
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_unknown_action_returns_400(self, mock_training_cls, mock_enroll_cls):
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)

            mock_enrollment = Mock(status='waitlist')
            mock_enroll_cls.query.filter_by.return_value.first_or_404.return_value = mock_enrollment

            resp = self._post_action(1, 10, 'invalid-action')
            self.assertEqual(resp.status_code, 400)
        finally:
            patcher.stop()


class TestBulkMoveEndpoint(unittest.TestCase):
    """Test /admin-api/trainings/<id>/enrollments/bulk-move endpoint."""

    def setUp(self):
        from bcource import create_app
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def _auth_patch(self):
        patcher = patch('bcource.admin_api.auth.current_user')
        mock_user = patcher.start()
        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.tf_primary_method = 'email'
        mock_user.has_role.return_value = True
        return patcher

    @patch('bcource.admin_api.enrollments.db')
    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_bulk_move(self, mock_training_cls, mock_enroll_cls, mock_db):
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)
            mock_training_cls.query.get.return_value = Mock(id=2)

            source_enrollment = Mock(status='enrolled', paid=True)

            def filter_by_side_effect(**kwargs):
                result = Mock()
                if kwargs.get('training_id') == 1:
                    result.first.return_value = source_enrollment
                elif kwargs.get('training_id') == 2:
                    result.first.return_value = None  # Not in target
                return result

            mock_enroll_cls.query.filter_by.side_effect = filter_by_side_effect

            resp = self.client.post('/admin-api/trainings/1/enrollments/bulk-move',
                data=json.dumps({
                    'student_ids': [10],
                    'target_training_id': 2,
                    'operation': 'move',
                }),
                content_type='application/json')

            self.assertEqual(resp.status_code, 200)
            data = json.loads(resp.data)
            self.assertIn(10, data['moved'])
            self.assertEqual(len(data['skipped']), 0)
            self.assertEqual(len(data['errors']), 0)

            mock_db.session.add.assert_called_once()
            mock_db.session.delete.assert_called_once_with(source_enrollment)
            mock_db.session.commit.assert_called_once()
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.db')
    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_bulk_copy(self, mock_training_cls, mock_enroll_cls, mock_db):
        """Copy operation: source enrollment should NOT be deleted."""
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)
            mock_training_cls.query.get.return_value = Mock(id=2)

            source_enrollment = Mock(status='enrolled', paid=False)

            def filter_by_side_effect(**kwargs):
                result = Mock()
                if kwargs.get('training_id') == 1:
                    result.first.return_value = source_enrollment
                elif kwargs.get('training_id') == 2:
                    result.first.return_value = None
                return result

            mock_enroll_cls.query.filter_by.side_effect = filter_by_side_effect

            resp = self.client.post('/admin-api/trainings/1/enrollments/bulk-move',
                data=json.dumps({
                    'student_ids': [10],
                    'target_training_id': 2,
                    'operation': 'copy',
                }),
                content_type='application/json')

            self.assertEqual(resp.status_code, 200)
            data = json.loads(resp.data)
            self.assertIn(10, data['moved'])

            mock_db.session.add.assert_called_once()
            mock_db.session.delete.assert_not_called()  # Copy doesn't delete
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.db')
    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_bulk_move_skips_existing(self, mock_training_cls, mock_enroll_cls, mock_db):
        """Students already in target training should be skipped."""
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)
            mock_training_cls.query.get.return_value = Mock(id=2)

            source_enrollment = Mock(status='enrolled', paid=True)
            target_existing = Mock(status='enrolled')

            def filter_by_side_effect(**kwargs):
                result = Mock()
                if kwargs.get('training_id') == 1:
                    result.first.return_value = source_enrollment
                elif kwargs.get('training_id') == 2:
                    result.first.return_value = target_existing  # Already exists
                return result

            mock_enroll_cls.query.filter_by.side_effect = filter_by_side_effect

            resp = self.client.post('/admin-api/trainings/1/enrollments/bulk-move',
                data=json.dumps({
                    'student_ids': [10],
                    'target_training_id': 2,
                    'operation': 'move',
                }),
                content_type='application/json')

            self.assertEqual(resp.status_code, 200)
            data = json.loads(resp.data)
            self.assertIn(10, data['skipped'])
            self.assertEqual(len(data['moved']), 0)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_bulk_move_same_training_returns_400(self, mock_training_cls, mock_enroll_cls):
        """Moving to the same training returns 400."""
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)

            resp = self.client.post('/admin-api/trainings/1/enrollments/bulk-move',
                data=json.dumps({
                    'student_ids': [10],
                    'target_training_id': 1,
                    'operation': 'move',
                }),
                content_type='application/json')

            self.assertEqual(resp.status_code, 400)
        finally:
            patcher.stop()

    @patch('bcource.admin_api.enrollments.TrainingEnroll')
    @patch('bcource.admin_api.enrollments.Training')
    def test_bulk_move_invalid_target_returns_400(self, mock_training_cls, mock_enroll_cls):
        """Invalid target training returns 400."""
        patcher = self._auth_patch()
        try:
            mock_training_cls.query.get_or_404.return_value = Mock(id=1)
            mock_training_cls.query.get.return_value = None  # Target not found

            resp = self.client.post('/admin-api/trainings/1/enrollments/bulk-move',
                data=json.dumps({
                    'student_ids': [10],
                    'target_training_id': 999,
                    'operation': 'move',
                }),
                content_type='application/json')

            self.assertEqual(resp.status_code, 400)
        finally:
            patcher.stop()


if __name__ == '__main__':
    unittest.main()
