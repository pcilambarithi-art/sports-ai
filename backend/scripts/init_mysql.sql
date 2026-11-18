-- MySQL 8 Database Initialization Script for ApexPulse AI Sports Coaching System
-- Run as MySQL root: mysql -u root -p < init_mysql.sql

CREATE DATABASE IF NOT EXISTS sports_coaching
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'apexpulse'@'localhost' IDENTIFIED BY 'change_this_secure_password';
GRANT ALL PRIVILEGES ON sports_coaching.* TO 'apexpulse'@'localhost';
FLUSH PRIVILEGES;
