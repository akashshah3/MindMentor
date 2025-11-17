"""
Health check script to verify database setup
Run this to confirm everything is working correctly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data.init_db import get_db_path, init_database_silent
from src.data.seed_jee_data import seed_jee_topics_silent
import sqlite3


def check_database():
    """Run health checks on the database"""
    print("🔍 Running database health checks...\n")
    
    db_path = get_db_path()
    
    # Check 1: Database file exists
    print("1️⃣ Checking if database file exists...")
    if db_path.exists():
        print(f"   ✅ Database found at: {db_path}")
    else:
        print(f"   ❌ Database not found at: {db_path}")
        print("   🔧 Creating database...")
        if init_database_silent():
            print("   ✅ Database created successfully")
        else:
            print("   ❌ Failed to create database")
            return False
    
    # Check 2: Database has tables
    print("\n2️⃣ Checking database schema...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        expected_tables = [
            'users', 'topics', 'llm_cache', 'lessons', 'questions',
            'quizzes', 'attempts', 'student_profiles', 'schedules',
            'achievements', 'study_sessions'
        ]
        
        found_tables = [t[0] for t in tables]
        print(f"   Found {len(found_tables)} tables")
        
        missing = set(expected_tables) - set(found_tables)
        if missing:
            print(f"   ⚠️ Missing tables: {missing}")
        else:
            print(f"   ✅ All expected tables present")
        
    except sqlite3.Error as e:
        print(f"   ❌ Database error: {e}")
        conn.close()
        return False
    
    # Check 3: Topics are seeded
    print("\n3️⃣ Checking JEE topics...")
    try:
        cursor.execute("SELECT COUNT(*) FROM topics")
        topic_count = cursor.fetchone()[0]
        
        if topic_count == 0:
            print("   ⚠️ No topics found. Seeding...")
            conn.close()
            if seed_jee_topics_silent():
                print("   ✅ Topics seeded successfully")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM topics")
                topic_count = cursor.fetchone()[0]
            else:
                print("   ❌ Failed to seed topics")
                return False
        
        print(f"   ✅ Found {topic_count} topics")
        
        # Show breakdown by subject
        cursor.execute("""
            SELECT subject, COUNT(*) as count 
            FROM topics 
            GROUP BY subject
        """)
        breakdown = cursor.fetchall()
        print("\n   📊 Topics by subject:")
        for subject, count in breakdown:
            print(f"      • {subject}: {count} topics")
        
    except sqlite3.Error as e:
        print(f"   ❌ Database error: {e}")
        conn.close()
        return False
    finally:
        conn.close()
    
    # Check 4: Test write permission
    print("\n4️⃣ Testing write permissions...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Try to create a test table
        cursor.execute("CREATE TABLE IF NOT EXISTS _health_check (id INTEGER)")
        cursor.execute("DROP TABLE _health_check")
        conn.commit()
        conn.close()
        
        print("   ✅ Write permissions OK")
    except sqlite3.Error as e:
        print(f"   ❌ Write permission error: {e}")
        return False
    
    print("\n" + "="*50)
    print("✅ All health checks passed!")
    print("="*50)
    return True


if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1)
