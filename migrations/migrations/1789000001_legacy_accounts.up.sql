-- Accommodates accounts imported from the 2.1-era server.
--   * Old registrations were not unique per email; the service still refuses a
--     duplicate on registration, but the index can no longer enforce it.
--   * A 2.1 client presented plaintext passwords, so those accounts only hold
--     bcrypt(plaintext). A 2.2 client presents gjp2, which cannot be checked
--     against that hash; the legacy hash is kept for a future web login that
--     can re-hash the password into gjp2_bcrypt.
--   * Level names were allowed up to 32 characters.

ALTER TABLE users
  DROP INDEX ux_users_email,
  ADD INDEX ix_users_email (email);

ALTER TABLE user_credentials
  MODIFY gjp2_bcrypt VARCHAR(128) NULL,
  ADD COLUMN legacy_password_bcrypt VARCHAR(128) NULL COMMENT 'bcrypt(plaintext) from 2.1; needs a plaintext password to verify' AFTER gjp2_bcrypt;

ALTER TABLE levels MODIFY name VARCHAR(32) NOT NULL;
