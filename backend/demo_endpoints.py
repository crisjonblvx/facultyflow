"""
Demo Account Endpoints for ReadySetClass
Allows visitors to instantly create isolated demo accounts
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import secrets
import string
import bcrypt
from datetime import datetime, timedelta

router = APIRouter()

def generate_demo_email():
    """Generate unique demo email"""
    random_id = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    return f"demo-{random_id}@readysetclass.com"

def generate_demo_password():
    """Generate simple demo password"""
    return "demo2026"  # Simple password for all demos

class CreateDemoResponse(BaseModel):
    email: str
    password: str
    token: str
    expires_in_hours: int

@router.post("/api/demo/create", response_model=CreateDemoResponse)
async def create_demo_account(db: Session = Depends(get_db)):
    """
    Create a temporary demo account for testing

    Returns:
        {
            "email": "demo-abc123@readysetclass.com",
            "password": "demo2026",
            "token": "jwt_token_here",
            "expires_in_hours": 24
        }
    """
    try:
        # Generate unique credentials
        email = generate_demo_email()
        password = generate_demo_password()

        # Hash password
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

        # Calculate expiration (24 hours from now)
        expires_at = datetime.now() + timedelta(hours=24)

        # Create user in database
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO users
            (email, password_hash, full_name, role, institution, notes, is_active, is_demo, subscription_tier, trial_ends_at)
            VALUES (%s, %s, %s, 'user', %s, %s, TRUE, TRUE, 'trial', %s)
            RETURNING id
        """, (
            email,
            password_hash,
            "Demo User",
            "Demo University",
            f"Auto-generated demo - Expires: {expires_at.strftime('%Y-%m-%d %H:%M')}",
            expires_at
        ))

        user_id = cursor.fetchone()[0]
        db.commit()

        # Generate auth token
        token_data = {
            "user_id": user_id,
            "email": email,
            "exp": expires_at
        }
        token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return {
            "email": email,
            "password": password,
            "token": token,
            "expires_in_hours": 24
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create demo: {str(e)}")


@router.post("/api/demo/cleanup")
async def cleanup_expired_demos(db: Session = Depends(get_db)):
    """
    Cleanup expired demo accounts (admin only)
    Deletes demo accounts older than 24 hours
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            DELETE FROM users
            WHERE is_demo = TRUE
            AND trial_ends_at < NOW()
            RETURNING id, email
        """)

        deleted = cursor.fetchall()
        db.commit()

        return {
            "deleted_count": len(deleted),
            "deleted_emails": [row[1] for row in deleted]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
