"""
Tests for the messaging system.

This module tests the message framework including:
- SystemMessage functionality
- SendEmail functionality
- Email templates and rendering
- iCalendar attachment generation
- HTML sanitization
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bcource.messages import (
    SystemMessage,
    SendEmail,
    cleanhtml,
    EmailStudentEnrolledInTraining,
    EmailStudentDerolledInTraining,
    EmailStudentEnrolledInTrainingWaitlist,
    EmailAttendeeListReminder
)


class TestCleanHTML(unittest.TestCase):
    """Test HTML cleaning utility function."""

    def test_cleanhtml_simple(self):
        """Test cleaning simple HTML."""
        html = "<p>Hello World</p>"
        result = cleanhtml(html)
        self.assertEqual(result, "Hello World")

    def test_cleanhtml_complex(self):
        """Test cleaning complex HTML."""
        html = "<div><h1>Title</h1><p>Paragraph with <strong>bold</strong> text.</p></div>"
        result = cleanhtml(html)
        self.assertIn("Title", result)
        self.assertIn("Paragraph with bold text", result)
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)

    def test_cleanhtml_empty(self):
        """Test cleaning empty HTML."""
        html = ""
        result = cleanhtml(html)
        self.assertEqual(result, "")

    def test_cleanhtml_whitespace(self):
        """Test cleaning HTML with whitespace."""
        html = "<p>   Spaced   Text   </p>"
        result = cleanhtml(html)
        self.assertIn("Spaced", result)
        self.assertIn("Text", result)


class TestSystemMessage(unittest.TestCase):
    """Test SystemMessage base class."""

    def setUp(self):
        """Set up test fixtures."""
        from bcource import create_app
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    def test_system_message_requires_recipient(self):
        """Test that SystemMessage requires envelop_to."""
        with self.assertRaises(Exception) as context:
            SystemMessage(envelop_to=None)
        self.assertIn('envelop_to cannot be None', str(context.exception))

    def test_system_message_with_body_and_subject(self):
        """Test SystemMessage with explicit body and subject."""
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.fullname = "Test User"

        msg = SystemMessage(
            envelop_to=mock_user,
            body="Test body",
            subject="Test subject"
        )

        self.assertEqual(msg.body, "Test body")
        self.assertEqual(msg.subject, "Test subject")
        self.assertEqual(msg.CONTENT_TAG, 'mail-a-form')

    def test_system_message_converts_single_recipient_to_list(self):
        """Test that single recipient is converted to list."""
        mock_user = Mock()
        mock_user.email = "test@example.com"

        with patch('bcource.messages.Content') as mock_content:
            mock_content.get_tag.return_value = "Body"
            mock_content.get_subject.return_value = "Subject"

            msg = SystemMessage(envelop_to=mock_user, CONTENT_TAG="test_tag")

            self.assertIsInstance(msg.envelop_to, list)
            self.assertEqual(len(msg.envelop_to), 1)
            self.assertEqual(msg.envelop_to[0], mock_user)

    def test_system_message_with_list_of_recipients(self):
        """Test SystemMessage with list of recipients."""
        mock_user1 = Mock()
        mock_user2 = Mock()

        with patch('bcource.messages.Content') as mock_content:
            mock_content.get_tag.return_value = "Body"
            mock_content.get_subject.return_value = "Subject"

            msg = SystemMessage(
                envelop_to=[mock_user1, mock_user2],
                CONTENT_TAG="test_tag"
            )

            self.assertEqual(len(msg.envelop_to), 2)

    def test_system_message_with_custom_taglist(self):
        """Test SystemMessage with custom taglist."""
        mock_user = Mock()

        with patch('bcource.messages.Content') as mock_content:
            mock_content.get_tag.return_value = "Body"
            mock_content.get_subject.return_value = "Subject"

            msg = SystemMessage(
                envelop_to=mock_user,
                CONTENT_TAG="test_tag",
                taglist=['custom', 'tags']
            )

            self.assertIn('custom', msg.taglist)
            self.assertIn('tags', msg.taglist)

    def test_system_message_render_subject_removes_html(self):
        """Test that render_subject removes HTML tags."""
        mock_user = Mock()

        with patch('bcource.messages.Content') as mock_content:
            mock_content.get_tag.return_value = "Body"
            mock_content.get_subject.return_value = "<strong>Subject</strong>"

            msg = SystemMessage(envelop_to=mock_user, CONTENT_TAG="test_tag")
            rendered = msg.render_subject()

            self.assertNotIn('<', rendered)
            self.assertIn('Subject', rendered)

    def test_system_message_render_body(self):
        """Test render_body returns body content."""
        mock_user = Mock()

        with patch('bcource.messages.Content') as mock_content:
            mock_content.get_tag.return_value = "Test Body Content"
            mock_content.get_subject.return_value = "Subject"

            msg = SystemMessage(envelop_to=mock_user, CONTENT_TAG="test_tag")
            rendered = msg.render_body()

            self.assertEqual(rendered, "Test Body Content")

    @patch('bcource.messages.Message.create_db_message')
    def test_system_message_send(self, mock_create_db_message):
        """Test SystemMessage send method."""
        mock_user = Mock()
        mock_user.email = "test@example.com"

        with patch('bcource.messages.Content') as mock_content:
            mock_content.get_tag.return_value = "Body"
            mock_content.get_subject.return_value = "Subject"

            msg = SystemMessage(
                envelop_to=mock_user,
                CONTENT_TAG="test_tag",
                taglist=['test']
            )
            msg.send()

            mock_create_db_message.assert_called_once()
            call_kwargs = mock_create_db_message.call_args[1]
            self.assertEqual(call_kwargs['envelop_to'], [mock_user])
            self.assertEqual(call_kwargs['tags'], ['test'])

    def test_system_message_uses_class_name_as_content_tag(self):
        """Test that class name is used as CONTENT_TAG by default."""
        mock_user = Mock()

        with patch('bcource.messages.Content') as mock_content:
            mock_content.get_tag.return_value = "Body"
            mock_content.get_subject.return_value = "Subject"

            msg = SystemMessage(envelop_to=mock_user)

            self.assertEqual(msg.CONTENT_TAG, 'SystemMessage')

    def test_system_message_with_kwargs(self):
        """Test SystemMessage passes kwargs to template."""
        mock_user = Mock()

        with patch('bcource.messages.Content') as mock_content:
            mock_content.get_tag.return_value = "Body"
            mock_content.get_subject.return_value = "Subject"

            msg = SystemMessage(
                envelop_to=mock_user,
                CONTENT_TAG="test_tag",
                custom_var="value"
            )

            self.assertIn('custom_var', msg.kwargs)
            self.assertEqual(msg.kwargs['custom_var'], 'value')


class TestSendEmail(unittest.TestCase):
    """Test SendEmail class."""

    def setUp(self):
        """Set up test fixtures."""
        from bcource import create_app
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    def test_send_email_adds_email_tag(self):
        """Test that SendEmail adds 'email' tag."""
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.fullname = "Test User"

        with patch('bcource.messages.Content') as mock_content:
            mock_content.get_tag.return_value = "Body"
            mock_content.get_subject.return_value = "Subject"

            with patch('bcource.messages.security.datastore.find_user') as mock_find:
                mock_system_user = Mock()
                mock_system_user.email = "system@example.com"
                mock_system_user.fullname = "System"
                mock_find.return_value = mock_system_user

                msg = SendEmail(envelop_to=mock_user, CONTENT_TAG="test_tag")

                self.assertIn('email', msg.taglist)

    @patch('bcource.messages.Message.create_db_message')
    @patch('bcource.messages.EmailMessage')
    def test_send_email_sends_to_all_recipients(self, mock_email_msg, mock_create_db):
        """Test that SendEmail sends to all recipients."""
        mock_user1 = Mock()
        mock_user1.email = "user1@example.com"
        mock_user1.fullname = "User One"

        mock_user2 = Mock()
        mock_user2.email = "user2@example.com"
        mock_user2.fullname = "User Two"

        with patch('bcource.messages.Content') as mock_content:
            mock_content.get_tag.return_value = "Body"
            mock_content.get_subject.return_value = "Subject"

            with patch('bcource.messages.security.datastore.find_user') as mock_find:
                mock_system_user = Mock()
                mock_system_user.email = "system@example.com"
                mock_system_user.fullname = "System"
                mock_find.return_value = mock_system_user

                msg = SendEmail(
                    envelop_to=[mock_user1, mock_user2],
                    CONTENT_TAG="test_tag"
                )

                # Mock the email message instance
                mock_msg_instance = Mock()
                mock_email_msg.return_value = mock_msg_instance

                msg.send()

                # Should create 2 email messages (one per recipient)
                self.assertEqual(mock_email_msg.call_count, 2)
                self.assertEqual(mock_msg_instance.send.call_count, 2)

    def test_send_email_render_body(self):
        """Test email_render_body returns body."""
        mock_user = Mock()

        with patch('bcource.messages.Content') as mock_content:
            mock_content.get_tag.return_value = "Email Body"
            mock_content.get_subject.return_value = "Subject"

            msg = SendEmail(
                envelop_to=mock_user,
                body="Custom Body",
                subject="Custom Subject"
            )

            rendered = msg.email_render_body()
            self.assertEqual(rendered, "Custom Body")

    def test_send_email_process_attachment_default(self):
        """Test default process_attachment does nothing."""
        mock_user = Mock()
        mock_msg = Mock()

        with patch('bcource.messages.Content') as mock_content:
            mock_content.get_tag.return_value = "Body"
            mock_content.get_subject.return_value = "Subject"

            msg = SendEmail(envelop_to=mock_user, CONTENT_TAG="test")
            result = msg.process_attachment(mock_msg)

            self.assertEqual(result, mock_msg)


class TestEmailWithICalAttachments(unittest.TestCase):
    """Test email classes with iCal attachments."""

    def setUp(self):
        """Set up test fixtures."""
        from bcource import create_app
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create mock enrollment with training and events
        self.mock_user = Mock()
        self.mock_user.email = "student@example.com"
        self.mock_user.fullname = "Student Name"

        self.mock_student = Mock()
        self.mock_student.user = self.mock_user

        self.mock_location = Mock()
        self.mock_location.ical_adress = "Test Location, 123 Main St"

        self.mock_event = Mock()
        self.mock_event.start_time = datetime.datetime(2025, 6, 15, 10, 0, 0)
        self.mock_event.end_time = datetime.datetime(2025, 6, 15, 12, 0, 0)
        self.mock_event.location = self.mock_location

        self.mock_training = Mock()
        self.mock_training.name = "Test Training"
        self.mock_training.trainingevents = [self.mock_event]

        self.mock_enrollment = Mock()
        self.mock_enrollment.uuid = "test-uuid-123"
        self.mock_enrollment.sequence_next = 1
        self.mock_enrollment.student = self.mock_student
        self.mock_enrollment.training = self.mock_training

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    @patch('bcource.messages.Message.create_db_message')
    @patch('bcource.messages.EmailMessage')
    def test_email_enrolled_creates_ical_attachment(self, mock_email_msg, mock_create_db):
        """Test EmailStudentEnrolledInTraining creates iCal attachment."""
        with patch('bcource.messages.security.datastore.find_user') as mock_find:
            mock_system_user = Mock()
            mock_system_user.email = "system@example.com"
            mock_system_user.fullname = "System"
            mock_find.return_value = mock_system_user

            mock_msg_instance = Mock()
            mock_email_msg.return_value = mock_msg_instance

            msg = EmailStudentEnrolledInTraining(
                envelop_to=self.mock_user,
                body="You're enrolled",
                subject="Enrollment Confirmation",
                enrollment=self.mock_enrollment
            )

            msg.send()

            # Check that attachment was called
            mock_msg_instance.attach.assert_called_once()
            call_args = mock_msg_instance.attach.call_args[0]
            self.assertIn('Test Training', call_args[0])
            self.assertIn('.ics', call_args[0])
            self.assertEqual(call_args[2], 'text/calendar')

    @patch('bcource.messages.Message.create_db_message')
    @patch('bcource.messages.EmailMessage')
    def test_email_derolled_creates_cancellation_ical(self, mock_email_msg, mock_create_db):
        """Test EmailStudentDerolledInTraining creates cancellation iCal."""
        with patch('bcource.messages.security.datastore.find_user') as mock_find:
            mock_system_user = Mock()
            mock_system_user.email = "system@example.com"
            mock_system_user.fullname = "System"
            mock_find.return_value = mock_system_user

            mock_msg_instance = Mock()
            mock_email_msg.return_value = mock_msg_instance

            msg = EmailStudentDerolledInTraining(
                envelop_to=self.mock_user,
                body="You're derolled",
                subject="Enrollment Cancelled",
                enrollment=self.mock_enrollment
            )

            msg.send()

            # Check that attachment was called
            mock_msg_instance.attach.assert_called_once()
            call_args = mock_msg_instance.attach.call_args[0]
            self.assertIn('canceled', call_args[0])
            self.assertIn('.ics', call_args[0])

    @patch('bcource.messages.Message.create_db_message')
    @patch('bcource.messages.EmailMessage')
    def test_email_waitlist_creates_tentative_ical(self, mock_email_msg, mock_create_db):
        """Test EmailStudentEnrolledInTrainingWaitlist creates tentative iCal."""
        with patch('bcource.messages.security.datastore.find_user') as mock_find:
            mock_system_user = Mock()
            mock_system_user.email = "system@example.com"
            mock_system_user.fullname = "System"
            mock_find.return_value = mock_system_user

            mock_msg_instance = Mock()
            mock_email_msg.return_value = mock_msg_instance

            msg = EmailStudentEnrolledInTrainingWaitlist(
                envelop_to=self.mock_user,
                body="You're on waitlist",
                subject="Waitlist Confirmation",
                enrollment=self.mock_enrollment
            )

            msg.send()

            # Check that attachment was called
            mock_msg_instance.attach.assert_called_once()

    def test_email_enrolled_raises_without_enrollment(self):
        """Test that enrollment email raises error without enrollment."""
        with self.assertRaises(Exception) as context:
            msg = EmailStudentEnrolledInTraining(
                envelop_to=self.mock_user,
                body="Test",
                subject="Test"
            )
            mock_msg = Mock()
            msg.process_attachment(mock_msg)

        self.assertIn('enrollment', str(context.exception))


class TestEmailAttendeeListReminder(unittest.TestCase):
    """Test EmailAttendeeListReminder class."""

    def setUp(self):
        """Set up test fixtures."""
        from bcource import create_app
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create mock data
        self.mock_user1 = Mock()
        self.mock_user1.first_name = "Alice"
        self.mock_user1.last_name = "Smith"
        self.mock_user1.fullname = "Alice Smith"
        self.mock_user1.phone_number = "+31612345678"
        self.mock_user1.country = "NL"

        self.mock_student1 = Mock()
        self.mock_student1.user = self.mock_user1

        self.mock_enrollment1 = Mock()
        self.mock_enrollment1.student = self.mock_student1

        self.mock_user2 = Mock()
        self.mock_user2.first_name = "Bob"
        self.mock_user2.last_name = "Johnson"
        self.mock_user2.fullname = "Bob Johnson"
        self.mock_user2.phone_number = None
        self.mock_user2.country = "NL"

        self.mock_student2 = Mock()
        self.mock_student2.user = self.mock_user2

        self.mock_enrollment2 = Mock()
        self.mock_enrollment2.student = self.mock_student2

        self.mock_training = Mock()
        self.mock_training.name = "Advanced Training"

        self.mock_trainer = Mock()
        self.mock_trainer.email = "trainer@example.com"
        self.mock_trainer.fullname = "Trainer Name"

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    def test_attendee_list_generates_html_table(self):
        """Test that attendee list generates HTML table."""
        with patch('bcource.messages.security.datastore.find_user') as mock_find:
            mock_system_user = Mock()
            mock_system_user.email = "system@example.com"
            mock_system_user.fullname = "System"
            mock_find.return_value = mock_system_user

            msg = EmailAttendeeListReminder(
                envelop_to=self.mock_trainer,
                training=self.mock_training,
                enrollments=[self.mock_enrollment1, self.mock_enrollment2]
            )

            rendered = msg.email_render_body()

            # Check table structure
            self.assertIn('<table', rendered)
            self.assertIn('</table>', rendered)
            self.assertIn('Advanced Training', rendered)

            # Check student names
            self.assertIn('Alice Smith', rendered)
            self.assertIn('Bob Johnson', rendered)

            # Check phone number handling
            self.assertIn('N/A', rendered)  # For user without phone

    def test_attendee_list_sorts_by_name(self):
        """Test that attendee list is sorted by name."""
        with patch('bcource.messages.security.datastore.find_user') as mock_find:
            mock_system_user = Mock()
            mock_system_user.email = "system@example.com"
            mock_system_user.fullname = "System"
            mock_find.return_value = mock_system_user

            msg = EmailAttendeeListReminder(
                envelop_to=self.mock_trainer,
                training=self.mock_training,
                enrollments=[self.mock_enrollment2, self.mock_enrollment1]  # Reverse order
            )

            rendered = msg.email_render_body()

            # Alice should appear before Bob in the output
            alice_pos = rendered.find('Alice Smith')
            bob_pos = rendered.find('Bob Johnson')
            self.assertLess(alice_pos, bob_pos)

    def test_attendee_list_shows_total_count(self):
        """Test that total enrolled count is shown."""
        with patch('bcource.messages.security.datastore.find_user') as mock_find:
            mock_system_user = Mock()
            mock_system_user.email = "system@example.com"
            mock_system_user.fullname = "System"
            mock_find.return_value = mock_system_user

            msg = EmailAttendeeListReminder(
                envelop_to=self.mock_trainer,
                training=self.mock_training,
                enrollments=[self.mock_enrollment1, self.mock_enrollment2]
            )

            rendered = msg.email_render_body()

            self.assertIn('2 student(s)', rendered)

    def test_attendee_list_empty_enrollments(self):
        """Test attendee list with no enrollments."""
        with patch('bcource.messages.security.datastore.find_user') as mock_find:
            mock_system_user = Mock()
            mock_system_user.email = "system@example.com"
            mock_system_user.fullname = "System"
            mock_find.return_value = mock_system_user

            msg = EmailAttendeeListReminder(
                envelop_to=self.mock_trainer,
                training=self.mock_training,
                enrollments=[]
            )

            rendered = msg.email_render_body()

            self.assertIn('No training or enrollments found', rendered)


if __name__ == '__main__':
    unittest.main()
