-- ReadySetClass Student Edition - Phase 3 Tables
-- Migration 005: AI Study Tools
--
-- Tables for flashcards, study quizzes, writing help, and study schedules.

-- Flashcard decks
CREATE TABLE IF NOT EXISTS student_flashcard_decks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES student_courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    source_type VARCHAR(50) DEFAULT 'notes',
    card_count INTEGER DEFAULT 0,
    last_studied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Individual flashcards
CREATE TABLE IF NOT EXISTS student_flashcards (
    id SERIAL PRIMARY KEY,
    deck_id INTEGER REFERENCES student_flashcard_decks(id) ON DELETE CASCADE,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    difficulty VARCHAR(20) DEFAULT 'medium',
    times_seen INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    last_reviewed_at TIMESTAMP,
    next_review_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Study quiz sessions
CREATE TABLE IF NOT EXISTS student_quiz_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES student_courses(id) ON DELETE CASCADE,
    topic VARCHAR(500),
    questions_json TEXT NOT NULL,
    score INTEGER,
    total_questions INTEGER,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Writing help sessions
CREATE TABLE IF NOT EXISTS student_writing_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    assignment_id INTEGER REFERENCES student_assignments(id) ON DELETE CASCADE,
    help_type VARCHAR(50) NOT NULL,
    user_input TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Study schedule
CREATE TABLE IF NOT EXISTS student_study_schedule (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    schedule_json TEXT NOT NULL,
    generated_for_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, generated_for_date)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_flashcard_decks_user ON student_flashcard_decks(user_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_deck ON student_flashcards(deck_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_review ON student_flashcards(next_review_at);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user ON student_quiz_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_writing_sessions_user ON student_writing_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_study_schedule_user ON student_study_schedule(user_id);

SELECT 'AI Study Tools tables created successfully!' as message;
