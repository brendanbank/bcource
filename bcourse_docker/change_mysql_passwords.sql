-- Change MySQL Passwords Safely
-- Run this script while connected to MySQL as root

-- Change root password
ALTER USER 'root'@'localhost' IDENTIFIED BY 'NEW_ROOT_PASSWORD_HERE';

-- Change bcourse user password
ALTER USER 'bcourse'@'%' IDENTIFIED BY 'NEW_USER_PASSWORD_HERE';

-- Flush privileges to apply changes
FLUSH PRIVILEGES;

-- Verify the changes
SELECT User, Host FROM mysql.user WHERE User IN ('root', 'bcourse'); 