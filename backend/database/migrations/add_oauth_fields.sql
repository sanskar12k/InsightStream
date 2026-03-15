-- Migration: Add Google OAuth support to users table
-- Date: 2026-03-15
-- Description: Adds google_id and auth_provider fields to support OAuth authentication

-- Add google_id column for Google OAuth
ALTER TABLE users
ADD COLUMN google_id VARCHAR(255) NULL AFTER password_hash,
ADD UNIQUE INDEX idx_google_id (google_id);

-- Add auth_provider column
ALTER TABLE users
ADD COLUMN auth_provider ENUM('local', 'google') NOT NULL DEFAULT 'local' AFTER google_id,
ADD INDEX idx_auth_provider (auth_provider);

-- Make password_hash nullable (OAuth users don't have passwords)
ALTER TABLE users
MODIFY COLUMN password_hash VARCHAR(255) NULL;

-- Update existing users to have 'local' auth_provider
UPDATE users
SET auth_provider = 'local'
WHERE auth_provider IS NULL;
