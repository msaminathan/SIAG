-- ============================================================
--  SIAG Database Schema
--  Societal Impact Action Group - IIT Madras Alumni Association
--  Members, Projects, Media, Documents
-- ============================================================

CREATE DATABASE IF NOT EXISTS SIAG
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE SIAG;

-- ------------------------------------------------------------------
-- USERS (login + role)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  username    VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role        ENUM('admin','editor','viewer') NOT NULL DEFAULT 'viewer',
  full_name   VARCHAR(200),
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Seed a default admin user (password is set via bcrypt hash; see .env for APP_PASSWORD_HASH).
-- Hash generated with bcrypt; replace in production.
INSERT INTO users (username, password_hash, role, full_name)
VALUES ('admin', '$2b$12$LJ3m0.1EXAMPLEHASHREPLACETHIS', 'admin', 'SIAG Admin')
ON DUPLICATE KEY UPDATE username = username;

-- ------------------------------------------------------------------
-- MEMBERS
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS members (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  first_name   VARCHAR(150) NOT NULL,
  last_name    VARCHAR(150) NOT NULL,
  email        VARCHAR(200),
  phone        VARCHAR(30),
  graduation_year INT,
  department   VARCHAR(100),
  role_in_siag VARCHAR(100),
  password_hash VARCHAR(255),
  is_active    BOOLEAN DEFAULT TRUE,
  notes        TEXT,
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  created_by   INT,
  updated_by   INT,
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
  FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------------
-- PROJECTS
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  project_name    VARCHAR(250) NOT NULL,
  description     TEXT,
  category        VARCHAR(100),
  village         VARCHAR(150),
  district        VARCHAR(150),
  state           VARCHAR(150),
  status          ENUM('Planning','Active','On Hold','Completed','Closed') NOT NULL DEFAULT 'Planning',
  start_date      DATE,
  end_date        DATE,
  budget_in_inr   DECIMAL(15,2) DEFAULT 0.00,
  project_lead    VARCHAR(200),
  contact_email   VARCHAR(200),
  contact_phone   VARCHAR(30),
  outcome_summary TEXT,
  is_featured     BOOLEAN DEFAULT FALSE,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  created_by      INT,
  updated_by      INT,
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
  FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------------
-- PROJECT UPDATES (timeline / progress logs)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS project_updates (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  project_id  INT NOT NULL,
  update_date DATE NOT NULL,
  headline    VARCHAR(300),
  details     TEXT,
  created_by  INT,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------------
-- MEDIA  (photos, videos)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS media (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  title        VARCHAR(250) NOT NULL,
  media_type   ENUM('photo','video') NOT NULL DEFAULT 'photo',
  file_path    VARCHAR(500) NOT NULL,
  thumbnail_path VARCHAR(500),
  caption      TEXT,
  tags         VARCHAR(300),
  related_type ENUM('project','member','general') DEFAULT 'general',
  related_id   INT,
  is_published BOOLEAN DEFAULT FALSE,
  uploaded_by  INT,
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------------
-- DOCUMENTS  (PDFs, reports, spreadsheets)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  title        VARCHAR(250) NOT NULL,
  description  TEXT,
  file_path    VARCHAR(500) NOT NULL,
  file_type    VARCHAR(50),
  file_size_kb INT,
  version      VARCHAR(20) DEFAULT '1.0',
  related_type ENUM('project','member','general') DEFAULT 'general',
  related_id   INT,
  is_published BOOLEAN DEFAULT FALSE,
  uploaded_by  INT,
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------------
-- ACTIVITY LOG
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activity_log (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  user_id     INT,
  action      VARCHAR(100) NOT NULL,
  entity_type VARCHAR(100) NOT NULL,
  entity_id   INT,
  details     TEXT,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------------
-- USEFUL INDEXES
-- ------------------------------------------------------------------
CREATE INDEX idx_members_active       ON members(is_active);
CREATE INDEX idx_projects_status      ON projects(status);
CREATE INDEX idx_projects_category    ON projects(category);
CREATE INDEX idx_media_type_published ON media(media_type, is_published);
CREATE INDEX idx_documents_related    ON documents(related_type, related_id);
CREATE INDEX idx_log_user_action      ON activity_log(user_id, action);
