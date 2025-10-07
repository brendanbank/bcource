# Waitlist Automation - Quick Start Guide

## Setup in 5 Minutes

### 1. Verify Scheduler is Running

```bash
# Check if scheduler process is running
ps aux | grep run_scheduler.py

# If not running, start it:
python run_scheduler.py
```

### 2. Configure Automation (One-Time Setup)

**Via Python Console:**

```python
from bcource import create_app, db
from bcource.models import AutomationSchedule, AutomationClasses, BeforeAfterEnum
from datetime import timedelta

app = create_app()
with app.app_context():
    # Get AutomaticWaitList class
    waitlist_class = AutomationClasses.query.filter_by(
        class_name="AutomaticWaitList"
    ).first()

    # Create schedule (48-hour expiration)
    schedule = AutomationSchedule(
        name="waitlist_invitation_expiry",
        automation_class=waitlist_class,
        beforeafter=BeforeAfterEnum.after,
        interval=timedelta(hours=48),  # 48 hours to accept
        active=True
    )

    db.session.add(schedule)
    db.session.commit()
    print("✓ Waitlist automation configured!")
```

**Or via Flask-Admin:**

1. Go to: `http://your-domain/admin/automationschedule/`
2. Click **Create**
3. Fill in:
   - Name: `waitlist_invitation_expiry`
   - Automation Class: `AutomaticWaitList`
   - Before/After: `after`
   - Interval: `2 00:00:00` (2 days)
   - Active: ✓
4. Click **Save**

### 3. Test It Works

```python
from bcource import create_app
from bcource.automation.scheduler import app_scheduler

app = create_app()
with app.app_context():
    # List all scheduled jobs
    jobs = app_scheduler.get_jobs()
    for job in jobs:
        print(f"✓ Job: {job.id}")

    # Should see waitlist jobs if any invitations are pending
```

## Common Operations

### Check Active Invitations

```python
from bcource.models import TrainingEnroll

# Find all pending invitations
invitations = TrainingEnroll.query.filter_by(
    status="waitlist-invited"
).all()

for inv in invitations:
    print(f"{inv.student.user.fullname} - {inv.training.name}")
    print(f"  Invited: {inv.invite_date}")
```

### Manually Invite Student

```python
from bcource.students.common import invite_from_waitlist
from bcource.models import TrainingEnroll

# Get a waitlist enrollment
enrollment = TrainingEnroll.query.filter_by(
    status="waitlist"
).first()

# Invite (automatically creates expiration job)
invite_from_waitlist(enrollment)
```

### Check Scheduled Jobs

```bash
# In Python console
from bcource.automation.scheduler import app_scheduler

jobs = app_scheduler.get_jobs()
print(f"Total jobs: {len(jobs)}")

for job in jobs:
    if "AutomaticWaitList" in str(job.func_ref):
        print(f"Waitlist job: {job.id}")
        print(f"  Runs at: {job.next_run_time}")
```

### Enable/Disable Automation

```python
from bcource.models import AutomationSchedule

schedule = AutomationSchedule.query.filter_by(
    name="waitlist_invitation_expiry"
).first()

# Disable
schedule.active = False
db.session.commit()

# Enable
schedule.active = True
db.session.commit()

# Refresh jobs
from bcource.automation.scheduler_ops import renew_automations
renew_automations()
```

## Development vs Production

### Development Mode (Immediate Execution)

```bash
# In .env
ENVIRONMENT=DEVELOPMENT
```

Jobs execute ~1 second after scheduling (great for testing)

### Production Mode (Scheduled Execution)

```bash
# In .env
ENVIRONMENT=PRODUCTION
```

Jobs execute at scheduled time (e.g., 48 hours later)

## Troubleshooting Quick Fixes

### Issue: No Jobs Being Created

```python
# 1. Check automation is registered
from bcource.automation.automation_base import get_registered_automation_classes
print("AutomaticWaitList" in get_registered_automation_classes())

# 2. Check database entry
from bcource.models import AutomationClasses
cls = AutomationClasses.query.filter_by(class_name="AutomaticWaitList").first()
print(f"Found: {cls}")

# 3. Check schedule is active
from bcource.models import AutomationSchedule
schedule = AutomationSchedule.query.filter_by(name="waitlist_invitation_expiry").first()
print(f"Active: {schedule.active if schedule else 'NOT FOUND'}")

# 4. Force refresh
from bcource.automation.scheduler_ops import renew_automations
renew_automations()
```

### Issue: Jobs Not Running

```bash
# Check scheduler process
ps aux | grep run_scheduler.py

# If not found, start it:
python run_scheduler.py &

# Check logs
tail -f /var/log/bcource-scheduler.log  # or wherever logs are
```

### Issue: Invitations Not Expiring

```python
# Check if jobs exist for invitation
from bcource.models import TrainingEnroll
from bcource.automation.scheduler import app_scheduler

enrollment = TrainingEnroll.query.filter_by(
    status="waitlist-invited"
).first()

if enrollment:
    job_id = f"waitlist_invitation_expiry/{enrollment.uuid}/PRODUCTION"
    job = app_scheduler.get_job(job_id)
    print(f"Job found: {job}")
    if job:
        print(f"Next run: {job.next_run_time}")
```

## Configuration Options

### Change Expiration Time

```python
from bcource.models import AutomationSchedule
from datetime import timedelta

schedule = AutomationSchedule.query.filter_by(
    name="waitlist_invitation_expiry"
).first()

# Change to 24 hours
schedule.interval = timedelta(hours=24)
db.session.commit()

# Refresh jobs
from bcource.automation.scheduler_ops import renew_automations
renew_automations()
```

### Create Multiple Schedules

```python
# Short window for urgent trainings
urgent = AutomationSchedule(
    name="waitlist_urgent_expiry",
    automation_class=waitlist_class,
    interval=timedelta(hours=12),
    active=True
)

# Long window for regular trainings
regular = AutomationSchedule(
    name="waitlist_regular_expiry",
    automation_class=waitlist_class,
    interval=timedelta(hours=72),
    active=True
)

db.session.add_all([urgent, regular])
db.session.commit()
```

## Monitoring Commands

### Check System Health

```bash
# Python console
from bcource.automation.scheduler import app_scheduler
from bcource.models import AutomationSchedule, TrainingEnroll

# 1. Scheduler status
print(f"Scheduler running: {app_scheduler.running}")

# 2. Active schedules
active = AutomationSchedule.query.filter_by(active=True).count()
print(f"Active schedules: {active}")

# 3. Pending invitations
pending = TrainingEnroll.query.filter_by(status="waitlist-invited").count()
print(f"Pending invitations: {pending}")

# 4. Scheduled jobs
jobs = len(app_scheduler.get_jobs())
print(f"Scheduled jobs: {jobs}")
```

### View Recent Activity

```python
from bcource.models import TrainingEnroll
from datetime import datetime, timedelta

# Invitations sent in last 24 hours
recent = TrainingEnroll.query.filter(
    TrainingEnroll.status.in_(["waitlist-invited", "waitlist-invite-expired"]),
    TrainingEnroll.invite_date > datetime.utcnow() - timedelta(hours=24)
).all()

print(f"Recent activity (24h): {len(recent)}")
for enrollment in recent:
    print(f"  {enrollment.student.user.fullname} - {enrollment.status}")
```

## Email Testing

### Check Email Configuration

```python
# In development mode
from flask import current_app
print(f"Mail backend: {current_app.config.get('MAIL_BACKEND')}")
# Should be 'console' in development

# In production
print(f"Mail server: {current_app.config.get('MAIL_SERVER')}")
print(f"Mail port: {current_app.config.get('MAIL_PORT')}")
```

### Test Email Sending

```python
from bcource.messages import EmailStudentEnrolledInTrainingInvited
from bcource.models import TrainingEnroll

enrollment = TrainingEnroll.query.filter_by(
    status="waitlist-invited"
).first()

if enrollment:
    # Test sending invitation email
    email = EmailStudentEnrolledInTrainingInvited(
        envelop_to=enrollment.student.user,
        enrollment=enrollment
    )
    email.send()
    print("✓ Test email sent")
```

## Best Practices

### ✅ DO
- Keep scheduler running at all times
- Monitor job queue size regularly
- Set reasonable expiration intervals (24-72 hours)
- Test in development before deploying
- Back up database regularly

### ❌ DON'T
- Run multiple scheduler instances
- Set very short intervals in production (<12 hours)
- Manually modify job queue without backup
- Disable automation without notifying students
- Skip testing after configuration changes

## Quick Reference Table

| Action | Command |
|--------|---------|
| **Start scheduler** | `python run_scheduler.py` |
| **Check scheduler** | `ps aux \| grep run_scheduler` |
| **List jobs** | `app_scheduler.get_jobs()` |
| **Refresh jobs** | `renew_automations()` |
| **Enable schedule** | `schedule.active = True` |
| **Disable schedule** | `schedule.active = False` |
| **Change interval** | `schedule.interval = timedelta(hours=X)` |
| **Manual invite** | `invite_from_waitlist(enrollment)` |
| **Check invitations** | `TrainingEnroll.query.filter_by(status="waitlist-invited")` |

## Getting Help

- **Full Documentation**: [WAITLIST_AUTOMATION_GUIDE.md](WAITLIST_AUTOMATION_GUIDE.md)
- **Test Strategy**: [WAITLIST_TEST_STRATEGY.md](../test/WAITLIST_TEST_STRATEGY.md)
- **Automation README**: `bcource/automation/README.md`
- **Logs**: Check scheduler logs for error messages
