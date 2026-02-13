-- ReadySetClass Student Edition - Phase 2 Tables
-- Migration 004: Assignments, Grades & Submission Tracking
--
-- Adds tables for Submission Validation, Grade Tracking, and Deadline Dashboard.

-- Student assignments (synced from Canvas)
CREATE TABLE IF NOT EXISTS student_assignments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES student_courses(id) ON DELETE CASCADE,
    canvas_assignment_id VARCHAR(100) NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    points_possible DECIMAL(10, 2),
    assignment_group_name VARCHAR(255),
    assignment_group_weight DECIMAL(5, 2),
    due_at TIMESTAMP,
    unlock_at TIMESTAMP,
    lock_at TIMESTAMP,
    submission_types TEXT[],
    allowed_file_types TEXT[],
    graded BOOLEAN DEFAULT false,
    score DECIMAL(10, 2),
    grade VARCHAR(10),
    submitted BOOLEAN DEFAULT false,
    submitted_at TIMESTAMP,
    submission_workflow_state VARCHAR(50) DEFAULT 'unsubmitted',
    turnitin_enabled BOOLEAN DEFAULT false,
    canvas_url TEXT,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, canvas_assignment_id)
);

-- Student submissions (validation tracking)
CREATE TABLE IF NOT EXISTS student_submissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    assignment_id INTEGER REFERENCES student_assignments(id) ON DELETE CASCADE,
    file_name VARCHAR(500),
    file_size BIGINT,
    file_type VARCHAR(100),
    validation_status VARCHAR(20) DEFAULT 'pending',
    validation_issues TEXT[],
    validation_suggestions TEXT[],
    submitted_to_canvas BOOLEAN DEFAULT false,
    submitted_to_canvas_at TIMESTAMP,
    canvas_submission_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Assignment groups (for weighted grade calculation)
CREATE TABLE IF NOT EXISTS student_assignment_groups (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES student_courses(id) ON DELETE CASCADE,
    canvas_group_id VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    position INTEGER,
    group_weight DECIMAL(5, 2),
    drop_lowest INTEGER DEFAULT 0,
    drop_highest INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, canvas_group_id)
);

-- Grade snapshots (for trend tracking over time)
CREATE TABLE IF NOT EXISTS student_grade_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES student_courses(id) ON DELETE CASCADE,
    grade_percentage DECIMAL(5, 2),
    grade_letter VARCHAR(5),
    points_earned DECIMAL(10, 2),
    points_possible DECIMAL(10, 2),
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, course_id, snapshot_date)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_student_assignments_user ON student_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_student_assignments_course ON student_assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_student_assignments_due ON student_assignments(due_at);
CREATE INDEX IF NOT EXISTS idx_student_assignments_state ON student_assignments(user_id, submission_workflow_state);
CREATE INDEX IF NOT EXISTS idx_student_submissions_user ON student_submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_student_submissions_assignment ON student_submissions(assignment_id);
CREATE INDEX IF NOT EXISTS idx_student_assignment_groups_course ON student_assignment_groups(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_student_grade_snapshots_user_course ON student_grade_snapshots(user_id, course_id);

SELECT 'Phase 2 tables created successfully!' as message;
