"""
Simple Quiz System - Clean implementation from scratch
Generates MCQ questions and handles grading
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import json

from src.data.db import Database
from src.llm.client import GeminiClient
from src.llm.models import TaskType


@dataclass
class Question:
    """Simple question structure"""
    id: int
    topic_id: int
    topic_name: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str  # 'A', 'B', 'C', or 'D'
    explanation: str


@dataclass
class QuizResult:
    """Quiz results"""
    total_questions: int
    correct_answers: int
    score_percentage: float
    question_results: List[Dict]  # List of {question_id, user_answer, correct_answer, is_correct}


class SimpleQuizGenerator:
    """Generate simple MCQ quizzes"""
    
    def __init__(self, db: Database):
        self.db = db
        self.llm = GeminiClient()
    
    def generate_quiz(
        self,
        user_id: int,
        topic_ids: List[int],
        num_questions: int = 5,
        difficulty: str = "Medium"
    ) -> List[Question]:
        """
        Generate MCQ quiz questions
        
        Args:
            user_id: User ID
            topic_ids: List of topic IDs to include
            num_questions: Number of questions to generate
            difficulty: Easy, Medium, or Hard
        
        Returns:
            List of Question objects
        """
        # Get topic information
        topics = []
        for topic_id in topic_ids:
            topic = self.db.get_topic_by_id(topic_id)
            if topic:
                topics.append(topic)
        
        if not topics:
            return []
        
        # Create simple, reliable prompt
        topic_names = [t['topic_name'] for t in topics]
        prompt_template = """Generate {num_questions} multiple choice questions for JEE preparation.

Topics: {topics}
Difficulty: {difficulty}

For each question, provide:
1. A clear question
2. Four options (A, B, C, D)
3. The correct answer (just the letter: A, B, C, or D)
4. A brief explanation

Format your response as a JSON array with this exact structure:
[
  {{
    "question": "What is the formula for kinetic energy?",
    "option_a": "KE = 1/2 * m * v",
    "option_b": "KE = 1/2 * m * v^2",
    "option_c": "KE = m * v^2",
    "option_d": "KE = m * g * h",
    "correct_answer": "B",
    "explanation": "Kinetic energy is half of mass times velocity squared."
  }}
]

IMPORTANT:
- Return ONLY the JSON array, no other text
- Use simple text, NO LaTeX symbols or special formatting
- For math: use ^ for power (x^2), * for multiply, / for divide
- Correct answer must be exactly one letter: A, B, C, or D
- Generate exactly {num_questions} questions"""

        # Generate questions with LLM
        try:
            response_data, was_cached = self.llm.generate_json(
                task_type=TaskType.QUESTION_GENERATION,
                prompt_template=prompt_template,
                params={
                    'num_questions': num_questions,
                    'topics': ', '.join(topic_names),
                    'difficulty': difficulty
                },
                temperature=0.7,
                max_tokens=4096
            )
            
            # Handle response - should be a list or dict with questions
            if isinstance(response_data, list):
                questions_data = response_data
            elif isinstance(response_data, dict) and 'questions' in response_data:
                questions_data = response_data['questions']
            else:
                print(f"Unexpected response format: {type(response_data)}")
                return []
            
            # Convert to Question objects
            questions = []
            for idx, q_data in enumerate(questions_data[:num_questions]):  # Limit to requested number
                # Assign to first topic (simple approach)
                topic = topics[idx % len(topics)]
                
                question = Question(
                    id=idx + 1,
                    topic_id=topic['id'],
                    topic_name=topic['topic_name'],
                    question_text=q_data['question'],
                    option_a=q_data['option_a'],
                    option_b=q_data['option_b'],
                    option_c=q_data['option_c'],
                    option_d=q_data['option_d'],
                    correct_answer=q_data['correct_answer'].upper(),
                    explanation=q_data.get('explanation', 'No explanation provided')
                )
                questions.append(question)
            
            return questions
            
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            return []
        except Exception as e:
            print(f"Error generating quiz: {e}")
            return []
    
    def grade_quiz(
        self,
        questions: List[Question],
        user_answers: Dict[int, str]  # {question_id: answer_letter}
    ) -> QuizResult:
        """
        Grade the quiz
        
        Args:
            questions: List of questions
            user_answers: Dictionary mapping question ID to answer letter
        
        Returns:
            QuizResult object
        """
        correct_count = 0
        question_results = []
        
        for question in questions:
            user_answer = user_answers.get(question.id, '')
            is_correct = (user_answer.upper() == question.correct_answer.upper())
            
            if is_correct:
                correct_count += 1
            
            question_results.append({
                'question_id': question.id,
                'question_text': question.question_text,
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'is_correct': is_correct,
                'explanation': question.explanation,
                'option_a': question.option_a,
                'option_b': question.option_b,
                'option_c': question.option_c,
                'option_d': question.option_d
            })
        
        total = len(questions)
        percentage = (correct_count / total * 100) if total > 0 else 0
        
        return QuizResult(
            total_questions=total,
            correct_answers=correct_count,
            score_percentage=round(percentage, 1),
            question_results=question_results
        )
    
    def save_quiz_attempt(
        self,
        user_id: int,
        topic_ids: List[int],
        result: QuizResult,
        time_taken_minutes: int
    ):
        """Save quiz attempt to database"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Save to attempts table for each question
            for qr in result.question_results:
                cursor.execute(
                    """
                    INSERT INTO attempts (
                        user_id, topic_id, question_id, user_answer,
                        correctness, score, time_taken_seconds, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        topic_ids[0] if topic_ids else None,  # Use first topic
                        qr['question_id'],
                        qr['user_answer'],
                        1 if qr['is_correct'] else 0,
                        1.0 if qr['is_correct'] else 0.0,
                        time_taken_minutes * 60 / result.total_questions,
                        datetime.now().isoformat()
                    )
                )
            
            # Update student profiles
            for topic_id in topic_ids:
                # Get current profile
                profile = self.db.get_student_profile(user_id, topic_id)
                
                if profile:
                    # Update existing
                    old_attempts = profile['total_attempts'] or 0
                    old_correct = profile['correct_attempts'] or 0
                    
                    new_attempts = old_attempts + result.total_questions
                    new_correct = old_correct + result.correct_answers
                    new_accuracy = new_correct / new_attempts if new_attempts > 0 else 0
                    new_mastery = min(new_accuracy * 1.2, 1.0)  # Boost accuracy slightly for mastery
                    
                    cursor.execute(
                        """
                        UPDATE student_profiles
                        SET total_attempts = ?,
                            correct_attempts = ?,
                            accuracy = ?,
                            mastery_score = ?,
                            last_attempt_date = ?,
                            updated_at = ?
                        WHERE user_id = ? AND topic_id = ?
                        """,
                        (
                            new_attempts,
                            new_correct,
                            new_accuracy,
                            new_mastery,
                            datetime.now().date().isoformat(),
                            datetime.now().isoformat(),
                            user_id,
                            topic_id
                        )
                    )
                else:
                    # Create new profile
                    accuracy = result.correct_answers / result.total_questions
                    mastery = min(accuracy * 1.2, 1.0)
                    
                    cursor.execute(
                        """
                        INSERT INTO student_profiles (
                            user_id, topic_id, mastery_score, last_attempt_date,
                            total_attempts, correct_attempts, accuracy,
                            updated_at, next_review_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            user_id,
                            topic_id,
                            mastery,
                            datetime.now().date().isoformat(),
                            result.total_questions,
                            result.correct_answers,
                            accuracy,
                            datetime.now().isoformat(),
                            datetime.now().date().isoformat()
                        )
                    )
            
            conn.commit()
