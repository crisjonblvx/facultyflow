"""
Create demo account for ReadySetClass
Allows visitors to test drive the app
"""
import os
import psycopg2
import bcrypt

def create_demo():
    """Create demo account with sample data"""

    DATABASE_URL = os.getenv('DATABASE_URL')

    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        return

    # Fix postgres:// to postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    print("=" * 50)
    print("Create Demo Account for ReadySetClass")
    print("=" * 50)

    # Demo credentials
    email = "demo@readysetclass.com"
    password = "TryReadySetClass2026"  # Public demo password

    # Hash password
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    # Connect to database
    print("\n🔄 Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Create demo user
        cursor.execute("""
            INSERT INTO users
            (email, password_hash, full_name, role, institution, notes, is_active, is_demo, subscription_tier, trial_ends_at)
            VALUES (%s, %s, %s, 'user', %s, %s, TRUE, TRUE, 'trial', NOW() + INTERVAL '365 days')
            ON CONFLICT (email) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                is_demo = TRUE,
                trial_ends_at = NOW() + INTERVAL '365 days',
                updated_at = NOW()
            RETURNING id
        """, (
            email,
            password_hash,
            "Demo User",
            "Demo University",
            "Demo Account - Never Expires - Full Access"
        ))

        user_id = cursor.fetchone()[0]

        conn.commit()

        print("\n" + "=" * 50)
        print("✅ DEMO ACCOUNT CREATED SUCCESSFULLY!")
        print("=" * 50)
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"User ID: {user_id}")
        print(f"Role: user (demo)")
        print(f"Trial: 365 days")
        print(f"\nPublic Credentials (share with visitors):")
        print(f"  Email: demo@readysetclass.com")
        print(f"  Password: TryReadySetClass2026")
        print(f"\nLogin at: https://readysetclass.com/login.html")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Error creating demo: {e}")
        conn.rollback()

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_demo()
