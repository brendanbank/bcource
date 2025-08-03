# Automation Module Documentation

## Overview

The automation module provides a flexible, extensible system for scheduling and executing automated tasks in the Bcourse application. It uses APScheduler for job management and provides a base framework for creating custom automation tasks.

## Architecture

### Core Components

1. **BaseAutomationTask** - Abstract base class for all automation tasks
2. **Scheduler** - Background scheduler using APScheduler
3. **Registry** - Central registry for automation classes
4. **Task Execution** - Job execution framework

### Key Files

- `automation_base.py` - Core automation framework and base classes
- `scheduler.py` - Background scheduler configuration
- `scheduler_ops.py` - Scheduler operations and initialization
- `automation_tasks.py` - Concrete automation task implementations
- `lock.py` - Distributed locking mechanism

## Usage

### Creating a New Automation Task

```python
from bcource.automation.automation_base import BaseAutomationTask, register_automation

@register_automation(
    name="my_task",
    description="Description of what this task does",
    enabled=True
)
class MyAutomationTask(BaseAutomationTask):
    
    @staticmethod
    def query():
        """Return items that need processing."""
        return MyModel.query.filter(MyModel.needs_processing == True).all()
    
    @staticmethod
    def get_event_dt(item):
        """Return the datetime when this item should be processed."""
        return item.scheduled_time
    
    def execute(self):
        """Execute the automation logic."""
        # Your automation logic here
        pass
```

### Required Methods

#### `query()` (static method)
- **Purpose**: Returns items that need processing
- **Return**: List of model instances
- **Example**: `Training.query.filter(Training.active == True).all()`

#### `get_event_dt(item)` (static method)
- **Purpose**: Returns the datetime when an item should be processed
- **Parameters**: `item` - Model instance from query()
- **Return**: `datetime` object
- **Example**: `return item.start_time`

#### `execute()` (instance method)
- **Purpose**: Contains the actual automation logic
- **Access**: `self.id`, `self.automation_name`, `self.args`, `self.kwags`
- **Example**: Send emails, update status, process data

### Optional Methods

#### `setup()` (instance method)
- **Purpose**: Optional setup before execution
- **Called**: Before `execute()`

#### `teardown()` (instance method)
- **Purpose**: Optional cleanup after execution
- **Called**: After `execute()`

## Configuration

### Scheduler Settings

```python
# Default job settings
misfire_grace_time = 1  # Seconds to wait before considering job misfired
max_instances = 1       # Maximum concurrent instances
replace_existing = True # Replace existing jobs with same ID
```

### Environment Variables

- `ENVIRONMENT` - Set to "DEVELOPMENT" for immediate execution
- `SQLALCHEMY_DATABASE_URI` - Database connection for job storage

## Built-in Tasks

### StudentReminderTask
- **Purpose**: Send reminder emails to enrolled students
- **Trigger**: Before training event start time
- **Email**: iCal invitation with training details

### TrainerReminderTask
- **Purpose**: Send reminder emails to trainers
- **Trigger**: Before training event start time
- **Email**: Training reminder notification

### AutomaticWaitList
- **Purpose**: Manage waitlist invitations automatically
- **Trigger**: When spots become available
- **Action**: Invite next person from waitlist

### StudentOpenSpotReminder
- **Purpose**: Notify students when spots become available
- **Trigger**: After waitlist processing
- **Email**: Spot availability notification

## Job Management

### Job Creation

```python
# Create job for single item
job = MyAutomationTask.create_job(item, automation)

# Create jobs for all items
jobs = MyAutomationTask.create_jobs(automation)
```

### Job Execution

Jobs are executed via the `_execute_automation_task_job` function:
1. Retrieves automation class from registry
2. Instantiates task with ID and automation name
3. Calls `execute()` method
4. Handles errors and logging

### Job Scheduling

Jobs are scheduled based on:
- **Event DateTime**: When the task should run
- **Before/After**: Relative to event time
- **Interval**: Time offset from event
- **Environment**: Immediate execution in development

## Registry System

### Registration

```python
@register_automation(
    name="custom_name",        # Optional, defaults to class name
    description="Description", # Optional
    enabled=True              # Optional, defaults to True
)
class MyTask(BaseAutomationTask):
    pass
```

### Retrieval

```python
# Get all registered automations
automations = get_registered_automation_classes()

# Get specific automation
task_class = get_automation_class("MyTask")
```

## Database Integration

### Job Storage
- Jobs are stored in the application database
- Uses SQLAlchemyJobStore for persistence
- Survives application restarts

### Job Identification
```python
str_id = f"{automation.name}/{item.id}/{environment}"
```

## Error Handling

### Misfired Jobs
- Jobs scheduled in the past are logged as warnings
- Grace period configurable via `misfire_grace_time`
- Development environment executes immediately

### Logging
- All automation activities are logged
- Uses standard Python logging
- Log level: WARNING for execution, INFO for setup

## Development vs Production

### Development Mode
- Jobs execute immediately (1 second delay)
- Useful for testing automation logic
- Set `ENVIRONMENT=DEVELOPMENT`

### Production Mode
- Jobs execute at scheduled times
- Respects event datetimes and intervals
- Set `ENVIRONMENT=PRODUCTION`

## Best Practices

### 1. Idempotency
- Ensure tasks can run multiple times safely
- Use database transactions for data changes
- Handle partial failures gracefully

### 2. Resource Management
- Use `setup()` and `teardown()` for resource cleanup
- Limit concurrent executions with `max_instances`
- Monitor memory usage in long-running tasks

### 3. Error Handling
- Log errors with context information
- Return appropriate status codes
- Handle missing data gracefully

### 4. Performance
- Keep queries efficient
- Use database indexes for query methods
- Consider pagination for large datasets

## Monitoring

### Job Status
```python
# Check job status
job = app_scheduler.get_job(job_id)
print(f"Job state: {job.next_run_time}")
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Task started")
logger.warning("Task completed with warnings")
logger.error("Task failed")
```

## Troubleshooting

### Common Issues

1. **Jobs not executing**
   - Check if scheduler is started
   - Verify job is in database
   - Check environment configuration

2. **Jobs executing multiple times**
   - Verify `max_instances = 1`
   - Check for duplicate job IDs
   - Review `replace_existing` setting

3. **Jobs executing at wrong time**
   - Verify timezone settings
   - Check `get_event_dt()` implementation
   - Review interval calculations

### Debug Mode
```python
# Enable debug logging
logging.getLogger('bcource.automation').setLevel(logging.DEBUG)
```

## Security Considerations

1. **Database Access**
   - Use read-only queries where possible
   - Validate input data
   - Use parameterized queries

2. **Email Sending**
   - Validate recipient addresses
   - Rate limit email sending
   - Log email activities

3. **Job Execution**
   - Limit job execution time
   - Monitor resource usage
   - Implement circuit breakers

## Future Enhancements

1. **Retry Logic**
   - Implement exponential backoff
   - Add retry limits
   - Handle transient failures

2. **Monitoring**
   - Add metrics collection
   - Implement health checks
   - Create dashboard

3. **Scalability**
   - Support distributed execution
   - Add job queuing
   - Implement load balancing 