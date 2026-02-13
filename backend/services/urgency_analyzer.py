"""
Urgency Analyzer for Canvas Announcements
Rule-based urgency classifier using keyword scoring, time sensitivity,
and formatting signals.

No AI API calls - fast, free, and deterministic.
AI-enhanced analysis can be added in Phase 2.
"""

import re
from datetime import datetime
from typing import Dict, List


class UrgencyAnalyzer:
    """
    Classifies announcement urgency as HIGH, MEDIUM, or LOW.

    Scoring:
    - Urgent keywords: +10 per match
    - Medium keywords: +5 per match
    - Posted < 2 hours ago: +15
    - Posted < 12 hours ago: +5
    - Weekday during class hours: +5
    - ALL CAPS title: +5
    - Multiple exclamation marks: +3
    - Brief message (< 200 chars): +2

    Thresholds:
    - >= 25: HIGH (red, immediate notification)
    - >= 10: MEDIUM (orange, push notification)
    - < 10: LOW (green, digest only)
    """

    URGENT_KEYWORDS = [
        r'\bcancel(led|lation)?\b',
        r'\bmoved?\b',
        r'\bchanged?\b',
        r'\bemergency\b',
        r'\bimportant\b',
        r'\burgent\b',
        r'\btoday\b',
        r'\btomorrow\b',
        r'\basap\b',
        r'\bdue date change',
        r'\bexam location',
        r'\bzoom link',
        r'\broom change',
        r'\bclass moved',
        r'\bdeadline extended',
        r'\bpostponed\b',
        r'\brescheduled\b',
        r'\bfinal exam\b',
        r'\bgrade[s]? posted\b',
        r'\bextra credit\b',
        r'\bno class\b',
        r'\bclosed\b',
    ]

    MEDIUM_KEYWORDS = [
        r'\breminder\b',
        r'\bupcoming\b',
        r'\bposted\b',
        r'\bavailable\b',
        r'\bnew assignment\b',
        r'\bquiz\b',
        r'\btest\b',
        r'\bhomework\b',
        r'\breading\b',
        r'\bstudy guide\b',
        r'\boffice hours\b',
        r'\breview session\b',
        r'\bproject\b',
        r'\bpresentation\b',
        r'\blab\b',
        r'\bsubmit\b',
    ]

    def analyze(self, title: str, message: str, posted_at: datetime) -> Dict:
        """
        Analyze an announcement and return urgency classification.

        Args:
            title: Announcement title
            message: Announcement body text
            posted_at: When the announcement was posted

        Returns:
            {
                'level': 'HIGH' | 'MEDIUM' | 'LOW',
                'score': int,
                'reasons': List[str]
            }
        """
        score = 0
        reasons: List[str] = []

        text = f"{title} {message}".lower()

        # 1. Urgent keyword scoring (+10 each)
        urgent_matches = sum(
            1 for pattern in self.URGENT_KEYWORDS
            if re.search(pattern, text, re.IGNORECASE)
        )
        if urgent_matches > 0:
            score += urgent_matches * 10
            reasons.append(f"Urgent keywords found ({urgent_matches})")

        # 2. Medium keyword scoring (+5 each)
        medium_matches = sum(
            1 for pattern in self.MEDIUM_KEYWORDS
            if re.search(pattern, text, re.IGNORECASE)
        )
        if medium_matches > 0:
            score += medium_matches * 5
            reasons.append(f"Important keywords found ({medium_matches})")

        # 3. Time sensitivity
        now = datetime.utcnow()
        if posted_at.tzinfo:
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)

        try:
            hours_since = (now - posted_at).total_seconds() / 3600
        except TypeError:
            hours_since = 24  # fallback

        if hours_since < 2:
            score += 15
            reasons.append("Posted recently (< 2 hours)")
        elif hours_since < 12:
            score += 5
            reasons.append("Posted today")

        # 4. Weekday during class hours
        if posted_at.weekday() < 5 and 8 <= posted_at.hour <= 18:
            score += 5
            reasons.append("Posted during class hours")

        # 5. ALL CAPS title
        if title.isupper() and len(title) > 5:
            score += 5
            reasons.append("Title in ALL CAPS")

        # 6. Multiple exclamation marks
        if title.count('!') >= 2:
            score += 3
            reasons.append("Multiple exclamation marks")

        # 7. Brief message (short = likely urgent)
        if len(message) < 200:
            score += 2
            reasons.append("Brief message")

        # Classify
        if score >= 25:
            level = 'HIGH'
        elif score >= 10:
            level = 'MEDIUM'
        else:
            level = 'LOW'

        return {
            'level': level,
            'score': score,
            'reasons': reasons
        }
