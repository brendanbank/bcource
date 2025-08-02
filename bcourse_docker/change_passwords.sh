#!/bin/bash

# Change MySQL Passwords in Existing Database
# This script helps you change passwords without losing data

set -e

echo "🔐 Change MySQL Passwords in Existing Database"
echo "=============================================="

# Check if containers are running
if ! docker compose ps | grep -q "bcourse-mysql"; then
    echo "❌ MySQL container is not running"
    echo "Start containers first: docker compose up -d"
    exit 1
fi

# Generate new passwords
echo "🔐 Generating new secure passwords..."
ROOT_PASSWORD=$(python3 -c "
import secrets
import string
chars = string.ascii_letters + string.digits + '!@#$%^&*'
print(''.join(secrets.choice(chars) for _ in range(32)))
")

USER_PASSWORD=$(python3 -c "
import secrets
import string
chars = string.ascii_letters + string.digits + '!@#$%^&*'
print(''.join(secrets.choice(chars) for _ in range(24)))
")

echo "📝 New passwords generated:"
echo "   Root password: $ROOT_PASSWORD"
echo "   User password: $USER_PASSWORD"
echo ""

# Get current root password from .env
CURRENT_ROOT_PASSWORD=$(grep "^MYSQL_ROOT_PASSWORD=" ../.env | cut -d'=' -f2)
if [[ -z "$CURRENT_ROOT_PASSWORD" ]]; then
    echo "❌ Current root password not found in .env file"
    exit 1
fi

echo "🔍 Current root password found in .env file"
echo ""

# Create temporary SQL file with new passwords
TEMP_SQL="/tmp/change_passwords_$(date +%s).sql"
cat > "$TEMP_SQL" << EOF
-- Change MySQL Passwords
ALTER USER 'root'@'localhost' IDENTIFIED BY '$ROOT_PASSWORD';
ALTER USER 'bcourse'@'%' IDENTIFIED BY '$USER_PASSWORD';
FLUSH PRIVILEGES;
SELECT 'Passwords changed successfully' as status;
EOF

echo "📝 Created temporary SQL file: $TEMP_SQL"
echo ""

# Execute the password change
echo "🔄 Changing passwords in MySQL..."
if docker exec -i bcourse-mysql mysql -u root -p"$CURRENT_ROOT_PASSWORD" < "$TEMP_SQL"; then
    echo "✅ Passwords changed successfully in MySQL"
else
    echo "❌ Failed to change passwords in MySQL"
    echo "Check if the current root password is correct"
    rm -f "$TEMP_SQL"
    exit 1
fi

# Clean up temporary file
rm -f "$TEMP_SQL"

# Update .env file
echo ""
echo "📝 Updating .env file with new passwords..."
cp ../.env ../.env.backup.$(date +%Y%m%d_%H%M%S)

sed -i '' "s/^MYSQL_ROOT_PASSWORD=.*/MYSQL_ROOT_PASSWORD=$ROOT_PASSWORD/" ../.env
sed -i '' "s/^MYSQL_PASSWORD=.*/MYSQL_PASSWORD=$USER_PASSWORD/" ../.env

echo "✅ .env file updated with new passwords"
echo ""

echo "🎉 Password change completed!"
echo ""
echo "📝 Summary:"
echo "   ✅ MySQL passwords changed"
echo "   ✅ .env file updated"
echo "   ✅ Backup created: ../.env.backup.*"
echo ""
echo "⚠️  IMPORTANT:"
echo "   1. Restart your application: docker compose restart bcourse"
echo "   2. Test the application to ensure it can connect"
echo "   3. Store the new passwords securely"
echo "   4. The old passwords are no longer valid" 