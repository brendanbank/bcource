#!/usr/bin/env python
"""
Test script to send an SMS using the bcource SMS utility.
Usage: python test_sms.py <phone_number> [message]

Example:
    python test_sms.py "+31612345678" "This is a test message"
"""

import sys
import os

# Add the parent directory to the path so we can import bcource modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bcource import create_app
from bcource.sms_util import send_sms

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_sms.py <phone_number> [message]")
        print("Example: python test_sms.py '+31612345678' 'This is a test message'")
        print("\nPhone number must be in E.164 format (e.g., +31612345678)")
        sys.exit(1)

    phone_number = sys.argv[1]

    # Default test message
    if len(sys.argv) >= 3:
        message = sys.argv[2]
    else:
        message = "This is a test message from BCourse. Testing SMS functionality."

    # Validate phone number format
    if not phone_number.startswith('+'):
        print("ERROR: Phone number must be in E.164 format and start with '+'")
        print("Example: +31612345678 (Netherlands) or +1234567890 (USA)")
        sys.exit(1)

    # Create Flask app context (needed for config access)
    app = create_app()

    with app.app_context():
        # Check if AWS credentials are configured
        if not app.config.get('AWS_ACCESS_KEY_ID') or not app.config.get('AWS_SECRET_ACCESS_KEY'):
            print("ERROR: AWS credentials not configured in .env file")
            print("\nPlease ensure the following variables are set in your .env file:")
            print("  AWS_REGION=eu-central-1  (or your preferred region)")
            print("  AWS_ACCESS_KEY_ID=your_access_key")
            print("  AWS_SECRET_ACCESS_KEY=your_secret_key")
            print("  AWS_SNS_SENDER_ID=BCOURSE  (optional)")
            sys.exit(1)

        print(f"\n{'='*60}")
        print(f"Sending Test SMS")
        print(f"{'='*60}")
        print(f"To: {phone_number}")
        print(f"Message: {message}")
        print(f"Message length: {len(message)} characters")
        print(f"AWS Region: {app.config.get('AWS_REGION')}")
        print(f"Sender ID: {app.config.get('AWS_SNS_SENDER_ID', 'BCOURSE')}")
        print(f"{'='*60}\n")

        # Send the SMS
        success, error = send_sms(phone_number, message)

        if success:
            print("✓ SMS sent successfully!")
            print(f"\nNote: Check your phone ({phone_number}) for the message.")
        else:
            print(f"✗ Failed to send SMS: {error}")
            print("\nTroubleshooting:")
            print("1. Verify AWS credentials are correct")
            print("2. Check AWS SNS is enabled in your region")
            print("3. Verify phone number is in E.164 format")
            print("4. Check AWS SNS spending limits")
            print("5. For some regions, you may need to request SMS capability")
            sys.exit(1)

if __name__ == "__main__":
    main()
