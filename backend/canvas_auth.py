"""
Canvas API Authentication
Handles Canvas LMS API authentication and token management

Built for: FacultyFlow v2.0
Based on: Canvas API OAuth documentation
"""

import requests
from typing import Dict, Optional
import os


class CanvasAuth:
    """
    Canvas Authentication Handler
    Supports manual access token authentication
    """

    def __init__(self, base_url: str, access_token: str):
        """
        Initialize Canvas authentication

        Args:
            base_url: Canvas instance URL (e.g., "https://vuu.instructure.com")
            access_token: Canvas API access token
        """
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def test_connection(self) -> tuple[bool, Optional[Dict], Optional[str]]:
        """
        Test if the Canvas API token is valid

        Returns:
            tuple: (success: bool, user_data: dict or None, error_message: str or None)
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/users/self",
                headers=self.headers,
                timeout=10
            )

            print(f"Canvas API test response: {response.status_code}")

            if response.status_code == 200:
                return True, response.json(), None
            elif response.status_code == 401:
                error_msg = "Invalid Canvas API token. Please check your token and try again."
                print(f"Canvas auth failed: {response.text}")
                return False, None, error_msg
            else:
                error_msg = f"Canvas API error (status {response.status_code}): {response.text}"
                print(error_msg)
                return False, None, error_msg

        except requests.RequestException as e:
            error_msg = f"Connection test failed: {str(e)}"
            print(error_msg)
            return False, None, error_msg

    def get_user_profile(self) -> Optional[Dict]:
        """
        Get the authenticated user's Canvas profile

        Returns:
            dict: User profile data or None if failed
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/users/self/profile",
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            return None

        except requests.RequestException:
            return None


def encrypt_token(token: str) -> str:
    """
    Encrypt Canvas API token for secure storage

    Args:
        token: Plain text API token

    Returns:
        str: Encrypted token

    Note: In production, use proper encryption (e.g., Fernet from cryptography)
    """
    # TODO: Implement proper encryption using ENCRYPTION_KEY from environment
    # For now, return as-is (NOT SECURE - fix before production)
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if not encryption_key:
        # Placeholder - implement actual encryption
        return token

    # Implement Fernet encryption here
    return token


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt Canvas API token for use

    Args:
        encrypted_token: Encrypted token from database

    Returns:
        str: Decrypted token
    """
    # TODO: Implement proper decryption
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if not encryption_key:
        # Placeholder - implement actual decryption
        return encrypted_token

    # Implement Fernet decryption here
    return encrypted_token
