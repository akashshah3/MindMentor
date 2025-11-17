"""
Database operations for MindMentor
Handles all database interactions
"""

import sqlite3
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager


class Database:
    """Database connection and operations manager"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            # Default to project root
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "mindmentor.db"
        
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
        finally:
            conn.close()
    
    # ===== USER OPERATIONS =====
    
    def create_user(self, username: str, password_hash: str, name: str, 
                   email: Optional[str] = None, exam_target: Optional[str] = None,
                   daily_hours: Optional[float] = None) -> Optional[int]:
        """
        Create a new user
        
        Args:
            username: Unique username
            password_hash: Hashed password
            name: User's full name
            email: Optional email address
            exam_target: JEE_MAIN, JEE_ADVANCED, or BOTH
            daily_hours: Available study hours per day
            
        Returns:
            User ID if successful, None if username exists
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, name, email, 
                                     exam_target, daily_hours, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (username, password_hash, name, email, exam_target, 
                     daily_hours, datetime.now().isoformat()))
                
                conn.commit()
                return cursor.lastrowid
            
            except sqlite3.IntegrityError:
                # Username already exists
                return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Get user by username
        
        Args:
            username: Username to search for
            
        Returns:
            User data as dictionary, or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, password_hash, name, email, 
                       exam_target, daily_hours, created_at, last_login, is_active
                FROM users
                WHERE username = ? AND is_active = 1
            """, (username,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User data as dictionary, or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, password_hash, name, email,
                       exam_target, daily_hours, created_at, last_login, is_active
                FROM users
                WHERE id = ? AND is_active = 1
            """, (user_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_last_login(self, user_id: int):
        """
        Update user's last login timestamp
        
        Args:
            user_id: User ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET last_login = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), user_id))
            conn.commit()
    
    def update_user_profile(self, user_id: int, **kwargs):
        """
        Update user profile fields
        
        Args:
            user_id: User ID
            **kwargs: Fields to update (name, email, exam_target, daily_hours)
        """
        allowed_fields = {'name', 'email', 'exam_target', 'daily_hours'}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return
        
        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [user_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE users
                SET {set_clause}
                WHERE id = ?
            """, values)
            conn.commit()
    
    # ===== TOPIC OPERATIONS =====
    
    def get_all_topics(self, subject: Optional[str] = None) -> List[Dict]:
        """
        Get all topics, optionally filtered by subject
        
        Args:
            subject: Optional filter by subject (Physics, Chemistry, Mathematics)
            
        Returns:
            List of topic dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if subject:
                cursor.execute("""
                    SELECT id, subject, chapter_name, topic_name, 
                           exam_weight, difficulty_level
                    FROM topics
                    WHERE subject = ?
                    ORDER BY subject, chapter_name, topic_name
                """, (subject,))
            else:
                cursor.execute("""
                    SELECT id, subject, chapter_name, topic_name,
                           exam_weight, difficulty_level
                    FROM topics
                    ORDER BY subject, chapter_name, topic_name
                """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_topic_by_id(self, topic_id: int) -> Optional[Dict]:
        """
        Get topic by ID
        
        Args:
            topic_id: Topic ID
            
        Returns:
            Topic data as dictionary, or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, subject, chapter_name, topic_name,
                       exam_weight, difficulty_level, prerequisites
                FROM topics
                WHERE id = ?
            """, (topic_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_topics_by_chapter(self, subject: str, chapter_name: str) -> List[Dict]:
        """
        Get all topics in a chapter
        
        Args:
            subject: Subject name
            chapter_name: Chapter name
            
        Returns:
            List of topic dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, subject, chapter_name, topic_name,
                       exam_weight, difficulty_level
                FROM topics
                WHERE subject = ? AND chapter_name = ?
                ORDER BY topic_name
            """, (subject, chapter_name))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ===== STUDENT PROFILE OPERATIONS =====
    
    def get_student_profile(self, user_id: int, topic_id: int) -> Optional[Dict]:
        """
        Get student's learning profile for a topic
        
        Args:
            user_id: User ID
            topic_id: Topic ID
            
        Returns:
            Profile data as dictionary, or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, topic_id, mastery_score, last_attempt_date,
                       total_attempts, correct_attempts, accuracy, avg_time_seconds,
                       revision_count, next_review_date, weak_concepts, strength_level
                FROM student_profiles
                WHERE user_id = ? AND topic_id = ?
            """, (user_id, topic_id))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_student_profiles(self, user_id: int) -> List[Dict]:
        """
        Get all learning profiles for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of profile dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sp.*, t.subject, t.chapter_name, t.topic_name
                FROM student_profiles sp
                JOIN topics t ON sp.topic_id = t.id
                WHERE sp.user_id = ?
                ORDER BY sp.mastery_score ASC, t.subject, t.chapter_name
            """, (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ===== LLM CACHE OPERATIONS =====
    
    def get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """
        Get cached LLM response
        
        Args:
            cache_key: Unique cache key
            
        Returns:
            Cache entry as dictionary, or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, cache_key, model_used, response_content, 
                       created_at, last_accessed, access_count, content_type
                FROM llm_cache
                WHERE cache_key = ?
            """, (cache_key,))
            
            row = cursor.fetchone()
            
            if row:
                # Update access tracking
                cache_id = row['id']
                cursor.execute("""
                    UPDATE llm_cache
                    SET last_accessed = ?,
                        access_count = access_count + 1
                    WHERE id = ?
                """, (datetime.now().isoformat(), cache_id))
                conn.commit()
            
            return dict(row) if row else None
    
    def store_in_cache(self, cache_key: str, model_used: str, 
                      response_content: str, prompt_template: Optional[str] = None,
                      content_type: Optional[str] = None) -> int:
        """
        Store LLM response in cache
        
        Args:
            cache_key: Unique cache key
            model_used: Model name that generated the response
            response_content: The LLM response to cache
            prompt_template: Optional prompt template used
            content_type: Optional type of content (lesson, question, etc.)
            
        Returns:
            Cache entry ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO llm_cache 
                    (cache_key, model_used, prompt_template, response_content, 
                     content_type, created_at, last_accessed, access_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (cache_key, model_used, prompt_template, response_content,
                     content_type, datetime.now().isoformat(), datetime.now().isoformat()))
                
                conn.commit()
                return cursor.lastrowid
            
            except sqlite3.IntegrityError:
                # Cache key already exists - this shouldn't happen normally
                # but handle it by returning the existing entry
                cursor.execute("SELECT id FROM llm_cache WHERE cache_key = ?", (cache_key,))
                row = cursor.fetchone()
                return row['id'] if row else -1
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total entries
            cursor.execute("SELECT COUNT(*) as total FROM llm_cache")
            total = cursor.fetchone()['total']
            
            # Total accesses
            cursor.execute("SELECT SUM(access_count) as total_accesses FROM llm_cache")
            total_accesses = cursor.fetchone()['total_accesses'] or 0
            
            # By model
            cursor.execute("""
                SELECT model_used, COUNT(*) as count, SUM(access_count) as accesses
                FROM llm_cache
                GROUP BY model_used
            """)
            by_model = [dict(row) for row in cursor.fetchall()]
            
            # By content type
            cursor.execute("""
                SELECT content_type, COUNT(*) as count, SUM(access_count) as accesses
                FROM llm_cache
                WHERE content_type IS NOT NULL
                GROUP BY content_type
            """)
            by_type = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_entries': total,
                'total_accesses': total_accesses,
                'by_model': by_model,
                'by_type': by_type,
                'avg_accesses_per_entry': total_accesses / total if total > 0 else 0
            }
    
    def clear_old_cache(self, days: int = 30) -> int:
        """
        Clear cache entries older than specified days that haven't been accessed recently
        
        Args:
            days: Number of days of inactivity before clearing
            
        Returns:
            Number of entries deleted
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM llm_cache
                WHERE datetime(last_accessed) < datetime('now', '-' || ? || ' days')
            """, (days,))
            
            deleted = cursor.rowcount
            conn.commit()
            return deleted


# Singleton instance
db = Database()
