"""
Run database migrations for ReadySetClass
"""
import os
import psycopg2


def run_migration(conn, cursor, filename):
    """Execute a single migration file"""
    migration_path = os.path.join(os.path.dirname(__file__), 'migrations', filename)

    if not os.path.exists(migration_path):
        print(f"  ⚠️  Migration file not found: {filename}")
        return False

    print(f"  🔄 Running: {filename}")

    with open(migration_path, 'r') as f:
        migration_sql = f.read()

    try:
        cursor.execute(migration_sql)
        conn.commit()
        print(f"  ✅ {filename} completed")
        return True
    except Exception as e:
        print(f"  ❌ {filename} failed: {e}")
        conn.rollback()
        return False


def run_migrations():
    """Execute all migration files in order"""

    DATABASE_URL = os.getenv('DATABASE_URL')

    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        return

    # Fix postgres:// to postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    print("🔄 Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    migrations = [
        '001_create_auth_tables.sql',
        '002_add_subscriptions.sql',
        '003_student_announcement_tables.sql',
        '004_assignments_grades_tables.sql',
        '005_ai_study_tools_tables.sql',
    ]

    print(f"📦 Running {len(migrations)} migrations...\n")

    for migration in migrations:
        run_migration(conn, cursor, migration)

    print("\n✅ All migrations complete!")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    run_migrations()
