-- ReadySetClass Student Edition Tables
-- Migration 003: Announcement Alert System
--
-- Adds student-specific tables for the Student Edition MVP.
-- Uses student_ prefix to avoid collision with existing educator tables.

-- Extend users role CHECK to include 'student'
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check
    CHECK (role IN ('admin', 'demo', 'customer', 'student'));

-- Student courses (enrolled courses from Canvas)
CREATE TABLE IF NOT EXISTS student_courses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    canvas_course_id VARCHAR(100) NOT NULL,
    course_code VARCHAR(100),
    course_name VARCHAR(255) NOT NULL,
    term VARCHAR(100),
    current_grade_percentage DECIMAL(5, 2),
    current_grade_letter VARCHAR(5),
    is_favorite BOOLEAN DEFAULT false,
    notification_level VARCHAR(20) DEFAULT 'all',
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, canvas_course_id)
);

-- Student announcements (Canvas announcements per student)
CREATE TABLE IF NOT EXISTS student_announcements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES student_courses(id) ON DELETE CASCADE,
    canvas_announcement_id VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    urgency VARCHAR(20) DEFAULT 'LOW',
    urgency_score INTEGER DEFAULT 0,
    read_status BOOLEAN DEFAULT false,
    read_at TIMESTAMP,
    pinned BOOLEAN DEFAULT false,
    posted_at TIMESTAMP NOT NULL,
    posted_by_name VARCHAR(255),
    canvas_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, canvas_announcement_id)
);

-- Notification preferences
CREATE TABLE IF NOT EXISTS student_notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    push_enabled BOOLEAN DEFAULT true,
    email_urgent_enabled BOOLEAN DEFAULT true,
    digest_enabled BOOLEAN DEFAULT true,
    digest_time TIME DEFAULT '08:00:00',
    quiet_hours_enabled BOOLEAN DEFAULT true,
    quiet_hours_start TIME DEFAULT '22:00:00',
    quiet_hours_end TIME DEFAULT '07:00:00',
    quiet_hours_allow_urgent BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_student_courses_user ON student_courses(user_id);
CREATE INDEX IF NOT EXISTS idx_student_announcements_user ON student_announcements(user_id);
CREATE INDEX IF NOT EXISTS idx_student_announcements_course ON student_announcements(course_id);
CREATE INDEX IF NOT EXISTS idx_student_announcements_read ON student_announcements(user_id, read_status);
CREATE INDEX IF NOT EXISTS idx_student_announcements_urgency ON student_announcements(urgency);
CREATE INDEX IF NOT EXISTS idx_student_announcements_posted ON student_announcements(posted_at DESC);

SELECT 'Student Edition tables created successfully!' as message;
