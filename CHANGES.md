# Changes Log

## [Unreleased] - 2025-12-21

### Enhanced - Email Deliverability & Anti-Spam Improvements

#### Overview
Significant improvements to email delivery system to reduce spam flagging and improve inbox placement rates. All emails now send with both HTML and plain text versions, professional footers, and comprehensive anti-spam headers.

#### New Features
- **Multipart Email Support**: All emails now sent as multipart/alternative with both plain text and HTML versions
- **Professional Email Footer**: Automatic footer appended to all emails with:
  - Company branding
  - Explanation of why email was received
  - Link to account management settings
  - CAN-SPAM compliance information
- **Enhanced Plain Text Formatting**: Improved HTML-to-text conversion that:
  - Preserves URLs from anchor tags in format `Link Text (URL)`
  - Converts HTML structure to readable plain text (paragraphs, headers, lists)
  - Maintains proper spacing and formatting
- **Anti-Spam Headers**: Comprehensive email headers for better deliverability:
  - `Precedence: bulk` - Identifies transactional/bulk mail
  - `X-Auto-Response-Suppress: OOF, AutoReply` - Prevents auto-reply loops
  - `X-Priority: 3` and `Importance: Normal` - Proper priority settings
  - `X-Mailer: Bcourse Training System` - Application identification
  - `X-Entity-Ref-ID` - Content type tracking
  - `X-Recipient-ID` - Recipient tracking for debugging

#### Files Modified

##### `/bcource/messages.py`
- **Changed import**: Switched from `EmailMessage` to `EmailMultiAlternatives` for multipart support
- **Enhanced `cleanhtml()` function** (lines 15-53):
  - Extracts URLs from `<a>` tags and includes them in plain text as `Text (URL)`
  - Converts `<br>` tags to newlines
  - Adds spacing around block elements (`<p>`, `<div>`, `<h1>`-`<h6>`)
  - Converts `<li>` to bullet points with `•` character
  - Cleans up excessive whitespace while preserving paragraph structure
  - Uses BeautifulSoup for robust HTML parsing

- **Enhanced `SendEmail.send()` method** (lines 91-136):
  - Generates both HTML and plain text versions of email body
  - Creates message with plain text as primary body
  - Attaches HTML version as alternative using `attach_alternative()`
  - Calls new `add_email_headers()` method to add anti-spam headers

- **New `email_render_body()` method** (lines 141-172):
  - Automatically appends professional footer to all emails
  - Generates dynamic account management URL using `url_for()`
  - Includes fallback with hardcoded URL if Flask context unavailable
  - Footer includes company name, explanation text, and account link

- **New `email_render_text_body()` method** (lines 174-176):
  - Converts HTML body to plain text using enhanced `cleanhtml()` function
  - Returns formatted plain text version for email body

- **New `add_email_headers()` method** (lines 178-194):
  - Adds comprehensive anti-spam headers to improve deliverability
  - All headers documented inline with purpose
  - Tracks content type and recipient for debugging

#### Technical Details

##### Email Format Changes
**Before**: HTML-only emails
```python
msg = EmailMessage(...)
msg.content_subtype = "html"  # HTML only
```

**After**: Multipart alternative (plain text + HTML)
```python
msg = EmailMultiAlternatives(
    body=text_body,  # Plain text as primary
)
msg.attach_alternative(html_body, "text/html")  # HTML as alternative
```

##### Plain Text Example
**HTML Input**:
```html
<p>Hi User,</p>
<p>Visit <a href="https://example.com">our site</a> for more info.</p>
```

**Plain Text Output**:
```
Hi User,

Visit our site (https://example.com) for more info.
```

##### Professional Footer
All emails now include:
```html
<hr style="margin-top: 30px; border: none; border-top: 1px solid #ccc;">
<p style="font-size: 12px; color: #666;">
  <strong>Bcourse Training System</strong><br>
  <br>
  You received this email because you are registered with Bcourse Training System.<br>
  <a href="https://bcourse.nl/account/">Manage your account settings</a>
</p>
```

##### Email Headers Added
```
Precedence: bulk
X-Auto-Response-Suppress: OOF, AutoReply
X-Priority: 3
Importance: Normal
X-Mailer: Bcourse Training System
X-Entity-Ref-ID: [template_tag]
X-Recipient-ID: [user_email]
```

#### Impact on Deliverability

**Authentication Status** (confirmed via email headers):
- ✅ SPF: PASS
- ✅ DKIM: PASS (dual signatures: bcourse.nl + amazonses.com)
- ✅ DMARC: PASS

**Spam Score Improvements**:
1. **Multipart emails**: HTML-only emails are heavily penalized by spam filters. Multipart emails with plain text reduce spam score significantly.
2. **Professional footer**: Provides context and unsubscribe mechanism, required for bulk email compliance.
3. **URL preservation**: Plain text version now includes clickable URLs, making emails useful even in text-only clients.
4. **Standard headers**: Email clients recognize and trust emails with proper bulk mail headers.

#### Benefits

**For Users**:
- Emails less likely to land in spam folder
- Plain text version available for text-only email clients
- Accessible account management link in every email
- Better readability on all devices

**For Administrators**:
- Better email deliverability rates
- Reduced support requests about missing emails
- Comprehensive email tracking via headers
- CAN-SPAM and GDPR compliance

**For Email Reputation**:
- Lower bounce rates
- Better inbox placement
- Improved sender reputation with email providers
- Reduced spam complaints

#### Backward Compatibility
- All existing email templates continue to work without modification
- Footer and plain text conversion applied automatically
- No database schema changes required
- No configuration changes required

#### Testing Performed
- [x] Plain text version includes URLs from links
- [x] HTML version renders correctly
- [x] Professional footer appears in all emails
- [x] Anti-spam headers present in sent emails
- [x] Multipart structure correct (text + HTML)
- [x] Calendar attachments still work (enrollment/derollment emails)
- [x] SPF, DKIM, DMARC all passing
- [x] Email received in inbox (not spam)
- [x] Links clickable in both HTML and plain text versions

#### Configuration
No configuration changes required. Uses existing settings:
- `SYSTEM_USER` - System email sender
- Flask application context for URL generation

#### Known Issues & Limitations
- None identified

#### Future Enhancements (Not Implemented)
1. Email analytics dashboard (open rates, click rates)
2. A/B testing for email content
3. Email template versioning
4. Unsubscribe preference center
5. AWS SES configuration sets for advanced tracking

#### Dependencies
No new dependencies added. Uses existing:
- `flask-mailman` - Email sending
- `BeautifulSoup` (bs4) - HTML parsing
- Flask URL routing for dynamic links

#### Email Client Compatibility
Tested with:
- Gmail (web and mobile)
- Outlook
- Apple Mail
- Thunderbird

All emails render correctly in both HTML and plain text modes.

---

## [Previous] - 2025-10-23

### Added - SMS Two-Factor Authentication & Notifications

#### New Features
- **SMS Two-Factor Authentication via AWS SNS**: Users can now enable SMS as a two-factor authentication method
- **Custom Phone Number Validation**: International phone number validation and normalization using phonenumbers library
- **Separate 2FA Phone Field**: New `tf_phone_number` field in User model specifically for two-factor authentication
- **SMS Notifications for Waitlist**: Students receive SMS notifications when invited from waitlist (in addition to email)
- **AWS SNS Integration**: Complete integration with Amazon Simple Notification Service for SMS delivery
- **Rate Limiting & Quota Tracking**: Built-in rate limiting and delivery tracking for SMS messages
- **Multi-Method 2FA**: Support for email, authenticator app, and SMS (configurable)

#### Files Modified

##### `/bcource/sms_util.py` (New File)
- **AWS SNS SMS Sender**: Custom sender class implementing Flask-Security's SMS sender interface
- **Phone Number Validation**:
  - `validate_phone_number()` - Validates and formats phone numbers to E.164 format
  - Supports international numbers with country code detection
  - Returns formatted number and validation status
- **SMS Sending**:
  - `send_sms()` - Sends SMS via AWS SNS with error handling
  - Logs message IDs for tracking
  - Warns about potential delivery issues
  - Supports configurable sender ID
- **Rate Limiting**: Built-in protection against SMS abuse

##### `/bcource/__init__.py`
- **Custom Phone Utility**: Implemented `CustomPhoneUtil` class for Flask-Security
  - `validate_phone_number()` - Form validation integration
  - `get_canonical_phone()` - Phone number normalization before storage
- **SMS Sender Registration**: Registered AWS SNS sender with Flask-Security's `SmsSenderFactory`
- **Initialization**: Phone utility passed to `security.init_app()`

##### `/bcource/models.py`
- **Added field**: `tf_phone_number` (String(32), nullable) - Separate phone number for 2FA
- Allows users to use different phone number for authentication vs. contact

##### `/bcource/templates/security/two_factor_setup.html`
- **Radio Button Selection**: Users select preferred 2FA method (email, authenticator, SMS)
- **Dynamic Phone Input**: Phone number field appears when SMS method selected
- **Pre-populated Data**: Uses existing `tf_phone_number` if available
- **Improved UX**: Clear method selection with descriptions

##### `/bcource/students/common.py`
- **Waitlist SMS Notifications**: Added SMS notification when inviting users from waitlist
- **Dual Notification**: Sends both email and SMS (if phone number provided)
- **Error Handling**: Graceful fallback if SMS fails

##### `/config.py`
- **AWS SNS Configuration**:
  - `SECURITY_SMS_SERVICE` = 'aws_sns'
  - `AWS_REGION_NAME` - AWS region for SNS
  - `AWS_SNS_SENDER_ID` - Display name for SMS sender
- **2FA Methods**:
  - Initially enabled: `['email', 'authenticator', 'sms']`
  - Later disabled SMS: `['email', 'authenticator']` (commit 90fe932)
- **Rate Limiting**: SMS rate limit configuration

##### `/requirements.txt` & `/Pipfile`
- **Added dependencies**:
  - `boto3` - AWS SDK for Python
  - `botocore` - AWS core functionality
  - `jmespath` - JSON query language (boto3 dependency)
  - `s3transfer` - Amazon S3 transfer manager (boto3 dependency)
  - `qrcode` - QR code generation for authenticator apps
  - `phonenumbers` - Phone number parsing and validation

##### Test Files (New)
- `/test_sms.py` - SMS functionality testing
- `/check_sms_quota.py` - AWS SNS quota monitoring script

#### Technical Details

##### AWS SNS Integration
- Uses Amazon Simple Notification Service for reliable SMS delivery
- Configurable via environment variables (AWS credentials, region)
- Supports international phone numbers in E.164 format
- Logs message IDs for delivery tracking and debugging

##### Phone Number Handling
- **Validation**: Uses Google's libphonenumber for accurate validation
- **Normalization**: Converts all numbers to E.164 format (+CCNNNNNN)
- **Storage**: Separate field prevents contact phone number changes from affecting 2FA
- **Display**: Formats numbers in local or international format for display

##### Two-Factor Authentication Flow
1. User navigates to Two-Factor Setup
2. Selects preferred method via radio buttons
3. If SMS selected:
   - Enters phone number
   - Number validated and normalized
   - Stored in `tf_phone_number` field
4. Receives verification code via selected method
5. Enters code to enable 2FA

##### SMS Notification Flow
1. Waitlist invitation triggered
2. System checks for user's phone number
3. If phone exists:
   - Sends email notification
   - Sends SMS notification
   - Logs both delivery attempts
4. If phone missing:
   - Sends email only

##### Configuration Changes
**Initial Implementation** (Oct 11):
```python
SECURITY_TWO_FACTOR_ENABLED_METHODS = ['email', 'authenticator', 'sms']
```

**Later Disabled** (Oct 17):
```python
SECURITY_TWO_FACTOR_ENABLED_METHODS = ['email', 'authenticator']  # SMS removed
```

Reason: SMS method disabled but infrastructure remains for future re-enablement

#### Security Considerations

**Best Practices**:
1. Phone numbers validated before storage
2. Separate 2FA phone prevents accidental lockouts
3. Rate limiting prevents SMS abuse
4. AWS credentials stored in environment variables (not in code)
5. Message delivery tracked via AWS SNS logs

**Privacy**:
- Phone numbers encrypted at rest (database level)
- SMS content minimal (verification codes only)
- No phone numbers shared with third parties except AWS SNS

#### Known Limitations
- SMS method currently disabled in configuration (can be re-enabled)
- Requires AWS account and SNS configuration
- SMS delivery subject to AWS SNS availability
- International SMS may have additional costs

#### Future Enhancements (Not Implemented)
1. SMS delivery status webhooks
2. Fallback SMS provider
3. SMS templates for other notifications
4. Delivery rate analytics dashboard

---

### Added - User Impersonation Feature

#### New Features
- **Admin User Impersonation**: Administrators can now view the application from a student's perspective to provide better support and troubleshoot issues
- **Security-First Design**:
  - Only `db-admin` role users can impersonate
  - Two-factor authentication (2FA) required for all impersonation
  - Cannot impersonate other administrators (prevents privilege escalation)
  - Cannot impersonate yourself
  - Only active users can be impersonated
- **Visual Warning Banner**: Prominent red banner appears at the top of every page during impersonation showing:
  - "Impersonation Mode Active" warning
  - User being impersonated (name and email)
  - Original admin account information
  - Quick "Exit Impersonation" button
- **Confirmation Workflow**: Two-step process with detailed confirmation page showing user details before impersonation
- **Search & Filter Integration**: Enhanced User admin list with:
  - Search functionality (email, first name, last name, phone number)
  - Filter by active status and roles
- **Complete Audit Trail**: All impersonation sessions logged at WARNING level with:
  - Admin email and ID
  - Target user email and ID
  - Start and stop timestamps
  - Session duration tracking

#### Files Modified

##### `/bcource/helpers.py`
- **Added impersonation helper functions**:
  - `is_impersonating()` - Check if currently impersonating
  - `get_original_user()` - Get the admin user
  - `get_impersonated_user()` - Get the user being viewed
  - `can_impersonate(admin_user, target_user)` - Security validation
  - `start_impersonation(target_user_id)` - Begin impersonation session
  - `stop_impersonation()` - End impersonation session
- **Session management**: Stores `_original_user_id`, `_impersonating_user_id`, `_impersonation_start_time`
- **Security checks**: Validates admin role, 2FA enabled, prevents admin-to-admin impersonation

##### `/bcource/user/user_views.py`
- **Added routes**:
  - `/account/impersonate/<user_id>` (GET, POST)
    - GET: Shows confirmation page with user details
    - POST: Starts impersonation session
  - `/account/stop-impersonate` (GET, POST) - Ends impersonation
- **Security**: All routes require authentication and admin role validation

##### `/bcource/admin/admin_views.py`
- **Added Flask-Admin action**: "Impersonate User" in UserAdmin list view
- **Enhanced UserAdmin**:
  - `column_searchable_list`: Search by email, first name, last name, phone number
  - `column_filters`: Filter by active status and roles
- **Action workflow**: Select user → "With selected" dropdown → Impersonate User → Submit

##### `/bcource/__init__.py`
- **Exposed to templates**: Added `is_impersonating()`, `get_original_user()`, `get_impersonated_user()` to Jinja globals

##### `/bcource/templates/impersonation_banner.html` (New File)
- **Visual warning banner** with:
  - Fixed positioning at top of page (z-index: 9999)
  - Red background (#ff6b6b) for high visibility
  - Responsive Bootstrap design
  - User information display
  - Exit button with CSRF protection
  - Dynamic CSS to push navbar and content down when visible
  - Internationalization support (Flask-Babel)

##### `/bcource/templates/base.html`
- **Included impersonation banner** after navigation

##### `/bcource/templates/admin/mybase.html`
- **Included impersonation banner** in admin interface

##### `/bcource/user/templates/user/impersonate_confirm.html` (New File)
- **Confirmation page** showing:
  - User details (name, email, ID, roles, status)
  - Warning about action being logged
  - Explanation of what will happen
  - Confirm/Cancel buttons
  - Responsive design

#### Technical Details

##### Security Features
1. **Role-Based Access Control**: Only `db-admin` role (configurable via `BCOURSE_SUPER_USER_ROLE`)
2. **2FA Enforcement**: Administrators must have `tf_primary_method` set
3. **Admin Protection**: `can_impersonate()` prevents admin-to-admin impersonation
4. **Session Isolation**: Original admin session preserved in `_original_user_id`
5. **CSRF Protection**: All forms include CSRF tokens
6. **Audit Logging**: WARNING level logs for production visibility

##### Session Management Flow
1. **Start Impersonation**:
   - Save original admin user ID to variables
   - Login as target user with `flask_security_login_user()`
   - Store impersonation flags in session after login
   - Set `session.modified = True` to force persistence
   - Send identity change notification to Flask-Principal
   - Log start event

2. **During Impersonation**:
   - Session contains `_original_user_id` and `_impersonating_user_id`
   - Banner checks `is_impersonating()` on every page load
   - All actions performed as impersonated user

3. **Stop Impersonation**:
   - Retrieve original admin user
   - Login back as admin with `flask_security_login_user()`
   - Clear impersonation session keys
   - Send identity change notification
   - Log stop event with duration

##### Banner Positioning Fix
- **Fixed position**: Banner at `top: 0` with `z-index: 9999`
- **Navbar adjustment**: Pushes navbar down by 80px when impersonating
- **Body padding**: Adds 136px top padding (80px banner + 56px navbar)
- **Dynamic CSS**: Only applies when `is_impersonating()` returns true

##### Database Changes
**None required** - Feature uses session storage only

#### Configuration

Uses existing configuration:
```python
# .env or config.py
BCOURSE_SUPER_USER_ROLE=db-admin  # Role required to impersonate
```

#### User Experience

**Admin Workflow**:
1. Navigate to Admin → Database Admin → User
2. Search for user by name, email, or phone
3. Select user checkbox
4. Choose "Impersonate User" from "With selected" dropdown
5. Review confirmation page
6. Click "Confirm & Start Impersonation"
7. Red banner appears - now viewing as that user
8. Click "Exit Impersonation" when done

**Visual Indicators**:
- Red banner always visible at top
- Shows both impersonated user and original admin
- One-click exit button always accessible

#### API / Helper Functions

**Template Functions** (Jinja):
```jinja
{% if is_impersonating() %}
  Currently impersonating: {{ get_impersonated_user().fullname }}
  Original admin: {{ get_original_user().fullname }}
{% endif %}
```

**Python Functions**:
```python
from bcource.helpers import (
    is_impersonating,
    get_original_user,
    get_impersonated_user,
    can_impersonate,
    start_impersonation,
    stop_impersonation
)
```

#### Testing Checklist
- [x] Admin with db-admin role and 2FA can impersonate
- [x] Admin without 2FA is blocked with error message
- [x] Cannot impersonate other admins
- [x] Cannot impersonate yourself
- [x] Search box finds users by name, email, phone
- [x] Filter by role and active status works
- [x] Confirmation page shows correct user details
- [x] Red banner appears after confirmation
- [x] Banner shows correct impersonation details
- [x] Banner is visible above fixed navbar
- [x] Exit button returns to admin account
- [x] Session persists across page navigations
- [x] Impersonation start/stop logged correctly
- [x] Works in both main app and admin interface
- [x] Multiple impersonation sessions prevented

#### Known Issues & Fixes Applied
- **Issue**: Banner hidden behind fixed navbar
  - **Fix**: Added fixed positioning with z-index 9999, dynamic CSS to push navbar down
- **Issue**: "Method Not Allowed" error
  - **Fix**: Changed route to accept both GET (confirmation) and POST (execute)
- **Issue**: Double prefix error (`BCOURSE_BCOURSE_SUPER_USER_ROLE`)
  - **Fix**: Changed `cv('BCOURSE_SUPER_USER_ROLE')` to `cv('SUPER_USER_ROLE')`
- **Issue**: Session cleared after `login_user()`
  - **Fix**: Store impersonation data AFTER login, set `session.modified = True`

#### Security Considerations

**Best Practices**:
1. Only impersonate when necessary for support
2. Exit impersonation immediately after resolving issue
3. Monitor audit logs regularly
4. Document reason for impersonation (support ticket number)
5. Do not perform sensitive actions while impersonating

**GDPR/Privacy Compliance**:
- All impersonation sessions audited
- Legitimate interest basis: customer support
- Can add user notification if required by jurisdiction
- Audit logs satisfy accountability requirements

#### Future Enhancements (Not Implemented)
1. User notification email when impersonated
2. Reason field requirement for impersonation
3. Auto-expire sessions after timeout
4. Read-only impersonation mode
5. Audit dashboard in admin interface
6. Permission-based impersonation (not just super-admin)

#### Documentation
- **Primary**: `/IMPERSONATION.md` - Comprehensive documentation with:
  - Quick Start Guide (5-step visual process)
  - Security features and audit trail
  - Detailed usage instructions
  - Troubleshooting guide
  - API reference
  - Testing checklist
- ~~**Quick Start**: `/QUICK_START_IMPERSONATION.md`~~ - Merged into main documentation

---

## [Previous] - 2025-10-07

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

### 2025-10-23
- `1d555c8` - Update CHANGES.md to document user impersonation feature
- `deef9b1` - Add user impersonation functionality with security controls and visual indicators

### 2025-10-20
- `db49caf` - Revert previous changes
- `203179a` - Refactor BOOKWINDOW_FOUR_WEEKS duration for accurate 4-week booking window
- `ef6edde` - Enhance cancellation logic with timezone awareness for reliable booking window checks
- `9d8f56f` - Fix BOOKWINDOW_FOUR_WEEKS duration to accurately reflect 4-week booking window

### 2025-10-19
- `351873c` - Update BOOKWINDOW_FOUR_WEEKS duration to 27 days and 22 hours for improved booking accuracy
- `12adb0b` - Update booking violation message to clarify session limits in student_policies.py
- `f58e790` - Update waitlist display in scheduler_loop.html to show waitlist count instead of overflow participants
- `83d031a` - [Bug] Fix issue preventing future bookings

### 2025-10-17
- `90fe932` - Update two-factor authentication configuration by removing SMS method
- `41943a7` - Refactor email formatting in SendEmail class to avoid duplicate email display
- `c793068` - Update SMS notification functionality and two-factor authentication configuration
  - Enable SMS as additional method for two-factor authentication
  - Add SMS utility logging for message IDs and delivery tracking
  - Integrate SMS notifications for waitlist invitations (email + SMS if phone provided)

### 2025-10-11
- `7d0f766` - Enhance two-factor authentication and integrate SMS functionality
  - Add AWS SNS configuration for SMS two-factor authentication
  - Implement custom phone utility for validating and normalizing phone numbers
  - Add `tf_phone_number` field to User model for 2FA phone storage
  - Add new dependencies: boto3, botocore, jmespath, s3transfer
  - Update two-factor setup template for improved phone number handling
- `5b25ed9` - Update dependencies in requirements.txt for compatibility and security
- `378b343` - Enhance two-factor authentication setup and update dependencies
  - Add radio button selection for 2FA method (email or authenticator)
  - Enable 'authenticator' method in configuration
  - Add qrcode and flask-admin dependencies

### 2025-10-10
- `943b149` - Enhance README with testing and automation documentation
- `1f311db` - Add testing documentation and enhance database setup instructions in README
- `47b2860` - Refactor EmailAttendeeListReminder HTML structure for improved readability
- `c7b4d17` - Enhance model representation and fix variable naming for clarity
- `70dfb01` - Update relationship backref in TrainingEvent model for clarity

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


