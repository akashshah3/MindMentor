"""
Database initialization script for MindMentor
Creates the SQLite database and applies schema
"""

import sqlite3
import os
from pathlib import Path
import sys


def get_db_path():
    """Get the database file path"""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "mindmentor.db"


def get_schema_path():
    """Get the schema SQL file path"""
    return Path(__file__).parent / "schema.sql"


def init_database(db_path=None, schema_path=None):
    """
    Initialize the database with schema
    
    Args:
        db_path: Path to database file (default: project_root/mindmentor.db)
        schema_path: Path to schema SQL file (default: src/data/schema.sql)
    """
    if db_path is None:
        db_path = get_db_path()
    
    if schema_path is None:
        schema_path = get_schema_path()
    
    # Check if database already exists and has tables
    db_exists = os.path.exists(db_path)
    
    if db_exists:
        # Check if it has tables (to see if it's already initialized)
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            if len(tables) > 0:
                # Database already initialized
                return True
        except:
            pass
    
    # Read schema SQL
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Create database and apply schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.executescript(schema_sql)
        conn.commit()
        print(f"✅ Database created successfully at {db_path}")
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\n📋 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        return True
    
    except sqlite3.Error as e:
        print(f"❌ Error creating database: {e}", file=sys.stderr)
        return False
    
    finally:
        conn.close()


def init_database_silent(db_path=None, schema_path=None):
    """
    Initialize the database silently (for production/Streamlit Cloud)
    Returns True if successful or already initialized
    """
    if db_path is None:
        db_path = get_db_path()
    
    if schema_path is None:
        schema_path = get_schema_path()
    
    # Check if database already exists and has tables
    db_exists = os.path.exists(db_path)
    
    if db_exists:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            if len(tables) > 0:
                return True  # Already initialized
        except:
            pass
    
    # Read schema SQL
    try:
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
    except FileNotFoundError:
        print(f"❌ Schema file not found at {schema_path}", file=sys.stderr)
        return False
    
    # Create database and apply schema
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"❌ Error creating database: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    print("=== MindMentor Database Initialization ===\n")
    success = init_database()
    
    if success:
        print("\n✅ Database initialization complete!")
        print("\nNext steps:")
        print("1. Run seed_jee_data.py to populate JEE syllabus")
        print("2. Copy .env.example to .env and add your Gemini API key")
        print("3. Run the application with: streamlit run app.py")
    else:
        print("\n❌ Database initialization failed!")
