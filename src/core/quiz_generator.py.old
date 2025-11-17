"""
Quiz Generator - Create adaptive quizzes based on topics and difficulty
"""

from typing import Dict, List, Optional
from datetime import datetime
import json
from src.llm.client import gemini_client
from src.llm.models import TaskType
from src.llm.prompts import PromptTemplates
from src.data.db import Database


class QuizGenerator:
    """Generates adaptive quizzes for JEE preparation"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def generate_quiz(
        self,
        user_id: int,
        topic_ids: List[int],
        question_count: int = 10,
        difficulty: str = "Medium",
        question_types: Optional[List[str]] = None,
        force_refresh: bool = False
    ) -> Dict:
        """
        Generate a quiz with multiple questions
        
        Args:
            user_id: User ID
            topic_ids: List of topic IDs to generate questions from
            question_count: Number of questions to generate
            difficulty: Overall difficulty level (Easy, Medium, Hard)
            question_types: List of question types to include (MCQ, Numeric, Descriptive)
            force_refresh: If True, bypass cache and generate fresh questions
            
        Returns:
            Quiz data dictionary with questions and metadata
        """
        if question_types is None:
            question_types = ['MCQ', 'MCQ', 'MCQ', 'Numeric', 'Descriptive']  # Default mix
        
        # Get topics
        topics = []
        for topic_id in topic_ids:
            topic = self.db.get_topic_by_id(topic_id)
            if topic:
                topics.append(topic)
        
        if not topics:
            raise ValueError("No valid topics found")
        
        # Generate questions for each topic
        all_questions = []
        questions_per_topic = max(1, question_count // len(topics))
        
        for topic in topics:
            # Determine question types for this topic
            types_for_topic = question_types[:questions_per_topic]
            
            questions = self._generate_questions_for_topic(
                topic=topic,
                count=questions_per_topic,
                difficulty=difficulty,
                question_types=types_for_topic,
                force_refresh=force_refresh
            )
            
            all_questions.extend(questions)
        
        # Trim to exact count
        all_questions = all_questions[:question_count]
        
        # Create quiz metadata
        quiz_data = {
            'user_id': user_id,
            'topic_ids': topic_ids,
            'difficulty': difficulty,
            'total_questions': len(all_questions),
            'questions': all_questions,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'time_limit_minutes': self._calculate_time_limit(all_questions)
        }
        
        return quiz_data
    
    def _generate_questions_for_topic(
        self,
        topic: Dict,
        count: int,
        difficulty: str,
        question_types: List[str],
        force_refresh: bool = False
    ) -> List[Dict]:
        """Generate questions for a specific topic"""
        
        # Build question type distribution
        type_counts = {}
        for q_type in question_types:
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
        
        all_questions = []
        
        for q_type, type_count in type_counts.items():
            questions = self._generate_questions_by_type(
                topic=topic,
                question_type=q_type,
                count=type_count,
                difficulty=difficulty,
                force_refresh=force_refresh
            )
            all_questions.extend(questions)
        
        return all_questions
    
    def _generate_questions_by_type(
        self,
        topic: Dict,
        question_type: str,
        count: int,
        difficulty: str,
        force_refresh: bool = False
    ) -> List[Dict]:
        """Generate questions of a specific type using LLM"""
        
        try:
            # Generate questions using LLM with caching
            response, was_cached = gemini_client.generate_json(
                task_type=TaskType.QUESTION_GENERATION,
                prompt_template=PromptTemplates.QUESTION_GENERATION,
                params={
                    'subject': topic.get('subject', ''),
                    'topic_name': topic.get('topic_name', ''),
                    'question_type': question_type,
                    'difficulty': difficulty,
                    'count': count,
                    'exam_level': 'Main and Advanced'
                },
                max_tokens=8192,  # Questions can be lengthy
                temperature=0.8,  # Higher temperature for variety
                force_refresh=force_refresh  # Pass force_refresh to bypass cache
            )
            
            # Extract questions from response
            if 'questions' in response:
                questions = response['questions']
            else:
                # Response might be the questions array directly
                questions = response if isinstance(response, list) else []
            
            # Add metadata to each question
            for i, question in enumerate(questions):
                question['topic_id'] = topic.get('id')
                question['topic_name'] = topic.get('topic_name', '')
                question['subject'] = topic.get('subject', '')
                question['question_type'] = question_type
                question['difficulty'] = difficulty
                question['question_number'] = i + 1
            
            return questions[:count]
            
        except Exception as e:
            print(f"Error generating {question_type} questions: {e}")
            return []
    
    def _calculate_time_limit(self, questions: List[Dict]) -> int:
        """Calculate time limit based on question types"""
        total_minutes = 0
        
        for question in questions:
            q_type = question.get('question_type', 'MCQ')
            
            if q_type == 'MCQ':
                total_minutes += 2  # 2 minutes per MCQ
            elif q_type == 'Numeric':
                total_minutes += 3  # 3 minutes per numeric
            elif q_type == 'Descriptive':
                total_minutes += 5  # 5 minutes per descriptive
        
        return max(10, total_minutes)  # Minimum 10 minutes
    
    def save_quiz(self, quiz_data: Dict) -> int:
        """
        Save quiz to database
        
        Args:
            quiz_data: Quiz dictionary
            
        Returns:
            Quiz ID
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert quiz
            cursor.execute("""
                INSERT INTO quizzes
                (user_id, quiz_type, topics, 
                 total_questions, time_limit_minutes, started_at)
                VALUES (?, 'TOPIC', ?, ?, ?, ?)
            """, (
                quiz_data['user_id'],
                json.dumps(quiz_data['topic_ids']),
                quiz_data['total_questions'],
                quiz_data['time_limit_minutes'],
                quiz_data['created_at']
            ))
            
            quiz_id = cursor.lastrowid
            
            # Save questions to quiz_questions table
            for i, question in enumerate(quiz_data['questions'], 1):
                cursor.execute("""
                    INSERT INTO quiz_questions
                    (quiz_id, question_number, topic_id, question_type, 
                     question_text, options, correct_answer, solution, marks, difficulty)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    quiz_id,
                    i,
                    question['topic_id'],
                    question['question_type'],
                    question.get('question', question.get('question_text', '')),
                    json.dumps(question.get('options', [])),
                    question.get('correct_answer', question.get('answer', '')),
                    question.get('solution', question.get('explanation', '')),
                    question.get('marks', 4 if question['question_type'] == 'Descriptive' else 3),
                    question.get('difficulty', quiz_data['difficulty'])
                ))
            
            conn.commit()
            
        return quiz_id
    
    def get_quiz(self, quiz_id: int) -> Optional[Dict]:
        """Get quiz by ID with all questions"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get quiz metadata
            cursor.execute("""
                SELECT id, user_id, quiz_type, topics,
                       total_questions, time_limit_minutes, started_at
                FROM quizzes
                WHERE id = ?
            """, (quiz_id,))
            
            quiz_row = cursor.fetchone()
            if not quiz_row:
                return None
            
            quiz = dict(quiz_row)
            quiz['topic_ids'] = json.loads(quiz['topics'])
            
            # Get questions from quiz_questions table
            cursor.execute("""
                SELECT id, question_number, topic_id, question_type,
                       question_text, options, correct_answer, solution, marks, difficulty
                FROM quiz_questions
                WHERE quiz_id = ?
                ORDER BY question_number
            """, (quiz_id,))
            
            questions = []
            for row in cursor.fetchall():
                q = dict(row)
                q['question'] = q['question_text']
                q['options'] = json.loads(q['options']) if q['options'] else []
                questions.append(q)
            
            quiz['questions'] = questions
            
        return quiz
    
    def get_adaptive_difficulty(self, user_id: int, topic_id: int) -> str:
        """
        Determine adaptive difficulty based on student performance
        
        Args:
            user_id: User ID
            topic_id: Topic ID
            
        Returns:
            Difficulty level (Easy, Medium, Hard)
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get student profile for this topic
            cursor.execute("""
                SELECT mastery_score, accuracy
                FROM student_profiles
                WHERE user_id = ? AND topic_id = ?
            """, (user_id, topic_id))
            
            profile = cursor.fetchone()
            
            if not profile:
                return "Medium"  # Default for new topics
            
            mastery = profile['mastery_score']
            accuracy = profile.get('accuracy', 0.5)
            
            # Adaptive difficulty logic
            if mastery >= 0.8 and accuracy >= 0.8:
                return "Hard"
            elif mastery >= 0.5 and accuracy >= 0.6:
                return "Medium"
            else:
                return "Easy"
