# Waitlist Functional Test Strategy

## Overview

The waitlist functionality is a critical feature that manages training enrollment overflow. When a training reaches maximum capacity, additional students are added to a waitlist and can be invited to enroll when spots become available.

## Waitlist Workflow

### Core States
1. **waitlist** - Student is on the waitlist, waiting for a spot
2. **waitlist-invited** - Student has been invited from waitlist
3. **waitlist-invite-expired** - Invitation expired (automated)
4. **waitlist-declined** - Student declined the invitation
5. **force-off-waitlist** - Admin override to bypass waitlist
6. **enrolled** - Successfully enrolled (from waitlist or directly)

### Key Functions
- `enroll_common()` - Initial enrollment (may add to waitlist if full)
- `invite_from_waitlist()` - Invite next eligible student from waitlist
- `deinvite_from_waitlist()` - Expire an invitation
- `enroll_from_waitlist()` - Accept a waitlist invitation
- `deroll_common()` - Remove student and trigger next waitlist invitation
- `waitlist_enrollments_eligeble()` - Get eligible students for invitation
- `AutomaticWaitList` - Automated task to expire invitations

## Functional Test Scenarios

### 1. Basic Waitlist Entry

**Scenario**: Student joins waitlist when training is full
- **Setup**: Training with max_participants=5, 5 students enrolled
- **Action**: 6th student attempts to enroll
- **Expected**:
  - Student status = "waitlist"
  - Flash message: "added to the wait list"
  - EmailStudentEnrolledInTrainingWaitlist sent to student
  - EmailStudentEnrolledWaitlist sent to trainers
  - Database record created with waitlist status

**Test Data**:
```python
training = Training(max_participants=5)
enrolled_students = [Student(1-5)]  # 5 enrolled
waitlist_student = Student(6)
```

**Assertions**:
- `enrollment.status == "waitlist"`
- `training._spots_enrolled == 5`
- `training._spots_waitlist == 1`
- Email sent count == 2 (student + trainers)

---

### 2. Waitlist Invitation Flow

**Scenario**: Student is invited from waitlist when spot opens
- **Setup**: Training with 5 enrolled, 3 on waitlist, 1 student derolls
- **Action**: Student derolls, triggering waitlist invitation
- **Expected**:
  - First waitlist student status = "waitlist-invited"
  - EmailStudentEnrolledInTrainingInvited sent
  - Trainers notified of invitation
  - `invite_date` set to current time
  - Automation scheduled for invitation expiry

**Test Data**:
```python
training = Training(max_participants=5)
enrolled = [Student(1-5)]
waitlist = [Student(6), Student(7), Student(8)]  # Order matters
derolling_student = Student(1)
```

**Assertions**:
- `waitlist[0].status == "waitlist-invited"`
- `waitlist[0].invite_date != None`
- `waitlist[1].status == "waitlist"`  # Still waiting
- Email sent to Student(6)
- AutomaticWaitList job scheduled

---

### 3. Accepting Waitlist Invitation

**Scenario**: Student accepts invitation and enrolls
- **Setup**: Student with status="waitlist-invited"
- **Action**: Student accepts invitation via `enroll_from_waitlist()`
- **Expected**:
  - Status changes to "enrolled"
  - EmailStudentEnrolledInTrainingInviteAccepted sent
  - Trainers notified of acceptance
  - Enrollment count increases
  - Flash message: "successfully enrolled"

**Test Data**:
```python
enrollment = TrainingEnroll(
    student=student,
    training=training,
    status="waitlist-invited",
    invite_date=datetime.now()
)
```

**Assertions**:
- `enrollment.status == "enrolled"`
- `training._spots_enrolled` increased by 1
- Flash message contains "successfully enrolled"
- 2 emails sent (student + trainers)

---

### 4. Invitation Expiration (Automated)

**Scenario**: Waitlist invitation expires automatically
- **Setup**: Student invited 48 hours ago (or configured timeout)
- **Action**: AutomaticWaitList automation executes
- **Expected**:
  - Status changes to "waitlist-invite-expired"
  - EmailStudentEnrolledInTrainingDeInvited sent
  - Trainers notified of expiration
  - Next eligible student invited automatically

**Test Data**:
```python
enrollment = TrainingEnroll(
    status="waitlist-invited",
    invite_date=datetime.now() - timedelta(hours=48)
)
waitlist = [expired_student, next_student_1, next_student_2]
```

**Assertions**:
- `expired_student.status == "waitlist-invite-expired"`
- `next_student_1.status == "waitlist-invited"`
- 4 emails sent (2 for expired, 2 for new invite)

---

### 5. Multiple Waitlist Positions

**Scenario**: Multiple students on waitlist, spots open one by one
- **Setup**: 3 students on waitlist, 2 spots open sequentially
- **Action**:
  1. Student 1 derolls → Student 6 invited
  2. Student 2 derolls → Student 7 invited
- **Expected**:
  - Invitations sent in order of waitlist position
  - Only eligible students invited
  - Proper state transitions for each

**Test Data**:
```python
training = Training(max_participants=5)
enrolled = [Student(1-5)]
waitlist = [Student(6), Student(7), Student(8)]
```

**Test Steps**:
1. Deroll Student(1)
   - Assert: Student(6) invited
   - Assert: Student(7) still "waitlist"
2. Deroll Student(2)
   - Assert: Student(7) invited
   - Assert: Student(8) still "waitlist"

---

### 6. Waitlist Priority Calculation

**Scenario**: Calculate eligible students based on capacity
- **Setup**: Training with max_participants=10, 8 enrolled, 5 on waitlist
- **Action**: Call `waitlist_enrollments_eligeble()`
- **Expected**:
  - Returns first 2 students from waitlist
  - Order preserved (FIFO)
  - Students with expired invitations not included

**Test Data**:
```python
training = Training(max_participants=10)
enrolled = 8  # _spots_enrolled = 8
waitlist = [
    Student(9, status="waitlist"),
    Student(10, status="waitlist"),
    Student(11, status="waitlist-invite-expired"),
    Student(12, status="waitlist"),
    Student(13, status="waitlist")
]
```

**Assertions**:
- `len(eligible) == 2`  # Only 2 spots available
- `eligible[0] == Student(9)`
- `eligible[1] == Student(10)`
- Student(11) not included (expired)

---

### 7. Force Off Waitlist (Admin Override)

**Scenario**: Admin enrolls student bypassing waitlist
- **Setup**: Training at capacity, student on waitlist
- **Action**: Admin sets status="force-off-waitlist", then enrolls
- **Expected**:
  - Student enrolled despite full capacity
  - Training now over capacity
  - No automatic waitlist processing

**Test Data**:
```python
training = Training(max_participants=5)
enrolled = [Student(1-5)]
priority_student = Student(6, status="force-off-waitlist")
```

**Assertions**:
- `priority_student.status == "enrolled"`
- `training._spots_enrolled == 6`  # Over capacity
- No waitlist invitations triggered

---

### 8. Declining Waitlist Invitation

**Scenario**: Student manually declines invitation
- **Setup**: Student with status="waitlist-invited"
- **Action**: Student clicks decline (status → "waitlist-declined")
- **Expected**:
  - Status changes to "waitlist-declined"
  - Next eligible student invited
  - Trainers notified

**Test Data**:
```python
waitlist = [
    Student(6, status="waitlist-invited"),
    Student(7, status="waitlist"),
    Student(8, status="waitlist")
]
```

**Assertions**:
- `Student(6).status == "waitlist-declined"`
- `Student(7).status == "waitlist-invited"`
- Invitation email sent to Student(7)

---

### 9. Training Already Started

**Scenario**: Attempt to enroll after training has started
- **Setup**: Training with start_time in the past
- **Action**: Student attempts to enroll
- **Expected**:
  - Enrollment fails
  - Flash error: "training has already started"
  - No database changes

**Test Data**:
```python
training_event = TrainingEvent(
    start_time=datetime.now() - timedelta(hours=1)
)
training = Training(trainingevents=[training_event])
```

**Assertions**:
- `enroll_common()` returns False
- Flash message contains "already started"
- No enrollment record created

---

### 10. Student Re-enrollment After Expiration

**Scenario**: Student with expired invitation tries to re-enroll
- **Setup**: Student with status="waitlist-invite-expired"
- **Action**: Student attempts to enroll again
- **Expected**:
  - New enrollment attempt allowed
  - Previous enrollment record updated or new one created
  - Student added back to waitlist (if still full)

**Test Data**:
```python
existing_enrollment = TrainingEnroll(
    student=student,
    training=training,
    status="waitlist-invite-expired"
)
```

**Assertions**:
- Enrollment succeeds (not blocked)
- Status becomes "waitlist" or "enrolled" based on capacity
- `enrolled_user` found in `enroll_common()`

---

### 11. Inactive Student Cannot Enroll

**Scenario**: Student with inactive status attempts enrollment
- **Setup**: Student with studentstatus.name != 'active'
- **Action**: Attempt to enroll
- **Expected**:
  - Enrollment fails
  - Flash error: "Student is not active"
  - No database changes

**Test Data**:
```python
student = Student(
    studentstatus=StudentStatus(name='inactive')
)
```

**Assertions**:
- `enroll_common()` returns False
- Flash message contains "not active"

---

### 12. Deroll Triggers Cascade Invitation

**Scenario**: Derolling triggers multiple waitlist invitations
- **Setup**: Training at capacity, 5 students on waitlist, 2 deroll simultaneously
- **Action**: 2 students deroll
- **Expected**:
  - First 2 waitlist students invited
  - Proper ordering maintained
  - All notifications sent

**Test Data**:
```python
training = Training(max_participants=5)
enrolled = [Student(1-5)]
waitlist = [Student(6-10)]
derolling = [Student(1), Student(2)]
```

**Assertions**:
- `Student(6).status == "waitlist-invited"`
- `Student(7).status == "waitlist-invited"`
- `Student(8).status == "waitlist"`
- 4 invitation emails sent

---

### 13. Admin Deroll Bypasses Automation

**Scenario**: Admin derolls student without triggering waitlist
- **Setup**: Training at capacity with waitlist
- **Action**: Admin derolls with admin=True flag
- **Expected**:
  - Student removed
  - NO automatic waitlist invitations
  - Manual control maintained

**Test Data**:
```python
training = Training(max_participants=5)
enrolled = [Student(1-5)]
waitlist = [Student(6), Student(7)]
```

**Test Steps**:
```python
deroll_common(training, Student(1), admin=True)
```

**Assertions**:
- Student(1) removed
- `Student(6).status == "waitlist"`  # NOT invited
- No invitation emails sent

---

### 14. Email Notifications Complete Flow

**Scenario**: Verify all email touchpoints in waitlist flow
- **Setup**: Full enrollment flow from waitlist to enrolled
- **Action**: Complete journey: waitlist → invited → accepted
- **Expected Emails**:
  1. Student added to waitlist
  2. Trainers notified of waitlist addition
  3. Student invited from waitlist
  4. Trainers notified of invitation
  5. Student accepts invitation
  6. Trainers notified of acceptance

**Assertions**:
- Total emails sent = 6
- Each email has correct recipient
- Each email has correct content tag
- Proper taglist for filtering

---

### 15. Concurrent Invitation Handling

**Scenario**: Race condition - two students accept same spot
- **Setup**: 1 spot available, 2 invitations sent (bug scenario)
- **Action**: Both students attempt to accept
- **Expected**:
  - First acceptance succeeds
  - Second should fail gracefully
  - Database constraints enforced

**Test Data**:
```python
training = Training(max_participants=5)
enrolled = [Student(1-4)]
invited = [Student(5), Student(6)]  # Both invited (error state)
```

**Assertions**:
- One enrollment succeeds
- One fails with appropriate error
- No data corruption
- UniqueConstraint enforced (student_id, training_id)

---

## Integration Test Scenarios

### INT-1: Full Lifecycle Test
**Flow**: Enroll → Full → Waitlist → Deroll → Invite → Accept → Enrolled
- Create training with max_participants=2
- Enroll Student 1 & 2
- Enroll Student 3 (waitlist)
- Deroll Student 1
- Verify Student 3 invited
- Accept invitation
- Verify final enrollment state

### INT-2: Automation Integration Test
**Flow**: Test AutomaticWaitList automation job
- Create waitlist invitation 48 hours old
- Execute AutomaticWaitList.execute()
- Verify expiration and next invitation
- Check all notifications sent

### INT-3: Policy Integration Test
**Flow**: Waitlist with training policies
- Training with enrollment policies
- Student attempts enrollment when full
- Verify policy checks still apply to waitlist
- Verify policy checks apply when accepting invitation

---

## Edge Cases & Error Scenarios

### E-1: Waitlist with Zero Capacity Training
- Training with max_participants=0
- Student attempts to enroll
- Should fail gracefully

### E-2: Negative Capacity
- Training configuration error
- Graceful handling required

### E-3: Deleted Training with Active Waitlist
- Training deleted while waitlist exists
- Cascade delete behavior
- Notification handling

### E-4: Student Deleted with Active Invitation
- Student account deleted
- Invitation record handling
- Automation cleanup

### E-5: Rapid Sequential Derolls
- 5 students deroll in rapid succession
- Ensure all waitlist invitations sent
- No duplicate invitations

### E-6: Training Date Changes
- Training rescheduled after invitations sent
- Existing invitations handling
- Re-notification logic

---

## Performance Test Scenarios

### P-1: Large Waitlist Processing
- Training with 100+ students on waitlist
- Measure time to process `waitlist_enrollments_eligeble()`
- Ensure reasonable performance (<1 second)

### P-2: Bulk Derollment
- Remove 50 students simultaneously
- Measure waitlist invitation processing time
- Verify no database locks or deadlocks

### P-3: Concurrent Enrollment Load
- 100 simultaneous enrollment attempts
- Training with limited capacity
- Verify correct waitlist ordering

---

## Test Data Requirements

### Minimal Test Dataset
```python
# Practices
practice_default = Practice(name="Default", shortname="default")

# Locations
location_main = Location(name="Main Room", practice=practice_default)

# Student Status
status_active = StudentStatus(name="active", practice=practice_default)
status_inactive = StudentStatus(name="inactive", practice=practice_default)

# Users (10 students + 2 trainers)
users = [User(id=i, email=f"student{i}@test.com",
              fullname=f"Student {i}") for i in range(1, 11)]
trainers = [User(id=i, email=f"trainer{i}@test.com",
                 fullname=f"Trainer {i}") for i in range(11, 13)]

# Students
students = [Student(user=users[i], studentstatus=status_active,
                    practice=practice_default) for i in range(10)]

# Trainers
trainer_objs = [Trainer(user=trainers[i]) for i in range(2)]

# Training Types
training_type = TrainingType(name="Basic Training",
                             practice=practice_default)

# Training
training = Training(
    name="Test Training",
    max_participants=5,
    trainingtype=training_type,
    practice=practice_default,
    trainers=trainer_objs
)

# Training Event
event = TrainingEvent(
    training=training,
    start_time=datetime.now() + timedelta(days=7),
    end_time=datetime.now() + timedelta(days=7, hours=2),
    location=location_main
)
```

---

## Test Environment Setup

### Database Fixtures
- Clean database before each test
- Use transactions for isolation
- Rollback after each test

### Mock Configuration
- Email backend mocked for speed
- Automation scheduler mocked or isolated
- Freeze time for predictable date comparisons

### Test Utilities
```python
def create_full_training(num_students=5):
    """Create a training at capacity"""
    training = create_training(max_participants=num_students)
    for i in range(num_students):
        enroll_student(training, create_student(i))
    return training

def create_waitlist_scenario(enrolled=5, waitlist=3):
    """Create training with enrolled students and waitlist"""
    training = create_full_training(enrolled)
    waitlist_students = []
    for i in range(enrolled, enrolled + waitlist):
        student = create_student(i)
        enroll_student(training, student)  # Goes to waitlist
        waitlist_students.append(student)
    return training, waitlist_students

def assert_email_sent(recipient, content_tag):
    """Assert specific email was sent"""
    # Check mock email backend
    pass
```

---

## Success Criteria

### Functional Requirements
- ✅ All 15 functional scenarios pass
- ✅ All integration tests pass
- ✅ All edge cases handled gracefully
- ✅ No data corruption scenarios

### Non-Functional Requirements
- ✅ Performance: waitlist processing <1 second for 100 students
- ✅ Email delivery: All notifications sent within 5 seconds
- ✅ Automation: Expiration jobs execute on schedule
- ✅ Concurrency: No race conditions or deadlocks

### Code Coverage
- ✅ 90%+ coverage for waitlist functions
- ✅ 100% coverage for critical paths (invite, accept, expire)
- ✅ All error branches tested

---

## Execution Plan

### Phase 1: Unit Tests (Week 1)
- Test individual functions in isolation
- Mock dependencies
- Cover all 15 functional scenarios

### Phase 2: Integration Tests (Week 2)
- Test complete workflows
- Database integration
- Email integration
- Automation integration

### Phase 3: Edge Cases (Week 3)
- Error scenarios
- Boundary conditions
- Concurrency tests

### Phase 4: Performance Tests (Week 4)
- Load testing
- Stress testing
- Optimization based on results

---

## Maintenance & Regression

### Continuous Testing
- Run full suite on every commit
- Automated CI/CD integration
- Performance benchmarks tracked

### Regression Suite
- All bug fixes added as test cases
- Critical path tests run on deploy
- Weekly full suite execution

### Monitoring
- Production waitlist metrics
- Email delivery rates
- Automation success rates
- Error logging and alerting
