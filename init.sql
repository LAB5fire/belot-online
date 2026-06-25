-- PostgreSQL initialization for Belot Analyzer
-- Tables are created automatically by SQLAlchemy on startup.
-- This file sets up extensions and initial data.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Ensure the belot user has full privileges
GRANT ALL PRIVILEGES ON DATABASE belot TO belot;
