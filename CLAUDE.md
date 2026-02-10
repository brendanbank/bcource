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
