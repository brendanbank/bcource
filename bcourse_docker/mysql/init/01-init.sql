-- MySQL initialization script for bcourse
-- This script runs when the MySQL container is first created

-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS bcourse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create postalcodes database
CREATE DATABASE IF NOT EXISTS postalcodes CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use the database
USE bcourse;

-- Create additional databases if needed
-- CREATE DATABASE IF NOT EXISTS bcourse_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Grant privileges to the bcourse user
GRANT ALL PRIVILEGES ON bcourse.* TO 'bcourse'@'%';
GRANT ALL PRIVILEGES ON postalcodes.* TO 'bcourse'@'%';
GRANT ALL PRIVILEGES ON bcourse_test.* TO 'bcourse'@'%' IF EXISTS;

-- Flush privileges to apply changes
FLUSH PRIVILEGES;

-- Show databases for verification
SHOW DATABASES; 