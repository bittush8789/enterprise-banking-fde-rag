-- Initialize BankAssist AI Database
CREATE DATABASE IF NOT EXISTS bankassist CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE bankassist;

-- Grant privileges
GRANT ALL PRIVILEGES ON bankassist.* TO 'bankassist_user'@'%';
FLUSH PRIVILEGES;
