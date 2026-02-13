export interface User {
  id: number;
  email: string;
  role: string;
  full_name: string;
  is_demo: boolean;
  demo_expires_at: string | null;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface StudentCourse {
  id: number;
  canvas_course_id: string;
  course_code: string | null;
  course_name: string;
  term: string | null;
  current_grade_percentage: number | null;
  current_grade_letter: string | null;
  is_favorite: boolean;
  notification_level: string;
}

export interface Announcement {
  id: number;
  course_id: number;
  course_name: string;
  title: string;
  message: string;
  urgency: 'HIGH' | 'MEDIUM' | 'LOW';
  urgency_score: number;
  posted_at: string;
  posted_by_name: string | null;
  read_status: boolean;
  pinned: boolean;
  canvas_url: string | null;
}

export type AnnouncementFilter = 'all' | 'urgent' | 'unread' | 'pinned';

// Assignments / Deadlines
export interface Assignment {
  id: number;
  course_id: number;
  course_name: string;
  canvas_assignment_id: string;
  name: string;
  description: string | null;
  points_possible: number | null;
  assignment_group_name: string | null;
  due_at: string | null;
  unlock_at: string | null;
  lock_at: string | null;
  submission_types: string[] | null;
  allowed_file_types: string[] | null;
  graded: boolean;
  score: number | null;
  grade: string | null;
  submitted: boolean;
  submitted_at: string | null;
  submission_workflow_state: string;
  turnitin_enabled: boolean;
  canvas_url: string | null;
  time_remaining: string | null;
  is_overdue: boolean;
  is_upcoming: boolean;
}

export type AssignmentFilter = 'all' | 'upcoming' | 'overdue' | 'submitted' | 'graded' | 'unsubmitted';

// Grades
export interface CategoryScore {
  name: string;
  percentage: number;
  points_earned: number;
  points_possible: number;
  weight: number | null;
  graded_count: number;
  total_count: number;
}

export interface CourseGrade {
  course_id: number;
  course_name: string;
  course_code: string | null;
  current_percentage: number | null;
  current_letter: string | null;
  points_earned: number;
  points_possible: number;
  category_scores: CategoryScore[];
}

export interface GradesOverview {
  courses: CourseGrade[];
  gpa_estimate: number | null;
}

// Submission Validation
export interface ValidationResult {
  is_valid: boolean;
  issues: string[];
  suggestions: string[];
  warnings: string[];
  can_auto_fix: boolean;
  auto_fix_options: string[];
}

// AI Study Tools — Flashcards
export interface Flashcard {
  id: number;
  front: string;
  back: string;
  difficulty: 'easy' | 'medium' | 'hard';
  times_seen: number;
  times_correct: number;
}

export interface FlashcardDeck {
  id: number;
  course_id: number;
  title: string;
  description: string | null;
  card_count: number;
  last_studied_at: string | null;
  created_at: string;
}

// AI Study Tools — Quiz
export interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

export interface QuizSession {
  id: number;
  course_id: number;
  topic: string | null;
  questions: QuizQuestion[];
  score: number | null;
  total_questions: number;
  completed_at: string | null;
  created_at: string;
}

// AI Study Tools — Writing Help
export interface WritingHelpResult {
  help_type: string;
  response: string;
  assignment_name: string;
}

// AI Study Tools — Study Schedule
export interface StudyBlock {
  time: string;
  task: string;
  course: string;
  duration_minutes: number;
  priority: string;
}

export interface StudySchedule {
  schedule: StudyBlock[];
  summary: string;
  tips: string[];
  generated_for: string;
}

// Subscription
export interface SubscriptionStatus {
  tier: string;
  status: string;
  has_pro: boolean;
  ai_generations_used: number;
  ai_generations_limit: number;
  trial_ends_at: string | null;
  subscription_ends_at: string | null;
}
