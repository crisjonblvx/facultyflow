"""
Shared Authentication Helpers
Extracted from main.py for use by both educator and student routers.
"""

import os
import secrets
import bcrypt
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt

# Security
security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: Dict[str, Any]


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db_connection():
    """Get direct database connection"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(DATABASE_URL)


# ============================================================================
# TOKEN HELPERS
# ============================================================================

def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=30)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ============================================================================
# SESSION-BASED AUTH (Primary auth method)
# ============================================================================

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current user from session token"""
    token = credentials.credentials

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT s.user_id, s.expires_at, u.email, u.role, u.is_demo, u.demo_expires_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_token = %s AND u.is_active = TRUE
        """, (token,))

        session = cursor.fetchone()

        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        user_id, expires_at, email, role, is_demo, demo_expires_at = session

        # Check session expiry
        if datetime.now() > expires_at:
            raise HTTPException(status_code=401, detail="Session expired")

        # Check demo expiry
        if is_demo and demo_expires_at and datetime.now() > demo_expires_at:
            raise HTTPException(status_code=403, detail="Demo account expired")

        return {
            "user_id": user_id,
            "email": email,
            "role": role,
            "is_demo": is_demo
        }

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# SESSION HELPERS
# ============================================================================

def create_session(user_id: int, conn=None, cursor=None) -> str:
    """Create a new session token for a user. Returns the token."""
    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
        cursor = conn.cursor()

    try:
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)

        cursor.execute("""
            INSERT INTO sessions (user_id, session_token, expires_at)
            VALUES (%s, %s, %s)
        """, (user_id, session_token, expires_at))

        if own_connection:
            conn.commit()

        return session_token
    finally:
        if own_connection:
            cursor.close()
            conn.close()
