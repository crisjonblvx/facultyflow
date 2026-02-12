"""
Run database migrations for ReadySetClass
"""
import os
import psycopg2

def run_migrations():
    """Execute all migration files"""

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

    print("🔄 Running migration: 001_create_auth_tables.sql")

    # Read and execute migration
    migration_path = os.path.join(os.path.dirname(__file__), 'migrations', '001_create_auth_tables.sql')

    with open(migration_path, 'r') as f:
        migration_sql = f.read()

    try:
        cursor.execute(migration_sql)
        conn.commit()
        print("✅ Migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migrations()
