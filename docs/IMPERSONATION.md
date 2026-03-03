# User Impersonation Feature

## Quick Start Guide

**TL;DR**: Admin → Database Admin → User → Check user's box → "With selected" → Impersonate User → Confirm

### Navigation Path
```
Top Navigation Bar → Admin → Database Admin → User (left sidebar)
```

### 5-Step Process

1. **Go to User List**
   - Click "Admin" in the top black navigation bar
   - Select "Database Admin" from the dropdown
   - Click "User" in the left sidebar

2. **Find & Select a User**
   - Use the **search box** to find the user (search by name, email, or phone)
   - Check the checkbox next to their name (left side of the row)

3. **Start Impersonation**
   - Scroll to the bottom of the page
   - Find the dropdown labeled "With selected"
   - Choose "Impersonate User"
   - Click "Submit"

4. **Confirm**
   - Review the user's details on the confirmation page
   - Click "Confirm & Start Impersonation"

5. **You're Now Viewing As That User!**
   - You'll see a **red warning banner** at the top
   - The banner shows who you're viewing as
   - Click "Exit Impersonation" when done

### Requirements Checklist

Before you can impersonate:
- ✅ You must have the `db-admin` role
- ✅ You must have 2FA (two-factor authentication) enabled
- ✅ The user must not be another admin
- ✅ The user must be active

---

## Overview

The user impersonation feature allows administrators to view the application from a student's perspective. This is useful for:
- Troubleshooting user-reported issues
- Verifying what students see in their accounts
- Testing user-specific functionality
- Providing better support by seeing exactly what the user experiences

## Security Features

### Access Control
- **Admin-only**: Only users with the `db-admin` role (configurable via `BCOURSE_SUPER_USER_ROLE`) can impersonate
- **2FA Required**: Administrators must have two-factor authentication enabled
- **No Admin Impersonation**: Admins cannot impersonate other administrators (prevents privilege escalation)
- **No Self-Impersonation**: Cannot impersonate yourself
- **Active Users Only**: Can only impersonate active users

### Audit Trail
- All impersonation sessions are logged with:
  - Admin user email and ID
  - Target user email and ID
  - Start time
  - End time
- Logs use WARNING level for visibility in production
- Format: `IMPERSONATION STARTED: Admin user@example.com (ID: 1) is now impersonating student@example.com (ID: 42)`

### Session Management
- Original admin user ID is stored in session (`_original_user_id`)
- Impersonated user ID is stored in session (`_impersonating_user_id`)
- Start time tracked for audit purposes (`_impersonation_start_time`)
- Only one impersonation session at a time (must exit before starting another)

## Detailed Usage Guide

### Starting Impersonation

#### Method 1: Via Admin Interface (Recommended)

See the [Quick Start Guide](#quick-start-guide) above for the standard workflow.

**Tips:**
- The "Admin" menu only appears if you have the `admin-interface` permission
- Use the **search box** to quickly find users by name, email, or phone number
- You can also **filter** by role or active status on the right side

#### Method 2: Direct URL Access
You can also navigate directly to the impersonation confirmation page:

```
# Navigate to (GET request - shows confirmation page):
/account/impersonate/<user_id>

# Example:
/account/impersonate/42

# This will show the confirmation page
# Click "Confirm & Start Impersonation" to proceed
```

For programmatic access (POST):
```python
# POST to /account/impersonate/<user_id>
# Example: POST /account/impersonate/42
# Requires CSRF token in the request
```

### During Impersonation

When impersonating a user, you will see:
- A prominent **red banner** at the top of every page showing:
  - "Impersonation Mode Active"
  - The user you're viewing as (name and email)
  - Your original admin account
  - An "Exit Impersonation" button

You will have the exact same permissions and view as the impersonated user:
- See their enrolled trainings
- Access their messages
- View their profile
- Experience the interface as they would

### Ending Impersonation

To exit impersonation mode:
1. Click the **"Exit Impersonation"** button in the red banner at the top
2. You will be logged back in as your admin account
3. You will be redirected to the admin interface

Alternatively:
- Navigate to `/account/stop-impersonate` (GET or POST)

## API / Helper Functions

### Template Functions (available in Jinja templates)

```jinja
{% if is_impersonating() %}
  Currently impersonating: {{ get_impersonated_user().fullname }}
  Original admin: {{ get_original_user().fullname }}
{% endif %}
```

### Python Helper Functions

```python
from bcource.helpers import (
    is_impersonating,
    get_original_user,
    get_impersonated_user,
    can_impersonate,
    start_impersonation,
    stop_impersonation
)

# Check if currently impersonating
if is_impersonating():
    print("In impersonation mode")

# Get the original admin user
original_user = get_original_user()  # Returns User object or None

# Get the impersonated user
impersonated_user = get_impersonated_user()  # Returns User object or None

# Check if admin can impersonate a user
can_impersonate_user, error_msg = can_impersonate(admin_user, target_user)
if can_impersonate_user:
    # Proceed with impersonation
    success, message = start_impersonation(target_user_id)

# Stop impersonating
success, message = stop_impersonation()
```

## Implementation Details

### Files Modified

1. **bcource/helpers.py**
   - Added impersonation helper functions
   - Session management
   - Security checks

2. **bcource/user/user_views.py**
   - Added `/account/impersonate/<user_id>` route (POST)
   - Added `/account/stop-impersonate` route (GET/POST)

3. **bcource/admin/admin_views.py**
   - Added "Impersonate User" action to UserAdmin
   - Integrated with Flask-Admin actions system

4. **bcource/__init__.py**
   - Exposed impersonation functions to Jinja templates
   - Made functions globally available

5. **bcource/templates/impersonation_banner.html**
   - New template for the impersonation warning banner
   - Responsive design with Bootstrap

6. **bcource/templates/base.html**
   - Included impersonation banner after navigation

7. **bcource/templates/admin/mybase.html**
   - Included impersonation banner in admin interface

### Database Changes

**None required** - This feature uses session storage only.

### Configuration

The impersonation feature respects the following configuration values:

```python
# .env or config.py
BCOURSE_SUPER_USER_ROLE=db-admin  # Role required to impersonate
```

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| **Can't see the "Admin" menu** | You need the `admin-interface` permission. Check with another admin to grant you this permission. |
| **Can't find "Database Admin"** | Make sure you're logged in as an admin. Look for "Admin" in the top navigation bar. |
| **Don't see "Impersonate User" action** | Make sure you checked a user's checkbox first. The action appears at the bottom in a dropdown. |
| **"Permission denied" error** | Enable Two-Factor Authentication: Account menu → Two-Factor Setup |
| **"You cannot impersonate other administrators"** | This is by design for security. Admins cannot impersonate other admins to prevent privilege escalation. |
| **"You are already impersonating a user"** | Exit the current impersonation session first using the red banner button. |
| **Banner not visible** | Hard refresh the page (Cmd+Shift+R or Ctrl+Shift+R). The red banner should appear at the very top. |
| **Session lost / Can't exit** | Clear browser cookies, log in again as admin. The session will be reset. |

### Error Messages Explained

**"You do not have permission to impersonate users"**
- Ensure you have the super user role (default: `db-admin`)
- Check your user's roles in Admin → Database Admin → User

**"Two-factor authentication is required"**
- Enable 2FA on your admin account
- Navigate to: Account menu (person icon) → Two-Factor Setup
- Follow the setup wizard

**"User not found"**
- The user ID doesn't exist
- Try searching for the user in the admin interface first

## Quick Reference

| What | Where / How |
|------|-------------|
| **Start impersonation** | Admin → Database Admin → User → Select user → "With selected" → Impersonate User → Confirm |
| **Stop impersonation** | Click "Exit Impersonation" button in red banner at top of page |
| **Direct URL** | `/account/impersonate/<user_id>` (shows confirmation page) |
| **Exit URL** | `/account/stop-impersonate` |
| **Search users** | Use search box in User admin list (searches name, email, phone) |
| **Filter users** | Use filters on right side (by role, active status) |
| **Requirements** | `db-admin` role + 2FA enabled |
| **Restrictions** | Cannot impersonate other admins or yourself |
| **Audit logs** | Check application logs (WARNING level) for all impersonation activity |

### What You'll See During Impersonation

When impersonating, you'll see exactly what the student sees:
- ✅ Their enrolled trainings
- ✅ Their messages
- ✅ Their profile information
- ✅ Their available actions
- ✅ A **red warning banner** at the top reminding you that you're impersonating

The red banner includes:
- "Impersonation Mode Active" warning
- Who you're viewing as (name and email)
- Your original admin account
- Quick "Exit Impersonation" button

## Security Considerations

### Best Practices

1. **Only impersonate when necessary**: Use for troubleshooting and support only
2. **Inform users**: Consider notifying users when their account is being viewed (optional enhancement)
3. **Monitor logs**: Regularly review impersonation logs for unusual activity
4. **Short sessions**: Exit impersonation as soon as you're done
5. **Do not perform sensitive actions**: Avoid changing passwords, updating payment info, etc. while impersonating

### Logging

All impersonation activity is logged to the application logger at WARNING level:

```
WARNING - IMPERSONATION STARTED: Admin admin@example.com (ID: 1) is now impersonating student@example.com (ID: 42)
WARNING - IMPERSONATION STOPPED: Admin admin@example.com (ID: 1) stopped impersonating student@example.com (started at 2025-10-23T14:30:00)
```

### GDPR/Privacy Compliance

When using impersonation:
- Document the legitimate reason (e.g., user support ticket #123)
- Keep sessions brief and purposeful
- Consider adding a consent mechanism if required by your jurisdiction
- Maintain audit logs for compliance purposes

## Future Enhancements

Potential improvements to consider:

1. **User Notification**: Send email to user when their account is impersonated
2. **Reason Tracking**: Require admins to specify a reason for impersonation
3. **Time Limits**: Auto-expire impersonation sessions after X minutes
4. **Read-Only Mode**: Option to impersonate in read-only mode (prevent modifications)
5. **Audit Dashboard**: View all impersonation history in admin interface
6. **Permission-Based**: Allow specific permissions (not just super-admin) to impersonate

## Testing Checklist

To verify the impersonation feature is working correctly:

- [ ] Create a test admin user with `db-admin` role and 2FA enabled
- [ ] Create a test student user
- [ ] Log in as admin
- [ ] Navigate to Admin → Database Admin → User
- [ ] Use search box to find the student user
- [ ] Select the student user (checkbox)
- [ ] Use "Impersonate User" action from dropdown
- [ ] Review confirmation page with user details
- [ ] Click "Confirm & Start Impersonation"
- [ ] Verify the **red banner appears** at the top
- [ ] Verify banner shows correct user information
- [ ] Navigate through the application as the student
- [ ] Check that you see the student's data (not admin data)
- [ ] Click "Exit Impersonation" button
- [ ] Verify you're back as admin
- [ ] Check application logs for impersonation start/stop entries

---

**Version**: 1.0
**Last Updated**: 2025-10-23
**Maintained By**: Development Team
