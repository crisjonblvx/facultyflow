"""
Pydantic Schemas for Student Edition API
Request/response models for validation and serialization.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ============================================================================
# CANVAS CONNECTION
# ============================================================================

class CanvasConnectRequest(BaseModel):
    canvas_url: str
    access_token: str


class CanvasConnectResponse(BaseModel):
    status: str
    canvas_url: str
    user_name: Optional[str] = None
    courses_found: int = 0


# ============================================================================
# COURSES
# ============================================================================

class StudentCourseResponse(BaseModel):
    id: int
    canvas_course_id: str
    course_code: Optional[str] = None
    course_name: str
    term: Optional[str] = None
    current_grade_percentage: Optional[float] = None
    current_grade_letter: Optional[str] = None
    is_favorite: bool = False
    notification_level: str = "all"

    class Config:
        from_attributes = True


class CourseSyncResponse(BaseModel):
    courses: List[StudentCourseResponse]
    total: int


# ============================================================================
# ANNOUNCEMENTS
# ============================================================================

class AnnouncementResponse(BaseModel):
    id: int
    course_id: int
    course_name: str
    title: str
    message: str
    urgency: str
    urgency_score: int = 0
    posted_at: datetime
    posted_by_name: Optional[str] = None
    read_status: bool = False
    pinned: bool = False
    canvas_url: Optional[str] = None

    class Config:
        from_attributes = True


class AnnouncementsListResponse(BaseModel):
    announcements: List[AnnouncementResponse]
    total: int
    unread_count: int


class AnnouncementSyncResponse(BaseModel):
    new_count: int
    total: int


class PinRequest(BaseModel):
    pinned: bool


class MarkAllReadRequest(BaseModel):
    course_id: Optional[int] = None


# ============================================================================
# ASSIGNMENTS / DEADLINES
# ============================================================================

class AssignmentResponse(BaseModel):
    id: int
    course_id: int
    course_name: str
    canvas_assignment_id: str
    name: str
    description: Optional[str] = None
    points_possible: Optional[float] = None
    assignment_group_name: Optional[str] = None
    due_at: Optional[datetime] = None
    unlock_at: Optional[datetime] = None
    lock_at: Optional[datetime] = None
    submission_types: Optional[List[str]] = None
    allowed_file_types: Optional[List[str]] = None
    graded: bool = False
    score: Optional[float] = None
    grade: Optional[str] = None
    submitted: bool = False
    submitted_at: Optional[datetime] = None
    submission_workflow_state: str = "unsubmitted"
    turnitin_enabled: bool = False
    canvas_url: Optional[str] = None

    # Computed fields for deadline dashboard
    time_remaining: Optional[str] = None
    is_overdue: bool = False
    is_upcoming: bool = False

    class Config:
        from_attributes = True


class AssignmentsListResponse(BaseModel):
    assignments: List[AssignmentResponse]
    total: int


class AssignmentSyncResponse(BaseModel):
    synced_count: int
    total: int


# ============================================================================
# GRADES
# ============================================================================

class CategoryScore(BaseModel):
    name: str
    percentage: float
    points_earned: float
    points_possible: float
    weight: Optional[float] = None
    graded_count: int = 0
    total_count: int = 0


class CourseGradeResponse(BaseModel):
    course_id: int
    course_name: str
    course_code: Optional[str] = None
    current_percentage: Optional[float] = None
    current_letter: Optional[str] = None
    points_earned: float = 0
    points_possible: float = 0
    category_scores: List[CategoryScore] = []


class GradesOverviewResponse(BaseModel):
    courses: List[CourseGradeResponse]
    gpa_estimate: Optional[float] = None


class WhatIfRequest(BaseModel):
    course_id: int
    scenario_type: str  # "target_grade" or "assignment_scores"
    target_grade: Optional[float] = None
    assignment_scores: Optional[dict] = None


class WhatIfResponse(BaseModel):
    scenario_type: str
    result: dict


class GradeSnapshotResponse(BaseModel):
    course_id: int
    course_name: str
    snapshots: List[dict]


# ============================================================================
# SUBMISSION VALIDATION
# ============================================================================

class ValidationResponse(BaseModel):
    is_valid: bool
    issues: List[str] = []
    suggestions: List[str] = []
    warnings: List[str] = []
    can_auto_fix: bool = False
    auto_fix_options: List[str] = []


class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    validation_status: str = "pending"
    validation_issues: Optional[List[str]] = None
    submitted_to_canvas: bool = False
    submitted_to_canvas_at: Optional[datetime] = None
    created_at: datetime


# ============================================================================
# AI STUDY TOOLS
# ============================================================================

class FlashcardGenerateRequest(BaseModel):
    course_id: int
    topic: str
    notes: str
    card_count: int = 10


class FlashcardDeckResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    card_count: int = 0
    last_studied_at: Optional[datetime] = None
    created_at: datetime


class FlashcardResponse(BaseModel):
    id: int
    front: str
    back: str
    difficulty: str = "medium"
    times_seen: int = 0
    times_correct: int = 0


class FlashcardReviewRequest(BaseModel):
    card_id: int
    correct: bool


class QuizGenerateRequest(BaseModel):
    course_id: int
    topic: str
    context: str = ""
    num_questions: int = 5


class QuizQuestionResponse(BaseModel):
    question: str
    options: List[str]
    correct_index: int
    explanation: str


class QuizSessionResponse(BaseModel):
    id: int
    course_id: int
    topic: Optional[str] = None
    questions: List[QuizQuestionResponse]
    score: Optional[int] = None
    total_questions: int
    completed_at: Optional[datetime] = None
    created_at: datetime


class QuizSubmitRequest(BaseModel):
    session_id: int
    answers: List[int]


class WritingHelpRequest(BaseModel):
    assignment_id: int
    help_type: str  # "outline", "brainstorm", "feedback", "strengthen", "cite"
    user_input: str


class WritingHelpResponse(BaseModel):
    help_type: str
    response: str
    assignment_name: str


class StudyScheduleResponse(BaseModel):
    schedule: list
    summary: str
    tips: list
    generated_for: str


# ============================================================================
# SUBSCRIPTION
# ============================================================================

class SubscriptionStatusResponse(BaseModel):
    tier: str
    status: str
    has_pro: bool
    ai_generations_used: int
    ai_generations_limit: int  # -1 = unlimited
    trial_ends_at: Optional[str] = None
    subscription_ends_at: Optional[str] = None
