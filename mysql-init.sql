CREATE DATABASE IF NOT EXISTS tatneft_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'tatneft_user'@'%' IDENTIFIED BY 'tatneft_pass';
GRANT ALL PRIVILEGES ON tatneft_db.* TO 'tatneft_user'@'%';
FLUSH PRIVILEGES;