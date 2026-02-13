"""
Submission Validator Service
Validates student file submissions before uploading to Canvas.
Checks file size, type, integrity, and naming conventions.
"""

import os
import re
from typing import Dict, List, Optional


# Canvas max file size: 500MB
MAX_FILE_SIZE = 500 * 1024 * 1024

# File type categories
FILE_TYPE_MAP = {
    "document": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages"],
    "spreadsheet": [".xlsx", ".xls", ".csv", ".ods", ".numbers"],
    "presentation": [".pptx", ".ppt", ".key", ".odp"],
    "image": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".tiff", ".webp"],
    "video": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"],
    "audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "code": [".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".html", ".css", ".rb", ".go", ".rs"],
    "archive": [".zip", ".tar", ".gz", ".rar", ".7z"],
}

# Turnitin-compatible formats
TURNITIN_FORMATS = [".doc", ".docx", ".pdf", ".txt", ".rtf"]

# Problematic filename characters
BAD_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')


class SubmissionValidator:
    """Validates files before Canvas submission."""

    def validate(
        self,
        file_name: str,
        file_size: int,
        file_type: Optional[str] = None,
        allowed_types: Optional[List[str]] = None,
        turnitin_enabled: bool = False,
        is_url: bool = False,
        url: Optional[str] = None,
    ) -> Dict:
        """
        Run all validation checks on a file.
        Returns dict with is_valid, issues, suggestions, can_auto_fix, auto_fix_options.
        """
        issues = []
        suggestions = []
        warnings = []
        auto_fix_options = []

        # 1. File size check
        if file_size > MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            issues.append(f"File is {size_mb:.0f}MB, Canvas limit is 500MB")
            ext = os.path.splitext(file_name)[1].lower()
            if ext in FILE_TYPE_MAP["video"]:
                suggestions.append("Compress your video before uploading")
                auto_fix_options.append("compress_video")
            else:
                suggestions.append("Reduce file size or split into multiple files")

        # 2. File type check
        ext = os.path.splitext(file_name)[1].lower()
        if allowed_types and len(allowed_types) > 0:
            # Normalize allowed types (some Canvas configs have dots, some don't)
            normalized_allowed = []
            for t in allowed_types:
                t = t.strip().lower()
                if not t.startswith("."):
                    t = f".{t}"
                normalized_allowed.append(t)

            if ext not in normalized_allowed:
                issues.append(f"File type '{ext}' is not accepted. Allowed: {', '.join(normalized_allowed)}")
                suggestions.append(f"Convert your file to one of: {', '.join(normalized_allowed)}")

        # 3. Turnitin compatibility
        if turnitin_enabled and ext not in TURNITIN_FORMATS:
            issues.append(f"Turnitin requires: {', '.join(TURNITIN_FORMATS)}. Your file is '{ext}'")
            suggestions.append("Save your file as PDF or Word document for Turnitin")

        # 4. Google Drive / Dropbox link check
        if is_url and url:
            if "drive.google.com" in url or "docs.google.com" in url:
                warnings.append("Google Drive link detected — make sure sharing is set to 'Anyone with the link'")
                auto_fix_options.append("fix_google_drive")
            elif "dropbox.com" in url:
                if "dl=0" in url:
                    warnings.append("Dropbox link may not be directly accessible. Use the direct download link.")
                    suggestions.append("Change 'dl=0' to 'dl=1' in your Dropbox link")

        # 5. Filename check
        if BAD_FILENAME_CHARS.search(file_name):
            issues.append("Filename contains special characters that may cause issues")
            clean_name = BAD_FILENAME_CHARS.sub("_", file_name)
            suggestions.append(f"Rename your file to: {clean_name}")

        if len(file_name) > 200:
            issues.append("Filename is too long (over 200 characters)")
            suggestions.append("Shorten your filename")

        # 6. Empty file check
        if file_size == 0:
            issues.append("File is empty (0 bytes)")
            suggestions.append("Make sure your file has content before submitting")

        # 7. Very small file warning
        if 0 < file_size < 100:
            warnings.append("File is very small — make sure it contains the complete submission")

        is_valid = len(issues) == 0

        return {
            "is_valid": is_valid,
            "issues": issues,
            "suggestions": suggestions,
            "warnings": warnings,
            "can_auto_fix": len(auto_fix_options) > 0,
            "auto_fix_options": auto_fix_options,
        }

    def get_accepted_types_display(self, allowed_types: Optional[List[str]]) -> str:
        """Convert allowed types list to human-readable string."""
        if not allowed_types:
            return "Any file type"

        return ", ".join(t.upper().lstrip(".") for t in allowed_types)
