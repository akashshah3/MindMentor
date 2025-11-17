"""
Database migration to add quiz_attempts and quiz_questions tables
"""

import sqlite3
import os

def migrate():
    """Add missing quiz-related tables"""
    
    db_path = os.path.join(os.path.dirname(__file__), '../../mindmentor.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add quiz_attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                score REAL NOT NULL,
                max_score REAL NOT NULL,
                percentage REAL,
                time_taken_minutes INTEGER,
                attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Add quiz_questions junction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                question_type TEXT NOT NULL,
                question_text TEXT NOT NULL,
                options TEXT,
                correct_answer TEXT NOT NULL,
                solution TEXT,
                marks REAL DEFAULT 4.0,
                topic_id INTEGER NOT NULL,
                difficulty TEXT,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id),
                FOREIGN KEY (topic_id) REFERENCES topics(id),
                UNIQUE(quiz_id, question_number)
            )
        """)
        
        conn.commit()
        print("✅ Migration successful!")
        print("   - Added quiz_attempts table")
        print("   - Added quiz_questions table")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
