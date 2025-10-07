# Changes Log

## [Unreleased] - 2025-10-07

### Added - Delete Account Feature (GDPR Right to be Forgotten)

#### New Features
- **Self-Service Account Deletion**: Users can now delete their own accounts through a menu option in the user dropdown (person icon, far right of navigation)
- **Enrollment Protection**: Users cannot delete their account if they have active training enrollments
- **Past Training Indicator**: Active enrollments list shows which trainings have already ended with an asterisk (*)
- **Multi-Step Confirmation**: 
  - Users must type "DELETE" to enable the deletion button
  - Additional browser confirmation dialog for extra safety
- **Support Notification**: Automatic email notification sent to support team when a user deletes their account, including:
  - User's full name
  - User's email address
  - User ID
  - Deletion timestamp (UTC)

#### Files Modified

##### `/bcource/user/user_views.py`
- **Added imports**: `logout_user`, `TrainingEnroll`, `Student`
- **Added route**: `/account/delete-account` (GET, POST)
  - Checks for active training enrollments
  - Validates typed confirmation ("DELETE")
  - Handles timezone-aware datetime comparisons
  - Sends notification email to support before deletion
  - Logs account deletion attempts
  - Performs logout before deletion
  - Deletes user account with proper cascade handling
  - Error handling with rollback on failure

##### `/bcource/templates/nav.html`
- **Added menu item**: "Delete Account" in user dropdown menu
  - Positioned between "Contact Support" and "Sign out"
  - Styled with red text (`text-danger`) and trash icon
  - Only visible to authenticated users
  - Separated by dividers for visual clarity

##### `/bcource/user/templates/user/delete-account.html` (New File)
- **Created confirmation page** with:
  - Warning alert for permanent action
  - List of what data will be deleted
  - Enrollment blocking logic with list of active enrollments
  - Past training indicators with (*) marker
  - Link to training scheduler for unenrollment
  - Text input requiring "DELETE" to be typed
  - JavaScript validation to enable/disable delete button
  - Responsive Bootstrap design with danger theme
  - Full internationalization support (Flask-Babel)

##### `/bcource/models.py`
- **Fixed cascade delete relationships** to properly handle user deletion:
  - `User.messages`: Added `cascade="all, delete-orphan"`
  - `Message.envelop_from`: Added `cascade="all, delete"` to backref
  - `Message.envelop_to`: Added `cascade="all, delete-orphan"`
  - `Student.user`: Added `cascade="all, delete-orphan"` to backref
  - `Trainer.user`: Added `cascade="all, delete-orphan"` to backref
  - `UserSettings.user`: Added `cascade="all, delete"` to backref

#### Technical Details

##### Security Features
1. **CSRF Protection**: Form includes CSRF token validation
2. **Authentication Required**: Route protected with `@auth_required()` decorator
3. **Double Confirmation**: Typed confirmation + browser alert
4. **Enrollment Check**: Prevents deletion if enrolled in any training
5. **Audit Logging**: All deletion attempts logged with user ID and email
6. **Error Handling**: Graceful rollback on database errors

##### Database Behavior
- Cascading deletes automatically remove:
  - Personal information (name, email, phone, address, etc.)
  - Account credentials and security settings
  - Messages (sent and received)
  - Training enrollments and history
  - Student and Trainer records
  - User settings
  - WebAuthn credentials
  - All other user associations

##### Timezone Handling
- Properly handles both timezone-aware and timezone-naive datetimes
- Compares training end times with current UTC time
- Python-side comparison to avoid Jinja2 template errors

##### Email Notifications
- Uses existing `SendEmail` helper from `bcource.messages`
- Creates support user automatically if doesn't exist
- Tagged with `['account-deletion', 'notification']` for filtering
- Sent before user deletion to preserve sender information

#### User Experience
- Clear warning about permanent deletion
- Explanation of GDPR right to be forgotten
- Visual feedback for trainings that have already ended
- Helpful links to unenroll from trainings
- Clear error messages when deletion is blocked
- Success message after deletion
- Automatic redirect to home page after deletion

#### Configuration
- Uses `BCOURSE_SUPPORT_EMAIL` from `config.py` for support notifications
- No additional configuration required

#### Testing Checklist
- [x] User with no enrollments can delete account
- [x] User with active enrollments cannot delete account
- [x] Enrollment list displays correctly with past training markers
- [x] Confirmation text "DELETE" is case-insensitive
- [x] Browser confirmation dialog appears
- [x] User is logged out after deletion
- [x] Success message appears after deletion
- [x] Related records are properly deleted (cascade)
- [x] Error handling works correctly
- [x] Menu item appears only for logged-in users
- [x] Menu item is styled correctly (red text)
- [x] Support email notification is sent
- [x] Timezone handling works correctly

#### Migration Notes
- **IMPORTANT**: Application must be restarted after model changes for cascade deletes to take effect
- No database schema changes required (cascade is handled by SQLAlchemy ORM)
- All foreign keys already have `ondelete="CASCADE"` at database level

#### Known Limitations
- Users must manually unenroll from all trainings before deletion
- Past trainings show in enrollment list (users must wait for cleanup)
- Deletion is immediate and cannot be undone

#### Future Enhancements (Not Implemented)
- Optional grace period before permanent deletion
- Data export before deletion
- Automatic unenrollment from past trainings
- Admin-level account restoration within grace period

---

### Dependencies
- No new dependencies added
- Uses existing Flask-Security, Flask-Babel, SQLAlchemy functionality

### Browser Compatibility
- Tested with modern browsers supporting ES6 JavaScript
- Requires JavaScript enabled for delete button validation

### Accessibility
- Bootstrap icons with text labels
- Form labels properly associated with inputs
- Error messages clearly displayed
- Color not the only indicator (text and icons used)

---

## Notes
- All user-facing strings use Flask-Babel `_()` function for internationalization
- Feature complies with GDPR Article 17 (Right to Erasure)
- Audit trail maintained in application logs
- Support team notified of all account deletions

---

## Chronological Changes

### 2025-10-07
- `13ef0cc` - Implement account deletion feature with confirmation and logging
- `2f73d5b` - Add EmailAttendeeListReminder enhancements for trainer notifications
- `240c02a` - Update logging in SystemMessage to use envelop_to for message delivery details
- `8ce90a1` - Enhance logging for message sending in SystemMessage and SendEmail classes

### 2025-10-06
- `b3042d1` - Add notifications for trainers on waitlist invitation status
- `34b55b9` - Add notification for trainers when a user is invited from the waitlist
- `36d00a2` - Add support contact forms and functionality
- `b718675` - Add EmailAttendeeListReminder and SendAttendeeListTask for trainer notifications

### 2025-10-05
- `af94620` - Refactor deroll function in scheduler_views.py to streamline cancellation logic
- `50789c8` - Add DeleteTrainingTask automation to manage training deletions

### 2025-08-29
- `e36ed94` - Fix typo
- `a4350d7` - Update tooltip text in scheduler_loop.html for waitlist clarity
- `73d3056` - Refactor training enrollment tooltips in scheduler_loop.html for clarity
- `ddf3af8` - Update training enrollment display logic in templates for better clarity

### 2025-08-17
- `ce28706` - Correct spelling of 'Bcource' to 'Bcourse' in config.py and test.html for consistency
- `892350e` - Update email addresses in config.py and students_views.py for consistency and accuracy
- `a345765` - Update email configuration in config.py to use environment variables for enhanced flexibility

### 2025-08-12
- `21a17cc` - Enhance reset password template for improved layout and user experience

### 2025-08-03
- `a4750e6` - Add detailed docstrings to automation_base.py for better clarity and usage examples
- `d7cf655` - Remove interpunction from secrets


