# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bcource is a Flask-based training scheduling and management system for managing training courses, student enrollments, waitlists, and automated notifications. The application uses Flask-Security for authentication, SQLAlchemy for database access (MySQL), and APScheduler for automated task execution.

## Environment Setup

### Python Environment

The project uses Python 3.12 with pip and `requirements.txt` for dependency management:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

All configuration is environment-based via a `.env` file in the project root. Copy from `.env.example` if available and configure:
- Database connection strings (MySQL for main app and postal codes)
- Flask settings (SECRET_KEY, SERVER_NAME, etc.)
- Mail server settings (SMTP)
- AWS credentials (for SMS via SNS)
- Flask-Security settings (2FA, password policies)
- BCourse application defaults

## Development Commands

### Running the Application

```bash
# Development mode (uses console mail backend)
python run.py
```

The application runs on:
- Development: `http://0.0.0.0:5001`
- Testing with SSL: `https://0.0.0.0:5002`

Environment modes:
- `ENVIRONMENT=DEVELOPMENT` - Immediate automation execution, console email backend
- `ENVIRONMENT=PRODUCTION` - Scheduled automation, SMTP email backend

### Running the Scheduler

The scheduler must run as a separate process for automated tasks (reminders, waitlist management):

```bash
python run_scheduler.py
```

The scheduler uses a socket-based lock to prevent multiple instances (host/port configured via `BCOURSE_LOCK_HOST` and `BCOURSE_LOCK_PORT`).

### Running Tests

```bash
# Run all tests
cd test
../.venv/bin/python -m unittest discover -v

# Run specific test module
cd test
../.venv/bin/python -m unittest test_automation -v

# Run specific test class
cd test
../.venv/bin/python -m unittest test_automation.TestAutomationRegistry -v

# Run specific test method
cd test
../.venv/bin/python -m unittest test_automation.TestAutomationRegistry.test_register_automation_basic -v
```

Note: Tests reference `.venv/bin/python` directly.

### Database Migrations

```bash
# Initialize migrations (already done)
flask db init

# For multi-database setup (main + postalcodes)
flask db init --multidb

# Create migration
flask db migrate -m "description"

# Apply migrations
flask db upgrade

# Downgrade
flask db downgrade
```

### Database Dump

```bash
./dump.sh
```

## Architecture

### Application Structure

The application follows a modular Flask blueprint architecture:

- **bcource/__init__.py** - Application factory (`create_app()`) and core initialization
- **config.py** - Configuration loaded from environment variables via .env
- **run.py** - Application entry point
- **run_scheduler.py** - Scheduler daemon entry point

### Directory Structure

```
bcource/
├── __init__.py           - Application factory and initialization
├── models.py             - All database models
├── helpers.py            - Utility functions and template helpers
├── messages.py           - Email and message system
├── sms_util.py          - SMS functionality (AWS SNS)
├── filters.py           - Jinja template filters
├── menus.py             - Navigation menu structure
├── myformfields.py      - Custom form fields
├── admin/               - Flask-Admin customization
├── admin_api/           - REST API with Swagger UI (Flask-RESTX)
├── api/                 - API endpoints
├── automation/          - Automation framework and tasks
├── home/                - Landing pages blueprint
├── policy/              - Policy validation framework
├── scheduler/           - Scheduler UI and management
├── students/            - Student management blueprint
├── training/            - Training management blueprint
├── user/                - User account management blueprint
├── templates/           - Jinja templates
└── static/              - Static assets (CSS, JS, images)
```

### Core Modules (Blueprints)

- **home** - Landing pages, privacy policy, terms
- **user** - User profile management, account deletion, impersonation
- **students** - Student management, enrollment views
- **training** - Training course management, event scheduling
- **admin** - Flask-Admin interface for database management
- **admin_api** - REST API with Swagger UI for admin operations (Flask-RESTX)
- **scheduler** - Scheduler views and management
- **api** - API endpoints

### Key Subsystems

#### Automation System (`bcource/automation/`)

Extensible task automation framework built on APScheduler. See `bcource/automation/README.md` for detailed documentation.

Key concepts:
- **BaseAutomationTask**: Abstract base class for automation tasks
- **@register_automation**: Decorator to register automation classes
- **Required methods**: `query()`, `get_event_dt()`, `execute()`
- Development mode executes jobs immediately; production mode respects scheduling

Built-in automation tasks:
- StudentReminderTask - Send reminder emails to enrolled students
- TrainerReminderTask - Send reminder emails to trainers
- AutomaticWaitList - Automatically process waitlist invitations
- StudentOpenSpotReminder - Notify students of available spots

#### Policy System (`bcource/policy/`)

Rule-based validation framework using the PolicyBase metaclass pattern. Policies are composable validation rules applied to training enrollments and business logic.

- **base.py** - PolicyBase metaclass and validation infrastructure
- **rules.py** - Individual validation rules
- **policies.py** - Composed policies for different training types

#### Message System (`bcource/messages.py`)

Centralized messaging system for emails, SMS, and internal messages:
- **SystemMessage** - Base class for email/message composition using Content templates
- **SendEmail** - Email delivery with iCal attachment support
- **Content model** - Database-backed message templates with tag-based retrieval
- **SMS Support** - AWS SNS integration via `bcource/sms_util.py` for 2FA and notifications
  - Rate limiting per number (configurable hourly/daily limits)
  - Cooldown period between messages
  - Development mode uses test phone numbers

#### Admin API (`bcource/admin_api/`)

REST API for training and enrollment management with auto-generated Swagger UI. Built with Flask-RESTX.

- **Swagger UI**: `/admin-api/docs` (requires login as db-admin with 2FA first)
- **Auth**: `admin_required` decorator — checks authenticated + active + `db-admin` role + 2FA enabled (mirrors `accessible_as_admin()` from Flask-Admin)
- **CSRF**: Exempted for the blueprint (`csrf.exempt(admin_api_bp)` in `__init__.py`)

**Authentication — JWT Tokens:**

The API supports both session auth (browser) and JWT Bearer tokens (scripts/CLI).

To obtain a token:
```bash
curl -X POST https://<host>/admin-api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "..."}'
# Returns: {"token": "eyJ...", "expires_in": 86400}
```

To use the token:
```bash
curl https://<host>/admin-api/trainings/ \
  -H "Authorization: Bearer <token>"
```

Via Swagger UI (`/admin-api/docs`):
1. Use `POST /auth/token` with credentials to get a token
2. Click the **Authorize** button (lock icon, top right)
3. Enter `Bearer <token>` and click Authorize
4. All subsequent requests will use the token

Token details:
- Signed with `SECRET_KEY` using HS256 (configurable via `JWT_ALGORITHM`)
- Expires after 24 hours by default (configurable via `JWT_EXPIRATION_SECONDS`)
- Requires the user to have `db-admin` role, 2FA enabled, and active account

Files:
- **api.py** - Blueprint, Api instance, namespace registration
- **auth.py** - `admin_required` decorator
- **serializers.py** - Flask-RESTX model definitions for Swagger
- **trainings.py** - Training CRUD + the shared `ns` namespace
- **training_events.py** - Event CRUD under trainings (imports `ns` from trainings.py)
- **enrollments.py** - Enrollment management + bulk operations (imports `ns` from trainings.py)
- **students.py** - Student search (read-only)
- **locations.py** - Location list (read-only)
- **training_types.py** - Training type list (read-only)

Key design decisions:
- All three training-related files share one `trainings` namespace (defined in `trainings.py`)
- Enrollment endpoints call business logic from `bcource/students/common.py` — never duplicate that logic
- Practice scoping: all queries filter by `Practice.default_row()`

## Business Logic

This section documents the critical business rules, validations, and side effects throughout the application. **Any new code (API endpoints, views, commands) MUST respect these rules by calling the existing functions rather than manipulating the database directly.**

### Enrollment System

All enrollment business logic lives in **`bcource/students/common.py`**. Always use these functions:

| Function | Transition | Side Effects |
|----------|-----------|-------------|
| `enroll_common(training, user)` | → `enrolled` or `waitlist` | Email + trainer notification; auto-determines status based on capacity |
| `deroll_common(training, user, admin=False)` | Deletes enrollment | Email + trainer notification; cascades waitlist invites when `admin=False` |
| `invite_from_waitlist(enrollment)` | `waitlist` → `waitlist-invited` | Email + SMS + trainer notification; sets `invite_date` |
| `deinvite_from_waitlist(enrollment)` | `waitlist-invited` → `waitlist-invite-expired` | Email + trainer notification |
| `enroll_from_waitlist(enrollment)` | `waitlist-invited` → `enrolled` | Confirmation email + trainer notification |

#### Enrollment Statuses

| Status | Meaning | Counts Against Capacity |
|--------|---------|:-----------------------:|
| `enrolled` | Actively enrolled | Yes |
| `waitlist` | Waiting for spot (training was full) | No |
| `waitlist-invited` | Invitation sent, awaiting response | Yes |
| `waitlist-invite-expired` | Invitation expired (no response) | No |
| `waitlist-declined` | Student rejected invitation | No |
| `force-off-waitlist` | Transient: admin forced enrollment | N/A (immediately becomes enrolled) |

**Capacity formula:** `spots_available = max_participants - count(enrolled + waitlist-invited)`

#### Status Transitions

```
New enrollment (enroll_common):
  spots available? → enrolled
  training full?   → waitlist

waitlist:
  invite action         → waitlist-invited  (invite_from_waitlist)
  force-enroll action   → force-off-waitlist → enrolled (enroll_common)

waitlist-invited:
  student accepts       → enrolled  (enroll_from_waitlist)
  student declines      → waitlist-declined  (+ cascades invitation to next eligible)
  invitation expires    → waitlist-invite-expired  (AutomaticWaitList automation)
  admin de-invites      → waitlist-invite-expired  (deinvite_from_waitlist)
  admin returns to list → waitlist  (silent, no notification)

waitlist-invite-expired / waitlist-declined:
  can re-enroll via enroll_common (treated as fresh enrollment)
```

#### Enrollment Validations (enforced by `enroll_common`)

1. Student must not already be enrolled (unless status is `waitlist-invite-expired`, `waitlist-declined`, or `force-off-waitlist`)
2. Training must not have started (ANY event with `start_time < now()` blocks enrollment)
3. Student must exist in the current practice
4. Student must have `studentstatus.name == "active"`
5. Unique constraint: `(student_id, training_id)` — one enrollment per student per training

#### De-enrollment Validations (enforced by `deroll_common`)

1. Student must be enrolled (any status)
2. Training must not have started (ANY event with `start_time < now()`)

#### Waitlist Cascade Logic

When a spot opens (student de-enrolls or invitation declined):
1. `training.waitlist_enrollments_eligeble()` finds eligible students (FIFO by `enrole_date`)
2. Each eligible student gets `invite_from_waitlist()` → email + SMS + trainer notification
3. **Admin de-enrollment (`admin=True`) does NOT cascade** — gives explicit control

#### TrainingEnroll Model Notes

- Composite primary key: `(student_id, training_id)` — not an auto-increment ID
- `uuid` field used for invitation URLs and automation job tracking
- `ical_sequence` tracks calendar update sequence numbers
- `paid` boolean flag toggled by trainers

### Policy System (`bcource/students/student_policies.py`)

Policies are attached to `TrainingType` via many-to-many relationship. A training enforces its type's policies unless `training.apply_policies == False`.

#### TrainingBookingPolicy (`max-2-sessions-4-weeks`)

- **Rule:** Student cannot book more than 2 trainings of the same type within a 28-day window
- **Window:** Centered on the new training's first event start_time
- **Enforced at:** Student self-enrollment (`scheduler_views.enroll`). NOT enforced for admin enrollment.
- **Bypassed when:** `training.apply_policies == False` or policy not attached to training type
- **Algorithm:** Binary search insertion into sorted date list, checks for 3+ bookings in any sliding window

#### CancelationPolicy (`24h-cancelation`)

- **Rule:** Student cannot cancel within 24 hours of training start
- **Enforced at:** Student self-deroll (`scheduler_views.deroll`). Does NOT block the deroll — only triggers special notification emails
- **Side effect when violated:** `EmailStudentDerolledInTrainingOutOfPolicy` + `EmailStudentDerolledInTrainingOutOfPolicyTrainer` sent
- **Bypassed when:** Training is inactive or policy not attached to training type

### Training Events

- Multiple events per training, ordered by `start_time`
- First event's `start_time` used as reference for policy validation (booking window, cancellation)
- **Training started check:** If ANY event's `start_time < now()`, enrollment and de-enrollment are blocked
- No overlap detection — same trainer or location can have overlapping events

### Student Management

- **Orphan user detection:** When the student list is loaded, users without Student records automatically get one created with default type/status/practice (`students_views.orphan_users`)
- **Only active students can enroll:** `studentstatus.name == "active"` is required
- **Status change notification:** When student status is changed to "active", `EmailStudentStatusActive` is sent
- **Deletion blocked if:** User has trainer record or has any enrollments

### Trainer Management

- Trainers belong to a practice (unique constraint: `user_id + practice_id`)
- When a user gains the `trainer` role, a Trainer record is auto-created
- When the `trainer` role is removed and no trainings assigned, the Trainer record is deleted
- Removing the role is blocked if the trainer still has training assignments

### Training Lifecycle

- **Creation:** Trainings start as `active=False` by default; must have events to be saved
- **Deactivation:** Sets `active=False`. Does NOT de-enroll students or cancel events. Training becomes hidden from student views but existing enrollments remain.
- **Deletion:** Only possible when no enrollments exist (any status)

### Automation Tasks (`bcource/automation/automation_tasks.py`)

The scheduler (`run_scheduler.py`) runs as a separate process with a socket lock to prevent multiple instances.

| Task | Trigger | Query | Action |
|------|---------|-------|--------|
| `StudentReminderTask` | Before event (configurable) | Active trainings with future events | Sends reminder email with iCal to each enrolled student |
| `TrainerReminderTask` | Before event (configurable) | Active trainings with future events | Sends reminder email to trainers |
| `AutomaticWaitList` | After `invite_date` + interval | Enrollments with `status=="waitlist-invited"` | Expires invitation → invites next eligible |
| `StudentOpenSpotReminder` | Before event (configurable) | Active trainings with spots available | Sends open spot notification; **sets `apply_policies=False`** on the training |
| `SendAttendeeListTask` | Before event (configurable) | Active trainings with enrolled students | Sends HTML attendee list to trainers |
| `DeleteTrainingTask` | After last event ends | Trainings with past events | Deletes all enrollments and the training |

### Notifications Reference

| Event | Student Email | Trainer Notification | SMS | iCal |
|-------|:------------:|:-------------------:|:---:|:----:|
| Enrolled (direct) | `EmailStudentEnrolledInTraining` | `EmailStudentEnrolled` | - | CONFIRMED |
| Enrolled (waitlist) | `EmailStudentEnrolledInTrainingWaitlist` | `EmailStudentEnrolledWaitlist` | - | TENTATIVE |
| Waitlist invited | `EmailStudentEnrolledInTrainingInvited` | SystemMessage (tag: waitlist/invited) | Yes | - |
| Invite accepted | `EmailStudentEnrolledInTrainingInviteAccepted` | SystemMessage (tag: waitlist/enrolled/accepted) | - | CONFIRMED |
| Invite expired | `EmailStudentEnrolledInTrainingDeInvited` | SystemMessage (tag: waitlist/expired) | - | - |
| De-enrolled | `EmailStudentDerolledInTraining` | `EmailStudentDerolled` | - | CANCELLED |
| De-enrolled (policy violation) | `EmailStudentDerolledInTrainingOutOfPolicy` | `EmailStudentDerolledInTrainingOutOfPolicyTrainer` | - | - |
| Student status → active | `EmailStudentStatusActive` | - | - | - |
| Training reminder | `EmailReminderIcal` | `EmailReminder` | - | CONFIRMED |
| Open spot alert | `EmailReminder` (tag: openspot) | - | - | - |
| Attendee list | - | `EmailAttendeeListReminder` | - | - |

### Critical Constraints Summary

| Constraint | Where Enforced | Consequence |
|-----------|---------------|-------------|
| Student must be active to enroll | `enroll_common()` | Enrollment rejected |
| Training must not have started | `enroll_common()`, `deroll_common()` | Action rejected |
| Max 2 trainings per 28 days (same type) | `TrainingBookingPolicy` in scheduler views only | Student enrollment blocked (admin bypasses) |
| 24h cancellation window | `CancelationPolicy` in scheduler views | De-enrollment allowed but triggers policy violation emails |
| One enrollment per student per training | DB unique constraint `(student_id, training_id)` | Insert fails |
| Cannot delete user with enrollments | `students_views.delete()` | Deletion blocked |
| Cannot delete user with trainer record | `students_views.delete()` | Deletion blocked |
| Admin de-enrollment skips waitlist cascade | `deroll_common(admin=True)` | No auto-invitation of waitlisted students |
| `StudentOpenSpotReminder` disables policies | `automation_tasks.py` | Sets `training.apply_policies=False` permanently |

### Database Models (`bcource/models.py`)

Primary models:
- **User** - Authentication via Flask-Security (email, 2FA, roles)
- **Student** - Student profiles with status and type
- **Training** - Training sessions with enrollment management
- **TrainingType** - Course types with associated policies
- **TrainingEvent** - Scheduled training events
- **TrainingEnroll** - Enrollment relationships with waitlist support
- **Trainer** - Trainer information
- **Location** - Training venue details
- **Practice** - Multi-practice support (practice-scoped data)
- **Message** - Internal message center
- **Content** - CMS-like content storage for email templates

Note: The application supports multi-practice deployments where data can be scoped to different practices.

### Multi-Database Setup

The application uses SQLAlchemy binds for multiple databases:
- **Default database**: Main application data
- **postalcodes database**: Dutch postal code lookup (separate bind)

See README.md for postal code database setup instructions.

### Configuration

All configuration is environment-based via `.env` file (see `config.py`):
- Flask settings (SECRET_KEY, DEBUG, SERVER_NAME)
- Database URIs (SQLALCHEMY_DATABASE_URI, SQLALCHEMY_BINDS_POSTALCODES)
- Mail server settings (SMTP)
- Flask-Security settings (2FA, registration, password policies)
- BCourse application defaults (practice, student types, location)
- Scheduler settings

### Custom Helpers (`bcource/helpers.py`)

- **db_datetime()** - UTC to local timezone conversion
- **format_phone_number()** - Phone number formatting
- **format_email()** - Email address formatting
- **nh3_save()** - HTML sanitization
- **config_value()** - Access config values from templates
- **MyFsModels** - Flask-Security model helpers

### Template System

- Base templates in `bcource/templates/`
- Flask-Admin customization in `bcource/templates/admin/`
- Blueprint-specific templates in each module's `templates/` directory
- Uses Flask-Babel for internationalization (English/Dutch)
- Mobile support via Flask-Mobility

### Static Assets

- Global static files in `bcource/static/`
- Blueprint-specific static files in each module's `static/` directory
- Custom fonts in `bcource/static/fonts/`

## Common Development Patterns

### Creating a New Automation Task

```python
from bcource.automation.automation_base import BaseAutomationTask, register_automation

@register_automation(
    name="task_name",
    description="Description",
    enabled=True
)
class MyTask(BaseAutomationTask):
    @staticmethod
    def query():
        # Return items to process
        return Model.query.filter(...).all()

    @staticmethod
    def get_event_dt(item):
        # Return when to execute
        return item.scheduled_time

    def execute(self):
        # Execution logic
        pass
```

### Sending System Messages

```python
from bcource.messages import SystemMessage

msg = SystemMessage(
    envelop_to=user,
    CONTENT_TAG='template_tag',
    **template_vars
)
msg.send()
```

### Working with Multi-Practice Data

Models with `GetAll` mixin support practice-scoped queries:

```python
# Get data for specific practice
items = TrainingType.get_all(practice='practice_shortname')

# Get default practice
practice = Practice.default_row()
```

### Accessing Configuration in Code

```python
from bcource.helpers import config_value as cv

value = cv('DEFAULT_PRACTICE')
```

## Testing

Tests are located in `test/` directory. The codebase currently has minimal test coverage.

Test coverage:
- **test_automation.py** - Tests for the automation system (21 tests)
- **test_messages.py** - Tests for the messaging system (26 tests)

Test strategies:
- **test/WAITLIST_TEST_STRATEGY.md** - Comprehensive functional test strategy for waitlist functionality

## Documentation

Additional documentation is available in the following files:

### Feature Documentation
- **IMPERSONATION.md** - Complete user impersonation feature guide
- **CHANGES.md** - Changelog of recent updates and features

### Subsystem Documentation
- **bcource/automation/README.md** - Detailed automation system documentation
- **docs/WAITLIST_AUTOMATION_GUIDE.md** - Complete waitlist automation guide
- **docs/WAITLIST_QUICK_START.md** - Quick start guide for waitlist setup (5 minutes)

### Deployment Documentation
- **bcourse_docker/PRODUCTION_DEPLOYMENT.md** - Production deployment procedures

## Admin Features

### User Impersonation

Administrators with the `db-admin` role and 2FA enabled can view the application from a student's perspective. This feature is fully documented in `IMPERSONATION.md`.

Quick access path: Admin → Database Admin → User → Select user → "Impersonate User"

Key security features:
- Requires `db-admin` role and 2FA
- Cannot impersonate other admins
- Full audit logging of all impersonation sessions
- Visible red banner during impersonation with quick exit

See `IMPERSONATION.md` for complete documentation.

## Deployment

- **Dockerfile** - Docker containerization support
- **bcourse.ini** - uWSGI configuration
- **bcourse.service** - systemd service for main app
- **bcourse-scheduler.service** - systemd service for scheduler
- **wait_for_mysql.sh** - Startup dependency script for Docker
- **bcourse_docker/PRODUCTION_DEPLOYMENT.md** - Production deployment guide

## Security Notes

- Flask-Security handles authentication with 2FA support (email, authenticator app, SMS)
- CSRF protection enabled via Flask-WTF
- HTML sanitization via nh3 library
- Password hashing via argon2
- Role-based access control for admin interface
- SMS rate limiting and cooldown protection
- User impersonation audit trail (see `IMPERSONATION.md`)
