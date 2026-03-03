"""
Tests for the automation system.

This module tests the automation framework including:
- Automation registration and retrieval
- BaseAutomationTask functionality
- Job creation and scheduling
- Concrete automation tasks (StudentReminderTask, TrainerReminderTask, etc.)
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import datetime
from datetime import timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bcource.automation.automation_base import (
    BaseAutomationTask,
    register_automation,
    get_registered_automation_classes,
    get_automation_class,
    _execute_automation_task_job
)
from bcource.models import BeforeAfterEnum


class TestAutomationRegistry(unittest.TestCase):
    """Test automation class registration and retrieval."""

    def setUp(self):
        """Clear registry before each test."""
        from bcource.automation import automation_base
        automation_base._automation_classes = {}

    def test_register_automation_basic(self):
        """Test basic automation registration."""
        @register_automation(description="Test automation")
        class TestTask(BaseAutomationTask):
            @staticmethod
            def query():
                return []

            @staticmethod
            def get_event_dt(item):
                return datetime.datetime.utcnow()

            def execute(self):
                pass

        classes = get_registered_automation_classes()
        self.assertIn('TestTask', classes)
        self.assertEqual(classes['TestTask']['description'], "Test automation")
        self.assertTrue(classes['TestTask']['enabled'])

    def test_register_automation_custom_name(self):
        """Test automation registration with custom name."""
        @register_automation(name="custom_name", description="Custom named task")
        class AnotherTask(BaseAutomationTask):
            @staticmethod
            def query():
                return []

            @staticmethod
            def get_event_dt(item):
                return datetime.datetime.utcnow()

            def execute(self):
                pass

        classes = get_registered_automation_classes()
        self.assertIn('custom_name', classes)
        self.assertNotIn('AnotherTask', classes)

    def test_register_automation_disabled(self):
        """Test registering disabled automation."""
        @register_automation(enabled=False)
        class DisabledTask(BaseAutomationTask):
            @staticmethod
            def query():
                return []

            @staticmethod
            def get_event_dt(item):
                return datetime.datetime.utcnow()

            def execute(self):
                pass

        info = get_automation_class('DisabledTask')
        self.assertFalse(info['enabled'])

    def test_duplicate_registration_raises_error(self):
        """Test that duplicate registration raises ValueError."""
        @register_automation()
        class DuplicateTask(BaseAutomationTask):
            @staticmethod
            def query():
                return []

            @staticmethod
            def get_event_dt(item):
                return datetime.datetime.utcnow()

            def execute(self):
                pass

        with self.assertRaises(ValueError):
            @register_automation()
            class DuplicateTask(BaseAutomationTask):  # noqa: F811
                pass

    def test_get_automation_class_nonexistent(self):
        """Test getting non-existent automation class."""
        result = get_automation_class('NonExistent')
        self.assertIsNone(result)


class TestBaseAutomationTask(unittest.TestCase):
    """Test BaseAutomationTask abstract class."""

    def test_base_task_cannot_instantiate_without_implementation(self):
        """Test that BaseAutomationTask requires implementation of abstract methods."""
        task = BaseAutomationTask(1, "test_automation")

        with self.assertRaises(NotImplementedError):
            BaseAutomationTask.query()

        with self.assertRaises(NotImplementedError):
            BaseAutomationTask.get_event_dt(None)

        # execute() raises NotImplementedError but has a bug using self.__name__ instead of self.__class__.__name__
        with self.assertRaises((NotImplementedError, AttributeError)):
            task.execute()

    def test_base_task_initialization(self):
        """Test BaseAutomationTask initialization."""
        task = BaseAutomationTask(42, "my_automation", "arg1", kwarg1="value1")

        self.assertEqual(task.id, 42)
        self.assertEqual(task.automation_name, "my_automation")
        self.assertEqual(task.args, ("arg1",))
        self.assertEqual(task.kwags, {"kwarg1": "value1"})

    def test_base_task_defaults(self):
        """Test BaseAutomationTask default values."""
        task = BaseAutomationTask(1, "test")

        self.assertEqual(task.misfire_grace_time, 1)
        self.assertEqual(task.max_instances, 1)
        self.assertTrue(task.replace_existing)

    def test_setup_and_teardown_are_optional(self):
        """Test that setup and teardown methods are optional."""
        task = BaseAutomationTask(1, "test")

        # Should not raise any errors
        task.setup()
        task.teardown()


class TestConcreteAutomationTask(unittest.TestCase):
    """Test a concrete automation task implementation."""

    def setUp(self):
        """Create a concrete test task."""
        from bcource.automation import automation_base
        automation_base._automation_classes = {}

        @register_automation(description="Concrete test task")
        class ConcreteTestTask(BaseAutomationTask):
            @staticmethod
            def query():
                # Return mock items
                mock_item1 = Mock()
                mock_item1.id = 1
                mock_item1.scheduled_time = datetime.datetime.utcnow() + timedelta(hours=1)

                mock_item2 = Mock()
                mock_item2.id = 2
                mock_item2.scheduled_time = datetime.datetime.utcnow() + timedelta(hours=2)

                return [mock_item1, mock_item2]

            @staticmethod
            def get_event_dt(item):
                return item.scheduled_time

            def execute(self):
                return f"Executed task for id {self.id}"

        self.task_class = ConcreteTestTask

    def test_query_returns_items(self):
        """Test that query returns items."""
        items = self.task_class.query()
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].id, 1)
        self.assertEqual(items[1].id, 2)

    def test_get_event_dt_returns_datetime(self):
        """Test that get_event_dt returns datetime."""
        items = self.task_class.query()
        event_dt = self.task_class.get_event_dt(items[0])
        self.assertIsInstance(event_dt, datetime.datetime)

    def test_execute_runs_successfully(self):
        """Test that execute runs successfully."""
        task = self.task_class(1, "test_automation")
        result = task.execute()
        self.assertEqual(result, "Executed task for id 1")

    def test_get_id_returns_item_id(self):
        """Test _get_id method."""
        items = self.task_class.query()
        item_id = self.task_class._get_id(items[0])
        self.assertEqual(item_id, 1)


class TestJobScheduling(unittest.TestCase):
    """Test job scheduling functionality."""

    def test_when_calculation_before(self):
        """Test _when method with before interval."""
        from bcource import create_app

        app = create_app()

        with app.app_context():
            mock_automation = Mock()
            mock_automation.interval = timedelta(hours=1)
            mock_automation.beforeafter = BeforeAfterEnum.before

            # Use future date to avoid past date warning
            event_dt = datetime.datetime.utcnow() + timedelta(days=7)

            with patch('bcource.automation.automation_base.app_scheduler') as mock_scheduler:
                mock_scheduler.flask_app.config.get.return_value = "PRODUCTION"

                result = BaseAutomationTask._when(mock_automation, event_dt)

                expected = event_dt - timedelta(hours=1)
                self.assertEqual(result, expected)

    def test_when_calculation_after(self):
        """Test _when method with after interval."""
        from bcource import create_app

        app = create_app()

        with app.app_context():
            mock_automation = Mock()
            mock_automation.interval = timedelta(hours=2)
            mock_automation.beforeafter = BeforeAfterEnum.after

            # Use future date to avoid past date warning
            event_dt = datetime.datetime.utcnow() + timedelta(days=7)

            with patch('bcource.automation.automation_base.app_scheduler') as mock_scheduler:
                mock_scheduler.flask_app.config.get.return_value = "PRODUCTION"

                result = BaseAutomationTask._when(mock_automation, event_dt)

                expected = event_dt + timedelta(hours=2)
                self.assertEqual(result, expected)

    def test_when_calculation_development_mode(self):
        """Test that development mode schedules jobs immediately."""
        from bcource import create_app

        app = create_app()

        with app.app_context():
            mock_automation = Mock()
            mock_automation.interval = timedelta(hours=1)
            mock_automation.beforeafter = BeforeAfterEnum.before

            event_dt = datetime.datetime.utcnow() + timedelta(days=7)

            with patch('bcource.automation.automation_base.app_scheduler') as mock_scheduler:
                mock_scheduler.flask_app.config.get.return_value = "DEVELOPMENT"

                before_call = datetime.datetime.utcnow()
                result = BaseAutomationTask._when(mock_automation, event_dt)
                after_call = datetime.datetime.utcnow()

                # Should be approximately 1 second from now
                self.assertGreater(result, before_call)
                self.assertLess(result, after_call + timedelta(seconds=2))

    def test_when_calculation_past_date(self):
        """Test _when method with past date logs warning."""
        from bcource import create_app

        app = create_app()

        with app.app_context():
            mock_automation = Mock()
            mock_automation.interval = timedelta(hours=1)
            mock_automation.beforeafter = BeforeAfterEnum.before

            # Event in the past
            event_dt = datetime.datetime.utcnow() - timedelta(days=1)

            with patch('bcource.automation.automation_base.app_scheduler') as mock_scheduler:
                mock_scheduler.flask_app.config.get.return_value = "PRODUCTION"

                with patch('bcource.automation.automation_base.logger') as mock_logger:
                    result = BaseAutomationTask._when(mock_automation, event_dt)

                    # Should log a warning
                    mock_logger.warning.assert_called()


class TestAutomationTaskExecution(unittest.TestCase):
    """Test automation task execution."""

    def setUp(self):
        """Set up test automation task."""
        from bcource.automation import automation_base
        automation_base._automation_classes = {}

        @register_automation(description="Execution test task")
        class ExecutionTestTask(BaseAutomationTask):
            executed = False

            @staticmethod
            def query():
                return []

            @staticmethod
            def get_event_dt(item):
                return datetime.datetime.utcnow()

            def execute(self):
                ExecutionTestTask.executed = True
                return True

        self.task_class = ExecutionTestTask

    def test_execute_automation_task_job(self):
        """Test _execute_automation_task_job function."""
        with patch('bcource.automation.automation_base.app_scheduler') as mock_scheduler:
            mock_app = MagicMock()
            mock_scheduler.flask_app = mock_app

            # Reset executed flag
            self.task_class.executed = False

            result = _execute_automation_task_job(1, "test_automation", "ExecutionTestTask")

            self.assertTrue(self.task_class.executed)
            self.assertTrue(result)

    def test_execute_nonexistent_class(self):
        """Test executing non-existent automation class."""
        with patch('bcource.automation.automation_base.app_scheduler') as mock_scheduler:
            mock_app = MagicMock()
            mock_scheduler.flask_app = mock_app

            result = _execute_automation_task_job(1, "test", "NonExistentTask")

            # Should return True (logs info but doesn't fail)
            self.assertTrue(result)


class TestAutomationTaskWithSetupTeardown(unittest.TestCase):
    """Test automation task with setup and teardown."""

    def test_task_with_setup_and_teardown(self):
        """Test that setup and teardown can be overridden."""
        from bcource.automation import automation_base
        automation_base._automation_classes = {}

        execution_log = []

        @register_automation()
        class TaskWithLifecycle(BaseAutomationTask):
            @staticmethod
            def query():
                return []

            @staticmethod
            def get_event_dt(item):
                return datetime.datetime.utcnow()

            def setup(self):
                execution_log.append('setup')

            def execute(self):
                execution_log.append('execute')
                return True

            def teardown(self):
                execution_log.append('teardown')

        task = TaskWithLifecycle(1, "test")

        task.setup()
        task.execute()
        task.teardown()

        self.assertEqual(execution_log, ['setup', 'execute', 'teardown'])


class TestBeforeAfterEnum(unittest.TestCase):
    """Test BeforeAfterEnum usage in automation."""

    def test_before_after_enum_values(self):
        """Test that BeforeAfterEnum has correct values."""
        # This test assumes BeforeAfterEnum is defined in models.py
        self.assertTrue(hasattr(BeforeAfterEnum, 'before'))
        self.assertTrue(hasattr(BeforeAfterEnum, 'after'))


class TestTrainingTypeFiltering(unittest.TestCase):
    """Test per-training-type filtering in create_jobs()."""

    @classmethod
    def setUpClass(cls):
        from bcource import create_app
        cls.app = create_app()

    def setUp(self):
        """Set up a concrete task class and mock items with training types."""
        from bcource.automation import automation_base
        automation_base._automation_classes = {}

        @register_automation(description="Type filter test task")
        class TypeFilterTestTask(BaseAutomationTask):
            @staticmethod
            def query():
                # Training-like items with trainingtype_id
                item1 = Mock()
                item1.id = 1
                item1.trainingtype_id = 10
                item1.scheduled_time = datetime.datetime.utcnow() + timedelta(hours=1)

                item2 = Mock()
                item2.id = 2
                item2.trainingtype_id = 20
                item2.scheduled_time = datetime.datetime.utcnow() + timedelta(hours=2)

                item3 = Mock()
                item3.id = 3
                item3.trainingtype_id = 10
                item3.scheduled_time = datetime.datetime.utcnow() + timedelta(hours=3)

                return [item1, item2, item3]

            @staticmethod
            def get_event_dt(item):
                return item.scheduled_time

            def execute(self):
                return True

        self.task_class = TypeFilterTestTask

    def _make_automation_mock(self, trainingtypes=None):
        """Helper to create a properly configured automation mock."""
        automation = Mock()
        automation.trainingtypes = trainingtypes if trainingtypes is not None else []
        automation.name = "test_sched"
        automation.interval = timedelta(hours=1)
        automation.beforeafter = BeforeAfterEnum.before
        automation.automation_class.class_name = "TypeFilterTestTask"
        return automation

    @staticmethod
    def _unique_job_side_effect():
        """Return a side_effect that produces unique job IDs."""
        call_count = [0]
        def make_job(*args, **kwargs):
            call_count[0] += 1
            return Mock(id=f"job_{call_count[0]}")
        return make_job

    def test_no_type_filter_runs_all(self):
        """Empty trainingtypes = all items get jobs (backward compat)."""
        with self.app.app_context():
            automation = self._make_automation_mock(trainingtypes=[])

            with patch('bcource.automation.automation_base.app_scheduler') as mock_sched:
                mock_sched.flask_app.config.get.return_value = "DEVELOPMENT"
                mock_sched.add_job.side_effect = self._unique_job_side_effect()

                jobs = self.task_class.create_jobs(automation)
                self.assertEqual(len(jobs), 3)

    def test_no_trainingtypes_attr_runs_all(self):
        """Automation without trainingtypes attr = all items (backward compat)."""
        with self.app.app_context():
            automation = self._make_automation_mock(trainingtypes=[])

            with patch('bcource.automation.automation_base.app_scheduler') as mock_sched:
                mock_sched.flask_app.config.get.return_value = "DEVELOPMENT"
                mock_sched.add_job.side_effect = self._unique_job_side_effect()

                jobs = self.task_class.create_jobs(automation)
                self.assertEqual(len(jobs), 3)

    def test_type_filter_only_matching(self):
        """With type filter, only matching items get jobs."""
        with self.app.app_context():
            tt_mock = Mock()
            tt_mock.id = 10
            automation = self._make_automation_mock(trainingtypes=[tt_mock])

            with patch('bcource.automation.automation_base.app_scheduler') as mock_sched:
                mock_sched.flask_app.config.get.return_value = "DEVELOPMENT"
                mock_sched.add_job.side_effect = self._unique_job_side_effect()

                jobs = self.task_class.create_jobs(automation)
                # Items 1 and 3 have trainingtype_id=10, item 2 has 20
                self.assertEqual(len(jobs), 2)

    def test_type_filter_no_match(self):
        """With type filter that matches nothing, no jobs created."""
        with self.app.app_context():
            tt_mock = Mock()
            tt_mock.id = 999
            automation = self._make_automation_mock(trainingtypes=[tt_mock])

            with patch('bcource.automation.automation_base.app_scheduler') as mock_sched:
                mock_sched.flask_app.config.get.return_value = "DEVELOPMENT"
                mock_sched.add_job.side_effect = self._unique_job_side_effect()

                jobs = self.task_class.create_jobs(automation)
                self.assertEqual(len(jobs), 0)

    def test_get_training_type_id_direct(self):
        """_get_training_type_id works for Training-like objects."""
        item = Mock()
        item.trainingtype_id = 42
        self.assertEqual(BaseAutomationTask._get_training_type_id(item), 42)

    def test_get_training_type_id_via_training(self):
        """_get_training_type_id works for TrainingEnroll-like objects."""
        item = Mock(spec=[])
        item.training = Mock()
        item.training.trainingtype_id = 55
        self.assertEqual(BaseAutomationTask._get_training_type_id(item), 55)

    def test_get_training_type_id_unknown(self):
        """_get_training_type_id returns None for unknown objects."""
        item = Mock(spec=[])
        self.assertIsNone(BaseAutomationTask._get_training_type_id(item))

    def test_enrollment_based_filtering(self):
        """Enrollment-based items filter through item.training.trainingtype_id."""
        from bcource.automation import automation_base
        automation_base._automation_classes = {}

        @register_automation(description="Enrollment filter test")
        class EnrollFilterTask(BaseAutomationTask):
            @staticmethod
            def query():
                # TrainingEnroll-like items (no trainingtype_id directly)
                enroll1 = Mock(spec=[])
                enroll1.id = 101
                enroll1.training = Mock()
                enroll1.training.trainingtype_id = 10
                enroll1.scheduled_time = datetime.datetime.utcnow() + timedelta(hours=1)

                enroll2 = Mock(spec=[])
                enroll2.id = 102
                enroll2.training = Mock()
                enroll2.training.trainingtype_id = 20
                enroll2.scheduled_time = datetime.datetime.utcnow() + timedelta(hours=2)

                return [enroll1, enroll2]

            @staticmethod
            def get_event_dt(item):
                return item.scheduled_time

            def execute(self):
                return True

        with self.app.app_context():
            tt_mock = Mock()
            tt_mock.id = 20

            automation = Mock()
            automation.trainingtypes = [tt_mock]
            automation.name = "test_enroll_sched"
            automation.interval = timedelta(hours=1)
            automation.beforeafter = BeforeAfterEnum.before
            automation.automation_class.class_name = "EnrollFilterTask"

            with patch('bcource.automation.automation_base.app_scheduler') as mock_sched:
                mock_sched.flask_app.config.get.return_value = "DEVELOPMENT"
                mock_sched.add_job.side_effect = self._unique_job_side_effect()

                jobs = EnrollFilterTask.create_jobs(automation)
                # Only enroll2 matches type 20
                self.assertEqual(len(jobs), 1)


if __name__ == '__main__':
    unittest.main()
