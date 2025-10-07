# Waitlist Automation Guide

## Overview

The waitlist automation system automatically manages waitlist invitations and expirations using APScheduler. When a student is invited from the waitlist, an automated job is scheduled to expire that invitation if not accepted within a configured timeframe.

## Current Implementation

### AutomaticWaitList Task

Located in: `bcource/automation/automation_tasks.py`

```python
@register_automation(description="Automatic Waitlist.")
class AutomaticWaitList(BaseAutomationTask):
    def execute(self):
        # 1. Find the enrollment by UUID
        enrollment = TrainingEnroll().query.filter(
            TrainingEnroll.uuid == self.id
        ).first()

        # 2. Check if still in invited state
        if enrollment.status != "waitlist-invited":
            logging.warn(f'{enrollment} status is not waitlist-invited')
        else:
            # 3. Expire the invitation
            deinvite_from_waitlist(enrollment)

        # 4. Invite next eligible students
        waitlist_enrollments_eligeble = enrollment.training.waitlist_enrollments_eligeble()
        for enrollment in waitlist_enrollments_eligeble:
            invite_from_waitlist(enrollment)

        return True
```

## How It Works

### 1. Invitation Creation

When a student is invited from the waitlist (`invite_from_waitlist()`):

```python
def invite_from_waitlist(enrollment: TrainingEnroll):
    # Set status and timestamp
    enrollment.status = "waitlist-invited"
    enrollment.invite_date = datetime.utcnow()

    # Send invitation email
    system_msg.EmailStudentEnrolledInTrainingInvited(
        envelop_to=enrollment.student.user,
        enrollment=enrollment
    ).send()

    # Notify trainers
    system_msg.SystemMessage(
        envelop_to=enrollment.training.trainer_users,
        body=f"<p>{enrollment.student.user.fullname} has been invited...</p>",
        subject=f"Waitlist Invitation Sent - {enrollment.training.name}",
        taglist=['waitlist', 'invited']
    ).send()

    db.session.commit()
```

**This triggers an automation job that:**
- Queries for all enrollments with status "waitlist-invited"
- Schedules a job for each invitation based on `invite_date` + configured interval
- Job ID format: `{automation.name}/{enrollment.uuid}/{environment}`

### 2. Job Scheduling

The automation framework automatically creates jobs when `renew_automations()` is called:

```python
def renew_automations():
    automations = AutomationSchedule().query.filter(
        AutomationSchedule.active == True
    ).all()

    for automation in automations:
        # Get the automation class
        cls = get_automation_class(automation.automation_class.class_name)['class']

        # Create jobs for all matching items
        cls.create_jobs(automation)
```

### 3. Job Execution

When the scheduled time arrives:
1. `AutomaticWaitList.execute()` is called with the enrollment UUID
2. If invitation hasn't been accepted, it expires (`deinvite_from_waitlist()`)
3. Next eligible students are automatically invited
4. Process continues until no spots or no eligible students remain

### 4. Expiration Logic

```python
def deinvite_from_waitlist(enrollment: TrainingEnroll):
    # Mark as expired
    enrollment.status = "waitlist-invite-expired"
    enrollment.invite_date = datetime.utcnow()

    # Notify student
    system_msg.EmailStudentEnrolledInTrainingDeInvited(
        envelop_to=enrollment.student.user,
        enrollment=enrollment
    ).send()

    # Notify trainers
    system_msg.SystemMessage(
        envelop_to=enrollment.training.trainer_users,
        body=f"The waitlist invitation for {enrollment.student.user.fullname} has expired...",
        subject=f"Waitlist Invitation Expired - {enrollment.training.name}",
        taglist=['waitlist', 'expired']
    ).send()

    db.session.commit()
```

## Configuration

### Database Setup

The automation must be configured in the database via the Flask-Admin interface or programmatically:

#### Step 1: Verify AutomationClasses Entry

The automation class is auto-registered when the scheduler starts:

```python
# Automatically created by init_app_scheduler()
AutomationClasses(
    class_name="AutomaticWaitList",
    description="Automatic Waitlist.",
    module_path="bcource.automation.automation_tasks",
    qualified_name="bcource.automation.automation_tasks.AutomaticWaitList"
)
```

#### Step 2: Create AutomationSchedule Entry

You need to create a schedule entry for when invitations should expire:

```python
from bcource.models import AutomationSchedule, AutomationClasses, BeforeAfterEnum, EventsEnum
from datetime import timedelta

# Get the AutomaticWaitList class
waitlist_class = AutomationClasses.query.filter_by(
    class_name="AutomaticWaitList"
).first()

# Create a schedule to expire invitations 48 hours after they're sent
schedule = AutomationSchedule(
    name="waitlist_invitation_expiry",
    automation_class=waitlist_class,
    beforeafter=BeforeAfterEnum.after,  # After the invitation
    events=EventsEnum.invited,           # Event type
    interval=timedelta(hours=48),        # 48 hours to respond
    active=True
)

db.session.add(schedule)
db.session.commit()
```

**Configuration Parameters:**
- **name**: Unique identifier for this schedule
- **automation_class**: Links to AutomaticWaitList
- **beforeafter**: `BeforeAfterEnum.after` (after invitation)
- **events**: Event type that triggers timing
- **interval**: Time to wait before expiration (e.g., 48 hours)
- **active**: Enable/disable the automation

### Via Flask-Admin Interface

1. Navigate to: `http://your-domain/admin/automationschedule/`
2. Click "Create"
3. Fill in the form:
   - **Name**: `waitlist_invitation_expiry`
   - **Automation Class**: Select "AutomaticWaitList"
   - **Before/After**: Select "after"
   - **Events**: Select appropriate event type
   - **Interval**: Enter `2 00:00:00` (2 days) or `0 48:00:00` (48 hours)
   - **Active**: Check the box
4. Click "Save"

## Testing the Automation

### Manual Testing

```python
from bcource import create_app, db
from bcource.models import Training, Student, TrainingEnroll
from bcource.students.common import invite_from_waitlist
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    # Get a training with waitlist
    training = Training.query.filter_by(name="Your Training").first()

    # Get waitlist enrollments
    waitlist = TrainingEnroll.query.filter_by(
        training_id=training.id,
        status="waitlist"
    ).first()

    # Manually invite (this should create automation job)
    invite_from_waitlist(waitlist)

    # Check scheduled jobs
    from bcource.automation.scheduler import app_scheduler
    jobs = app_scheduler.get_jobs()
    for job in jobs:
        print(f"Job: {job.id}, Next run: {job.next_run_time}")
```

### Development Mode Testing

In development mode (`ENVIRONMENT=DEVELOPMENT`), jobs execute immediately (1 second delay):

```python
# In .env
ENVIRONMENT=DEVELOPMENT

# Jobs will execute ~1 second after scheduling
# Useful for testing without waiting for actual intervals
```

### Production Mode Testing

In production, jobs respect the configured intervals:

```python
# In .env
ENVIRONMENT=PRODUCTION

# Jobs execute at scheduled time (e.g., 48 hours later)
```

## Monitoring

### Check Active Jobs

```python
from bcource.automation.scheduler import app_scheduler

# List all scheduled jobs
jobs = app_scheduler.get_jobs()
for job in jobs:
    print(f"ID: {job.id}")
    print(f"  Next run: {job.next_run_time}")
    print(f"  Function: {job.func_ref}")
    print(f"  Args: {job.args}")
```

### Job ID Format

```
{automation_name}/{enrollment_uuid}/{environment}
```

Example:
```
waitlist_invitation_expiry/550e8400-e29b-41d4-a716-446655440000/DEVELOPMENT
```

### Logs

The automation logs key events:

```python
# Invitation sent
logger.info(f'invited user: {enrollment.student.user} from training: {enrollment.training}')

# Invitation expired
logger.info(f'deinvited user: {enrollment.student.user} from training: {enrollment.training}')

# Job execution
logger.warning(f'Started AutomaticWaitList id: {id} automation_name: {automation_name}')
```

## Troubleshooting

### Issue: Jobs Not Being Created

**Check 1: Automation registered**
```python
from bcource.automation.automation_base import get_registered_automation_classes

classes = get_registered_automation_classes()
print('AutomaticWaitList' in classes)  # Should be True
```

**Check 2: Database entry exists**
```python
from bcource.models import AutomationClasses

cls = AutomationClasses.query.filter_by(class_name="AutomaticWaitList").first()
print(cls)  # Should not be None
```

**Check 3: Schedule is active**
```python
from bcource.models import AutomationSchedule

schedule = AutomationSchedule.query.filter_by(
    name="waitlist_invitation_expiry"
).first()
print(f"Active: {schedule.active}")  # Should be True
```

**Check 4: Scheduler is running**
```bash
# Check if run_scheduler.py is running
ps aux | grep run_scheduler.py

# Should see a process like:
# python run_scheduler.py
```

### Issue: Jobs Execute Immediately in Production

**Cause**: Environment variable not set correctly

**Fix**:
```bash
# Check .env file
grep ENVIRONMENT .env

# Should be:
ENVIRONMENT=PRODUCTION

# Not:
ENVIRONMENT=DEVELOPMENT
```

### Issue: Jobs Schedule in the Past

**Cause**: `invite_date` is in the past or interval calculation is wrong

**Check**:
```python
enrollment = TrainingEnroll.query.filter_by(
    status="waitlist-invited"
).first()

print(f"Invite date: {enrollment.invite_date}")
print(f"Current time: {datetime.utcnow()}")

# Scheduled time should be: invite_date + interval
```

**Log output**:
```
WARNING: job is scheduler in the past: 2025-06-10 15:00:00
         task will probably be ignored event_dt: 2025-06-08 15:00:00
```

### Issue: Multiple Jobs for Same Enrollment

**Cause**: Jobs not being replaced properly

**Check**:
```python
jobs = app_scheduler.get_jobs()
job_ids = [job.id for job in jobs]

# Count occurrences of same UUID
from collections import Counter
counts = Counter([jid.split('/')[1] for jid in job_ids if '/' in jid])
duplicates = {k: v for k, v in counts.items() if v > 1}
print(f"Duplicates: {duplicates}")
```

**Fix**: Ensure `replace_existing=True` in job configuration (already default)

### Issue: Invitations Not Cascading

**Symptom**: First invitation expires but next student not invited

**Debug**:
```python
# In AutomaticWaitList.execute()
enrollment = TrainingEnroll().query.filter(
    TrainingEnroll.uuid == self.id
).first()

print(f"Found enrollment: {enrollment}")
print(f"Status: {enrollment.status}")

# Check eligible students
waitlist_eligible = enrollment.training.waitlist_enrollments_eligeble()
print(f"Eligible students: {list(waitlist_eligible)}")
```

**Common causes**:
1. No more students on waitlist
2. Training at or over capacity
3. Students not active
4. Status not "waitlist"

## Advanced Configuration

### Custom Expiration Intervals

Different intervals for different training types:

```python
# VIP trainings: 7 days to respond
vip_schedule = AutomationSchedule(
    name="waitlist_vip_expiry",
    automation_class=waitlist_class,
    beforeafter=BeforeAfterEnum.after,
    interval=timedelta(days=7),
    active=True
)

# Regular trainings: 48 hours
regular_schedule = AutomationSchedule(
    name="waitlist_regular_expiry",
    automation_class=waitlist_class,
    beforeafter=BeforeAfterEnum.after,
    interval=timedelta(hours=48),
    active=True
)
```

### Disable Automation Temporarily

```python
# Via code
schedule = AutomationSchedule.query.filter_by(
    name="waitlist_invitation_expiry"
).first()
schedule.active = False
db.session.commit()

# Refresh automations to remove jobs
from bcource.automation.scheduler_ops import renew_automations
renew_automations()
```

### Manual Invitation Without Automation

If you need to invite without triggering expiration automation:

```python
from bcource.students.common import invite_from_waitlist

# Invite student
invite_from_waitlist(enrollment)

# Manually remove the scheduled job
from bcource.automation.scheduler import app_scheduler
job_id = f"waitlist_invitation_expiry/{enrollment.uuid}/PRODUCTION"
app_scheduler.remove_job(job_id)
```

## Best Practices

### 1. Monitor Job Queue Size

```python
# Add to monitoring
def check_job_queue():
    jobs = app_scheduler.get_jobs()
    waitlist_jobs = [j for j in jobs if 'AutomaticWaitList' in str(j.func_ref)]

    if len(waitlist_jobs) > 100:
        logger.warning(f"Large waitlist job queue: {len(waitlist_jobs)}")

    return len(waitlist_jobs)
```

### 2. Set Reasonable Intervals

- **Too short**: Students don't have time to respond
- **Too long**: Spots stay unfilled unnecessarily
- **Recommended**: 24-72 hours depending on training urgency

### 3. Handle Edge Cases

- Student accepts just before expiration
- Training cancelled with pending invitations
- Multiple derolls in quick succession

### 4. Test Before Production

```python
# Test with short interval in development
test_schedule = AutomationSchedule(
    name="waitlist_test",
    interval=timedelta(seconds=30),  # 30 second test
    active=True
)
```

### 5. Backup Jobs Regularly

```python
# Export scheduled jobs
jobs = app_scheduler.get_jobs()
job_data = [{
    'id': job.id,
    'next_run': job.next_run_time,
    'args': job.args
} for job in jobs]

import json
with open('jobs_backup.json', 'w') as f:
    json.dump(job_data, f, default=str)
```

## Performance Considerations

### Query Optimization

The automation queries all "waitlist-invited" enrollments frequently:

```python
# Ensure index exists
CREATE INDEX idx_training_enroll_status
ON training_enroll(status);

# Also useful
CREATE INDEX idx_training_enroll_invite_date
ON training_enroll(invite_date);
```

### Job Cleanup

Old jobs are automatically removed when:
- Enrollment status changes from "waitlist-invited"
- `renew_automations()` runs and finds stale jobs
- Job completes execution

## Integration with Other Systems

### Email Notifications

Four emails sent during automation:

1. **Invitation sent** (to student)
   - Template: `EmailStudentEnrolledInTrainingInvited`
   - Tag: `invited`

2. **Invitation sent** (to trainers)
   - Template: `SystemMessage`
   - Tags: `waitlist`, `invited`

3. **Invitation expired** (to student)
   - Template: `EmailStudentEnrolledInTrainingDeInvited`
   - Tag: `devited` (sic)

4. **Invitation expired** (to trainers)
   - Template: `SystemMessage`
   - Tags: `waitlist`, `expired`

### Cascade Logic

When invitation expires:
1. Mark as expired
2. Send notifications
3. Calculate eligible students
4. Invite next student(s)
5. Schedule new expiration jobs

This continues until:
- No more students on waitlist
- Training reaches capacity
- No eligible students remain

## Scaling Considerations

### High-Volume Waitlists

For trainings with 100+ waitlisted students:

1. **Batch Processing**: Invite multiple students at once
2. **Stagger Invitations**: Add small delays between invitations
3. **Rate Limit Emails**: Prevent SMTP overload

```python
# Example: Invite in batches with delays
def invite_batch_from_waitlist(training, batch_size=5):
    eligible = training.waitlist_enrollments_eligeble()

    for i, enrollment in enumerate(list(eligible)[:batch_size]):
        # Stagger invitations by 1 minute each
        delay = timedelta(minutes=i)
        schedule_invitation(enrollment, delay)
```

### Distributed Systems

If running multiple app instances:
- Use centralized database for job storage (already configured)
- Only run ONE scheduler instance (`run_scheduler.py`)
- Socket lock prevents multiple schedulers (`BCOURSE_LOCK_HOST/PORT`)

## Security Considerations

### Prevent Job Manipulation

- Job IDs include environment to separate dev/prod
- UUID-based identification prevents enumeration
- Status checks prevent invalid state transitions

### Email Abuse Prevention

- Rate limit invitation emails per student
- Log all automation actions
- Monitor for unusual patterns

```python
# Example rate limit check
def check_invitation_rate(student, limit=3, window_hours=24):
    recent = TrainingEnroll.query.filter(
        TrainingEnroll.student_id == student.id,
        TrainingEnroll.status == 'waitlist-invited',
        TrainingEnroll.invite_date > datetime.utcnow() - timedelta(hours=window_hours)
    ).count()

    return recent < limit
```

## Summary

The waitlist automation provides:
- ✅ Automatic invitation expiration
- ✅ Cascade invitation to next students
- ✅ Email notifications to all parties
- ✅ Configurable time intervals
- ✅ Development/production mode support
- ✅ Robust error handling
- ✅ Database-backed job persistence

Key maintenance tasks:
- Monitor job queue size
- Review logs for errors
- Adjust intervals based on acceptance rates
- Keep scheduler running (`run_scheduler.py`)
- Regular database backups
