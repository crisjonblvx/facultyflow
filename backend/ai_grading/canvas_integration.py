"""
Canvas LMS Integration for AI Grading

Handles fetching submissions from Canvas and posting grades back.
"""

import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CanvasGradingIntegration:
    """
    Handles Canvas API interactions for AI grading workflow

    Responsibilities:
    - Fetch assignment details and submissions
    - Post grades and comments to Canvas
    - Handle Canvas API authentication and errors
    """

    def __init__(self, canvas_url: str, canvas_token: str):
        """
        Initialize Canvas integration

        Args:
            canvas_url: Canvas instance URL (e.g., "https://canvas.instructure.com")
            canvas_token: Canvas API access token
        """
        self.canvas_url = canvas_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {canvas_token}",
            "Content-Type": "application/json"
        }
        self.api_base = f"{self.canvas_url}/api/v1"

    def get_assignment_details(
        self,
        course_id: str,
        assignment_id: str
    ) -> Dict:
        """
        Get assignment details including rubric

        Returns assignment metadata and rubric information
        """

        url = f"{self.api_base}/courses/{course_id}/assignments/{assignment_id}"

        params = {
            "include[]": ["rubric", "rubric_assessment"]
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            assignment = response.json()

            return {
                "id": assignment.get("id"),
                "name": assignment.get("name"),
                "description": assignment.get("description"),
                "points_possible": assignment.get("points_possible"),
                "due_at": assignment.get("due_at"),
                "rubric": assignment.get("rubric", []),
                "submission_types": assignment.get("submission_types", [])
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch assignment details: {e}")
            raise Exception(f"Canvas API error: {str(e)}")

    def get_assignment_submissions(
        self,
        course_id: str,
        assignment_id: str,
        include_unsubmitted: bool = False
    ) -> List[Dict]:
        """
        Fetch all submissions for an assignment

        Args:
            course_id: Canvas course ID
            assignment_id: Canvas assignment ID
            include_unsubmitted: Whether to include students who haven't submitted

        Returns:
            List of submission dicts with student info and submission content
        """

        url = f"{self.api_base}/courses/{course_id}/assignments/{assignment_id}/submissions"

        params = {
            "include[]": ["user", "submission_comments", "rubric_assessment"],
            "per_page": 100
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            submissions = response.json()

            # Format submissions for AI grading
            formatted = []

            for sub in submissions:
                workflow_state = sub.get("workflow_state", "")

                # Skip unsubmitted unless requested
                if workflow_state not in ["submitted", "graded"] and not include_unsubmitted:
                    continue

                # Extract submission text/content
                submission_text = self._extract_submission_text(sub)

                # Only include if there's actual content
                if not submission_text or len(submission_text.strip()) < 10:
                    continue

                formatted_sub = {
                    "submission_id": str(sub.get("id")),
                    "student_id": str(sub.get("user_id")),
                    "student_name": sub.get("user", {}).get("name", "Unknown Student"),
                    "student_email": sub.get("user", {}).get("email"),
                    "submission_text": submission_text,
                    "submitted_at": sub.get("submitted_at"),
                    "workflow_state": workflow_state,
                    "score": sub.get("score"),  # Existing grade if any
                    "attachments": sub.get("attachments", []),
                    "submission_type": sub.get("submission_type")
                }

                formatted.append(formatted_sub)

            logger.info(f"Fetched {len(formatted)} submissions for assignment {assignment_id}")
            return formatted

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch submissions: {e}")
            raise Exception(f"Canvas API error: {str(e)}")

    def _extract_submission_text(self, submission: Dict) -> str:
        """
        Extract text content from various submission types

        Handles:
        - online_text_entry (HTML body)
        - online_upload (would need file parsing - TODO)
        - online_url (would fetch URL content - TODO)
        """

        submission_type = submission.get("submission_type")

        # Text submission
        if submission_type == "online_text_entry":
            body = submission.get("body", "")
            # Strip HTML tags (basic)
            import re
            text = re.sub(r'<[^>]+>', '', body)
            text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
            return text.strip()

        # File upload - return filename for now
        # TODO: Parse common file types (PDF, DOCX, TXT)
        elif submission_type == "online_upload":
            attachments = submission.get("attachments", [])
            if attachments:
                filenames = [att.get("filename", "") for att in attachments]
                return f"[File submission: {', '.join(filenames)}]"

        # URL submission
        elif submission_type == "online_url":
            url = submission.get("url", "")
            return f"[URL submission: {url}]"

        return ""

    def post_grade(
        self,
        course_id: str,
        assignment_id: str,
        student_id: str,
        score: float,
        comment: Optional[str] = None,
        rubric_assessment: Optional[Dict] = None
    ) -> Dict:
        """
        Post a grade to Canvas for a specific student

        Args:
            course_id: Canvas course ID
            assignment_id: Canvas assignment ID
            student_id: Canvas student ID
            score: Numeric score
            comment: Optional feedback comment
            rubric_assessment: Optional rubric scores dict

        Returns:
            Canvas submission object
        """

        url = f"{self.api_base}/courses/{course_id}/assignments/{assignment_id}/submissions/{student_id}"

        data = {
            "submission": {
                "posted_grade": str(score)
            }
        }

        # Add comment/feedback if provided
        if comment:
            data["comment"] = {
                "text_comment": comment
            }

        # Add rubric assessment if provided
        if rubric_assessment:
            data["rubric_assessment"] = rubric_assessment

        try:
            response = requests.put(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()

            logger.info(f"Posted grade {score} for student {student_id}")
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post grade for student {student_id}: {e}")
            raise Exception(f"Canvas API error: {str(e)}")

    def post_grades_batch(
        self,
        course_id: str,
        assignment_id: str,
        grades: List[Dict]
    ) -> Dict:
        """
        Post multiple grades at once

        Args:
            grades: List of dicts:
                [
                    {
                        "student_id": "12345",
                        "score": 85.5,
                        "comment": "Great work!",
                        "rubric_assessment": {...}
                    },
                    ...
                ]

        Returns:
            Dict with success and failure counts:
            {
                "success": [list of successful submissions],
                "failed": [list of failed submissions with errors],
                "success_count": 23,
                "failed_count": 2
            }
        """

        results = {
            "success": [],
            "failed": [],
            "success_count": 0,
            "failed_count": 0
        }

        for grade in grades:
            try:
                result = self.post_grade(
                    course_id=course_id,
                    assignment_id=assignment_id,
                    student_id=grade["student_id"],
                    score=grade["score"],
                    comment=grade.get("comment"),
                    rubric_assessment=grade.get("rubric_assessment")
                )

                results["success"].append({
                    "student_id": grade["student_id"],
                    "score": grade["score"],
                    "canvas_response": result
                })
                results["success_count"] += 1

            except Exception as e:
                logger.error(f"Failed to post grade for {grade['student_id']}: {e}")
                results["failed"].append({
                    "student_id": grade["student_id"],
                    "score": grade["score"],
                    "error": str(e)
                })
                results["failed_count"] += 1

        logger.info(f"Batch grading complete: {results['success_count']} success, {results['failed_count']} failed")
        return results

    def get_course_assignments(
        self,
        course_id: str,
        include_ungraded: bool = True
    ) -> List[Dict]:
        """
        Get all assignments for a course

        Useful for listing assignments that need grading

        Returns list of assignment summaries
        """

        url = f"{self.api_base}/courses/{course_id}/assignments"

        params = {
            "per_page": 100,
            "order_by": "due_at"
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            assignments = response.json()

            formatted = []
            for assignment in assignments:
                # Skip if no submissions
                if not include_ungraded and assignment.get("has_submitted_submissions", False) == False:
                    continue

                formatted.append({
                    "id": assignment.get("id"),
                    "name": assignment.get("name"),
                    "points_possible": assignment.get("points_possible"),
                    "due_at": assignment.get("due_at"),
                    "needs_grading_count": assignment.get("needs_grading_count", 0),
                    "published": assignment.get("published", False)
                })

            return formatted

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch course assignments: {e}")
            raise Exception(f"Canvas API error: {str(e)}")

    def get_submission_count(
        self,
        course_id: str,
        assignment_id: str
    ) -> Dict:
        """
        Get submission statistics for an assignment

        Returns:
            {
                "total_students": 25,
                "submitted": 23,
                "graded": 5,
                "needs_grading": 18
            }
        """

        try:
            submissions = self.get_assignment_submissions(
                course_id=course_id,
                assignment_id=assignment_id,
                include_unsubmitted=True
            )

            stats = {
                "total_students": len(submissions),
                "submitted": sum(1 for s in submissions if s["workflow_state"] in ["submitted", "graded"]),
                "graded": sum(1 for s in submissions if s.get("score") is not None),
                "needs_grading": sum(1 for s in submissions if s["workflow_state"] == "submitted" and s.get("score") is None)
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get submission count: {e}")
            raise
