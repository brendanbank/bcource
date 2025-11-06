# WebAuthn Biometric Authentication Setup Guide

This guide explains how WebAuthn biometric authentication has been added to your BCourse application.

## What is WebAuthn?

WebAuthn is a web standard that allows users to authenticate using:
- **Built-in biometric sensors**: Touch ID (MacBook, iPhone), Face ID (iPhone/iPad), Windows Hello
- **Hardware security keys**: YubiKey, Titan keys, etc.

It's more secure than passwords and provides a seamless user experience.

## What Was Implemented

### 1. Configuration Changes

**File: [config.py](config.py#L82-L94)**

Added WebAuthn to the two-factor authentication methods and configured settings:

```python
SECURITY_TWO_FACTOR_ENABLED_METHODS = ['email', 'authenticator', 'webauthn']

# WebAuthn Configuration
SECURITY_WAN_ALLOW_AS_FIRST_FACTOR = True  # Passwordless login
SECURITY_WAN_ALLOW_AS_MULTI_FACTOR = True   # Use as 2FA
SECURITY_WAN_ALLOW_USER_HINTS = True        # Username hints
SECURITY_WAN_ALLOW_AS_VERIFY = ['first', 'secondary']
SECURITY_WAN_RP_NAME = environ.get("SECURITY_WAN_RP_NAME", "BCourse Training System")
```

### 2. User Management Routes

**File: [bcource/user/user_views.py](bcource/user/user_views.py#L679-L714)**

Added two new routes for managing security keys:

- `GET /account/security-keys` - View and manage all registered keys
- `POST /account/security-keys/delete/<id>` - Remove a security key

### 3. User Interface Template

**File: [bcource/user/templates/user/security-keys.html](bcource/user/templates/user/security-keys.html)**

Created a management page that shows:
- List of registered biometric credentials
- Registration date and last used timestamp
- Button to register new credentials
- Option to remove credentials
- Instructions for supported devices

### 4. JavaScript Files

**Files:**
- [bcource/static/js/webauthn.js](bcource/static/js/webauthn.js) - WebAuthn API handlers
- [bcource/static/js/base64.js](bcource/static/js/base64.js) - Base64 encoding utilities

These files handle the browser's WebAuthn API calls for registration and authentication.

### 5. Database Model

**File: [bcource/models.py](bcource/models.py#L864-L871)**

The `WebAuthn` model already existed in your codebase (from Flask-Security):

```python
class WebAuthn(db.Model, sqla.FsWebAuthnMixin):
    credential_id: Mapped[str] = mapped_column(String(1024))

    @declared_attr
    def user_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
```

The `User` model also has the relationship defined at [models.py:738-741](bcource/models.py#L738-L741).

## How to Complete the Setup

### Step 1: Add Environment Variable

Add this to your `.env` file:

```bash
SECURITY_WAN_RP_NAME="BCourse Training System"
```

This is the name users will see when registering their biometric credentials.

### Step 2: Create Database Migration

When your MySQL database is running:

```bash
# Activate virtual environment
source .venv/bin/activate  # or: pipenv shell

# Create migration
flask db migrate -m "Add WebAuthn support for biometric authentication"

# Apply migration
flask db upgrade
```

### Step 3: Restart Your Application

```bash
python run.py
```

## How Users Register Biometrics

Users have two ways to register biometric authentication:

### Option 1: Through Two-Factor Setup

1. Log in to the application
2. Go to **Two-Factor Setup** (usually at `/auth/two_factor_setup`)
3. Select **WebAuthn** as the authentication method
4. Follow the browser prompts to use Touch ID, Face ID, or a security key
5. Give the credential a memorable name

### Option 2: Through Security Keys Page

1. Log in to the application
2. Navigate to **Account** → **Security Keys** (`/account/security-keys`)
3. Click **Register Security Key**
4. Follow the same registration process

## How Users Log In with Biometrics

### Passwordless Login (if enabled)

1. Go to the login page
2. Click **Sign in with WebAuthn** (or similar)
3. Enter email/username
4. Browser prompts for biometric verification
5. Use fingerprint, face, or security key
6. Logged in!

### As Second Factor (2FA)

1. Enter email and password normally
2. When prompted for 2FA
3. Select **WebAuthn** option
4. Use biometric verification
5. Logged in!

## User Experience Flow

```
Registration:
User → Account Settings → Security Keys → Register → Browser Prompt → Touch ID/Face ID → Named & Saved

Login (Passwordless):
User → Login Page → WebAuthn Option → Enter Email → Browser Prompt → Touch ID/Face ID → Logged In

Login (2FA):
User → Login Page → Email/Password → 2FA Required → WebAuthn → Touch ID/Face ID → Logged In
```

## Supported Devices and Browsers

### Devices
- ✅ MacBook with Touch ID
- ✅ iPhone/iPad with Face ID or Touch ID (iOS 14.5+)
- ✅ Android phones with fingerprint scanner
- ✅ Windows devices with Windows Hello
- ✅ Any device with USB/NFC security keys (YubiKey, etc.)

### Browsers
- ✅ Safari 14+
- ✅ Chrome 67+
- ✅ Firefox 60+
- ✅ Edge 18+

### Important Notes

1. **HTTPS Required**: WebAuthn only works over HTTPS in production (browsers enforce this)
2. **Development**: Works on localhost without HTTPS
3. **Multiple Credentials**: Users can register multiple biometric devices (e.g., MacBook + iPhone)
4. **Backup Methods**: Recommend users also set up authenticator app or email 2FA as backup

## Security Features

- **Phishing Resistant**: Biometric credentials are tied to your domain
- **No Shared Secrets**: Private keys never leave the user's device
- **Device Authentication**: Verifies both user and device
- **Man-in-the-Middle Protection**: Uses cryptographic challenge-response

## Troubleshooting

### "WebAuthn not supported"
- User's browser doesn't support WebAuthn
- Update browser or use a different one

### "No authenticator available"
- Device doesn't have biometric sensor
- User can use hardware security key instead

### Registration fails silently
- Check browser console for errors
- Ensure JavaScript files are loaded correctly
- Verify HTTPS is enabled (production)

### Database migration issues
- Ensure MySQL is running
- Check database connection in `.env`
- Verify Flask-Security and webauthn packages are installed

## Files Modified/Created

### Modified Files:
1. `config.py` - Added WebAuthn configuration
2. `bcource/user/user_views.py` - Added security keys management routes
3. `CLAUDE.md` - Updated documentation

### Created Files:
1. `bcource/user/templates/user/security-keys.html` - Management UI
2. `bcource/static/js/webauthn.js` - WebAuthn handler
3. `bcource/static/js/base64.js` - Base64 utilities
4. `WEBAUTHN_SETUP.md` - This guide

### Existing Files (Flask-Security):
1. `bcource/templates/security/wan_register.html` - Registration page
2. `bcource/templates/security/wan_signin.html` - Sign-in page
3. `bcource/templates/security/wan_verify.html` - Verification page
4. `bcource/models.py` - WebAuthn model (lines 864-871)

## Testing the Implementation

1. **Start the application** with database running
2. **Create a test user account** or use existing account
3. **Navigate to** `/account/security-keys`
4. **Click** "Register Security Key"
5. **Follow browser prompts** to use Touch ID/Face ID
6. **Give it a name** (e.g., "MacBook Pro Touch ID")
7. **Verify** it appears in the list
8. **Log out and test** passwordless login or 2FA

## Further Customization

### Change Relying Party Name
Edit `.env`:
```bash
SECURITY_WAN_RP_NAME="Your Custom Name"
```

### Disable Passwordless Login
Edit `config.py`:
```python
SECURITY_WAN_ALLOW_AS_FIRST_FACTOR = False
```

### Require Biometrics for Certain Roles
Add custom logic in your views using Flask-Security decorators.

## Additional Resources

- [Flask-Security WebAuthn Documentation](https://flask-security-too.readthedocs.io/en/stable/features.html#webauthn)
- [WebAuthn Guide](https://webauthn.guide/)
- [Can I Use WebAuthn](https://caniuse.com/webauthn)

## Support

For issues or questions:
1. Check browser console for JavaScript errors
2. Review Flask application logs
3. Verify database migration applied correctly
4. Test on multiple devices/browsers
5. Contact support at the email configured in your application
