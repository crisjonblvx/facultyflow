"""
Authentication Router
Shared auth endpoints for both educator and student editions.
"""

import bcrypt
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends

from auth_helpers import (
    LoginRequest, RegisterRequest,
    get_db_connection, get_current_user_from_token, create_session
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(request: LoginRequest):
    """Login endpoint - works for both educators and students"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, email, password_hash, role, is_active, is_demo, demo_expires_at, full_name
            FROM users
            WHERE email = %s
        """, (request.email,))

        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id, email, password_hash, role, is_active, is_demo, demo_expires_at, full_name = user

        # Check password
        password_bytes = request.password.encode('utf-8')
        stored_hash_bytes = password_hash.encode('utf-8')
        if not bcrypt.checkpw(password_bytes, stored_hash_bytes):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not is_active:
            raise HTTPException(status_code=403, detail="Account disabled")

        if is_demo and demo_expires_at and datetime.now() > demo_expires_at:
            raise HTTPException(status_code=403, detail="Demo account expired")

        # Create session
        session_token = create_session(user_id, conn, cursor)

        # Log activity
        cursor.execute("""
            INSERT INTO activity_log (user_id, action, details)
            VALUES (%s, 'login', %s)
        """, (user_id, '{"timestamp": "' + datetime.now().isoformat() + '"}'))

        cursor.execute("UPDATE users SET last_active_at = NOW() WHERE id = %s", (user_id,))

        conn.commit()

        return {
            "token": session_token,
            "user": {
                "id": user_id,
                "email": email,
                "role": role,
                "full_name": full_name,
                "is_demo": is_demo,
                "demo_expires_at": demo_expires_at.isoformat() if demo_expires_at else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")
    finally:
        cursor.close()
        conn.close()


@router.post("/register")
async def register(request: RegisterRequest):
    """Register a new student account"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (request.email.lower(),))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Email already registered")

        # Validate password
        if len(request.password) < 8:
            raise HTTPException(status_code=422, detail="Password must be at least 8 characters")

        # Hash password
        password_bytes = request.password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

        # Create user with student role
        cursor.execute("""
            INSERT INTO users (email, password_hash, full_name, role, is_active)
            VALUES (%s, %s, %s, 'student', TRUE)
            RETURNING id
        """, (request.email.lower(), password_hash, request.full_name))

        user_id = cursor.fetchone()[0]

        # Create session
        session_token = create_session(user_id, conn, cursor)

        # Log activity
        cursor.execute("""
            INSERT INTO activity_log (user_id, action, details)
            VALUES (%s, 'register', '{"method": "student_signup"}')
        """, (user_id,))

        conn.commit()

        return {
            "token": session_token,
            "user": {
                "id": user_id,
                "email": request.email.lower(),
                "role": "student",
                "full_name": request.full_name,
                "is_demo": False,
                "demo_expires_at": None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")
    finally:
        cursor.close()
        conn.close()


@router.post("/logout")
async def logout(current_user=Depends(get_current_user_from_token)):
    """Logout endpoint"""
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(current_user=Depends(get_current_user_from_token)):
    """Get current user info"""
    return current_user
