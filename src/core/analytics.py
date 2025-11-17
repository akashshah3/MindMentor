"""
Analytics Engine - Generate insights and statistics from student data
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from src.data.db import Database


class AnalyticsEngine:
    """Generate learning analytics and insights"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_learning_overview(self, user_id: int) -> Dict:
        """
        Get comprehensive learning overview
        
        Returns:
            Dictionary with overview statistics
        """
        profiles = self.db.get_all_student_profiles(user_id)
        
        if not profiles:
            return {
                'topics_started': 0,
                'topics_mastered': 0,
                'average_mastery': 0,
                'total_attempts': 0,
                'total_correct': 0,
                'overall_accuracy': 0,
                'strong_topics_count': 0,
                'weak_topics_count': 0,
                'average_topics_count': 0
            }
        
        # Calculate statistics
        topics_started = len(profiles)
        topics_mastered = len([p for p in profiles if p.get('strength_level') == 'MASTERED'])
        avg_mastery = sum(p['mastery_score'] for p in profiles) / len(profiles)
        total_attempts = sum(p['total_attempts'] for p in profiles)
        total_correct = sum(p['correct_attempts'] for p in profiles)
        overall_accuracy = (total_correct / total_attempts * 100) if total_attempts > 0 else 0
        
        # Count by strength level
        strong_count = len([p for p in profiles if p.get('strength_level') in ['STRONG', 'MASTERED']])
        weak_count = len([p for p in profiles if p.get('strength_level') == 'WEAK'])
        average_count = len([p for p in profiles if p.get('strength_level') == 'AVERAGE'])
        
        return {
            'topics_started': topics_started,
            'topics_mastered': topics_mastered,
            'average_mastery': avg_mastery,
            'total_attempts': total_attempts,
            'total_correct': total_correct,
            'overall_accuracy': overall_accuracy,
            'strong_topics_count': strong_count,
            'weak_topics_count': weak_count,
            'average_topics_count': average_count
        }
    
    def get_subject_breakdown(self, user_id: int) -> Dict[str, Dict]:
        """
        Get statistics broken down by subject
        
        Returns:
            Dictionary with subject-wise statistics
        """
        profiles = self.db.get_all_student_profiles(user_id)
        
        subjects = {}
        
        for profile in profiles:
            subject = profile.get('subject', 'Unknown')
            
            if subject not in subjects:
                subjects[subject] = {
                    'topics_started': 0,
                    'topics_mastered': 0,
                    'total_mastery': 0,
                    'total_attempts': 0,
                    'correct_attempts': 0
                }
            
            subjects[subject]['topics_started'] += 1
            if profile.get('strength_level') == 'MASTERED':
                subjects[subject]['topics_mastered'] += 1
            subjects[subject]['total_mastery'] += profile['mastery_score']
            subjects[subject]['total_attempts'] += profile['total_attempts']
            subjects[subject]['correct_attempts'] += profile['correct_attempts']
        
        # Calculate averages
        for subject in subjects:
            data = subjects[subject]
            if data['topics_started'] > 0:
                data['average_mastery'] = data['total_mastery'] / data['topics_started']
            else:
                data['average_mastery'] = 0
            
            if data['total_attempts'] > 0:
                data['accuracy'] = data['correct_attempts'] / data['total_attempts'] * 100
            else:
                data['accuracy'] = 0
        
        return subjects
    
    def get_weak_topics(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get topics that need attention"""
        profiles = self.db.get_all_student_profiles(user_id)
        
        # Sort by mastery score (ascending) and filter weak topics
        weak = [p for p in profiles if p['mastery_score'] < 0.6]
        weak.sort(key=lambda x: x['mastery_score'])
        
        return weak[:limit]
    
    def get_strong_topics(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get topics where student is strong"""
        profiles = self.db.get_all_student_profiles(user_id)
        
        # Sort by mastery score (descending) and filter strong topics
        strong = [p for p in profiles if p['mastery_score'] >= 0.6]
        strong.sort(key=lambda x: x['mastery_score'], reverse=True)
        
        return strong[:limit]
    
    def get_recent_activity(self, user_id: int, days: int = 7) -> List[Dict]:
        """
        Get recent learning activity
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            List of recent activities
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Get recent chat sessions
            cursor.execute("""
                SELECT 
                    ch.timestamp,
                    t.topic_name,
                    t.subject,
                    'Learning Session' as activity_type
                FROM chat_history ch
                JOIN topics t ON ch.topic_id = t.id
                WHERE ch.user_id = ?
                    AND ch.timestamp >= ?
                GROUP BY DATE(ch.timestamp), ch.topic_id
                ORDER BY ch.timestamp DESC
                LIMIT 20
            """, (user_id, cutoff_date))
            
            activities = []
            for row in cursor.fetchall():
                activities.append(dict(row))
            
            return activities
    
    def get_study_streak(self, user_id: int) -> Dict:
        """
        Calculate study streak
        
        Returns:
            Dictionary with current streak and longest streak
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all unique study dates from chat history
            cursor.execute("""
                SELECT DISTINCT DATE(timestamp) as study_date
                FROM chat_history
                WHERE user_id = ?
                ORDER BY study_date DESC
            """, (user_id,))
            
            dates = [row['study_date'] for row in cursor.fetchall()]
            
            if not dates:
                return {'current_streak': 0, 'longest_streak': 0, 'last_study_date': None}
            
            # Calculate current streak
            current_streak = 0
            today = datetime.now().date()
            
            for i, date_str in enumerate(dates):
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                expected_date = today - timedelta(days=i)
                
                if date == expected_date:
                    current_streak += 1
                else:
                    break
            
            # Calculate longest streak
            longest_streak = 1
            current_run = 1
            
            for i in range(1, len(dates)):
                prev_date = datetime.strptime(dates[i-1], '%Y-%m-%d').date()
                curr_date = datetime.strptime(dates[i], '%Y-%m-%d').date()
                
                if (prev_date - curr_date).days == 1:
                    current_run += 1
                    longest_streak = max(longest_streak, current_run)
                else:
                    current_run = 1
            
            return {
                'current_streak': current_streak,
                'longest_streak': longest_streak,
                'last_study_date': dates[0] if dates else None
            }
    
    def get_mastery_distribution(self, user_id: int) -> Dict[str, int]:
        """
        Get distribution of topics by mastery level
        
        Returns:
            Dictionary with counts by mastery range
        """
        profiles = self.db.get_all_student_profiles(user_id)
        
        distribution = {
            'Beginner (0-30%)': 0,
            'Learning (30-60%)': 0,
            'Proficient (60-80%)': 0,
            'Mastered (80-100%)': 0
        }
        
        for profile in profiles:
            mastery = profile['mastery_score'] * 100
            
            if mastery < 30:
                distribution['Beginner (0-30%)'] += 1
            elif mastery < 60:
                distribution['Learning (30-60%)'] += 1
            elif mastery < 80:
                distribution['Proficient (60-80%)'] += 1
            else:
                distribution['Mastered (80-100%)'] += 1
        
        return distribution
    
    def get_topic_recommendations(self, user_id: int, limit: int = 5) -> List[Dict]:
        """
        Recommend topics to study next based on:
        - JEE importance (exam_weight)
        - Current weakness (low mastery)
        - Not yet started topics
        
        Returns:
            List of recommended topics with reasons
        """
        # Get all topics
        all_topics = self.db.get_all_topics()
        
        # Get user's profiles
        profiles = self.db.get_all_student_profiles(user_id)
        studied_topic_ids = {p['topic_id'] for p in profiles}
        
        # Get weak topics (already started but need work)
        weak_topics = []
        for profile in profiles:
            if profile['mastery_score'] < 0.5:  # Weak threshold
                topic = self.db.get_topic_by_id(profile['topic_id'])
                if topic:
                    weak_topics.append({
                        'topic': topic,
                        'reason': f"Low mastery ({profile['mastery_score']*100:.0f}%)",
                        'priority': profile.get('exam_weight', 1.0) * (1 - profile['mastery_score'])
                    })
        
        # Get high-priority unstudied topics
        unstudied = []
        for topic in all_topics:
            if topic['id'] not in studied_topic_ids:
                priority = topic.get('exam_weight', 1.0)
                unstudied.append({
                    'topic': topic,
                    'reason': "Not started yet - High JEE importance",
                    'priority': priority
                })
        
        # Combine and sort by priority
        recommendations = weak_topics + unstudied
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        return recommendations[:limit]
