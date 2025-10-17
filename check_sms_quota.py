#!/usr/bin/env python3
"""
Check AWS SNS SMS quota and spending limits.

Usage:
    python check_sms_quota.py
"""
import boto3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_sms_quota():
    """Check AWS SNS SMS spending limits and attributes."""

    aws_region = os.getenv('AWS_REGION', 'eu-central-1')
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

    if not aws_access_key or not aws_secret_key:
        print("ERROR: AWS credentials not found in .env file")
        return

    print(f"Checking AWS SNS quota in region: {aws_region}")
    print("=" * 60)

    try:
        # Create SNS client
        sns_client = boto3.client(
            'sns',
            region_name=aws_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )

        # Get SMS attributes
        response = sns_client.get_sms_attributes()
        attributes = response.get('attributes', {})

        print("\nCurrent SMS Settings:")
        print("-" * 60)

        # Display all attributes
        for key, value in attributes.items():
            print(f"{key:30} : {value}")

        # Highlight important quota information
        print("\n" + "=" * 60)
        print("QUOTA INFORMATION:")
        print("=" * 60)

        spend_limit = attributes.get('MonthlySpendLimit', 'Not set')
        default_type = attributes.get('DefaultSMSType', 'Not set')

        print(f"\nMonthly Spend Limit          : ${spend_limit}")
        print(f"Default SMS Type             : {default_type}")
        print(f"Default Sender ID            : {attributes.get('DefaultSenderID', 'Not set')}")

        print("\nRECOMMENDATIONS:")
        print("-" * 60)

        if spend_limit == 'Not set' or float(spend_limit) < 10:
            print("WARNING: Monthly spend limit is very low or not set!")
            print("  -> Request quota increase at: https://console.aws.amazon.com/support/home")
            print("  -> Or go to: SNS Console -> Text messaging (SMS) -> Account information")

        # Try to get account-level information via Service Quotas API
        print("\n" + "=" * 60)
        print("CHECKING SERVICE QUOTAS:")
        print("=" * 60)

        try:
            quota_client = boto3.client(
                'service-quotas',
                region_name=aws_region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )

            # Get SNS quotas
            quotas_response = quota_client.list_service_quotas(
                ServiceCode='sns'
            )

            print("\nSNS Service Quotas:")
            for quota in quotas_response.get('Quotas', []):
                if 'SMS' in quota.get('QuotaName', ''):
                    print(f"\n{quota.get('QuotaName')}:")
                    print(f"  Value: {quota.get('Value')}")
                    print(f"  Adjustable: {quota.get('Adjustable')}")

        except Exception as e:
            print(f"\nCould not retrieve Service Quotas: {e}")
            print("(This may require additional IAM permissions)")

        # Check CloudWatch logs status
        print("\n" + "=" * 60)
        print("CLOUDWATCH LOGGING:")
        print("=" * 60)

        delivery_status_success_rate = attributes.get('DeliveryStatusSuccessSamplingRate')
        delivery_status_iam_role = attributes.get('DeliveryStatusIAMRole')

        if delivery_status_iam_role:
            print(f"\nDelivery logging ENABLED")
            print(f"  IAM Role: {delivery_status_iam_role}")
            print(f"  Success sampling: {delivery_status_success_rate}%")
            print(f"\nCheck logs at CloudWatch:")
            print(f"  Log group: /aws/sns/{aws_region}/<account-id>/DirectPublish")
        else:
            print("\nWARNING: Delivery status logging NOT enabled")
            print("Enable it to track SMS delivery failures!")
            print("\nTo enable:")
            print("1. Create IAM role with CloudWatch Logs write permissions")
            print("2. Run: aws sns set-sms-attributes \\")
            print("     --attributes DeliveryStatusIAMRole=<role-arn>")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_sms_quota()
