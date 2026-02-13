"""
Grade Calculator Service
Handles grade computation, weighted averages, what-if scenarios,
and drop-lowest/drop-highest rules.
"""

from typing import Dict, List, Optional
from decimal import Decimal


class GradeCalculator:
    """Calculates grades with support for weighted categories and what-if scenarios."""

    # Standard letter grade scale
    GRADE_SCALE = [
        (93, "A"), (90, "A-"), (87, "B+"), (83, "B"), (80, "B-"),
        (77, "C+"), (73, "C"), (70, "C-"), (67, "D+"), (63, "D"),
        (60, "D-"), (0, "F")
    ]

    def percentage_to_letter(self, percentage: float) -> str:
        """Convert a percentage to a letter grade."""
        for threshold, letter in self.GRADE_SCALE:
            if percentage >= threshold:
                return letter
        return "F"

    def calculate_category_score(
        self,
        assignments: List[Dict],
        drop_lowest: int = 0,
        drop_highest: int = 0
    ) -> Optional[Dict]:
        """
        Calculate score for a single assignment category/group.
        Returns points earned, points possible, and percentage.
        """
        graded = [a for a in assignments if a.get("graded") and a.get("points_possible")]
        if not graded:
            return None

        # Sort by score percentage for drop rules
        scored = []
        for a in graded:
            pct = (float(a["score"]) / float(a["points_possible"])) * 100 if a.get("score") is not None else 0
            scored.append({**a, "_pct": pct})

        scored.sort(key=lambda x: x["_pct"])

        # Apply drop rules
        if drop_lowest > 0 and len(scored) > drop_lowest:
            scored = scored[drop_lowest:]
        if drop_highest > 0 and len(scored) > drop_highest:
            scored = scored[:-drop_highest]

        if not scored:
            return None

        earned = sum(float(a.get("score", 0)) for a in scored)
        possible = sum(float(a["points_possible"]) for a in scored)
        percentage = (earned / possible * 100) if possible > 0 else 0

        return {
            "points_earned": round(earned, 2),
            "points_possible": round(possible, 2),
            "percentage": round(percentage, 2),
            "graded_count": len(scored),
            "total_count": len(assignments)
        }

    def calculate_weighted_grade(
        self,
        categories: List[Dict]
    ) -> Dict:
        """
        Calculate final weighted grade across categories.
        Each category dict should have: name, weight, assignments, drop_lowest, drop_highest
        """
        total_weight = 0
        weighted_sum = 0
        total_earned = 0
        total_possible = 0
        category_scores = {}

        for cat in categories:
            cat_score = self.calculate_category_score(
                cat.get("assignments", []),
                cat.get("drop_lowest", 0),
                cat.get("drop_highest", 0)
            )

            if cat_score is None:
                continue

            weight = float(cat.get("weight", 0))
            name = cat.get("name", "Unknown")

            category_scores[name] = {
                "percentage": cat_score["percentage"],
                "points_earned": cat_score["points_earned"],
                "points_possible": cat_score["points_possible"],
                "weight": weight,
                "graded_count": cat_score["graded_count"],
                "total_count": cat_score["total_count"],
            }

            if weight > 0:
                weighted_sum += cat_score["percentage"] * (weight / 100)
                total_weight += weight
            else:
                # Non-weighted: use points
                total_earned += cat_score["points_earned"]
                total_possible += cat_score["points_possible"]

        if total_weight > 0:
            # Weighted grading - scale to earned weight
            percentage = (weighted_sum / total_weight * 100) if total_weight > 0 else 0
        elif total_possible > 0:
            # Points-based grading
            percentage = (total_earned / total_possible) * 100
        else:
            percentage = 0

        percentage = round(percentage, 2)

        return {
            "percentage": percentage,
            "letter_grade": self.percentage_to_letter(percentage),
            "points_earned": round(total_earned, 2),
            "points_possible": round(total_possible, 2),
            "category_scores": category_scores
        }

    def calculate_points_grade(self, assignments: List[Dict]) -> Dict:
        """Simple points-based grade calculation (no categories)."""
        graded = [a for a in assignments if a.get("graded") and a.get("points_possible")]

        earned = sum(float(a.get("score", 0)) for a in graded)
        possible = sum(float(a["points_possible"]) for a in graded)
        percentage = (earned / possible * 100) if possible > 0 else 0
        percentage = round(percentage, 2)

        return {
            "percentage": percentage,
            "letter_grade": self.percentage_to_letter(percentage),
            "points_earned": round(earned, 2),
            "points_possible": round(possible, 2),
        }

    def what_if_target(
        self,
        current_earned: float,
        current_possible: float,
        remaining_possible: float,
        target_percentage: float
    ) -> Dict:
        """
        Calculate what score is needed on remaining assignments to achieve a target grade.
        """
        total_possible = current_possible + remaining_possible
        if total_possible <= 0:
            return {"achievable": False, "message": "No assignments available"}

        needed_total = target_percentage / 100 * total_possible
        needed_remaining = needed_total - current_earned

        if remaining_possible <= 0:
            return {
                "achievable": current_earned / current_possible * 100 >= target_percentage if current_possible > 0 else False,
                "needed_score": 0,
                "needed_percentage": 0,
                "message": "No remaining assignments."
            }

        needed_pct = (needed_remaining / remaining_possible) * 100

        achievable = needed_pct <= 100
        letter = self.percentage_to_letter(target_percentage)

        if not achievable:
            return {
                "achievable": False,
                "needed_score": round(needed_remaining, 2),
                "needed_percentage": round(needed_pct, 2),
                "message": f"Would need {needed_pct:.1f}% on remaining work — not achievable."
            }

        return {
            "achievable": True,
            "needed_score": round(needed_remaining, 2),
            "needed_percentage": round(needed_pct, 2),
            "message": f"Need {needed_pct:.1f}% average on remaining assignments to get {letter}"
        }

    def what_if_scores(
        self,
        assignments: List[Dict],
        hypothetical_scores: Dict[int, float]
    ) -> Dict:
        """
        Calculate projected grade if student gets hypothetical scores on specific assignments.
        hypothetical_scores: {assignment_id: score}
        """
        modified = []
        for a in assignments:
            a_copy = dict(a)
            if a["id"] in hypothetical_scores:
                a_copy["score"] = hypothetical_scores[a["id"]]
                a_copy["graded"] = True
            modified.append(a_copy)

        return self.calculate_points_grade(modified)
