"""
Student Edition Router
All student-specific API endpoints under /api/v1/student/
"""

from datetime import datetime, timezone, date
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from auth_helpers import get_current_user_from_token, get_db_connection
from canvas_auth import CanvasAuth, encrypt_token
from canvas_student_client import StudentCanvasClient
from services.urgency_analyzer import UrgencyAnalyzer
from services.grade_calculator import GradeCalculator
from services.submission_validator import SubmissionValidator
from services import ai_study
from schemas.student import (
    CanvasConnectRequest, CanvasConnectResponse,
    StudentCourseResponse, CourseSyncResponse,
    AnnouncementResponse, AnnouncementsListResponse,
    AnnouncementSyncResponse, PinRequest, MarkAllReadRequest,
    AssignmentResponse, AssignmentsListResponse, AssignmentSyncResponse,
    CourseGradeResponse, GradesOverviewResponse, CategoryScore,
    WhatIfRequest, WhatIfResponse, GradeSnapshotResponse,
    ValidationResponse, SubmissionResponse,
    FlashcardGenerateRequest, FlashcardDeckResponse, FlashcardResponse,
    FlashcardReviewRequest,
    QuizGenerateRequest, QuizSessionResponse, QuizQuestionResponse, QuizSubmitRequest,
    WritingHelpRequest, WritingHelpResponse,
    StudyScheduleResponse,
)

router = APIRouter(prefix="/api/v1/student", tags=["student"])

urgency_analyzer = UrgencyAnalyzer()
grade_calculator = GradeCalculator()
submission_validator = SubmissionValidator()


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def student_health():
    """Student API health check"""
    return {"status": "ok", "edition": "student", "version": "1.0.0"}


# ============================================================================
# CANVAS CONNECTION
# ============================================================================

@router.post("/canvas/connect", response_model=CanvasConnectResponse)
async def connect_canvas(
    request: CanvasConnectRequest,
    current_user=Depends(get_current_user_from_token)
):
    """Connect student's Canvas account with API token"""
    # Test the Canvas connection
    canvas_url = request.canvas_url.rstrip('/')
    if not canvas_url.startswith('http'):
        canvas_url = f"https://{canvas_url}"

    auth = CanvasAuth(canvas_url, request.access_token)
    success, user_data, error = auth.test_connection()

    if not success:
        raise HTTPException(status_code=400, detail=f"Canvas connection failed: {error}")

    # Save Canvas credentials to user record
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        encrypted_token = encrypt_token(request.access_token)
        cursor.execute("""
            UPDATE users
            SET canvas_url = %s, canvas_token_encrypted = %s, updated_at = NOW()
            WHERE id = %s
        """, (canvas_url, encrypted_token, current_user["user_id"]))
        conn.commit()

        user_name = user_data.get("name", "") if user_data else ""

        # Auto-sync courses after connecting
        client = StudentCanvasClient(canvas_url, request.access_token)
        courses = client.get_enrolled_courses()

        return CanvasConnectResponse(
            status="connected",
            canvas_url=canvas_url,
            user_name=user_name,
            courses_found=len(courses)
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Canvas connect error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save Canvas credentials")
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# COURSES
# ============================================================================

@router.post("/courses/sync", response_model=CourseSyncResponse)
async def sync_courses(current_user=Depends(get_current_user_from_token)):
    """Sync enrolled courses from Canvas"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get user's Canvas credentials
        cursor.execute("""
            SELECT canvas_url, canvas_token_encrypted
            FROM users WHERE id = %s
        """, (current_user["user_id"],))
        row = cursor.fetchone()

        if not row or not row[0] or not row[1]:
            raise HTTPException(status_code=400, detail="Canvas not connected. Please connect your Canvas account first.")

        canvas_url, token_encrypted = row
        # Note: decrypt_token is currently a passthrough (see canvas_auth.py)
        from canvas_auth import decrypt_token
        access_token = decrypt_token(token_encrypted)

        # Fetch courses from Canvas
        client = StudentCanvasClient(canvas_url, access_token)
        canvas_courses = client.get_enrolled_courses()

        synced_courses = []
        for cc in canvas_courses:
            canvas_course_id = str(cc.get("id", ""))
            course_name = cc.get("name", "Unknown Course")
            course_code = cc.get("course_code", "")

            # Get term info
            term = ""
            if cc.get("term"):
                term = cc["term"].get("name", "")

            # Get grade info from enrollments
            grade_pct = None
            grade_letter = None
            enrollments = cc.get("enrollments", [])
            for enrollment in enrollments:
                if enrollment.get("type") == "student":
                    grade_pct = enrollment.get("computed_current_score")
                    grade_letter = enrollment.get("computed_current_grade")
                    break

            # Upsert into student_courses
            cursor.execute("""
                INSERT INTO student_courses (user_id, canvas_course_id, course_code, course_name, term,
                    current_grade_percentage, current_grade_letter, last_synced_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (user_id, canvas_course_id)
                DO UPDATE SET
                    course_name = EXCLUDED.course_name,
                    course_code = EXCLUDED.course_code,
                    term = EXCLUDED.term,
                    current_grade_percentage = EXCLUDED.current_grade_percentage,
                    current_grade_letter = EXCLUDED.current_grade_letter,
                    last_synced_at = NOW(),
                    updated_at = NOW()
                RETURNING id, canvas_course_id, course_code, course_name, term,
                    current_grade_percentage, current_grade_letter, is_favorite, notification_level
            """, (current_user["user_id"], canvas_course_id, course_code, course_name,
                  term, grade_pct, grade_letter))

            row = cursor.fetchone()
            synced_courses.append(StudentCourseResponse(
                id=row[0],
                canvas_course_id=row[1],
                course_code=row[2],
                course_name=row[3],
                term=row[4],
                current_grade_percentage=float(row[5]) if row[5] else None,
                current_grade_letter=row[6],
                is_favorite=row[7],
                notification_level=row[8]
            ))

        conn.commit()

        return CourseSyncResponse(courses=synced_courses, total=len(synced_courses))

    except HTTPException:
        raise
    except Exception as e:
        print(f"Course sync error: {e}")
        raise HTTPException(status_code=500, detail=f"Course sync failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.get("/courses")
async def get_courses(current_user=Depends(get_current_user_from_token)):
    """Get cached student courses"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, canvas_course_id, course_code, course_name, term,
                current_grade_percentage, current_grade_letter, is_favorite, notification_level
            FROM student_courses
            WHERE user_id = %s
            ORDER BY course_name
        """, (current_user["user_id"],))

        courses = []
        for row in cursor.fetchall():
            courses.append(StudentCourseResponse(
                id=row[0],
                canvas_course_id=row[1],
                course_code=row[2],
                course_name=row[3],
                term=row[4],
                current_grade_percentage=float(row[5]) if row[5] else None,
                current_grade_letter=row[6],
                is_favorite=row[7],
                notification_level=row[8]
            ))

        return {"courses": courses, "total": len(courses)}

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# ANNOUNCEMENTS
# ============================================================================

@router.post("/announcements/sync", response_model=AnnouncementSyncResponse)
async def sync_announcements(current_user=Depends(get_current_user_from_token)):
    """Fetch new announcements from Canvas and analyze urgency"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get Canvas credentials
        cursor.execute("""
            SELECT canvas_url, canvas_token_encrypted
            FROM users WHERE id = %s
        """, (current_user["user_id"],))
        row = cursor.fetchone()

        if not row or not row[0] or not row[1]:
            raise HTTPException(status_code=400, detail="Canvas not connected")

        canvas_url, token_encrypted = row
        from canvas_auth import decrypt_token
        access_token = decrypt_token(token_encrypted)

        # Get student's courses
        cursor.execute("""
            SELECT id, canvas_course_id, course_name
            FROM student_courses
            WHERE user_id = %s
        """, (current_user["user_id"],))
        courses = cursor.fetchall()

        if not courses:
            raise HTTPException(status_code=400, detail="No courses synced. Please sync courses first.")

        client = StudentCanvasClient(canvas_url, access_token)
        canvas_course_ids = [int(c[1]) for c in courses]
        course_map = {str(c[1]): {"db_id": c[0], "name": c[2]} for c in courses}

        # Fetch announcements from Canvas
        canvas_announcements = client.get_all_announcements(canvas_course_ids)

        new_count = 0
        for ann in canvas_announcements:
            canvas_ann_id = str(ann.get("id", ""))

            # Check if we already have this announcement
            cursor.execute("""
                SELECT id FROM student_announcements
                WHERE user_id = %s AND canvas_announcement_id = %s
            """, (current_user["user_id"], canvas_ann_id))

            if cursor.fetchone():
                continue  # Already stored

            # Determine which course this belongs to
            context_code = ann.get("context_code", "")  # e.g., "course_12345"
            canvas_cid = context_code.replace("course_", "")
            course_info = course_map.get(canvas_cid)

            if not course_info:
                continue  # Course not in student's synced courses

            title = ann.get("title", "No Title")
            message = ann.get("message", "")

            # Parse posted_at
            posted_at_str = ann.get("posted_at", "")
            try:
                posted_at = datetime.fromisoformat(posted_at_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                posted_at = datetime.utcnow()

            # Analyze urgency
            urgency_result = urgency_analyzer.analyze(title, message, posted_at)

            # Get author name
            author = ann.get("author", {})
            posted_by = author.get("display_name", "") if isinstance(author, dict) else ""

            # Canvas URL
            canvas_url_link = ann.get("html_url", "")

            # Insert
            cursor.execute("""
                INSERT INTO student_announcements
                    (user_id, course_id, canvas_announcement_id, title, message,
                     urgency, urgency_score, posted_at, posted_by_name, canvas_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                current_user["user_id"],
                course_info["db_id"],
                canvas_ann_id,
                title,
                message,
                urgency_result["level"],
                urgency_result["score"],
                posted_at,
                posted_by,
                canvas_url_link
            ))

            new_count += 1

        conn.commit()

        # Get total count
        cursor.execute("""
            SELECT COUNT(*) FROM student_announcements WHERE user_id = %s
        """, (current_user["user_id"],))
        total = cursor.fetchone()[0]

        return AnnouncementSyncResponse(new_count=new_count, total=total)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Announcement sync error: {e}")
        raise HTTPException(status_code=500, detail=f"Announcement sync failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.get("/announcements", response_model=AnnouncementsListResponse)
async def get_announcements(
    filter: Optional[str] = Query("all", regex="^(all|urgent|unread|pinned)$"),
    course_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user_from_token)
):
    """Get announcements with filters"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        user_id = current_user["user_id"]

        # Build query
        where_clauses = ["a.user_id = %s"]
        params = [user_id]

        if filter == "urgent":
            where_clauses.append("a.urgency = 'HIGH'")
        elif filter == "unread":
            where_clauses.append("a.read_status = false")
        elif filter == "pinned":
            where_clauses.append("a.pinned = true")

        if course_id:
            where_clauses.append("a.course_id = %s")
            params.append(course_id)

        where_sql = " AND ".join(where_clauses)

        # Get announcements
        cursor.execute(f"""
            SELECT a.id, a.course_id, c.course_name, a.title, a.message,
                a.urgency, a.urgency_score, a.posted_at, a.posted_by_name,
                a.read_status, a.pinned, a.canvas_url
            FROM student_announcements a
            JOIN student_courses c ON a.course_id = c.id
            WHERE {where_sql}
            ORDER BY a.pinned DESC, a.posted_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        announcements = []
        for row in cursor.fetchall():
            announcements.append(AnnouncementResponse(
                id=row[0],
                course_id=row[1],
                course_name=row[2],
                title=row[3],
                message=row[4],
                urgency=row[5],
                urgency_score=row[6],
                posted_at=row[7],
                posted_by_name=row[8],
                read_status=row[9],
                pinned=row[10],
                canvas_url=row[11]
            ))

        # Get total count for this filter
        cursor.execute(f"""
            SELECT COUNT(*) FROM student_announcements a
            JOIN student_courses c ON a.course_id = c.id
            WHERE {where_sql}
        """, params)
        total = cursor.fetchone()[0]

        # Get unread count (always useful)
        cursor.execute("""
            SELECT COUNT(*) FROM student_announcements
            WHERE user_id = %s AND read_status = false
        """, (user_id,))
        unread_count = cursor.fetchone()[0]

        return AnnouncementsListResponse(
            announcements=announcements,
            total=total,
            unread_count=unread_count
        )

    finally:
        cursor.close()
        conn.close()


@router.post("/announcements/{announcement_id}/read")
async def mark_as_read(
    announcement_id: int,
    current_user=Depends(get_current_user_from_token)
):
    """Mark an announcement as read"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE student_announcements
            SET read_status = true, read_at = NOW(), updated_at = NOW()
            WHERE id = %s AND user_id = %s
            RETURNING id
        """, (announcement_id, current_user["user_id"]))

        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Announcement not found")

        conn.commit()
        return {"success": True}

    finally:
        cursor.close()
        conn.close()


@router.post("/announcements/{announcement_id}/pin")
async def toggle_pin(
    announcement_id: int,
    request: PinRequest,
    current_user=Depends(get_current_user_from_token)
):
    """Pin or unpin an announcement"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE student_announcements
            SET pinned = %s, updated_at = NOW()
            WHERE id = %s AND user_id = %s
            RETURNING id
        """, (request.pinned, announcement_id, current_user["user_id"]))

        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Announcement not found")

        conn.commit()
        return {"success": True}

    finally:
        cursor.close()
        conn.close()


@router.post("/announcements/mark-all-read")
async def mark_all_read(
    request: MarkAllReadRequest,
    current_user=Depends(get_current_user_from_token)
):
    """Mark all announcements as read, optionally filtered by course"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if request.course_id:
            cursor.execute("""
                UPDATE student_announcements
                SET read_status = true, read_at = NOW(), updated_at = NOW()
                WHERE user_id = %s AND course_id = %s AND read_status = false
            """, (current_user["user_id"], request.course_id))
        else:
            cursor.execute("""
                UPDATE student_announcements
                SET read_status = true, read_at = NOW(), updated_at = NOW()
                WHERE user_id = %s AND read_status = false
            """, (current_user["user_id"],))

        marked_count = cursor.rowcount
        conn.commit()

        return {"success": True, "marked_count": marked_count}

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# ASSIGNMENTS / DEADLINE DASHBOARD
# ============================================================================

def _get_canvas_client(cursor, user_id):
    """Helper to get a Canvas client for the current user."""
    cursor.execute("""
        SELECT canvas_url, canvas_token_encrypted
        FROM users WHERE id = %s
    """, (user_id,))
    row = cursor.fetchone()
    if not row or not row[0] or not row[1]:
        raise HTTPException(status_code=400, detail="Canvas not connected")
    from canvas_auth import decrypt_token
    return StudentCanvasClient(row[0], decrypt_token(row[1]))


def _compute_time_remaining(due_at):
    """Compute human-readable time remaining string."""
    if not due_at:
        return None, False, False

    now = datetime.now(timezone.utc)
    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=timezone.utc)

    delta = due_at - now
    total_seconds = delta.total_seconds()

    is_overdue = total_seconds < 0
    is_upcoming = 0 < total_seconds < 7 * 24 * 3600  # within 7 days

    if is_overdue:
        abs_seconds = abs(total_seconds)
        if abs_seconds < 3600:
            return f"{int(abs_seconds / 60)}m overdue", True, False
        elif abs_seconds < 86400:
            return f"{int(abs_seconds / 3600)}h overdue", True, False
        else:
            return f"{int(abs_seconds / 86400)}d overdue", True, False
    elif total_seconds < 3600:
        return f"{int(total_seconds / 60)}m left", False, True
    elif total_seconds < 86400:
        return f"{int(total_seconds / 3600)}h left", False, True
    elif total_seconds < 7 * 86400:
        return f"{int(total_seconds / 86400)}d left", False, True
    else:
        return f"{int(total_seconds / 86400)}d left", False, False


@router.post("/assignments/sync", response_model=AssignmentSyncResponse)
async def sync_assignments(current_user=Depends(get_current_user_from_token)):
    """Sync assignments from Canvas for all enrolled courses"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        client = _get_canvas_client(cursor, current_user["user_id"])

        # Get student's courses
        cursor.execute("""
            SELECT id, canvas_course_id, course_name
            FROM student_courses WHERE user_id = %s
        """, (current_user["user_id"],))
        courses = cursor.fetchall()

        if not courses:
            raise HTTPException(status_code=400, detail="No courses synced yet")

        synced_count = 0

        for course_db_id, canvas_cid, course_name in courses:
            try:
                canvas_assignments = client.get_course_assignments(int(canvas_cid))
            except Exception:
                continue

            for ca in canvas_assignments:
                canvas_aid = str(ca.get("id", ""))
                name = ca.get("name", "Untitled")
                description = ca.get("description", "")
                points = ca.get("points_possible")
                group_name = ca.get("assignment_group", {}).get("name") if isinstance(ca.get("assignment_group"), dict) else None

                # Parse dates
                due_at = None
                if ca.get("due_at"):
                    try:
                        due_at = datetime.fromisoformat(ca["due_at"].replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass

                unlock_at = None
                if ca.get("unlock_at"):
                    try:
                        unlock_at = datetime.fromisoformat(ca["unlock_at"].replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass

                lock_at = None
                if ca.get("lock_at"):
                    try:
                        lock_at = datetime.fromisoformat(ca["lock_at"].replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass

                sub_types = ca.get("submission_types", [])
                allowed_types = ca.get("allowed_extensions", [])
                turnitin = ca.get("turnitin_enabled", False) or ca.get("vericite_enabled", False)
                canvas_url = ca.get("html_url", "")

                # Check submission
                submission = ca.get("submission", {}) or {}
                submitted = submission.get("workflow_state") in ("submitted", "graded", "pending_review")
                submitted_at = None
                if submission.get("submitted_at"):
                    try:
                        submitted_at = datetime.fromisoformat(submission["submitted_at"].replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass
                graded = submission.get("workflow_state") == "graded"
                score = submission.get("score")
                grade = submission.get("grade")
                workflow_state = submission.get("workflow_state", "unsubmitted")

                cursor.execute("""
                    INSERT INTO student_assignments
                        (user_id, course_id, canvas_assignment_id, name, description,
                         points_possible, assignment_group_name, due_at, unlock_at, lock_at,
                         submission_types, allowed_file_types, turnitin_enabled,
                         graded, score, grade, submitted, submitted_at,
                         submission_workflow_state, canvas_url, last_synced_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (user_id, canvas_assignment_id)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        points_possible = EXCLUDED.points_possible,
                        assignment_group_name = EXCLUDED.assignment_group_name,
                        due_at = EXCLUDED.due_at,
                        unlock_at = EXCLUDED.unlock_at,
                        lock_at = EXCLUDED.lock_at,
                        submission_types = EXCLUDED.submission_types,
                        allowed_file_types = EXCLUDED.allowed_file_types,
                        turnitin_enabled = EXCLUDED.turnitin_enabled,
                        graded = EXCLUDED.graded,
                        score = EXCLUDED.score,
                        grade = EXCLUDED.grade,
                        submitted = EXCLUDED.submitted,
                        submitted_at = EXCLUDED.submitted_at,
                        submission_workflow_state = EXCLUDED.submission_workflow_state,
                        canvas_url = EXCLUDED.canvas_url,
                        last_synced_at = NOW(),
                        updated_at = NOW()
                """, (
                    current_user["user_id"], course_db_id, canvas_aid, name, description,
                    points, group_name, due_at, unlock_at, lock_at,
                    sub_types, allowed_types, turnitin,
                    graded, score, grade, submitted, submitted_at,
                    workflow_state, canvas_url
                ))
                synced_count += 1

        conn.commit()

        # Get total
        cursor.execute("SELECT COUNT(*) FROM student_assignments WHERE user_id = %s",
                       (current_user["user_id"],))
        total = cursor.fetchone()[0]

        return AssignmentSyncResponse(synced_count=synced_count, total=total)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Assignment sync error: {e}")
        raise HTTPException(status_code=500, detail=f"Assignment sync failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.get("/assignments", response_model=AssignmentsListResponse)
async def get_assignments(
    filter: Optional[str] = Query("all", regex="^(all|upcoming|overdue|submitted|graded|unsubmitted)$"),
    course_id: Optional[int] = None,
    sort: str = Query("due_date", regex="^(due_date|points|name)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user_from_token)
):
    """Get assignments with filters for the deadline dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        user_id = current_user["user_id"]
        where_clauses = ["a.user_id = %s"]
        params = [user_id]

        now = datetime.now(timezone.utc)

        if filter == "upcoming":
            where_clauses.append("a.due_at > %s AND a.submitted = false")
            params.append(now)
        elif filter == "overdue":
            where_clauses.append("a.due_at < %s AND a.submitted = false AND a.due_at IS NOT NULL")
            params.append(now)
        elif filter == "submitted":
            where_clauses.append("a.submitted = true")
        elif filter == "graded":
            where_clauses.append("a.graded = true")
        elif filter == "unsubmitted":
            where_clauses.append("a.submitted = false")

        if course_id:
            where_clauses.append("a.course_id = %s")
            params.append(course_id)

        where_sql = " AND ".join(where_clauses)

        sort_sql = {
            "due_date": "a.due_at ASC NULLS LAST",
            "points": "a.points_possible DESC NULLS LAST",
            "name": "a.name ASC",
        }.get(sort, "a.due_at ASC NULLS LAST")

        cursor.execute(f"""
            SELECT a.id, a.course_id, c.course_name, a.canvas_assignment_id, a.name,
                a.description, a.points_possible, a.assignment_group_name,
                a.due_at, a.unlock_at, a.lock_at,
                a.submission_types, a.allowed_file_types,
                a.graded, a.score, a.grade, a.submitted, a.submitted_at,
                a.submission_workflow_state, a.turnitin_enabled, a.canvas_url
            FROM student_assignments a
            JOIN student_courses c ON a.course_id = c.id
            WHERE {where_sql}
            ORDER BY {sort_sql}
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        assignments = []
        for row in cursor.fetchall():
            due_at = row[8]
            time_remaining, is_overdue, is_upcoming = _compute_time_remaining(due_at)

            assignments.append(AssignmentResponse(
                id=row[0], course_id=row[1], course_name=row[2],
                canvas_assignment_id=row[3], name=row[4],
                description=row[5], points_possible=float(row[6]) if row[6] else None,
                assignment_group_name=row[7],
                due_at=due_at, unlock_at=row[9], lock_at=row[10],
                submission_types=row[11], allowed_file_types=row[12],
                graded=row[13], score=float(row[14]) if row[14] else None,
                grade=row[15], submitted=row[16], submitted_at=row[17],
                submission_workflow_state=row[18],
                turnitin_enabled=row[19], canvas_url=row[20],
                time_remaining=time_remaining,
                is_overdue=is_overdue,
                is_upcoming=is_upcoming
            ))

        # Total count
        cursor.execute(f"""
            SELECT COUNT(*) FROM student_assignments a
            JOIN student_courses c ON a.course_id = c.id
            WHERE {where_sql}
        """, params)
        total = cursor.fetchone()[0]

        return AssignmentsListResponse(assignments=assignments, total=total)

    finally:
        cursor.close()
        conn.close()


@router.get("/assignments/{assignment_id}")
async def get_assignment_detail(
    assignment_id: int,
    current_user=Depends(get_current_user_from_token)
):
    """Get a single assignment with full details"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT a.id, a.course_id, c.course_name, a.canvas_assignment_id, a.name,
                a.description, a.points_possible, a.assignment_group_name,
                a.due_at, a.unlock_at, a.lock_at,
                a.submission_types, a.allowed_file_types,
                a.graded, a.score, a.grade, a.submitted, a.submitted_at,
                a.submission_workflow_state, a.turnitin_enabled, a.canvas_url
            FROM student_assignments a
            JOIN student_courses c ON a.course_id = c.id
            WHERE a.id = %s AND a.user_id = %s
        """, (assignment_id, current_user["user_id"]))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Assignment not found")

        due_at = row[8]
        time_remaining, is_overdue, is_upcoming = _compute_time_remaining(due_at)

        return AssignmentResponse(
            id=row[0], course_id=row[1], course_name=row[2],
            canvas_assignment_id=row[3], name=row[4],
            description=row[5], points_possible=float(row[6]) if row[6] else None,
            assignment_group_name=row[7],
            due_at=due_at, unlock_at=row[9], lock_at=row[10],
            submission_types=row[11], allowed_file_types=row[12],
            graded=row[13], score=float(row[14]) if row[14] else None,
            grade=row[15], submitted=row[16], submitted_at=row[17],
            submission_workflow_state=row[18],
            turnitin_enabled=row[19], canvas_url=row[20],
            time_remaining=time_remaining,
            is_overdue=is_overdue,
            is_upcoming=is_upcoming
        )

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# GRADES
# ============================================================================

@router.get("/grades", response_model=GradesOverviewResponse)
async def get_grades(current_user=Depends(get_current_user_from_token)):
    """Get grade overview across all courses with category breakdowns"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        user_id = current_user["user_id"]

        # Get all courses
        cursor.execute("""
            SELECT id, course_name, course_code, current_grade_percentage, current_grade_letter
            FROM student_courses WHERE user_id = %s ORDER BY course_name
        """, (user_id,))
        courses = cursor.fetchall()

        course_grades = []
        gpa_points = []

        for course_id, course_name, course_code, canvas_pct, canvas_letter in courses:
            # Get assignments for this course
            cursor.execute("""
                SELECT id, name, points_possible, score, grade, graded,
                       assignment_group_name, assignment_group_weight
                FROM student_assignments
                WHERE user_id = %s AND course_id = %s
            """, (user_id, course_id))
            assignments = cursor.fetchall()

            # Build category map
            categories = {}
            for a_id, a_name, pts, score, a_grade, is_graded, group_name, group_weight in assignments:
                cat_name = group_name or "Assignments"
                if cat_name not in categories:
                    categories[cat_name] = {
                        "name": cat_name,
                        "weight": float(group_weight) if group_weight else 0,
                        "assignments": [],
                        "drop_lowest": 0,
                        "drop_highest": 0,
                    }
                categories[cat_name]["assignments"].append({
                    "id": a_id,
                    "name": a_name,
                    "points_possible": float(pts) if pts else None,
                    "score": float(score) if score is not None else None,
                    "graded": is_graded,
                })

            cat_list = list(categories.values())
            has_weights = any(c["weight"] > 0 for c in cat_list)

            if has_weights:
                result = grade_calculator.calculate_weighted_grade(cat_list)
            elif assignments:
                flat_assignments = []
                for c in cat_list:
                    flat_assignments.extend(c["assignments"])
                result = grade_calculator.calculate_points_grade(flat_assignments)
                result["category_scores"] = {}
                for c in cat_list:
                    cs = grade_calculator.calculate_category_score(c["assignments"])
                    if cs:
                        result["category_scores"][c["name"]] = cs
            else:
                result = None

            # Use Canvas grades as primary if available, fall back to calculated
            pct = float(canvas_pct) if canvas_pct else (result["percentage"] if result else None)
            letter = canvas_letter or (result["letter_grade"] if result else None)
            earned = result["points_earned"] if result else 0
            possible = result["points_possible"] if result else 0

            cat_scores = []
            if result and result.get("category_scores"):
                for cat_name, cat_data in result["category_scores"].items():
                    cat_scores.append(CategoryScore(
                        name=cat_name,
                        percentage=cat_data["percentage"],
                        points_earned=cat_data["points_earned"],
                        points_possible=cat_data["points_possible"],
                        weight=cat_data.get("weight"),
                        graded_count=cat_data.get("graded_count", 0),
                        total_count=cat_data.get("total_count", 0),
                    ))

            course_grades.append(CourseGradeResponse(
                course_id=course_id,
                course_name=course_name,
                course_code=course_code,
                current_percentage=pct,
                current_letter=letter,
                points_earned=earned,
                points_possible=possible,
                category_scores=cat_scores
            ))

            # GPA estimate
            if letter:
                gpa_map = {"A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7,
                           "C+": 2.3, "C": 2.0, "C-": 1.7, "D+": 1.3, "D": 1.0, "D-": 0.7, "F": 0.0}
                gpa_val = gpa_map.get(letter)
                if gpa_val is not None:
                    gpa_points.append(gpa_val)

        gpa = round(sum(gpa_points) / len(gpa_points), 2) if gpa_points else None

        return GradesOverviewResponse(courses=course_grades, gpa_estimate=gpa)

    finally:
        cursor.close()
        conn.close()


@router.post("/grades/sync")
async def sync_grades(current_user=Depends(get_current_user_from_token)):
    """Sync latest grades from Canvas (re-syncs assignments + updates course grades)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        client = _get_canvas_client(cursor, current_user["user_id"])
        user_id = current_user["user_id"]

        # Re-sync courses to get latest grade percentages
        canvas_courses = client.get_enrolled_courses()
        for cc in canvas_courses:
            canvas_cid = str(cc.get("id", ""))
            grade_pct = None
            grade_letter = None
            for enrollment in cc.get("enrollments", []):
                if enrollment.get("type") == "student":
                    grade_pct = enrollment.get("computed_current_score")
                    grade_letter = enrollment.get("computed_current_grade")
                    break

            cursor.execute("""
                UPDATE student_courses
                SET current_grade_percentage = %s, current_grade_letter = %s,
                    last_synced_at = NOW(), updated_at = NOW()
                WHERE user_id = %s AND canvas_course_id = %s
            """, (grade_pct, grade_letter, user_id, canvas_cid))

        # Take grade snapshots
        cursor.execute("""
            SELECT id, course_name, current_grade_percentage, current_grade_letter
            FROM student_courses WHERE user_id = %s
        """, (user_id,))
        for course_id, _, pct, letter in cursor.fetchall():
            if pct is not None:
                # Get total points for snapshot
                cursor.execute("""
                    SELECT COALESCE(SUM(score), 0), COALESCE(SUM(points_possible), 0)
                    FROM student_assignments
                    WHERE user_id = %s AND course_id = %s AND graded = true
                """, (user_id, course_id))
                earned, possible = cursor.fetchone()

                cursor.execute("""
                    INSERT INTO student_grade_snapshots
                        (user_id, course_id, grade_percentage, grade_letter,
                         points_earned, points_possible, snapshot_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, course_id, snapshot_date) DO UPDATE SET
                        grade_percentage = EXCLUDED.grade_percentage,
                        grade_letter = EXCLUDED.grade_letter,
                        points_earned = EXCLUDED.points_earned,
                        points_possible = EXCLUDED.points_possible
                """, (user_id, course_id, pct, letter, earned, possible, date.today()))

        conn.commit()
        return {"success": True, "message": "Grades synced"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Grade sync error: {e}")
        raise HTTPException(status_code=500, detail=f"Grade sync failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.post("/grades/what-if", response_model=WhatIfResponse)
async def what_if_calculator(
    request: WhatIfRequest,
    current_user=Depends(get_current_user_from_token)
):
    """Calculate what-if grade scenarios"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        user_id = current_user["user_id"]

        cursor.execute("""
            SELECT id, name, points_possible, score, graded
            FROM student_assignments
            WHERE user_id = %s AND course_id = %s
        """, (user_id, request.course_id))

        assignments = []
        for row in cursor.fetchall():
            assignments.append({
                "id": row[0], "name": row[1],
                "points_possible": float(row[2]) if row[2] else 0,
                "score": float(row[3]) if row[3] is not None else None,
                "graded": row[4]
            })

        if request.scenario_type == "target_grade" and request.target_grade is not None:
            graded = [a for a in assignments if a["graded"] and a["points_possible"]]
            ungraded = [a for a in assignments if not a["graded"] and a["points_possible"]]

            current_earned = sum(a.get("score", 0) or 0 for a in graded)
            current_possible = sum(a["points_possible"] for a in graded)
            remaining_possible = sum(a["points_possible"] for a in ungraded)

            result = grade_calculator.what_if_target(
                current_earned, current_possible, remaining_possible, request.target_grade
            )

            # Also compute projected grade
            projected = grade_calculator.calculate_points_grade(assignments)

            return WhatIfResponse(
                scenario_type="target_grade",
                result={**result, "current_grade": projected}
            )

        elif request.scenario_type == "assignment_scores" and request.assignment_scores:
            hyp = {int(k): v for k, v in request.assignment_scores.items()}
            result = grade_calculator.what_if_scores(assignments, hyp)

            return WhatIfResponse(
                scenario_type="assignment_scores",
                result={"projected_grade": result}
            )

        else:
            raise HTTPException(status_code=400, detail="Invalid scenario type")

    finally:
        cursor.close()
        conn.close()


@router.get("/grades/history/{course_id}")
async def get_grade_history(
    course_id: int,
    current_user=Depends(get_current_user_from_token)
):
    """Get grade trend data for a course"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT course_name FROM student_courses
            WHERE id = %s AND user_id = %s
        """, (course_id, current_user["user_id"]))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Course not found")

        cursor.execute("""
            SELECT snapshot_date, grade_percentage, grade_letter,
                   points_earned, points_possible
            FROM student_grade_snapshots
            WHERE user_id = %s AND course_id = %s
            ORDER BY snapshot_date ASC
        """, (current_user["user_id"], course_id))

        snapshots = []
        for srow in cursor.fetchall():
            snapshots.append({
                "date": srow[0].isoformat(),
                "percentage": float(srow[1]) if srow[1] else None,
                "letter": srow[2],
                "earned": float(srow[3]) if srow[3] else 0,
                "possible": float(srow[4]) if srow[4] else 0,
            })

        return GradeSnapshotResponse(
            course_id=course_id,
            course_name=row[0],
            snapshots=snapshots
        )

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# SUBMISSION VALIDATION
# ============================================================================

@router.post("/submissions/validate", response_model=ValidationResponse)
async def validate_submission(
    assignment_id: int = Query(...),
    file_name: str = Query(...),
    file_size: int = Query(...),
    is_url: bool = Query(False),
    url: Optional[str] = Query(None),
    current_user=Depends(get_current_user_from_token)
):
    """Validate a file before submitting to Canvas"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get assignment details for validation rules
        cursor.execute("""
            SELECT allowed_file_types, turnitin_enabled, submission_types
            FROM student_assignments
            WHERE id = %s AND user_id = %s
        """, (assignment_id, current_user["user_id"]))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Assignment not found")

        allowed_types, turnitin, sub_types = row

        result = submission_validator.validate(
            file_name=file_name,
            file_size=file_size,
            allowed_types=allowed_types,
            turnitin_enabled=turnitin or False,
            is_url=is_url,
            url=url,
        )

        # Log the validation
        cursor.execute("""
            INSERT INTO student_submissions
                (user_id, assignment_id, file_name, file_size, file_type,
                 validation_status, validation_issues, validation_suggestions)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            current_user["user_id"], assignment_id, file_name, file_size,
            file_name.rsplit(".", 1)[-1] if "." in file_name else None,
            "valid" if result["is_valid"] else "invalid",
            result["issues"] if result["issues"] else None,
            result["suggestions"] if result["suggestions"] else None
        ))
        conn.commit()

        return ValidationResponse(**result)

    finally:
        cursor.close()
        conn.close()


@router.get("/submissions/{assignment_id}")
async def get_submission_history(
    assignment_id: int,
    current_user=Depends(get_current_user_from_token)
):
    """Get submission/validation history for an assignment"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, assignment_id, file_name, file_size, validation_status,
                   validation_issues, submitted_to_canvas, submitted_to_canvas_at, created_at
            FROM student_submissions
            WHERE user_id = %s AND assignment_id = %s
            ORDER BY created_at DESC
        """, (current_user["user_id"], assignment_id))

        submissions = []
        for row in cursor.fetchall():
            submissions.append(SubmissionResponse(
                id=row[0], assignment_id=row[1], file_name=row[2],
                file_size=row[3], validation_status=row[4],
                validation_issues=row[5],
                submitted_to_canvas=row[6],
                submitted_to_canvas_at=row[7],
                created_at=row[8]
            ))

        return {"submissions": submissions, "total": len(submissions)}

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# AI STUDY TOOLS - FLASHCARDS
# ============================================================================

@router.post("/flashcards/generate")
async def generate_flashcards(
    request: FlashcardGenerateRequest,
    current_user=Depends(get_current_user_from_token)
):
    """Generate flashcards from notes using AI"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        user_id = current_user["user_id"]

        # Verify course belongs to user
        cursor.execute("SELECT course_name FROM student_courses WHERE id = %s AND user_id = %s",
                       (request.course_id, user_id))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Course not found")

        # Generate flashcards with AI
        cards = ai_study.generate_flashcards(request.topic, request.notes, request.card_count)
        if not cards:
            raise HTTPException(status_code=500, detail="Could not generate flashcards")

        # Create deck
        cursor.execute("""
            INSERT INTO student_flashcard_decks (user_id, course_id, title, description, card_count, source_type)
            VALUES (%s, %s, %s, %s, %s, 'notes')
            RETURNING id
        """, (user_id, request.course_id, request.topic, f"Generated from notes about {request.topic}", len(cards)))
        deck_id = cursor.fetchone()[0]

        # Insert cards
        card_responses = []
        for card in cards:
            cursor.execute("""
                INSERT INTO student_flashcards (deck_id, front, back, difficulty)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (deck_id, card.get("front", ""), card.get("back", ""), card.get("difficulty", "medium")))
            card_id = cursor.fetchone()[0]
            card_responses.append(FlashcardResponse(
                id=card_id, front=card["front"], back=card["back"],
                difficulty=card.get("difficulty", "medium")
            ))

        conn.commit()

        return {
            "deck": FlashcardDeckResponse(
                id=deck_id, course_id=request.course_id,
                title=request.topic, card_count=len(cards),
                created_at=datetime.now(timezone.utc)
            ),
            "cards": card_responses
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Flashcard generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.get("/flashcards/decks")
async def get_flashcard_decks(current_user=Depends(get_current_user_from_token)):
    """Get all flashcard decks for the current user"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT d.id, d.course_id, d.title, d.description, d.card_count,
                   d.last_studied_at, d.created_at, c.course_name
            FROM student_flashcard_decks d
            JOIN student_courses c ON d.course_id = c.id
            WHERE d.user_id = %s
            ORDER BY d.updated_at DESC
        """, (current_user["user_id"],))

        decks = []
        for row in cursor.fetchall():
            decks.append({
                **FlashcardDeckResponse(
                    id=row[0], course_id=row[1], title=row[2],
                    description=row[3], card_count=row[4],
                    last_studied_at=row[5], created_at=row[6]
                ).model_dump(),
                "course_name": row[7]
            })

        return {"decks": decks, "total": len(decks)}

    finally:
        cursor.close()
        conn.close()


@router.get("/flashcards/decks/{deck_id}/cards")
async def get_deck_cards(
    deck_id: int,
    current_user=Depends(get_current_user_from_token)
):
    """Get all cards in a deck"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Verify deck ownership
        cursor.execute("""
            SELECT d.title, d.course_id, c.course_name
            FROM student_flashcard_decks d
            JOIN student_courses c ON d.course_id = c.id
            WHERE d.id = %s AND d.user_id = %s
        """, (deck_id, current_user["user_id"]))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Deck not found")

        cursor.execute("""
            SELECT id, front, back, difficulty, times_seen, times_correct
            FROM student_flashcards WHERE deck_id = %s
            ORDER BY id
        """, (deck_id,))

        cards = [FlashcardResponse(
            id=r[0], front=r[1], back=r[2], difficulty=r[3],
            times_seen=r[4], times_correct=r[5]
        ) for r in cursor.fetchall()]

        return {"deck_title": row[0], "course_name": row[2], "cards": cards}

    finally:
        cursor.close()
        conn.close()


@router.post("/flashcards/review")
async def review_flashcard(
    request: FlashcardReviewRequest,
    current_user=Depends(get_current_user_from_token)
):
    """Record a flashcard review result"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE student_flashcards
            SET times_seen = times_seen + 1,
                times_correct = times_correct + %s,
                last_reviewed_at = NOW(),
                next_review_at = NOW() + INTERVAL '%s hours'
            WHERE id = %s
            RETURNING id
        """, (1 if request.correct else 0, 1 if not request.correct else 24, request.card_id))

        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Card not found")

        # Update deck last_studied_at
        cursor.execute("""
            UPDATE student_flashcard_decks SET last_studied_at = NOW(), updated_at = NOW()
            WHERE id = (SELECT deck_id FROM student_flashcards WHERE id = %s)
        """, (request.card_id,))

        conn.commit()
        return {"success": True}

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# AI STUDY TOOLS - QUIZ
# ============================================================================

@router.post("/quiz/generate")
async def generate_quiz(
    request: QuizGenerateRequest,
    current_user=Depends(get_current_user_from_token)
):
    """Generate a quiz using AI"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        user_id = current_user["user_id"]

        # Build context from course content if not provided
        context = request.context
        if not context:
            # Pull recent announcements + assignment descriptions as context
            cursor.execute("""
                SELECT title, message FROM student_announcements
                WHERE user_id = %s AND course_id = %s
                ORDER BY posted_at DESC LIMIT 5
            """, (user_id, request.course_id))
            ann_text = "\n".join(f"{r[0]}: {r[1][:200]}" for r in cursor.fetchall())

            cursor.execute("""
                SELECT name, description FROM student_assignments
                WHERE user_id = %s AND course_id = %s AND description IS NOT NULL
                ORDER BY due_at DESC NULLS LAST LIMIT 5
            """, (user_id, request.course_id))
            assign_text = "\n".join(f"{r[0]}: {(r[1] or '')[:200]}" for r in cursor.fetchall())

            context = f"Course announcements:\n{ann_text}\n\nAssignments:\n{assign_text}"

        questions = ai_study.generate_quiz(request.topic, context, request.num_questions)
        if not questions:
            raise HTTPException(status_code=500, detail="Could not generate quiz")

        import json
        cursor.execute("""
            INSERT INTO student_quiz_sessions
                (user_id, course_id, topic, questions_json, total_questions)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, created_at
        """, (user_id, request.course_id, request.topic, json.dumps(questions), len(questions)))
        session_id, created_at = cursor.fetchone()
        conn.commit()

        return QuizSessionResponse(
            id=session_id,
            course_id=request.course_id,
            topic=request.topic,
            questions=[QuizQuestionResponse(**q) for q in questions],
            total_questions=len(questions),
            created_at=created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Quiz generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.post("/quiz/submit")
async def submit_quiz(
    request: QuizSubmitRequest,
    current_user=Depends(get_current_user_from_token)
):
    """Submit quiz answers and get score"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT questions_json, total_questions FROM student_quiz_sessions
            WHERE id = %s AND user_id = %s
        """, (request.session_id, current_user["user_id"]))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Quiz session not found")

        import json
        questions = json.loads(row[0])
        total = row[1]

        score = 0
        results = []
        for i, q in enumerate(questions):
            answer = request.answers[i] if i < len(request.answers) else -1
            correct = answer == q["correct_index"]
            if correct:
                score += 1
            results.append({
                "question": q["question"],
                "your_answer": q["options"][answer] if 0 <= answer < len(q["options"]) else "No answer",
                "correct_answer": q["options"][q["correct_index"]],
                "correct": correct,
                "explanation": q["explanation"]
            })

        cursor.execute("""
            UPDATE student_quiz_sessions
            SET score = %s, completed_at = NOW()
            WHERE id = %s
        """, (score, request.session_id))
        conn.commit()

        return {
            "score": score,
            "total": total,
            "percentage": round(score / total * 100) if total > 0 else 0,
            "results": results
        }

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# AI STUDY TOOLS - WRITING HELP
# ============================================================================

@router.post("/writing/help", response_model=WritingHelpResponse)
async def get_writing_help(
    request: WritingHelpRequest,
    current_user=Depends(get_current_user_from_token)
):
    """Get AI writing assistance for an assignment"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        valid_types = ["outline", "brainstorm", "feedback", "strengthen", "cite"]
        if request.help_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"help_type must be one of: {valid_types}")

        cursor.execute("""
            SELECT a.name, a.description, c.course_name
            FROM student_assignments a
            JOIN student_courses c ON a.course_id = c.id
            WHERE a.id = %s AND a.user_id = %s
        """, (request.assignment_id, current_user["user_id"]))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Assignment not found")

        assignment_name, assignment_desc, course_name = row

        response_text = ai_study.writing_help(
            help_type=request.help_type,
            assignment_name=f"{course_name} - {assignment_name}",
            assignment_description=assignment_desc or "No description provided",
            user_input=request.user_input,
        )

        # Save session
        cursor.execute("""
            INSERT INTO student_writing_sessions
                (user_id, assignment_id, help_type, user_input, ai_response)
            VALUES (%s, %s, %s, %s, %s)
        """, (current_user["user_id"], request.assignment_id, request.help_type,
              request.user_input, response_text))
        conn.commit()

        return WritingHelpResponse(
            help_type=request.help_type,
            response=response_text,
            assignment_name=assignment_name
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Writing help error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# AI STUDY TOOLS - STUDY SCHEDULE
# ============================================================================

@router.get("/study/schedule")
async def get_study_schedule(current_user=Depends(get_current_user_from_token)):
    """Generate an AI study schedule based on upcoming deadlines"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        user_id = current_user["user_id"]

        # Check for cached schedule from today
        cursor.execute("""
            SELECT schedule_json FROM student_study_schedule
            WHERE user_id = %s AND generated_for_date = %s
        """, (user_id, date.today()))
        cached = cursor.fetchone()
        if cached:
            import json
            data = json.loads(cached[0])
            return StudyScheduleResponse(
                schedule=data.get("schedule", []),
                summary=data.get("summary", ""),
                tips=data.get("tips", []),
                generated_for=date.today().isoformat()
            )

        # Get upcoming assignments
        now = datetime.now(timezone.utc)
        cursor.execute("""
            SELECT a.name, c.course_name, a.due_at, a.points_possible, a.submitted
            FROM student_assignments a
            JOIN student_courses c ON a.course_id = c.id
            WHERE a.user_id = %s AND (a.due_at > %s OR a.due_at IS NULL) AND a.submitted = false
            ORDER BY a.due_at ASC NULLS LAST
            LIMIT 20
        """, (user_id, now))

        assignments = []
        for row in cursor.fetchall():
            assignments.append({
                "name": row[0], "course_name": row[1],
                "due_at": row[2].isoformat() if row[2] else "No due date",
                "points_possible": float(row[3]) if row[3] else None,
                "submitted": row[4]
            })

        cursor.execute("SELECT course_name FROM student_courses WHERE user_id = %s", (user_id,))
        courses = [{"name": r[0]} for r in cursor.fetchall()]

        result = ai_study.generate_study_schedule(assignments, courses)

        # Cache it
        import json
        cursor.execute("""
            INSERT INTO student_study_schedule (user_id, schedule_json, generated_for_date)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, generated_for_date) DO UPDATE SET
                schedule_json = EXCLUDED.schedule_json
        """, (user_id, json.dumps(result), date.today()))
        conn.commit()

        return StudyScheduleResponse(
            schedule=result.get("schedule", []),
            summary=result.get("summary", ""),
            tips=result.get("tips", []),
            generated_for=date.today().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Schedule generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.post("/study/schedule/refresh")
async def refresh_study_schedule(current_user=Depends(get_current_user_from_token)):
    """Force regenerate today's study schedule"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM student_study_schedule
            WHERE user_id = %s AND generated_for_date = %s
        """, (current_user["user_id"], date.today()))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return await get_study_schedule(current_user)
