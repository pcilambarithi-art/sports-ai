-- PostgreSQL 16 Database Initialization Script for ApexPulse AI Sports Coaching System
-- Run as postgres superuser: psql -U postgres -f init_postgres.sql

CREATE USER apexpulse WITH PASSWORD 'change_this_secure_password';
CREATE DATABASE sports_coaching OWNER apexpulse;
GRANT ALL PRIVILEGES ON DATABASE sports_coaching TO apexpulse;
