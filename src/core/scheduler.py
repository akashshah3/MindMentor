"""
Study Scheduler - Generates personalized study schedules using SM-2 spaced repetition algorithm
"""

from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
import json
from dataclasses import dataclass

from src.data.db import Database


@dataclass
class ScheduledItem:
    """Represents a single scheduled study item"""
    topic_id: int
    topic_name: str
    subject: str
    activity_type: str  # 'learn', 'revise', 'practice'
    duration_minutes: int
    priority: float
    difficulty: str
    reason: str  # Why this topic is scheduled


@dataclass
class DailySchedule:
    """Represents a complete day's schedule"""
    date: date
    items: List[ScheduledItem]
    total_minutes: int
    completion_percentage: float = 0.0
    notes: str = ""


class StudyScheduler:
    """
    Generates adaptive study schedules using:
    - SM-2 spaced repetition algorithm for revision
    - JEE topic weights for prioritization
    - Student mastery scores for personalization
    - Time constraints and daily hours
    """
    
    # SM-2 Algorithm constants
    DEFAULT_EASE_FACTOR = 2.5
    MIN_EASE_FACTOR = 1.3
    
    # Activity durations (in minutes)
    LEARN_DURATION = 60  # New topic learning
    REVISE_DURATION = 30  # Revision of learned topic
    PRACTICE_DURATION = 45  # Practice problems
    
    def __init__(self, db: Database, user_id: int):
        self.db = db
        self.user_id = user_id
        self.user_info = self._get_user_info()
        self.daily_minutes = int((self.user_info.get('daily_hours') or 4) * 60)
    
    def _get_user_info(self) -> Dict:
        """Get user's study preferences and constraints"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT daily_hours, exam_target FROM users WHERE id = ?",
                (self.user_id,)
            )
            user = cursor.fetchone()
            
            if user:
                return {
                    'daily_hours': user['daily_hours'] or 4.0,
                    'exam_target': user['exam_target'] or 'BOTH'
                }
            return {'daily_hours': 4.0, 'exam_target': 'BOTH'}
    
    def generate_schedule(
        self,
        start_date: date,
        num_days: int = 7,
        focus_subjects: Optional[List[str]] = None
    ) -> List[DailySchedule]:
        """
        Generate a personalized study schedule for the specified number of days
        
        Args:
            start_date: Start date for the schedule
            num_days: Number of days to schedule (default: 7)
            focus_subjects: Optional list of subjects to focus on ['Physics', 'Chemistry', 'Mathematics']
        
        Returns:
            List of DailySchedule objects
        """
        schedules = []
        scheduled_topic_ids = set()  # Track topics already scheduled this week
        
        for day_offset in range(num_days):
            current_date = start_date + timedelta(days=day_offset)
            daily_items = self._generate_daily_items(current_date, focus_subjects, scheduled_topic_ids)
            
            # Add newly scheduled topic IDs to the set
            for item in daily_items:
                scheduled_topic_ids.add(item.topic_id)
            
            # Calculate total time
            total_time = sum(item.duration_minutes for item in daily_items)
            
            # Get existing schedule if any
            existing = self._get_existing_schedule(current_date)
            completion = existing.get('completion_percentage', 0.0) if existing else 0.0
            notes = existing.get('notes', '') if existing else ''
            
            schedules.append(DailySchedule(
                date=current_date,
                items=daily_items,
                total_minutes=total_time,
                completion_percentage=completion,
                notes=notes
            ))
        
        return schedules
    
    def _generate_daily_items(
        self,
        schedule_date: date,
        focus_subjects: Optional[List[str]] = None,
        exclude_topic_ids: Optional[set] = None
    ) -> List[ScheduledItem]:
        """Generate study items for a single day"""
        items = []
        remaining_minutes = self.daily_minutes
        
        if exclude_topic_ids is None:
            exclude_topic_ids = set()
        
        # 1. Get items due for revision (SM-2 based)
        revision_items = self._get_revision_due_topics(schedule_date, focus_subjects, exclude_topic_ids)
        for item in revision_items:
            if remaining_minutes >= self.REVISE_DURATION:
                items.append(item)
                remaining_minutes -= item.duration_minutes
        
        # 2. Get weak topics that need practice
        if remaining_minutes >= self.PRACTICE_DURATION:
            practice_items = self._get_practice_topics(focus_subjects, exclude_topic_ids, limit=2)
            for item in practice_items:
                if remaining_minutes >= self.PRACTICE_DURATION:
                    items.append(item)
                    remaining_minutes -= item.duration_minutes
        
        # 3. Add new topics to learn (prioritized by JEE weight)
        if remaining_minutes >= self.LEARN_DURATION:
            learn_items = self._get_new_topics_to_learn(focus_subjects, exclude_topic_ids, limit=3)
            for item in learn_items:
                if remaining_minutes >= self.LEARN_DURATION:
                    items.append(item)
                    remaining_minutes -= item.duration_minutes
        
        # Sort by priority (revision > practice > new learning)
        priority_order = {'revise': 3, 'practice': 2, 'learn': 1}
        items.sort(key=lambda x: priority_order.get(x.activity_type, 0), reverse=True)
        
        return items
    
    def _get_revision_due_topics(
        self,
        schedule_date: date,
        focus_subjects: Optional[List[str]] = None,
        exclude_topic_ids: Optional[set] = None
    ) -> List[ScheduledItem]:
        """Get topics due for revision using SM-2 algorithm"""
        if exclude_topic_ids is None:
            exclude_topic_ids = set()
            
        subject_filter = ""
        params = [self.user_id, schedule_date.isoformat()]
        
        if focus_subjects:
            placeholders = ','.join('?' * len(focus_subjects))
            subject_filter = f"AND t.subject IN ({placeholders})"
            params.extend(focus_subjects)
        
        # Add exclusion filter for already scheduled topics
        exclude_filter = ""
        if exclude_topic_ids:
            placeholders = ','.join('?' * len(exclude_topic_ids))
            exclude_filter = f"AND sp.topic_id NOT IN ({placeholders})"
            params.extend(list(exclude_topic_ids))
        
        query = f"""
            SELECT 
                sp.topic_id,
                t.topic_name,
                t.subject,
                t.difficulty_level,
                t.exam_weight,
                sp.mastery_score,
                sp.next_review_date,
                sp.revision_count
            FROM student_profiles sp
            JOIN topics t ON sp.topic_id = t.id
            WHERE sp.user_id = ?
                AND sp.next_review_date <= ?
                AND sp.mastery_score < 1.0
                {subject_filter}
                {exclude_filter}
            ORDER BY sp.next_review_date ASC, t.exam_weight DESC
            LIMIT 5
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            topics = [dict(row) for row in cursor.fetchall()]
        
        items = []
        for topic in topics:
            items.append(ScheduledItem(
                topic_id=topic['topic_id'],
                topic_name=topic['topic_name'],
                subject=topic['subject'],
                activity_type='revise',
                duration_minutes=self.REVISE_DURATION,
                priority=3.0 + topic['exam_weight'],  # Highest priority
                difficulty=topic['difficulty_level'],
                reason=f"Due for revision (Mastery: {int(topic['mastery_score']*100)}%)"
            ))
        
        return items
    
    def _get_practice_topics(
        self,
        focus_subjects: Optional[List[str]] = None,
        exclude_topic_ids: Optional[set] = None,
        limit: int = 2
    ) -> List[ScheduledItem]:
        """Get weak topics that need more practice"""
        if exclude_topic_ids is None:
            exclude_topic_ids = set()
            
        subject_filter = ""
        params = [self.user_id, 0.6]  # Mastery < 60% = needs practice
        
        if focus_subjects:
            placeholders = ','.join('?' * len(focus_subjects))
            subject_filter = f"AND t.subject IN ({placeholders})"
            params.extend(focus_subjects)
        
        # Add exclusion filter for already scheduled topics
        exclude_filter = ""
        if exclude_topic_ids:
            placeholders = ','.join('?' * len(exclude_topic_ids))
            exclude_filter = f"AND sp.topic_id NOT IN ({placeholders})"
            params.extend(list(exclude_topic_ids))
        
        params.append(limit)
        
        query = f"""
            SELECT 
                sp.topic_id,
                t.topic_name,
                t.subject,
                t.difficulty_level,
                t.exam_weight,
                sp.mastery_score,
                sp.accuracy
            FROM student_profiles sp
            JOIN topics t ON sp.topic_id = t.id
            WHERE sp.user_id = ?
                AND sp.mastery_score < ?
                AND sp.mastery_score > 0
                {subject_filter}
                {exclude_filter}
            ORDER BY sp.mastery_score ASC, t.exam_weight DESC
            LIMIT ?
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            topics = [dict(row) for row in cursor.fetchall()]
        
        items = []
        for topic in topics:
            items.append(ScheduledItem(
                topic_id=topic['topic_id'],
                topic_name=topic['topic_name'],
                subject=topic['subject'],
                activity_type='practice',
                duration_minutes=self.PRACTICE_DURATION,
                priority=2.0 + topic['exam_weight'],
                difficulty=topic['difficulty_level'],
                reason=f"Weak area (Mastery: {int(topic['mastery_score']*100)}%, Accuracy: {int(topic['accuracy']*100)}%)"
            ))
        
        return items
    
    def _get_new_topics_to_learn(
        self,
        focus_subjects: Optional[List[str]] = None,
        exclude_topic_ids: Optional[set] = None,
        limit: int = 3
    ) -> List[ScheduledItem]:
        """Get new topics to learn, prioritized by JEE exam weight"""
        if exclude_topic_ids is None:
            exclude_topic_ids = set()
            
        subject_filter = ""
        params = [self.user_id]
        
        if focus_subjects:
            placeholders = ','.join('?' * len(focus_subjects))
            subject_filter = f"AND t.subject IN ({placeholders})"
            params.extend(focus_subjects)
        
        # Add exclusion filter for already scheduled topics
        exclude_filter = ""
        if exclude_topic_ids:
            placeholders = ','.join('?' * len(exclude_topic_ids))
            exclude_filter = f"AND t.id NOT IN ({placeholders})"
            params.extend(list(exclude_topic_ids))
        
        params.append(limit)
        
        query = f"""
            SELECT 
                t.id as topic_id,
                t.topic_name,
                t.subject,
                t.difficulty_level,
                t.exam_weight
            FROM topics t
            WHERE NOT EXISTS (
                SELECT 1 FROM student_profiles sp 
                WHERE sp.user_id = ? AND sp.topic_id = t.id
            )
            {subject_filter}
            {exclude_filter}
            ORDER BY t.exam_weight DESC, t.difficulty_level ASC
            LIMIT ?
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            topics = [dict(row) for row in cursor.fetchall()]
        
        items = []
        for topic in topics:
            items.append(ScheduledItem(
                topic_id=topic['topic_id'],
                topic_name=topic['topic_name'],
                subject=topic['subject'],
                activity_type='learn',
                duration_minutes=self.LEARN_DURATION,
                priority=1.0 + topic['exam_weight'],
                difficulty=topic['difficulty_level'],
                reason=f"High priority topic (JEE weight: {topic['exam_weight']:.1f})"
            ))
        
        return items
    
    def _get_existing_schedule(self, schedule_date: date) -> Optional[Dict]:
        """Get existing schedule for a date if it exists"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT planned_items, completed, completion_percentage, notes
                FROM schedules
                WHERE user_id = ? AND date = ?
                """,
                (self.user_id, schedule_date.isoformat())
            )
            result = cursor.fetchone()
            
            if result:
                return {
                    'planned_items': result['planned_items'],
                    'completed': result['completed'],
                    'completion_percentage': result['completion_percentage'],
                    'notes': result['notes']
                }
            return None
    
    def save_schedule(self, daily_schedule: DailySchedule) -> bool:
        """Save or update a daily schedule in the database"""
        # Convert items to JSON
        items_json = json.dumps([
            {
                'topic_id': item.topic_id,
                'topic_name': item.topic_name,
                'subject': item.subject,
                'activity_type': item.activity_type,
                'duration_minutes': item.duration_minutes,
                'priority': item.priority,
                'difficulty': item.difficulty,
                'reason': item.reason
            }
            for item in daily_schedule.items
        ])
        
        # Check if schedule exists
        existing = self._get_existing_schedule(daily_schedule.date)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if existing:
                # Update existing schedule
                query = """
                    UPDATE schedules
                    SET planned_items = ?,
                        completion_percentage = ?,
                        notes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND date = ?
                """
                params = (
                    items_json,
                    daily_schedule.completion_percentage,
                    daily_schedule.notes,
                    self.user_id,
                    daily_schedule.date.isoformat()
                )
            else:
                # Insert new schedule
                query = """
                    INSERT INTO schedules (user_id, date, planned_items, completion_percentage, notes)
                    VALUES (?, ?, ?, ?, ?)
                """
                params = (
                    self.user_id,
                    daily_schedule.date.isoformat(),
                    items_json,
                    daily_schedule.completion_percentage,
                    daily_schedule.notes
                )
            
            cursor.execute(query, params)
            conn.commit()
        
        return True
    
    def update_next_review_date(self, topic_id: int, quality: int) -> None:
        """
        Update next review date using SM-2 algorithm
        
        Args:
            topic_id: Topic ID
            quality: Quality of recall (0-5)
                0: Complete blackout
                1: Incorrect response, correct answer seemed familiar
                2: Incorrect response, correct answer remembered
                3: Correct response, difficult recall
                4: Correct response, hesitation
                5: Perfect response
        """
        # Get current student profile
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT mastery_score, revision_count, next_review_date
                FROM student_profiles
                WHERE user_id = ? AND topic_id = ?
                """,
                (self.user_id, topic_id)
            )
            profile = cursor.fetchone()
        
            if not profile:
                return
            
            revision_count = profile['revision_count'] or 0
            
            # Calculate ease factor (EF)
            # EF' = EF + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            ease_factor = self.DEFAULT_EASE_FACTOR
            ease_factor = max(
                self.MIN_EASE_FACTOR,
                ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            )
            
            # Calculate interval
            if quality < 3:
                # Reset if recall was poor
                interval_days = 1
                revision_count = 0
            else:
                if revision_count == 0:
                    interval_days = 1
                elif revision_count == 1:
                    interval_days = 6
                else:
                    # I(n) = I(n-1) * EF
                    last_interval = 6 if revision_count == 1 else int(6 * (ease_factor ** (revision_count - 1)))
                    interval_days = int(last_interval * ease_factor)
                
                revision_count += 1
            
            # Calculate next review date
            next_review = datetime.now().date() + timedelta(days=interval_days)
            
            # Update database
            cursor.execute(
                """
                UPDATE student_profiles
                SET revision_count = ?,
                    next_review_date = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND topic_id = ?
                """,
                (revision_count, next_review.isoformat(), self.user_id, topic_id)
            )
            conn.commit()
    
    def mark_item_completed(
        self,
        schedule_date: date,
        topic_id: int,
        quality: Optional[int] = None
    ) -> bool:
        """
        Mark a scheduled item as completed
        
        Args:
            schedule_date: Date of the schedule
            topic_id: Topic ID that was completed
            quality: Optional quality rating (0-5) for SM-2 algorithm
        """
        # Get the schedule
        existing = self._get_existing_schedule(schedule_date)
        if not existing:
            return False
        
        # Parse planned items
        planned_items = json.loads(existing['planned_items'])
        
        # Remove the completed item
        updated_items = [item for item in planned_items if item['topic_id'] != topic_id]
        
        # Calculate completion percentage
        total_items = len(planned_items)
        completed_items = total_items - len(updated_items)
        completion_pct = (completed_items / total_items * 100) if total_items > 0 else 0
        
        # Update schedule
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE schedules
                SET planned_items = ?,
                    completion_percentage = ?,
                    completed = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND date = ?
                """,
                (
                    json.dumps(updated_items),
                    completion_pct,
                    1 if completion_pct >= 100 else 0,
                    self.user_id,
                    schedule_date.isoformat()
                )
            )
            conn.commit()
        
        # Update next review date if quality provided
        if quality is not None:
            self.update_next_review_date(topic_id, quality)
        
        return True
    
    def get_schedule_stats(self, start_date: date, end_date: date) -> Dict:
        """Get statistics about schedules in a date range"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    date,
                    completion_percentage,
                    completed,
                    planned_items
                FROM schedules
                WHERE user_id = ? AND date BETWEEN ? AND ?
                ORDER BY date
                """,
                (self.user_id, start_date.isoformat(), end_date.isoformat())
            )
            schedules = [dict(row) for row in cursor.fetchall()]
        
        if not schedules:
            return {
                'total_days': 0,
                'completed_days': 0,
                'avg_completion': 0.0,
                'total_topics_scheduled': 0,
                'total_topics_completed': 0
            }
        
        total_days = len(schedules)
        completed_days = sum(1 for s in schedules if s['completed'])
        avg_completion = sum(s['completion_percentage'] for s in schedules) / total_days
        
        total_scheduled = 0
        total_completed = 0
        for schedule in schedules:
            items = json.loads(schedule['planned_items'])
            total_scheduled += len(items)
            completed = int(len(items) * schedule['completion_percentage'] / 100)
            total_completed += completed
        
        return {
            'total_days': total_days,
            'completed_days': completed_days,
            'avg_completion': round(avg_completion, 1),
            'total_topics_scheduled': total_scheduled,
            'total_topics_completed': total_completed
        }
