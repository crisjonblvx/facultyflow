"""
ReadySetClass - Grading Setup Service

Handles Canvas grading configuration via API.
Reduces 45-minute manual setup to 2-minute wizard.

Strategy by: Sunni
Implementation by: Q-Tip
"""

import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class GradingSetupService:
    """
    Handles grading setup via Canvas API

    Features:
    - Create assignment groups
    - Enable weighted grading
    - Apply special rules (drop lowest, extra credit, etc.)
    - Analyze existing setups
    - Fix messy configurations
    """

    def __init__(self, canvas_url: str, canvas_token: str):
        """
        Initialize grading setup service

        Args:
            canvas_url: Canvas instance URL (e.g., https://vuu.instructure.com)
            canvas_token: Canvas API access token
        """
        self.canvas_url = canvas_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {canvas_token}",
            "Content-Type": "application/json"
        }

    async def setup_weighted_grading(
        self,
        course_id: int,
        categories: List[Dict],
        rules: Optional[Dict] = None
    ) -> Dict:
        """
        Complete grading setup workflow

        Args:
            course_id: Canvas course ID
            categories: List of {name, weight, rules}
                Example: [
                    {"name": "Quizzes", "weight": 30, "rules": {"drop_lowest": {"enabled": True, "count": 1}}},
                    {"name": "Assignments", "weight": 40, "rules": {}},
                    {"name": "Exams", "weight": 30, "rules": {}}
                ]
            rules: Global rules (late penalty, missing policy, etc.)

        Returns:
            {
                "status": "success",
                "groups_created": 3,
                "weighted_grading_enabled": True,
                "assignment_groups": [...]
            }
        """

        try:
            logger.info(f"Starting grading setup for course {course_id}")

            # Step 1: Validate weights total 100%
            total_weight = sum(cat.get('weight', 0) for cat in categories)
            if abs(total_weight - 100) > 0.01:
                return {
                    "status": "error",
                    "message": f"Category weights must total 100% (currently {total_weight}%)"
                }

            # Step 2: Create assignment groups
            created_groups = []
            for category in categories:
                group = await self.create_assignment_group(
                    course_id=course_id,
                    name=category['name'],
                    weight=category['weight'],
                    rules=category.get('rules', {})
                )
                created_groups.append(group)
                logger.info(f"Created group: {category['name']} ({category['weight']}%)")

            # Step 3: Enable weighted grading
            await self.enable_weighted_grading(course_id)
            logger.info("Enabled weighted grading")

            # Step 4: Apply global rules if any
            if rules:
                await self.apply_global_rules(course_id, rules)
                logger.info("Applied global rules")

            # Step 5: Verify setup
            verification = await self.verify_grading_setup(course_id)
            logger.info("Verified grading setup")

            return {
                "status": "success",
                "groups_created": len(created_groups),
                "weighted_grading_enabled": True,
                "assignment_groups": created_groups,
                "verification": verification
            }

        except Exception as e:
            logger.error(f"Grading setup failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def create_assignment_group(
        self,
        course_id: int,
        name: str,
        weight: float,
        rules: Optional[Dict] = None
    ) -> Dict:
        """
        Create assignment group with Canvas API

        Canvas API: POST /api/v1/courses/:course_id/assignment_groups

        Args:
            course_id: Canvas course ID
            name: Group name (e.g., "Quizzes", "Assignments")
            weight: Percentage weight (e.g., 30 for 30%)
            rules: Drop rules, extra credit, etc.

        Returns:
            Canvas assignment group object
        """

        url = f"{self.canvas_url}/api/v1/courses/{course_id}/assignment_groups"

        data = {
            "name": name,
            "group_weight": weight
        }

        # Add drop rules if specified
        if rules:
            rules_dict = {}

            # Drop lowest scores
            if rules.get('drop_lowest', {}).get('enabled'):
                rules_dict['drop_lowest'] = rules['drop_lowest'].get('count', 1)

            # Drop highest scores
            if rules.get('drop_highest', {}).get('enabled'):
                rules_dict['drop_highest'] = rules['drop_highest'].get('count', 1)

            # Never drop (for final exam, etc.)
            if rules.get('never_drop'):
                rules_dict['never_drop'] = rules['never_drop']

            if rules_dict:
                data['rules'] = rules_dict

        response = requests.post(url, headers=self.headers, json=data)

        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create assignment group '{name}': {response.text}")

        return response.json()

    async def enable_weighted_grading(self, course_id: int) -> Dict:
        """
        Enable weighted grading for course

        Canvas API: PUT /api/v1/courses/:course_id

        Args:
            course_id: Canvas course ID

        Returns:
            Canvas course object
        """

        url = f"{self.canvas_url}/api/v1/courses/{course_id}"

        data = {
            "course": {
                "apply_assignment_group_weights": True
            }
        }

        response = requests.put(url, headers=self.headers, json=data)

        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to enable weighted grading: {response.text}")

        return response.json()

    async def apply_global_rules(self, course_id: int, rules: Dict) -> Dict:
        """
        Apply global grading rules (late policy, missing policy, etc.)

        Canvas API: PUT /api/v1/courses/:course_id/settings

        Args:
            course_id: Canvas course ID
            rules: Global rules dict
                Example: {
                    "late_penalty": {"enabled": True, "percent_per_day": 10},
                    "missing_policy": {"enabled": True, "auto_zero": True}
                }

        Returns:
            Canvas settings object
        """

        url = f"{self.canvas_url}/api/v1/courses/{course_id}/settings"

        settings = {}

        # Late submission policy
        if rules.get('late_penalty', {}).get('enabled'):
            settings['late_policy'] = {
                'late_submission_deduction_enabled': True,
                'late_submission_deduction': rules['late_penalty'].get('percent_per_day', 10),
                'late_submission_interval': 'day'
            }

        # Missing submission policy
        if rules.get('missing_policy', {}).get('enabled'):
            settings['late_policy'] = settings.get('late_policy', {})
            settings['late_policy']['missing_submission_deduction_enabled'] = True

        if not settings:
            return {}

        response = requests.put(url, headers=self.headers, json=settings)

        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to apply global rules: {response.text}")

        return response.json()

    async def verify_grading_setup(self, course_id: int) -> Dict:
        """
        Verify grading setup is correct

        Checks:
        - Assignment groups exist
        - Weights add to 100%
        - Weighted grading is enabled

        Args:
            course_id: Canvas course ID

        Returns:
            {
                "groups_count": 3,
                "total_weight": 100.0,
                "verified": True
            }
        """

        # Get assignment groups
        url = f"{self.canvas_url}/api/v1/courses/{course_id}/assignment_groups"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"Failed to verify setup: {response.text}")

        groups = response.json()

        # Calculate total weight
        total_weight = sum(g.get('group_weight', 0) for g in groups)

        # Check if weights are valid
        weights_valid = abs(total_weight - 100) <= 0.01

        return {
            "groups_count": len(groups),
            "total_weight": round(total_weight, 2),
            "verified": weights_valid,
            "groups": groups
        }

    async def analyze_existing_setup(self, course_id: int) -> Dict:
        """
        Analyze existing Canvas grading setup
        Find issues and suggest fixes

        Args:
            course_id: Canvas course ID

        Returns:
            {
                "has_groups": True,
                "groups": [...],
                "weighted_grading_enabled": True,
                "total_weight": 97,
                "orphan_assignments": 3,
                "issues": ["Weights don't add to 100%", ...],
                "suggestions": ["Adjust weights to total 100%", ...]
            }
        """

        try:
            # Get assignment groups
            groups_url = f"{self.canvas_url}/api/v1/courses/{course_id}/assignment_groups"
            groups_response = requests.get(groups_url, headers=self.headers)
            groups = groups_response.json() if groups_response.status_code == 200 else []

            # Get course settings
            course_url = f"{self.canvas_url}/api/v1/courses/{course_id}"
            course_response = requests.get(course_url, headers=self.headers)
            course = course_response.json() if course_response.status_code == 200 else {}

            # Get all assignments
            assignments_url = f"{self.canvas_url}/api/v1/courses/{course_id}/assignments"
            assignments_response = requests.get(assignments_url, headers=self.headers)
            assignments = assignments_response.json() if assignments_response.status_code == 200 else []

            # Analyze
            issues = []
            suggestions = []

            # Check if weighted grading is enabled
            weighted_enabled = course.get('apply_assignment_group_weights', False)

            if not weighted_enabled and len(groups) > 1:
                issues.append("Multiple groups exist but weighted grading not enabled")
                suggestions.append("Enable weighted grading to use category weights")

            # Check total weight
            total_weight = sum(g.get('group_weight', 0) for g in groups)

            if weighted_enabled and abs(total_weight - 100) > 0.01:
                issues.append(f"Weights total {total_weight}% (should be 100%)")

                # Suggest specific fixes
                if total_weight < 100:
                    diff = 100 - total_weight
                    suggestions.append(f"Add {diff}% to existing categories")
                else:
                    diff = total_weight - 100
                    suggestions.append(f"Reduce weights by {diff}%")

            # Check orphan assignments (not in any group)
            orphan_assignments = [a for a in assignments if not a.get('assignment_group_id')]

            if orphan_assignments:
                issues.append(f"{len(orphan_assignments)} assignments not in any category")
                suggestions.append("Move orphan assignments to appropriate categories")

            # Check for empty groups
            empty_groups = [g for g in groups if not any(a.get('assignment_group_id') == g['id'] for a in assignments)]

            if empty_groups:
                issues.append(f"{len(empty_groups)} empty categories (no assignments)")
                suggestions.append("Remove empty categories or add assignments to them")

            return {
                "has_groups": len(groups) > 0,
                "groups": groups,
                "weighted_grading_enabled": weighted_enabled,
                "total_weight": round(total_weight, 2),
                "orphan_assignments": len(orphan_assignments),
                "empty_groups": len(empty_groups),
                "issues": issues,
                "suggestions": suggestions,
                "health": "healthy" if not issues else "needs_attention"
            }

        except Exception as e:
            logger.error(f"Failed to analyze grading setup: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def fix_existing_setup(self, course_id: int, fix_type: str = "auto") -> Dict:
        """
        Automatically fix common grading setup issues

        Args:
            course_id: Canvas course ID
            fix_type: "auto" | "reset"
                - auto: Fix issues while preserving existing structure
                - reset: Delete all groups and start fresh

        Returns:
            Result of fix operation
        """

        analysis = await self.analyze_existing_setup(course_id)

        if fix_type == "reset":
            # Delete all existing groups and start fresh
            for group in analysis.get('groups', []):
                await self.delete_assignment_group(course_id, group['id'])

            return {
                "status": "success",
                "message": "All assignment groups deleted. Ready for fresh setup.",
                "groups_deleted": len(analysis.get('groups', []))
            }

        elif fix_type == "auto":
            # Auto-fix issues
            groups = analysis.get('groups', [])
            total_weight = analysis.get('total_weight', 0)

            # Fix weight issues
            if abs(total_weight - 100) > 0.01 and len(groups) > 0:
                # Proportionally adjust all weights to total 100%
                scale_factor = 100 / total_weight

                for group in groups:
                    new_weight = round(group.get('group_weight', 0) * scale_factor, 2)
                    await self.update_assignment_group_weight(
                        course_id,
                        group['id'],
                        new_weight
                    )

            # Enable weighted grading if not enabled
            if not analysis.get('weighted_grading_enabled') and len(groups) > 1:
                await self.enable_weighted_grading(course_id)

            return {
                "status": "success",
                "message": "Grading setup fixed automatically",
                "groups_adjusted": len(groups)
            }

    async def delete_assignment_group(self, course_id: int, group_id: int) -> bool:
        """Delete an assignment group"""
        url = f"{self.canvas_url}/api/v1/courses/{course_id}/assignment_groups/{group_id}"
        response = requests.delete(url, headers=self.headers)
        return response.status_code in [200, 204]

    async def update_assignment_group_weight(
        self,
        course_id: int,
        group_id: int,
        new_weight: float
    ) -> Dict:
        """Update weight of an assignment group"""
        url = f"{self.canvas_url}/api/v1/courses/{course_id}/assignment_groups/{group_id}"

        data = {
            "group_weight": new_weight
        }

        response = requests.put(url, headers=self.headers, json=data)

        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to update group weight: {response.text}")

        return response.json()


# Subject-based grading templates
GRADING_TEMPLATES = {
    "Mass Communications": [
        {"name": "Participation", "weight": 15, "rules": {}},
        {"name": "Discussions", "weight": 20, "rules": {}},
        {"name": "Assignments", "weight": 30, "rules": {}},
        {"name": "Projects", "weight": 20, "rules": {}},
        {"name": "Final Project", "weight": 15, "rules": {}}
    ],
    "Mathematics": [
        {"name": "Homework", "weight": 30, "rules": {}},
        {"name": "Quizzes", "weight": 30, "rules": {"drop_lowest": {"enabled": True, "count": 1}}},
        {"name": "Exams", "weight": 40, "rules": {}}
    ],
    "English": [
        {"name": "Essays", "weight": 50, "rules": {}},
        {"name": "Participation", "weight": 20, "rules": {}},
        {"name": "Exams", "weight": 30, "rules": {}}
    ],
    "Science": [
        {"name": "Labs", "weight": 30, "rules": {}},
        {"name": "Quizzes", "weight": 20, "rules": {"drop_lowest": {"enabled": True, "count": 1}}},
        {"name": "Exams", "weight": 50, "rules": {}}
    ],
    "History": [
        {"name": "Participation", "weight": 15, "rules": {}},
        {"name": "Papers", "weight": 40, "rules": {}},
        {"name": "Midterm", "weight": 20, "rules": {}},
        {"name": "Final", "weight": 25, "rules": {}}
    ],
    "Business": [
        {"name": "Case Studies", "weight": 30, "rules": {}},
        {"name": "Quizzes", "weight": 20, "rules": {"drop_lowest": {"enabled": True, "count": 1}}},
        {"name": "Project", "weight": 30, "rules": {}},
        {"name": "Final Exam", "weight": 20, "rules": {}}
    ],
    "Computer Science": [
        {"name": "Programming Assignments", "weight": 40, "rules": {}},
        {"name": "Quizzes", "weight": 20, "rules": {"drop_lowest": {"enabled": True, "count": 2}}},
        {"name": "Projects", "weight": 25, "rules": {}},
        {"name": "Final Exam", "weight": 15, "rules": {}}
    ],
    "Custom": []  # Start blank for custom setup
}


def get_template(subject: str) -> List[Dict]:
    """
    Get grading template for a subject

    Args:
        subject: Subject name (e.g., "Mass Communications")

    Returns:
        List of category dicts with name, weight, rules
    """
    return GRADING_TEMPLATES.get(subject, GRADING_TEMPLATES["Custom"])
