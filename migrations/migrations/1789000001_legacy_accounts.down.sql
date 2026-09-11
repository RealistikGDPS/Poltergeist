ALTER TABLE levels MODIFY name VARCHAR(20) NOT NULL;
ALTER TABLE user_credentials
  DROP COLUMN legacy_password_bcrypt,
  MODIFY gjp2_bcrypt VARCHAR(128) NOT NULL;
ALTER TABLE users
  DROP INDEX ix_users_email,
  ADD UNIQUE INDEX ux_users_email (email);
