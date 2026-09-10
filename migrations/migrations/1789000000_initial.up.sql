-- Poltergeist database schema (Geometry Dash 2.2). MySQL 9, InnoDB, utf8mb4.
--
-- Conventions
--   * DATETIME columns end in `_at` and hold UTC; the pool runs with
--     time_zone = '+00:00'.
--   * Deletes are soft (`deleted_at`). Listing indexes are ordered as
--     equality columns, `deleted_at`, sort column.
--   * Rows pairing two users are unique per pair; re-adding clears `deleted_at`.
--   * Small integer columns with a fixed vocabulary carry it in a comment.
--     MySQL ENUM is used for server-internal discriminators.
--   * Colours are MEDIUMINT UNSIGNED holding 0xRRGGBB. IPs are VARBINARY(16).
--   * Large content (level strings, replays, account saves) lives in object
--     storage keyed by row id. Tables hold metadata only.
--   * Permissions are dotted strings (`levels.rate`, `users.ban.*`) granted
--     through roles and per-user overrides. What a user may do is never a
--     column on the user.
--
-- A user is both the GD account and the GD player; both wire ids are users.id.

SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- ---------------------------------------------------------------------------
-- Users
-- ---------------------------------------------------------------------------

CREATE TABLE users (
  id                       INT UNSIGNED     NOT NULL AUTO_INCREMENT,
  username                 VARCHAR(20)      NOT NULL,
  email                    VARCHAR(255)     NOT NULL,
  comment_colour           MEDIUMINT UNSIGNED NULL,
  message_privacy          TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 all, 1 friends, 2 none',
  friend_request_privacy   TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 all, 1 none',
  comment_history_privacy  TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 all, 1 friends, 2 none',
  youtube                  VARCHAR(64)      NOT NULL DEFAULT '',
  twitter                  VARCHAR(64)      NOT NULL DEFAULT '',
  twitch                   VARCHAR(64)      NOT NULL DEFAULT '',
  discord                  VARCHAR(64)      NOT NULL DEFAULT '',
  instagram                VARCHAR(64)      NOT NULL DEFAULT '',
  tiktok                   VARCHAR(64)      NOT NULL DEFAULT '',
  custom                   VARCHAR(64)      NOT NULL DEFAULT '',
  registered_at            DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_seen_at             DATETIME         NULL,
  deleted_at               DATETIME         NULL,
  PRIMARY KEY (id),
  UNIQUE KEY ux_users_username (username),
  UNIQUE KEY ux_users_email (email),
  CONSTRAINT ck_users_message_privacy CHECK (message_privacy BETWEEN 0 AND 2),
  CONSTRAINT ck_users_friend_request_privacy CHECK (friend_request_privacy BETWEEN 0 AND 1),
  CONSTRAINT ck_users_comment_history_privacy CHECK (comment_history_privacy BETWEEN 0 AND 2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- The 2.2 client only ever presents gjp2 (sha1 of the password and a salt), so
-- that is what is hashed.
CREATE TABLE user_credentials (
  user_id      INT UNSIGNED NOT NULL,
  gjp2_bcrypt  VARCHAR(128) NOT NULL,
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  CONSTRAINT fk_user_credentials_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE user_stats (
  user_id          INT UNSIGNED      NOT NULL,
  stars            INT UNSIGNED      NOT NULL DEFAULT 0,
  moons            INT UNSIGNED      NOT NULL DEFAULT 0,
  demons           INT UNSIGNED      NOT NULL DEFAULT 0,
  diamonds         INT UNSIGNED      NOT NULL DEFAULT 0,
  secret_coins     INT UNSIGNED      NOT NULL DEFAULT 0,
  user_coins       INT UNSIGNED      NOT NULL DEFAULT 0,
  creator_points   INT UNSIGNED      NOT NULL DEFAULT 0,
  icon_type        TINYINT UNSIGNED  NOT NULL DEFAULT 0 COMMENT '0 cube, 1 ship, 2 ball, 3 ufo, 4 wave, 5 robot, 6 spider, 7 swing, 8 jetpack',
  colour1          TINYINT UNSIGNED  NOT NULL DEFAULT 0,
  colour2          TINYINT UNSIGNED  NOT NULL DEFAULT 3,
  colour3          TINYINT           NOT NULL DEFAULT -1 COMMENT 'glow colour, -1 follows colour2',
  glow             BOOLEAN           NOT NULL DEFAULT FALSE,
  icon_cube        SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  icon_ship        SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  icon_ball        SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  icon_ufo         SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  icon_wave        SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  icon_robot       SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  icon_spider      SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  icon_swing       SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  icon_jetpack     SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  icon_explosion   SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  demons_easy               SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  demons_medium             SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  demons_hard               SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  demons_insane             SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  demons_extreme            SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  demons_easy_platformer    SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  demons_medium_platformer  SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  demons_hard_platformer    SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  demons_insane_platformer  SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  demons_extreme_platformer SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  demons_weekly             SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  demons_gauntlet           SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  demons_event              SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  classic_auto      INT UNSIGNED NOT NULL DEFAULT 0,
  classic_easy      INT UNSIGNED NOT NULL DEFAULT 0,
  classic_normal    INT UNSIGNED NOT NULL DEFAULT 0,
  classic_hard      INT UNSIGNED NOT NULL DEFAULT 0,
  classic_harder    INT UNSIGNED NOT NULL DEFAULT 0,
  classic_insane    INT UNSIGNED NOT NULL DEFAULT 0,
  classic_daily     INT UNSIGNED NOT NULL DEFAULT 0,
  classic_gauntlet  INT UNSIGNED NOT NULL DEFAULT 0,
  platformer_auto   INT UNSIGNED NOT NULL DEFAULT 0,
  platformer_easy   INT UNSIGNED NOT NULL DEFAULT 0,
  platformer_normal INT UNSIGNED NOT NULL DEFAULT 0,
  platformer_hard   INT UNSIGNED NOT NULL DEFAULT 0,
  platformer_harder INT UNSIGNED NOT NULL DEFAULT 0,
  platformer_insane INT UNSIGNED NOT NULL DEFAULT 0,
  platformer_event  INT UNSIGNED NOT NULL DEFAULT 0,
  updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  KEY ix_user_stats_stars (stars DESC),
  KEY ix_user_stats_moons (moons DESC),
  KEY ix_user_stats_demons (demons DESC),
  KEY ix_user_stats_user_coins (user_coins DESC),
  KEY ix_user_stats_creator_points (creator_points DESC),
  CONSTRAINT fk_user_stats_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT ck_user_stats_icon_type CHECK (icon_type BETWEEN 0 AND 8),
  CONSTRAINT ck_user_stats_colour3 CHECK (colour3 >= -1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Save data itself lives in object storage under the user id.
CREATE TABLE user_saves (
  user_id             INT UNSIGNED     NOT NULL,
  game_version        TINYINT UNSIGNED NOT NULL,
  binary_version      TINYINT UNSIGNED NOT NULL,
  game_manager_bytes  INT UNSIGNED     NOT NULL,
  local_levels_bytes  INT UNSIGNED     NOT NULL,
  saved_at            DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  CONSTRAINT fk_user_saves_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Active when revoked_at IS NULL AND (expires_at IS NULL OR expires_at > NOW()).
CREATE TABLE user_bans (
  id                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id             INT UNSIGNED NOT NULL,
  type                ENUM('account', 'comment', 'upload', 'leaderboard', 'creator') NOT NULL,
  reason              VARCHAR(255) NOT NULL DEFAULT '',
  issued_by_user_id   INT UNSIGNED NULL,
  created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at          DATETIME     NULL COMMENT 'NULL is permanent',
  revoked_at          DATETIME     NULL,
  revoked_by_user_id  INT UNSIGNED NULL,
  PRIMARY KEY (id),
  KEY ix_user_bans_user_type (user_id, type, revoked_at, expires_at),
  CONSTRAINT fk_user_bans_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_user_bans_issued_by FOREIGN KEY (issued_by_user_id) REFERENCES users (id),
  CONSTRAINT fk_user_bans_revoked_by FOREIGN KEY (revoked_by_user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE user_devices (
  user_id        INT UNSIGNED     NOT NULL,
  udid           VARCHAR(64)      NOT NULL,
  platform       TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 unknown, 1 ios, 2 android, 3 windows, 8 macos',
  first_seen_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_seen_at   DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, udid),
  KEY ix_user_devices_udid (udid),
  CONSTRAINT fk_user_devices_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------------
-- Permissions
-- ---------------------------------------------------------------------------

CREATE TABLE roles (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name         VARCHAR(32)  NOT NULL,
  description  VARCHAR(255) NOT NULL DEFAULT '',
  priority     INT          NOT NULL DEFAULT 0 COMMENT 'higher roles may manage lower ones',
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at   DATETIME     NULL,
  PRIMARY KEY (id),
  UNIQUE KEY ux_roles_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- A permission is a dotted string. A trailing `.*` or a bare `*` matches every
-- permission under that prefix.
CREATE TABLE role_permissions (
  role_id     INT UNSIGNED NOT NULL,
  permission  VARCHAR(64)  NOT NULL,
  PRIMARY KEY (role_id, permission),
  CONSTRAINT fk_role_permissions_role FOREIGN KEY (role_id) REFERENCES roles (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE user_roles (
  user_id             INT UNSIGNED NOT NULL,
  role_id             INT UNSIGNED NOT NULL,
  granted_by_user_id  INT UNSIGNED NULL,
  created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at          DATETIME     NULL COMMENT 'NULL is permanent',
  deleted_at          DATETIME     NULL,
  PRIMARY KEY (user_id, role_id),
  KEY ix_user_roles_role (role_id),
  CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles (id),
  CONSTRAINT fk_user_roles_granted_by FOREIGN KEY (granted_by_user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Per-user overrides on top of roles. A deny always wins over any allow.
CREATE TABLE user_permissions (
  user_id             INT UNSIGNED NOT NULL,
  permission          VARCHAR(64)  NOT NULL,
  effect              ENUM('allow', 'deny') NOT NULL,
  granted_by_user_id  INT UNSIGNED NULL,
  created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at          DATETIME     NULL,
  deleted_at          DATETIME     NULL,
  PRIMARY KEY (user_id, permission),
  CONSTRAINT fk_user_permissions_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_user_permissions_granted_by FOREIGN KEY (granted_by_user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------------
-- Social
-- ---------------------------------------------------------------------------

-- Two rows per friendship, one per direction, written together.
CREATE TABLE friendships (
  user_id         INT UNSIGNED NOT NULL,
  friend_user_id  INT UNSIGNED NOT NULL,
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  seen_at         DATETIME     NULL,
  deleted_at      DATETIME     NULL,
  PRIMARY KEY (user_id, friend_user_id),
  KEY ix_friendships_friend (friend_user_id),
  CONSTRAINT fk_friendships_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_friendships_friend FOREIGN KEY (friend_user_id) REFERENCES users (id),
  CONSTRAINT ck_friendships_not_self CHECK (user_id <> friend_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE user_blocks (
  user_id          INT UNSIGNED NOT NULL,
  blocked_user_id  INT UNSIGNED NOT NULL,
  created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at       DATETIME     NULL,
  PRIMARY KEY (user_id, blocked_user_id),
  KEY ix_user_blocks_blocked (blocked_user_id),
  CONSTRAINT fk_user_blocks_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_user_blocks_blocked FOREIGN KEY (blocked_user_id) REFERENCES users (id),
  CONSTRAINT ck_user_blocks_not_self CHECK (user_id <> blocked_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE friend_requests (
  id                 INT UNSIGNED NOT NULL AUTO_INCREMENT,
  sender_user_id     INT UNSIGNED NOT NULL,
  recipient_user_id  INT UNSIGNED NOT NULL,
  message            VARCHAR(140) NOT NULL DEFAULT '',
  created_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  read_at            DATETIME     NULL,
  deleted_at         DATETIME     NULL,
  PRIMARY KEY (id),
  UNIQUE KEY ux_friend_requests_pair (sender_user_id, recipient_user_id),
  KEY ix_friend_requests_inbox (recipient_user_id, deleted_at, created_at DESC),
  KEY ix_friend_requests_outbox (sender_user_id, deleted_at, created_at DESC),
  CONSTRAINT fk_friend_requests_sender FOREIGN KEY (sender_user_id) REFERENCES users (id),
  CONSTRAINT fk_friend_requests_recipient FOREIGN KEY (recipient_user_id) REFERENCES users (id),
  CONSTRAINT ck_friend_requests_not_self CHECK (sender_user_id <> recipient_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE messages (
  id                    INT UNSIGNED NOT NULL AUTO_INCREMENT,
  sender_user_id        INT UNSIGNED NOT NULL,
  recipient_user_id     INT UNSIGNED NOT NULL,
  subject               VARCHAR(35)  NOT NULL,
  body                  VARCHAR(200) NOT NULL,
  created_at            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  read_at               DATETIME     NULL,
  sender_deleted_at     DATETIME     NULL,
  recipient_deleted_at  DATETIME     NULL,
  PRIMARY KEY (id),
  KEY ix_messages_inbox (recipient_user_id, recipient_deleted_at, created_at DESC),
  KEY ix_messages_outbox (sender_user_id, sender_deleted_at, created_at DESC),
  CONSTRAINT fk_messages_sender FOREIGN KEY (sender_user_id) REFERENCES users (id),
  CONSTRAINT fk_messages_recipient FOREIGN KEY (recipient_user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE account_comments (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id     INT UNSIGNED NOT NULL,
  content     VARCHAR(140) NOT NULL,
  likes       INT          NOT NULL DEFAULT 0,
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at  DATETIME     NULL,
  PRIMARY KEY (id),
  KEY ix_account_comments_user (user_id, deleted_at, created_at DESC),
  CONSTRAINT fk_account_comments_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------------
-- Songs
-- ---------------------------------------------------------------------------

-- Upstream (Newgrounds, music library) ids are inserted explicitly; rows
-- created here are allocated from 100,000,000 so they never collide.
CREATE TABLE artists (
  id               INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name             VARCHAR(64)  NOT NULL,
  youtube_channel  VARCHAR(64)  NOT NULL DEFAULT '',
  website          VARCHAR(255) NOT NULL DEFAULT '',
  scouted          BOOLEAN      NOT NULL DEFAULT FALSE,
  created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at       DATETIME     NULL,
  PRIMARY KEY (id),
  KEY ix_artists_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci AUTO_INCREMENT=100000000;

CREATE TABLE songs (
  id                   INT UNSIGNED     NOT NULL AUTO_INCREMENT,
  name                 VARCHAR(128)     NOT NULL,
  artist_id            INT UNSIGNED     NOT NULL,
  size_bytes           INT UNSIGNED     NOT NULL,
  url                  VARCHAR(512)     NOT NULL,
  source               ENUM('newgrounds', 'library', 'custom') NOT NULL,
  video_id             VARCHAR(16)      NOT NULL DEFAULT '',
  priority             INT              NOT NULL DEFAULT 0,
  nong                 TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 none, 1 NCS, 2 CHOMPO',
  is_new               BOOLEAN          NOT NULL DEFAULT FALSE,
  new_badge            TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 yellow, 1 blue',
  soundtrack_url       VARCHAR(512)     NOT NULL DEFAULT '',
  uploaded_by_user_id  INT UNSIGNED     NULL,
  created_at           DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  disabled_at          DATETIME         NULL,
  deleted_at           DATETIME         NULL,
  PRIMARY KEY (id),
  KEY ix_songs_artist (artist_id),
  KEY ix_songs_name (name),
  CONSTRAINT fk_songs_artist FOREIGN KEY (artist_id) REFERENCES artists (id),
  CONSTRAINT fk_songs_uploaded_by FOREIGN KEY (uploaded_by_user_id) REFERENCES users (id),
  CONSTRAINT ck_songs_nong CHECK (nong BETWEEN 0 AND 2),
  CONSTRAINT ck_songs_new_badge CHECK (new_badge BETWEEN 0 AND 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci AUTO_INCREMENT=100000000;

-- ---------------------------------------------------------------------------
-- Levels
-- ---------------------------------------------------------------------------

-- updated_at is the content update time, set by the app on re-upload only.
-- custom_song_id is not a foreign key: song rows are fetched from upstream
-- lazily and an upload must not fail because upstream is unreachable.
CREATE TABLE levels (
  id                  INT UNSIGNED       NOT NULL AUTO_INCREMENT,
  user_id             INT UNSIGNED       NOT NULL,
  name                VARCHAR(20)        NOT NULL,
  description         VARCHAR(300)       NOT NULL DEFAULT '',
  version             SMALLINT UNSIGNED  NOT NULL DEFAULT 1,
  length              TINYINT UNSIGNED   NOT NULL DEFAULT 0 COMMENT '0 tiny, 1 short, 2 medium, 3 long, 4 xl, 5 platformer',
  official_song_id    SMALLINT UNSIGNED  NOT NULL DEFAULT 0,
  custom_song_id      INT UNSIGNED       NULL,
  game_version        TINYINT UNSIGNED   NOT NULL,
  binary_version      TINYINT UNSIGNED   NOT NULL DEFAULT 0,
  visibility          TINYINT UNSIGNED   NOT NULL DEFAULT 0 COMMENT '0 public, 1 friends, 2 unlisted',
  two_player          BOOLEAN            NOT NULL DEFAULT FALSE,
  low_detail_mode     BOOLEAN            NOT NULL DEFAULT FALSE,
  original_id         INT UNSIGNED       NULL,
  copyable            BOOLEAN            NOT NULL DEFAULT FALSE,
  copy_password       MEDIUMINT UNSIGNED NULL COMMENT 'NULL with copyable is a free copy',
  object_count        INT UNSIGNED       NOT NULL DEFAULT 0,
  coins               TINYINT UNSIGNED   NOT NULL DEFAULT 0,
  coins_verified      BOOLEAN            NOT NULL DEFAULT FALSE,
  requested_stars     TINYINT UNSIGNED   NOT NULL DEFAULT 0,
  editor_seconds      INT UNSIGNED       NOT NULL DEFAULT 0,
  editor_seconds_copies INT UNSIGNED     NOT NULL DEFAULT 0,
  verification_frames INT UNSIGNED       NOT NULL DEFAULT 0 COMMENT '240 per second',
  downloads           INT UNSIGNED       NOT NULL DEFAULT 0,
  likes               INT                NOT NULL DEFAULT 0,
  difficulty          TINYINT            NOT NULL DEFAULT -1 COMMENT '-1 unrated, 0 auto, 1 easy .. 5 insane, 6 easy demon .. 10 extreme demon',
  stars               TINYINT UNSIGNED   NOT NULL DEFAULT 0,
  feature_order       INT UNSIGNED       NOT NULL DEFAULT 0 COMMENT '0 not featured, higher sorts first',
  rating              TINYINT UNSIGNED   NOT NULL DEFAULT 0 COMMENT '0 none, 1 epic, 2 legendary, 3 mythic',
  rated_at            DATETIME           NULL,
  rated_by_user_id    INT UNSIGNED       NULL,
  update_locked       BOOLEAN            NOT NULL DEFAULT FALSE,
  uploaded_at         DATETIME           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at          DATETIME           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at          DATETIME           NULL,
  PRIMARY KEY (id),
  KEY ix_levels_user (user_id, deleted_at, uploaded_at DESC),
  KEY ix_levels_user_name (user_id, name),
  KEY ix_levels_likes (deleted_at, visibility, likes DESC),
  KEY ix_levels_downloads (deleted_at, visibility, downloads DESC),
  KEY ix_levels_uploaded (deleted_at, visibility, uploaded_at DESC),
  KEY ix_levels_featured (deleted_at, visibility, feature_order DESC),
  KEY ix_levels_rated (deleted_at, visibility, rated_at DESC),
  KEY ix_levels_stars (deleted_at, stars),
  KEY ix_levels_name (deleted_at, visibility, name),
  KEY ix_levels_custom_song (custom_song_id),
  KEY ix_levels_original (original_id),
  CONSTRAINT fk_levels_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_levels_original FOREIGN KEY (original_id) REFERENCES levels (id),
  CONSTRAINT fk_levels_rated_by FOREIGN KEY (rated_by_user_id) REFERENCES users (id),
  CONSTRAINT ck_levels_length CHECK (length BETWEEN 0 AND 5),
  CONSTRAINT ck_levels_visibility CHECK (visibility BETWEEN 0 AND 2),
  CONSTRAINT ck_levels_copy_password CHECK (copy_password IS NULL OR (copyable AND copy_password <= 999999)),
  CONSTRAINT ck_levels_coins CHECK (coins <= 3),
  CONSTRAINT ck_levels_difficulty CHECK (difficulty BETWEEN -1 AND 10),
  CONSTRAINT ck_levels_stars CHECK (stars <= 10),
  CONSTRAINT ck_levels_rating CHECK (rating BETWEEN 0 AND 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- The level string and verification replay live in object storage under the
-- level id. This row describes the stored object. Song and SFX ids reference
-- the client's music and SFX libraries, which are not mirrored here.
CREATE TABLE level_data (
  level_id      INT UNSIGNED  NOT NULL,
  size_bytes    INT UNSIGNED  NOT NULL,
  sha1          BINARY(20)    NOT NULL,
  extra_string  VARCHAR(1024) NOT NULL DEFAULT '' COMMENT 'opaque client capacity string, echoed on download',
  song_ids      JSON          NOT NULL DEFAULT (JSON_ARRAY()),
  sfx_ids       JSON          NOT NULL DEFAULT (JSON_ARRAY()),
  has_replay    BOOLEAN       NOT NULL DEFAULT FALSE,
  updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (level_id),
  CONSTRAINT fk_level_data_level FOREIGN KEY (level_id) REFERENCES levels (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------------
-- Lists, packs, gauntlets, timely
-- ---------------------------------------------------------------------------

CREATE TABLE level_lists (
  id                  INT UNSIGNED      NOT NULL AUTO_INCREMENT,
  user_id             INT UNSIGNED      NOT NULL,
  name                VARCHAR(64)       NOT NULL,
  description         VARCHAR(300)      NOT NULL DEFAULT '',
  version             SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  difficulty          TINYINT           NOT NULL DEFAULT -1 COMMENT 'same scale as levels.difficulty',
  visibility          TINYINT UNSIGNED  NOT NULL DEFAULT 0 COMMENT '0 public, 1 friends, 2 unlisted',
  original_id         INT UNSIGNED      NULL,
  downloads           INT UNSIGNED      NOT NULL DEFAULT 0,
  likes               INT               NOT NULL DEFAULT 0,
  rated_at            DATETIME          NULL,
  rated_by_user_id    INT UNSIGNED      NULL,
  reward_diamonds     TINYINT UNSIGNED  NOT NULL DEFAULT 0,
  reward_requirement  TINYINT UNSIGNED  NOT NULL DEFAULT 0 COMMENT 'levels to complete for the reward',
  uploaded_at         DATETIME          NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at          DATETIME          NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at          DATETIME          NULL,
  PRIMARY KEY (id),
  KEY ix_level_lists_user (user_id, deleted_at, uploaded_at DESC),
  KEY ix_level_lists_likes (deleted_at, visibility, likes DESC),
  KEY ix_level_lists_downloads (deleted_at, visibility, downloads DESC),
  KEY ix_level_lists_uploaded (deleted_at, visibility, uploaded_at DESC),
  KEY ix_level_lists_rated (deleted_at, visibility, rated_at DESC),
  KEY ix_level_lists_name (deleted_at, visibility, name),
  CONSTRAINT fk_level_lists_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_level_lists_original FOREIGN KEY (original_id) REFERENCES level_lists (id),
  CONSTRAINT fk_level_lists_rated_by FOREIGN KEY (rated_by_user_id) REFERENCES users (id),
  CONSTRAINT ck_level_lists_difficulty CHECK (difficulty BETWEEN -1 AND 10),
  CONSTRAINT ck_level_lists_visibility CHECK (visibility BETWEEN 0 AND 2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE level_list_levels (
  list_id   INT UNSIGNED      NOT NULL,
  position  SMALLINT UNSIGNED NOT NULL,
  level_id  INT UNSIGNED      NOT NULL,
  PRIMARY KEY (list_id, position),
  UNIQUE KEY ux_level_list_levels_level (list_id, level_id),
  KEY ix_level_list_levels_level (level_id),
  CONSTRAINT fk_level_list_levels_list FOREIGN KEY (list_id) REFERENCES level_lists (id),
  CONSTRAINT fk_level_list_levels_level FOREIGN KEY (level_id) REFERENCES levels (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE map_packs (
  id           INT UNSIGNED       NOT NULL AUTO_INCREMENT,
  name         VARCHAR(64)        NOT NULL,
  stars        TINYINT UNSIGNED   NOT NULL,
  coins        TINYINT UNSIGNED   NOT NULL,
  difficulty   TINYINT UNSIGNED   NOT NULL COMMENT '0 auto, 1 easy .. 5 insane, 6 hard demon, 7 easy demon, 8 medium demon, 9 insane demon, 10 extreme demon',
  text_colour  MEDIUMINT UNSIGNED NOT NULL DEFAULT 0xFFFFFF,
  bar_colour   MEDIUMINT UNSIGNED NOT NULL DEFAULT 0xFFFFFF,
  created_at   DATETIME           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at   DATETIME           NULL,
  PRIMARY KEY (id),
  CONSTRAINT ck_map_packs_stars CHECK (stars <= 10),
  CONSTRAINT ck_map_packs_coins CHECK (coins <= 2),
  CONSTRAINT ck_map_packs_difficulty CHECK (difficulty BETWEEN 0 AND 10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE map_pack_levels (
  map_pack_id  INT UNSIGNED     NOT NULL,
  position     TINYINT UNSIGNED NOT NULL,
  level_id     INT UNSIGNED     NOT NULL,
  PRIMARY KEY (map_pack_id, position),
  UNIQUE KEY ux_map_pack_levels_level (map_pack_id, level_id),
  KEY ix_map_pack_levels_level (level_id),
  CONSTRAINT fk_map_pack_levels_pack FOREIGN KEY (map_pack_id) REFERENCES map_packs (id),
  CONSTRAINT fk_map_pack_levels_level FOREIGN KEY (level_id) REFERENCES levels (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Ids are defined by the client (1 Fire .. 60 Love).
CREATE TABLE gauntlets (
  id          TINYINT UNSIGNED NOT NULL,
  created_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at  DATETIME         NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE gauntlet_levels (
  gauntlet_id  TINYINT UNSIGNED NOT NULL,
  position     TINYINT UNSIGNED NOT NULL,
  level_id     INT UNSIGNED     NOT NULL,
  PRIMARY KEY (gauntlet_id, position),
  UNIQUE KEY ux_gauntlet_levels_level (level_id),
  CONSTRAINT fk_gauntlet_levels_gauntlet FOREIGN KEY (gauntlet_id) REFERENCES gauntlets (id),
  CONSTRAINT fk_gauntlet_levels_level FOREIGN KEY (level_id) REFERENCES levels (id),
  CONSTRAINT ck_gauntlet_levels_position CHECK (position BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- sequence is a per-type counter (Daily #n). Event levels carry a chest,
-- described in timely_level_rewards.
CREATE TABLE timely_levels (
  id                    INT UNSIGNED     NOT NULL AUTO_INCREMENT,
  type                  TINYINT UNSIGNED NOT NULL COMMENT '0 daily, 1 weekly, 2 event',
  sequence              INT UNSIGNED     NOT NULL,
  level_id              INT UNSIGNED     NOT NULL,
  starts_at             DATETIME         NOT NULL,
  ends_at               DATETIME         NOT NULL,
  chest_type            TINYINT UNSIGNED NULL COMMENT 'events only: 1 small, 2 large, 3 event',
  scheduled_by_user_id  INT UNSIGNED     NULL,
  created_at            DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at            DATETIME         NULL,
  PRIMARY KEY (id),
  UNIQUE KEY ux_timely_levels_sequence (type, sequence),
  KEY ix_timely_levels_schedule (type, deleted_at, starts_at DESC),
  KEY ix_timely_levels_level (level_id),
  CONSTRAINT fk_timely_levels_level FOREIGN KEY (level_id) REFERENCES levels (id),
  CONSTRAINT fk_timely_levels_scheduled_by FOREIGN KEY (scheduled_by_user_id) REFERENCES users (id),
  CONSTRAINT ck_timely_levels_type CHECK (type BETWEEN 0 AND 2),
  CONSTRAINT ck_timely_levels_window CHECK (ends_at > starts_at),
  CONSTRAINT ck_timely_levels_event_chest CHECK ((type = 2) = (chest_type IS NOT NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Item ids are the game's: 1..6 shards and demon key, 7 orbs, 8 diamonds,
-- 10..14 shards, 15 gold key, 1001..1015 unlocks.
CREATE TABLE timely_level_rewards (
  timely_level_id  INT UNSIGNED      NOT NULL,
  item             SMALLINT UNSIGNED NOT NULL,
  amount           INT UNSIGNED      NOT NULL,
  PRIMARY KEY (timely_level_id, item),
  CONSTRAINT fk_timely_level_rewards_timely FOREIGN KEY (timely_level_id) REFERENCES timely_levels (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------------
-- Level interaction
-- ---------------------------------------------------------------------------

-- Level and list comments share one id space.
CREATE TABLE comments (
  id          INT UNSIGNED     NOT NULL AUTO_INCREMENT,
  user_id     INT UNSIGNED     NOT NULL,
  level_id    INT UNSIGNED     NULL,
  list_id     INT UNSIGNED     NULL,
  content     VARCHAR(100)     NOT NULL,
  percent     TINYINT UNSIGNED NOT NULL DEFAULT 0,
  likes       INT              NOT NULL DEFAULT 0,
  is_spam     BOOLEAN          NOT NULL DEFAULT FALSE,
  created_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at  DATETIME         NULL,
  PRIMARY KEY (id),
  KEY ix_comments_level_recent (level_id, deleted_at, created_at DESC),
  KEY ix_comments_level_liked (level_id, deleted_at, likes DESC),
  KEY ix_comments_list_recent (list_id, deleted_at, created_at DESC),
  KEY ix_comments_list_liked (list_id, deleted_at, likes DESC),
  KEY ix_comments_user_recent (user_id, deleted_at, created_at DESC),
  KEY ix_comments_user_liked (user_id, deleted_at, likes DESC),
  CONSTRAINT fk_comments_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_comments_level FOREIGN KEY (level_id) REFERENCES levels (id),
  CONSTRAINT fk_comments_list FOREIGN KEY (list_id) REFERENCES level_lists (id),
  CONSTRAINT ck_comments_one_target CHECK ((level_id IS NULL) <> (list_id IS NULL)),
  CONSTRAINT ck_comments_percent CHECK (percent <= 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE likes (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id      INT UNSIGNED NOT NULL,
  target_type  ENUM('level', 'comment', 'account_comment', 'level_list') NOT NULL,
  target_id    INT UNSIGNED NOT NULL,
  is_like      BOOLEAN      NOT NULL,
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY ux_likes_target_user (target_type, target_id, user_id),
  CONSTRAINT fk_likes_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- One row per (level, user, timely run); timely_level_id NULL is the ordinary
-- board. progress is the client's list of best-percent milestones.
CREATE TABLE level_scores (
  id               INT UNSIGNED      NOT NULL AUTO_INCREMENT,
  level_id         INT UNSIGNED      NOT NULL,
  user_id          INT UNSIGNED      NOT NULL,
  timely_level_id  INT UNSIGNED      NULL,
  percent          TINYINT UNSIGNED  NOT NULL,
  attempts         INT UNSIGNED      NOT NULL DEFAULT 0,
  clicks           INT UNSIGNED      NOT NULL DEFAULT 0,
  seconds          INT UNSIGNED      NOT NULL DEFAULT 0,
  coins            TINYINT UNSIGNED  NOT NULL DEFAULT 0,
  progress         JSON              NOT NULL DEFAULT (JSON_ARRAY()),
  level_version    SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  submitted_at     DATETIME          NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at       DATETIME          NULL,
  PRIMARY KEY (id),
  UNIQUE KEY ux_level_scores_entry (level_id, user_id, (IFNULL(timely_level_id, 0))),
  KEY ix_level_scores_top (level_id, timely_level_id, deleted_at, percent DESC, submitted_at),
  KEY ix_level_scores_week (level_id, deleted_at, submitted_at DESC),
  KEY ix_level_scores_user (user_id),
  KEY ix_level_scores_timely (timely_level_id),
  CONSTRAINT fk_level_scores_level FOREIGN KEY (level_id) REFERENCES levels (id),
  CONSTRAINT fk_level_scores_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_level_scores_timely FOREIGN KEY (timely_level_id) REFERENCES timely_levels (id),
  CONSTRAINT ck_level_scores_percent CHECK (percent <= 100),
  CONSTRAINT ck_level_scores_coins CHECK (coins <= 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE level_platformer_scores (
  id               INT UNSIGNED      NOT NULL AUTO_INCREMENT,
  level_id         INT UNSIGNED      NOT NULL,
  user_id          INT UNSIGNED      NOT NULL,
  timely_level_id  INT UNSIGNED      NULL,
  time_ms          INT UNSIGNED      NOT NULL,
  points           INT UNSIGNED      NOT NULL DEFAULT 0,
  attempts         INT UNSIGNED      NOT NULL DEFAULT 0,
  clicks           INT UNSIGNED      NOT NULL DEFAULT 0,
  coins            TINYINT UNSIGNED  NOT NULL DEFAULT 0,
  level_version    SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  submitted_at     DATETIME          NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at       DATETIME          NULL,
  PRIMARY KEY (id),
  UNIQUE KEY ux_level_platformer_scores_entry (level_id, user_id, (IFNULL(timely_level_id, 0))),
  KEY ix_level_platformer_scores_time (level_id, timely_level_id, deleted_at, time_ms, submitted_at),
  KEY ix_level_platformer_scores_points (level_id, timely_level_id, deleted_at, points DESC, submitted_at),
  KEY ix_level_platformer_scores_week (level_id, deleted_at, submitted_at DESC),
  KEY ix_level_platformer_scores_user (user_id),
  KEY ix_level_platformer_scores_timely (timely_level_id),
  CONSTRAINT fk_level_platformer_scores_level FOREIGN KEY (level_id) REFERENCES levels (id),
  CONSTRAINT fk_level_platformer_scores_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_level_platformer_scores_timely FOREIGN KEY (timely_level_id) REFERENCES timely_levels (id),
  CONSTRAINT ck_level_platformer_scores_coins CHECK (coins <= 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE level_star_votes (
  level_id    INT UNSIGNED     NOT NULL,
  user_id     INT UNSIGNED     NOT NULL,
  stars       TINYINT UNSIGNED NOT NULL,
  created_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (level_id, user_id),
  CONSTRAINT fk_level_star_votes_level FOREIGN KEY (level_id) REFERENCES levels (id),
  CONSTRAINT fk_level_star_votes_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT ck_level_star_votes_stars CHECK (stars BETWEEN 1 AND 10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Moderator sends. The newest undeleted row per level is the pending suggestion.
CREATE TABLE level_suggestions (
  id                INT UNSIGNED     NOT NULL AUTO_INCREMENT,
  level_id          INT UNSIGNED     NOT NULL,
  user_id           INT UNSIGNED     NOT NULL,
  stars             TINYINT UNSIGNED NULL,
  feature           TINYINT UNSIGNED NULL COMMENT '0 rate only, 1 feature, 2 epic, 3 legendary, 4 mythic',
  demon_difficulty  TINYINT UNSIGNED NULL COMMENT '1 easy .. 5 extreme',
  created_at        DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at        DATETIME         NULL,
  PRIMARY KEY (id),
  KEY ix_level_suggestions_level (level_id, deleted_at, created_at DESC),
  KEY ix_level_suggestions_queue (deleted_at, created_at DESC),
  KEY ix_level_suggestions_user (user_id),
  CONSTRAINT fk_level_suggestions_level FOREIGN KEY (level_id) REFERENCES levels (id),
  CONSTRAINT fk_level_suggestions_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT ck_level_suggestions_any CHECK (stars IS NOT NULL OR feature IS NOT NULL OR demon_difficulty IS NOT NULL),
  CONSTRAINT ck_level_suggestions_stars CHECK (stars IS NULL OR stars BETWEEN 1 AND 10),
  CONSTRAINT ck_level_suggestions_feature CHECK (feature IS NULL OR feature BETWEEN 0 AND 4),
  CONSTRAINT ck_level_suggestions_demon CHECK (demon_difficulty IS NULL OR demon_difficulty BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE level_reports (
  id                   INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  level_id             INT UNSIGNED  NOT NULL,
  user_id              INT UNSIGNED  NULL,
  ip                   VARBINARY(16) NULL,
  created_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at          DATETIME      NULL,
  resolved_by_user_id  INT UNSIGNED  NULL,
  PRIMARY KEY (id),
  KEY ix_level_reports_level (level_id, resolved_at),
  KEY ix_level_reports_queue (resolved_at, created_at DESC),
  CONSTRAINT fk_level_reports_level FOREIGN KEY (level_id) REFERENCES levels (id),
  CONSTRAINT fk_level_reports_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_level_reports_resolved_by FOREIGN KEY (resolved_by_user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------------
-- Rewards
-- ---------------------------------------------------------------------------

CREATE TABLE quests (
  id          INT UNSIGNED     NOT NULL AUTO_INCREMENT,
  item        TINYINT UNSIGNED NOT NULL COMMENT '1 orbs, 2 coins, 3 stars',
  amount      INT UNSIGNED     NOT NULL,
  diamonds    TINYINT UNSIGNED NOT NULL,
  name        VARCHAR(64)      NOT NULL,
  created_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at  DATETIME         NULL,
  PRIMARY KEY (id),
  CONSTRAINT ck_quests_item CHECK (item BETWEEN 1 AND 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- The row id is the quest id the client sees, so each rotation is new to it.
CREATE TABLE user_quests (
  id           INT UNSIGNED     NOT NULL AUTO_INCREMENT,
  user_id      INT UNSIGNED     NOT NULL,
  slot         TINYINT UNSIGNED NOT NULL,
  quest_id     INT UNSIGNED     NOT NULL,
  assigned_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at   DATETIME         NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY ux_user_quests_slot (user_id, expires_at, slot),
  KEY ix_user_quests_quest (quest_id),
  CONSTRAINT fk_user_quests_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_user_quests_quest FOREIGN KEY (quest_id) REFERENCES quests (id),
  CONSTRAINT ck_user_quests_slot CHECK (slot BETWEEN 1 AND 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE chest_claims (
  id          INT UNSIGNED      NOT NULL AUTO_INCREMENT,
  user_id     INT UNSIGNED      NOT NULL,
  chest_type  TINYINT UNSIGNED  NOT NULL COMMENT '1 small, 2 large',
  orbs        SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  diamonds    SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  shard       TINYINT UNSIGNED  NOT NULL DEFAULT 0 COMMENT '0 none, else a shard item id',
  demon_keys  TINYINT UNSIGNED  NOT NULL DEFAULT 0,
  claimed_at  DATETIME          NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_chest_claims_user (user_id, chest_type, claimed_at DESC),
  CONSTRAINT fk_chest_claims_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT ck_chest_claims_type CHECK (chest_type BETWEEN 1 AND 2),
  CONSTRAINT ck_chest_claims_shard CHECK (shard BETWEEN 0 AND 6 OR shard BETWEEN 10 AND 14)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE secret_rewards (
  id          INT UNSIGNED     NOT NULL AUTO_INCREMENT,
  reward_key  VARCHAR(64)      NOT NULL,
  chest_type  TINYINT UNSIGNED NOT NULL COMMENT '1 small, 2 large',
  max_claims  INT UNSIGNED     NULL COMMENT 'NULL unlimited',
  expires_at  DATETIME         NULL,
  created_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at  DATETIME         NULL,
  PRIMARY KEY (id),
  UNIQUE KEY ux_secret_rewards_key (reward_key),
  CONSTRAINT ck_secret_rewards_chest_type CHECK (chest_type BETWEEN 1 AND 2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE secret_reward_items (
  secret_reward_id  INT UNSIGNED      NOT NULL,
  item              SMALLINT UNSIGNED NOT NULL,
  amount            INT UNSIGNED      NOT NULL,
  PRIMARY KEY (secret_reward_id, item),
  CONSTRAINT fk_secret_reward_items_reward FOREIGN KEY (secret_reward_id) REFERENCES secret_rewards (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE secret_reward_claims (
  secret_reward_id  INT UNSIGNED NOT NULL,
  user_id           INT UNSIGNED NOT NULL,
  claimed_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (secret_reward_id, user_id),
  KEY ix_secret_reward_claims_user (user_id),
  CONSTRAINT fk_secret_reward_claims_reward FOREIGN KEY (secret_reward_id) REFERENCES secret_rewards (id),
  CONSTRAINT fk_secret_reward_claims_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------------
-- Moderation
-- ---------------------------------------------------------------------------

CREATE TABLE mod_actions (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id      INT UNSIGNED NOT NULL,
  action       VARCHAR(32)  NOT NULL,
  target_type  ENUM('user', 'level', 'level_list', 'comment', 'account_comment', 'song', 'timely_level', 'map_pack', 'gauntlet', 'quest', 'secret_reward', 'role') NOT NULL,
  target_id    INT UNSIGNED NOT NULL,
  details      JSON         NULL,
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_mod_actions_user (user_id, created_at DESC),
  KEY ix_mod_actions_target (target_type, target_id, created_at DESC),
  CONSTRAINT fk_mod_actions_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------------
-- Seed data
-- ---------------------------------------------------------------------------

INSERT INTO roles (id, name, description, priority) VALUES
  (1, 'default', 'Granted to every account on registration.', 0),
  (2, 'moderator', 'Can send levels for rating.', 10),
  (3, 'elder_moderator', 'Can rate levels, schedule timely levels and issue bans.', 20),
  (4, 'leaderboard_moderator', 'Can remove players from the leaderboards.', 20),
  (5, 'admin', 'Everything.', 100);

INSERT INTO role_permissions (role_id, permission) VALUES
  (1, 'levels.upload'),
  (1, 'levels.report'),
  (1, 'lists.upload'),
  (1, 'comments.post'),
  (1, 'profile.post'),
  (1, 'messages.send'),
  (1, 'friends.request'),
  (1, 'users.block'),
  (1, 'scores.submit'),
  (1, 'stats.update'),
  (1, 'leaderboard.rank'),
  (1, 'rewards.claim'),
  (1, 'quests.view'),
  (1, 'saves.backup'),
  (1, 'songs.request'),
  (1, 'commands.use'),
  (2, 'mod.badge.moderator'),
  (2, 'levels.suggest'),
  (2, 'levels.view_suggestions'),
  (2, 'comments.colour'),
  (3, 'mod.badge.elder'),
  (3, 'levels.suggest'),
  (3, 'levels.view_suggestions'),
  (3, 'levels.view_reports'),
  (3, 'levels.rate'),
  (3, 'levels.feature'),
  (3, 'levels.rate_demon'),
  (3, 'levels.edit_any'),
  (3, 'levels.delete_any'),
  (3, 'lists.rate'),
  (3, 'lists.delete_any'),
  (3, 'comments.delete_any'),
  (3, 'comments.colour'),
  (3, 'profile.delete_any'),
  (3, 'timely.schedule'),
  (3, 'users.ban.comment'),
  (3, 'users.ban.upload'),
  (3, 'users.ban.creator'),
  (3, 'users.unban'),
  (4, 'mod.badge.leaderboard'),
  (4, 'users.ban.leaderboard'),
  (4, 'users.unban'),
  (5, '*');

INSERT INTO quests (item, amount, diamonds, name) VALUES
  (1, 200, 5, 'Orb Collector'),
  (1, 500, 10, 'Orb Hoarder'),
  (1, 1000, 15, 'Orb Magnate'),
  (2, 2, 5, 'Coin Finder'),
  (2, 5, 10, 'Coin Seeker'),
  (2, 8, 15, 'Coin Hunter'),
  (3, 5, 5, 'Star Gazer'),
  (3, 10, 10, 'Star Chaser'),
  (3, 20, 15, 'Star Catcher');
