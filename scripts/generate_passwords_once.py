#!/usr/bin/env python3
"""
Generate strong passwords once for manual copying to .env file
These passwords will remain the same until you manually change them.
"""

import secrets
import string

def generate_secure_password(length=32):
    """Generate a cryptographically secure password."""
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Ensure at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special_chars)
    ]
    
    # Fill the rest with random characters
    all_chars = lowercase + uppercase + digits + special_chars
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))
    
    # Shuffle the password
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    
    return ''.join(password_list)

def main():
    print("🔐 Generate Strong Passwords for .env File")
    print("=" * 50)
    print()
    print("These passwords will be used for your database.")
    print("Copy them to your .env file and they'll remain the same.")
    print()
    
    # Generate passwords
    root_password = generate_secure_password(32)
    user_password = generate_secure_password(24)
    
    print("📝 Copy these lines to your .env file:")
    print("=" * 50)
    # nosec: intentional - this script's purpose is to generate and display passwords for manual copying
    print(f"MYSQL_ROOT_PASSWORD={root_password}")  # noqa: T201
    print(f"MYSQL_PASSWORD={user_password}")  # noqa: T201
    print("=" * 50)
    print()
    
    print("📋 Password Details:")
    print(f"   Root password: {len(root_password)} characters")
    print(f"   User password: {len(user_password)} characters")
    print()
    
    print("✅ Security Requirements Met:")
    print("   ✅ Mixed case (upper and lower)")
    print("   ✅ Numbers included")
    print("   ✅ Special characters included")
    print("   ✅ Cryptographically secure")
    print()
    
    print("⚠️  IMPORTANT:")
    print("   1. Store these passwords securely")
    print("   2. Never commit them to version control")
    print("   3. These passwords will remain the same until you change them")
    print("   4. After updating .env, restart containers: docker compose down && docker compose up -d")

if __name__ == "__main__":
    main() 