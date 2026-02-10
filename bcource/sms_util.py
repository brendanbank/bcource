"""
AWS SNS SMS utility for sending two-factor authentication codes.
"""
import logging
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from flask import current_app
from flask_security import SmsSenderBaseClass
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

def _mask_phone(phone_number):
    """Mask phone number for logging, showing only last 4 digits."""
    if len(phone_number) > 4:
        return '*' * (len(phone_number) - 4) + phone_number[-4:]
    return '****'

# Rate limiting configuration - loaded from app config
def get_rate_limits():
    """Get rate limit configuration from Flask app config."""
    if current_app:
        return (
            current_app.config.get('SMS_RATE_LIMIT_PER_HOUR', 5),
            current_app.config.get('SMS_RATE_LIMIT_PER_DAY', 10),
            current_app.config.get('SMS_COOLDOWN_SECONDS', 60)
        )
    return 5, 10, 60  # Defaults if app not available

# In-memory rate limiting (for simple cases, use Redis for production distributed systems)
_sms_attempts = {}  # {phone_number: [timestamp1, timestamp2, ...]}
_last_sms_time = {}  # {phone_number: last_timestamp}


def check_rate_limit(phone_number):
    """
    Check if phone number has exceeded rate limits.
    
    Returns:
        tuple: (allowed: bool, error_message: str or None)
    """
    now = datetime.now()
    rate_limit_hour, rate_limit_day, cooldown = get_rate_limits()
    
    # Check cooldown period
    if phone_number in _last_sms_time:
        time_since_last = (now - _last_sms_time[phone_number]).total_seconds()
        if time_since_last < cooldown:
            wait_time = int(cooldown - time_since_last)
            return False, f"Please wait {wait_time} seconds before requesting another code"
    
    # Initialize attempts list if not exists
    if phone_number not in _sms_attempts:
        _sms_attempts[phone_number] = []
    
    # Clean up old attempts
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)
    _sms_attempts[phone_number] = [
        ts for ts in _sms_attempts[phone_number] if ts > one_day_ago
    ]
    
    # Count recent attempts
    attempts_last_hour = sum(1 for ts in _sms_attempts[phone_number] if ts > one_hour_ago)
    attempts_last_day = len(_sms_attempts[phone_number])
    
    # Check hourly limit
    if attempts_last_hour >= rate_limit_hour:
        return False, f"Too many SMS requests. Maximum {rate_limit_hour} per hour. Please try again later"
    
    # Check daily limit
    if attempts_last_day >= rate_limit_day:
        return False, f"Daily SMS limit reached ({rate_limit_day}). Please try again tomorrow"
    
    return True, None


def record_sms_attempt(phone_number):
    """Record an SMS attempt for rate limiting."""
    now = datetime.now()
    if phone_number not in _sms_attempts:
        _sms_attempts[phone_number] = []
    _sms_attempts[phone_number].append(now)
    _last_sms_time[phone_number] = now


def send_sms(phone_number, message):
    """
    Send SMS using AWS SNS.

    Args:
        phone_number (str): Phone number in E.164 format (e.g., +31612345678)
        message (str): SMS text content (max 160 characters for standard SMS)

    Returns:
        tuple: (success: bool, error_message: str or None)

    Example:
        success, error = send_sms("+31612345678", "Your code is: 123456")
    """
    try:
        # Validate phone number format
        if not phone_number.startswith('+'):
            logger.error(f"Invalid phone number format: {_mask_phone(phone_number)}. Must be E.164 format.")
            return False, "Phone number must be in E.164 format (e.g., +31612345678)"

        # Check rate limiting
        allowed, rate_limit_error = check_rate_limit(phone_number)
        if not allowed:
            logger.warning(f"Rate limit exceeded for {_mask_phone(phone_number)}: {rate_limit_error}")
            return False, rate_limit_error

        # Get AWS configuration
        aws_region = current_app.config.get('AWS_REGION', 'us-east-1')
        aws_access_key = current_app.config.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = current_app.config.get('AWS_SECRET_ACCESS_KEY')
        sender_id = current_app.config.get('AWS_SNS_SENDER_ID', 'BCOURSE')

        if not aws_access_key or not aws_secret_key:
            logger.error("AWS credentials not configured")
            return False, "AWS credentials not configured"

        # Create SNS client
        sns_client = boto3.client(
            'sns',
            region_name=aws_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )

        # Set SMS attributes for better delivery
        message_attributes = {
            'AWS.SNS.SMS.SenderID': {
                'DataType': 'String',
                'StringValue': sender_id
            },
            'AWS.SNS.SMS.SMSType': {
                'DataType': 'String',
                'StringValue': 'Transactional'  # Higher priority for 2FA codes
            }
        }

        # Send SMS via SNS
        response = sns_client.publish(
            PhoneNumber=phone_number,
            Message=message,
            MessageAttributes=message_attributes
        )

        # Log the MessageId for tracking
        message_id = response.get('MessageId', 'unknown')
        logger.info(f"[SMS] SNS accepted message {message_id} for {_mask_phone(phone_number)}")

        # Note: SNS returns 200 OK even if delivery will fail due to quota
        # Check CloudWatch logs at: /aws/sns/<region>/<account-id>/DirectPublish
        # for actual delivery status

        # Record successful attempt for rate limiting
        record_sms_attempt(phone_number)

        logger.info(f"[SMS] SMS queued successfully to {_mask_phone(phone_number)} (MessageId: {message_id})")
        logger.warning(f"[SMS] If delivery fails, check CloudWatch logs for MessageId: {message_id}")
        return True, None

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS SNS error sending SMS: {error_code} - {error_message}")
        return False, f"Failed to send SMS: {error_message}"

    except BotoCoreError as e:
        logger.error(f"AWS configuration error: {str(e)}")
        return False, f"AWS configuration error: {str(e)}"

    except Exception as e:
        logger.error(f"Unexpected error sending SMS: {str(e)}")
        return False, f"Unexpected error: {str(e)}"


def send_2fa_code(phone_number, code):
    """
    Send a two-factor authentication code via SMS.

    Args:
        phone_number (str): Phone number in E.164 format
        code (str): The verification code

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    app_name = current_app.config.get('SECURITY_TOTP_ISSUER', 'BCourse')
    message = f"{app_name}: Your verification code is {code}. Valid for 10 minutes."

    return send_sms(phone_number, message)


def validate_phone_number(phone_number):
    """
    Validate phone number format using phonenumbers library.

    Args:
        phone_number (str): Phone number to validate

    Returns:
        tuple: (is_valid: bool, formatted_number: str or None, error_message: str or None)
    """
    try:
        import phonenumbers

        # Parse the phone number
        parsed = phonenumbers.parse(phone_number, None)

        # Validate it
        if not phonenumbers.is_valid_number(parsed):
            return False, None, "Invalid phone number"

        # Format to E.164
        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

        return True, formatted, None

    except phonenumbers.phonenumberutil.NumberParseException as e:
        logger.error(f"Phone number parsing error: {e}")
        return False, None, str(e)
    except Exception as e:
        logger.error(f"Unexpected error validating phone number: {e}")
        return False, None, str(e)


class AwsSnsSender(SmsSenderBaseClass):
    """AWS SNS SMS sender for Flask-Security two-factor authentication"""

    def __init__(self):
        super().__init__()

    def send_sms(self, from_number, to_number, msg):
        """
        Send SMS via AWS SNS.
        
        Args:
            from_number: Sender ID (not used by SNS, but required by interface)
            to_number: Recipient phone number in E.164 format
            msg: Message text
            
        Returns:
            None (raises exception on error)
        """
        success, error = send_sms(to_number, msg)
        if not success:
            raise Exception(f"Failed to send SMS: {error}")
