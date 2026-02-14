"""
AI Grading Engine

Core engine for grading student submissions using GROQ's Llama 3.3 70B model.
"""

import asyncio
import json
import re
import os
from typing import List, Dict, Optional
from groq import AsyncGroq

# Initialize GROQ client
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))


class AIGradingEngine:
    """
    Core AI grading engine using GROQ's Llama 3.3 70B

    Features:
    - Grades submissions against rubric criteria
    - Generates personalized feedback
    - Assesses confidence in grades
    - Flags submissions needing manual review
    - Detects potential AI-generated content
    """

    def __init__(self, rubric: Dict, preferences: Optional[Dict] = None):
        """
        Initialize grading engine

        Args:
            rubric: Dict with structure:
                {
                    "criteria": [
                        {
                            "name": "Thesis Statement",
                            "points": 20,
                            "description": "Clear, arguable thesis..."
                        },
                        ...
                    ]
                }
            preferences: Optional grading preferences:
                {
                    "strictness": "lenient"|"balanced"|"strict",
                    "generate_feedback": True,
                    "flag_low_confidence": True,
                    "check_ai_content": True,
                    "check_plagiarism": False
                }
        """
        self.rubric = rubric
        self.preferences = preferences or {}

        # Default preferences
        if "strictness" not in self.preferences:
            self.preferences["strictness"] = "balanced"
        if "generate_feedback" not in self.preferences:
            self.preferences["generate_feedback"] = True

        # Grading strictness mapping
        self.strictness_map = {
            "lenient": "grade generously, give benefit of the doubt, interpret requirements broadly",
            "balanced": "grade fairly with standard academic expectations, be objective",
            "strict": "grade strictly with high standards, be critical and thorough"
        }

    async def grade_submission(
        self,
        submission_text: str,
        student_name: Optional[str] = None
    ) -> Dict:
        """
        Grade a single submission using AI

        Args:
            submission_text: The student's submission text
            student_name: Optional student name for personalized feedback

        Returns:
            Dict with structure:
            {
                "total_score": 85.5,
                "rubric_scores": {
                    "Thesis Statement": 18,
                    "Evidence": 27,
                    ...
                },
                "feedback": "Overall feedback...",
                "criterion_feedback": {
                    "Thesis Statement": "Specific feedback...",
                    ...
                },
                "confidence": "high"|"medium"|"low",
                "flags": ["needs_review_analysis"]
            }
        """

        # Validate input
        if not submission_text or len(submission_text.strip()) < 10:
            return {
                "error": "Submission text too short or empty",
                "confidence": "low",
                "flags": ["empty_submission"]
            }

        # Build grading prompt
        prompt = self._build_grading_prompt(submission_text, student_name)

        # Call GROQ API
        try:
            response = await groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=2048,
                top_p=0.9
            )

            # Parse AI response
            result = self._parse_grading_response(
                response.choices[0].message.content
            )

            # Check for parsing errors
            if "error" in result:
                return {
                    **result,
                    "confidence": "low",
                    "flags": ["parse_error"]
                }

            # Add confidence assessment
            result["confidence"] = self._assess_confidence(result, submission_text)

            # Add flags
            result["flags"] = self._generate_flags(
                submission_text,
                result
            )

            return result

        except Exception as e:
            print(f"AI Grading error: {e}")
            return {
                "error": str(e),
                "confidence": "low",
                "flags": ["api_error"]
            }

    def _get_system_prompt(self) -> str:
        """Generate system prompt for AI grader"""

        strictness = self.strictness_map.get(
            self.preferences.get("strictness", "balanced"),
            "grade fairly with standard academic expectations"
        )

        return f"""You are an expert college professor grading student assignments with years of experience.

GRADING PHILOSOPHY:
- {strictness}
- Provide constructive, personalized feedback that helps students improve
- Be specific about strengths and areas for improvement
- Maintain consistent standards across all submissions
- Focus on the rubric criteria provided
- Be fair and objective

OUTPUT FORMAT:
You MUST return your grading as valid JSON with this EXACT structure:
{{
  "rubric_scores": {{
    "Criterion Name": score_number,
    "Another Criterion": score_number
  }},
  "criterion_feedback": {{
    "Criterion Name": "1-2 sentences of specific feedback for this criterion",
    "Another Criterion": "1-2 sentences of specific feedback"
  }},
  "overall_feedback": "2-3 sentences of overall feedback addressing the student directly"
}}

CRITICAL RULES:
- Scores MUST be numbers (integers or decimals), NOT strings
- Criterion names in rubric_scores and criterion_feedback MUST match exactly
- Feedback should be 1-3 sentences per criterion
- Overall feedback should be encouraging but honest
- Address the student directly using "you" and their name if provided
- Return ONLY the JSON, no extra text before or after"""

    def _build_grading_prompt(
        self,
        submission_text: str,
        student_name: Optional[str] = None
    ) -> str:
        """Build the grading prompt with rubric and submission"""

        # Format rubric
        rubric_text = "GRADING RUBRIC:\n"
        for criterion in self.rubric.get("criteria", []):
            rubric_text += f"\n{criterion['name']} ({criterion['points']} points maximum):\n"
            rubric_text += f"  Description: {criterion['description']}\n"

        total_points = sum(c['points'] for c in self.rubric.get("criteria", []))

        prompt = f"""{rubric_text}

TOTAL POSSIBLE POINTS: {total_points}

{"STUDENT NAME: " + student_name if student_name else ""}

SUBMISSION TO GRADE:
---
{submission_text}
---

Please grade this submission according to the rubric above. Provide a score for each criterion and constructive feedback. Return your grading as JSON following the specified format."""

        return prompt

    def _parse_grading_response(self, response_text: str) -> Dict:
        """Parse AI response into structured format"""

        # Extract JSON from response
        # AI sometimes wraps JSON in markdown code blocks
        json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            # Try to find JSON directly
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            json_text = json_match.group(0) if json_match else response_text

        try:
            parsed = json.loads(json_text)

            # Validate structure
            if "rubric_scores" not in parsed:
                return {"error": "Missing rubric_scores in AI response"}

            # Calculate total score
            scores = parsed.get("rubric_scores", {})
            total_score = sum(float(score) for score in scores.values())

            return {
                "total_score": round(total_score, 2),
                "rubric_scores": scores,
                "criterion_feedback": parsed.get("criterion_feedback", {}),
                "feedback": parsed.get("overall_feedback", "")
            }

        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response as JSON: {e}")
            print(f"Response text: {response_text[:500]}")

            return {
                "error": "Failed to parse AI grading response as JSON",
                "raw_response": response_text[:500]
            }
        except Exception as e:
            print(f"Error processing AI response: {e}")
            return {
                "error": f"Error processing response: {str(e)}"
            }

    def _assess_confidence(self, result: Dict, submission_text: str) -> str:
        """
        Assess confidence in AI grading

        Returns: "high", "medium", or "low"
        """

        # Check for errors
        if "error" in result:
            return "low"

        # Get scores
        scores = result.get("rubric_scores", {})
        if not scores:
            return "low"

        # Calculate score statistics
        score_values = [float(v) for v in scores.values()]
        criteria = self.rubric.get("criteria", [])

        if not criteria:
            return "low"

        # Calculate percentage of max for each criterion
        percentages = []
        for criterion in criteria:
            criterion_name = criterion["name"]
            max_points = criterion["points"]

            if criterion_name in scores:
                score = float(scores[criterion_name])
                percentage = score / max_points if max_points > 0 else 0
                percentages.append(percentage)

        if not percentages:
            return "low"

        avg_percentage = sum(percentages) / len(percentages)

        # Check feedback quality
        feedback_length = len(result.get("feedback", ""))
        criterion_feedback = result.get("criterion_feedback", {})
        has_detailed_feedback = len(criterion_feedback) >= len(criteria) * 0.8

        # High confidence criteria:
        # - Scores in reasonable range (20-95%)
        # - Substantive feedback (>50 chars)
        # - Feedback for most criteria
        if (0.2 <= avg_percentage <= 0.95 and
            feedback_length > 50 and
            has_detailed_feedback):
            return "high"

        # Medium confidence:
        # - Scores somewhat reasonable (10-98%)
        # - Some feedback present
        elif (0.1 <= avg_percentage <= 0.98 and
              feedback_length > 20):
            return "medium"

        # Low confidence for everything else
        else:
            return "low"

    def _generate_flags(
        self,
        submission_text: str,
        grading_result: Dict
    ) -> List[str]:
        """
        Generate flags for submissions that need attention

        Returns list of flag strings
        """

        flags = []

        # Flag low confidence
        confidence = grading_result.get("confidence", "low")
        if confidence == "low":
            flags.append("low_confidence")
        elif confidence == "medium":
            flags.append("medium_confidence")

        # Calculate total score and max
        total_score = grading_result.get("total_score", 0)
        max_score = sum(c['points'] for c in self.rubric.get("criteria", []))

        if max_score > 0:
            percentage = total_score / max_score

            # Flag extremely low scores
            if percentage < 0.3:
                flags.append("very_low_score")

            # Flag extremely high scores (might be too generous)
            elif percentage > 0.95:
                flags.append("very_high_score")

        # Check for very short submissions
        if len(submission_text) < 200:
            flags.append("short_submission")

        # AI-generated content detection (if enabled)
        if self.preferences.get("check_ai_content", False):
            ai_probability = self._detect_ai_content(submission_text)
            if ai_probability > 0.7:
                flags.append(f"likely_ai_generated")
            elif ai_probability > 0.5:
                flags.append(f"possibly_ai_generated")

        return flags

    def _detect_ai_content(self, text: str) -> float:
        """
        Simple AI-generated content detector

        Returns probability (0-1) that text is AI-generated

        Note: This is a basic heuristic detector. Production systems should use:
        - GPTZero API
        - Originality.ai API
        - Copyleaks API
        - Or custom trained ML models
        """

        indicators = 0.0
        total_checks = 6.0

        # 1. Check for overly formal structure (perfect paragraphs)
        paragraphs = text.split("\n\n")
        if len(paragraphs) > 2:
            # AI tends to create evenly-sized paragraphs
            para_lengths = [len(p) for p in paragraphs if len(p) > 50]
            if para_lengths:
                avg_length = sum(para_lengths) / len(para_lengths)
                variance = sum((l - avg_length) ** 2 for l in para_lengths) / len(para_lengths)
                if variance < avg_length * 0.3:  # Low variance = too uniform
                    indicators += 0.5

        # 2. Check for common AI phrases
        ai_phrases = [
            "it is important to note",
            "it is worth mentioning",
            "it's important to note",
            "furthermore",
            "moreover",
            "in conclusion",
            "to summarize",
            "delve into",
            "dive into",
            "comprehensive understanding",
            "multifaceted"
        ]
        text_lower = text.lower()
        phrase_count = sum(1 for phrase in ai_phrases if phrase in text_lower)
        if phrase_count >= 3:
            indicators += 1.0
        elif phrase_count >= 2:
            indicators += 0.5

        # 3. Check for lack of personal voice
        personal_markers = [" i ", " my ", " me ", " we ", " our ", " us "]
        has_personal_voice = any(marker in text_lower for marker in personal_markers)
        if not has_personal_voice and len(text) > 300:
            indicators += 0.5

        # 4. Check for overly perfect grammar (no common typos)
        common_typos = ["teh ", "adn ", "recieve", "seperate", "definately"]
        has_typos = any(typo in text_lower for typo in common_typos)
        if not has_typos and len(text) > 500:
            indicators += 0.3

        # 5. Check sentence structure variety
        sentences = text.split(".")
        if len(sentences) > 5:
            sentence_lengths = [len(s.split()) for s in sentences if len(s.strip()) > 0]
            if sentence_lengths:
                avg_sent_length = sum(sentence_lengths) / len(sentence_lengths)
                # AI tends toward consistent 15-25 word sentences
                if 15 <= avg_sent_length <= 25:
                    indicators += 0.5

        # 6. Check for overly formal academic language
        formal_words = ["thus", "hence", "thereby", "wherein", "aforementioned", "subsequently"]
        formal_count = sum(1 for word in formal_words if word in text_lower)
        if formal_count >= 2:
            indicators += 0.5

        # Return probability
        probability = min(indicators / total_checks, 1.0)
        return probability

    async def grade_batch(
        self,
        submissions: List[Dict]
    ) -> List[Dict]:
        """
        Grade multiple submissions in parallel

        Args:
            submissions: List of dicts with structure:
                [
                    {
                        "student_name": "Sarah Johnson",
                        "submission_text": "Essay text...",
                        "submission_id": "12345",
                        "student_id": "67890"
                    },
                    ...
                ]

        Returns:
            List of grading results (one per submission)
        """

        # Grade submissions in parallel using asyncio
        tasks = [
            self.grade_submission(
                submission_text=sub.get("submission_text", ""),
                student_name=sub.get("student_name")
            )
            for sub in submissions
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Add submission metadata to results
        for i, result in enumerate(results):
            # Handle exceptions
            if isinstance(result, Exception):
                results[i] = {
                    "error": str(result),
                    "confidence": "low",
                    "flags": ["exception_during_grading"]
                }
                result = results[i]

            # Add submission IDs
            result["submission_id"] = submissions[i].get("submission_id")
            result["student_id"] = submissions[i].get("student_id")
            result["student_name"] = submissions[i].get("student_name")

        return results

    async def regenerate_feedback(
        self,
        submission_text: str,
        rubric_scores: Dict,
        student_name: Optional[str] = None
    ) -> str:
        """
        Regenerate just the feedback for a submission (keep scores)

        Useful when professor likes scores but wants different feedback
        """

        prompt = f"""You are a college professor providing feedback on a graded assignment.

RUBRIC AND SCORES:
{json.dumps(rubric_scores, indent=2)}

STUDENT: {student_name or "the student"}

SUBMISSION:
{submission_text}

Write 2-3 sentences of constructive overall feedback for this student based on their scores. Be encouraging but honest. Address the student directly using "you"."""

        try:
            response = await groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an encouraging college professor providing constructive feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=256
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error regenerating feedback: {e}")
            return "Unable to generate feedback at this time."


# Convenience function for simple usage
async def grade_single_submission(
    submission_text: str,
    rubric: Dict,
    student_name: Optional[str] = None,
    preferences: Optional[Dict] = None
) -> Dict:
    """
    Convenience function to grade a single submission

    Usage:
        result = await grade_single_submission(
            submission_text="Student's essay...",
            rubric={
                "criteria": [
                    {"name": "Thesis", "points": 20, "description": "..."},
                    {"name": "Evidence", "points": 30, "description": "..."}
                ]
            },
            student_name="Sarah Johnson"
        )
    """
    engine = AIGradingEngine(rubric=rubric, preferences=preferences)
    return await engine.grade_submission(submission_text, student_name)
