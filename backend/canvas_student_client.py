"""
Canvas LMS API Client - Student Edition
Read-only Canvas API methods for student operations.

Subclasses the existing CanvasClient to reuse _make_request() and rate limiting.
"""

from typing import Dict, List, Optional
from canvas_client import CanvasClient


class StudentCanvasClient(CanvasClient):
    """
    Canvas API client for student operations (read-only).
    Students can view their enrolled courses, announcements, and grades
    but cannot create content.
    """

    def get_enrolled_courses(self) -> List[Dict]:
        """Get courses where user is enrolled as a student"""
        return self._make_request(
            method="GET",
            endpoint="/api/v1/courses",
            params={
                "enrollment_type": "student",
                "enrollment_state": "active",
                "state[]": "available",
                "include[]": ["term", "total_scores", "current_grading_period_scores"],
                "per_page": 50
            }
        ) or []

    def get_course_announcements(
        self,
        course_id: int,
        start_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Get announcements for a specific course.

        Canvas Announcements API returns discussion_topic objects
        where is_announcement=true.

        Args:
            course_id: Canvas course ID
            start_date: ISO date string to filter announcements from
        """
        params = {
            "context_codes[]": f"course_{course_id}",
            "per_page": 50
        }
        if start_date:
            params["start_date"] = start_date

        return self._make_request(
            method="GET",
            endpoint="/api/v1/announcements",
            params=params
        ) or []

    def get_all_announcements(
        self,
        course_ids: List[int],
        start_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Get announcements across multiple courses in a single API call.

        Args:
            course_ids: List of Canvas course IDs
            start_date: ISO date string to filter announcements from
        """
        if not course_ids:
            return []

        context_codes = [f"course_{cid}" for cid in course_ids]
        params = {
            "context_codes[]": context_codes,
            "per_page": 50
        }
        if start_date:
            params["start_date"] = start_date

        return self._make_request(
            method="GET",
            endpoint="/api/v1/announcements",
            params=params
        ) or []

    def get_course_assignments(
        self,
        course_id: int,
        include_submission: bool = True
    ) -> List[Dict]:
        """Get assignments for a course (for future deadline dashboard)"""
        params = {"per_page": 50}
        if include_submission:
            params["include[]"] = "submission"

        return self._make_request(
            method="GET",
            endpoint=f"/api/v1/courses/{course_id}/assignments",
            params=params
        ) or []

    def get_course_grades(self, course_id: int) -> Optional[Dict]:
        """Get enrollment/grade data for a specific course"""
        enrollments = self._make_request(
            method="GET",
            endpoint=f"/api/v1/courses/{course_id}/enrollments",
            params={
                "type[]": "StudentEnrollment",
                "user_id": "self",
                "include[]": ["current_points", "total_scores"]
            }
        )
        if enrollments and len(enrollments) > 0:
            return enrollments[0]
        return None

    def get_course_assignment_groups(self, course_id: int) -> List[Dict]:
        """Get assignment groups (categories) for a course with weights"""
        return self._make_request(
            method="GET",
            endpoint=f"/api/v1/courses/{course_id}/assignment_groups",
            params={
                "per_page": 50,
                "include[]": ["assignments"]
            }
        ) or []

    def get_assignment_details(self, course_id: int, assignment_id: int) -> Optional[Dict]:
        """Get a single assignment with submission info"""
        result = self._make_request(
            method="GET",
            endpoint=f"/api/v1/courses/{course_id}/assignments/{assignment_id}",
            params={"include[]": ["submission"]}
        )
        return result if result else None

    def submit_assignment(
        self,
        course_id: int,
        assignment_id: int,
        submission_type: str = "online_upload",
        file_ids: Optional[List[int]] = None,
        url: Optional[str] = None,
        body: Optional[str] = None
    ) -> Optional[Dict]:
        """Submit an assignment to Canvas"""
        data = {"submission": {"submission_type": submission_type}}
        if file_ids:
            data["submission"]["file_ids"] = file_ids
        if url:
            data["submission"]["url"] = url
        if body:
            data["submission"]["body"] = body

        return self._make_request(
            method="POST",
            endpoint=f"/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions",
            json_data=data
        )
