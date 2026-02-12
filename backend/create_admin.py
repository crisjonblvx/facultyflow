"""
Create admin account for ReadySetClass
Run this once to create CJ's admin account
"""
import os
import psycopg2
import bcrypt
from getpass import getpass

def create_admin():
    """Create admin account"""

    DATABASE_URL = os.getenv('DATABASE_URL')

    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        return

    # Fix postgres:// to postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    print("=" * 50)
    print("Create Admin Account for ReadySetClass")
    print("=" * 50)

    # Default admin email
    email = input("Admin email (default: cj@vuu.edu): ").strip() or "cj@vuu.edu"

    # Get password
    while True:
        password = getpass("Admin password: ")
        password_confirm = getpass("Confirm password: ")

        if password != password_confirm:
            print("❌ Passwords don't match! Try again.\n")
            continue

        if len(password) < 8:
            print("❌ Password must be at least 8 characters! Try again.\n")
            continue

        # Check password length (bcrypt max is 72 bytes)
        if len(password.encode('utf-8')) > 72:
            print("❌ Password too long! Keep it under 72 characters. Try again.\n")
            continue

        break

    # Hash password with bcrypt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    # Connect to database
    print("\n🔄 Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Create admin user
        cursor.execute("""
            INSERT INTO users
            (email, password_hash, full_name, role, institution, notes, is_active, is_demo)
            VALUES (%s, %s, %s, 'admin', %s, %s, TRUE, FALSE)
            ON CONFLICT (email) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                updated_at = NOW()
            RETURNING id
        """, (
            email,
            password_hash,
            "CJ (Founder)",
            "Virginia Union University",
            "Admin - Full Access - Never Expires"
        ))

        user_id = cursor.fetchone()[0]

        conn.commit()

        print("\n" + "=" * 50)
        print("✅ ADMIN ACCOUNT CREATED SUCCESSFULLY!")
        print("=" * 50)
        print(f"Email: {email}")
        print(f"User ID: {user_id}")
        print(f"Role: admin")
        print(f"\nLogin at: https://readysetclass.com/login.html")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Error creating admin: {e}")
        conn.rollback()

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_admin()
