"""
Grading System - Grade student answers with rule-based and LLM-based grading
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
import json
from src.llm.client import gemini_client
from src.llm.models import TaskType
from src.llm.prompts import PromptTemplates
from src.data.db import Database


class GradingEngine:
    """Grades quiz answers using appropriate methods"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def grade_answer(
        self,
        question: Dict,
        student_answer: str,
        use_partial_credit: bool = True
    ) -> Dict:
        """
        Grade a single answer
        
        Args:
            question: Question dictionary
            student_answer: Student's answer
            use_partial_credit: Whether to award partial credit
            
        Returns:
            Grading result with score, feedback, and is_correct
        """
        question_type = question.get('question_type', 'MCQ')
        
        if question_type == 'MCQ':
            return self._grade_mcq(question, student_answer)
        elif question_type == 'Numeric':
            return self._grade_numeric(question, student_answer, use_partial_credit)
        elif question_type == 'Descriptive':
            return self._grade_descriptive(question, student_answer)
        else:
            return {
                'score': 0,
                'max_score': question.get('marks', 4),
                'is_correct': False,
                'feedback': 'Unknown question type',
                'grading_method': 'error'
            }
    
    def _grade_mcq(self, question: Dict, student_answer: str) -> Dict:
        """Grade MCQ using rule-based comparison"""
        correct_answer = str(question.get('correct_answer', '')).strip().upper()
        student_ans = str(student_answer).strip().upper()
        
        is_correct = (student_ans == correct_answer)
        max_score = question.get('marks', 3)
        score = max_score if is_correct else 0
        
        feedback = ""
        if is_correct:
            feedback = "✅ Correct! Well done."
        else:
            feedback = f"❌ Incorrect. The correct answer is: {correct_answer}"
        
        return {
            'score': score,
            'max_score': max_score,
            'is_correct': is_correct,
            'feedback': feedback,
            'correct_answer': correct_answer,
            'grading_method': 'rule_based'
        }
    
    def _grade_numeric(
        self,
        question: Dict,
        student_answer: str,
        use_partial_credit: bool = True
    ) -> Dict:
        """Grade numeric answer with tolerance"""
        try:
            correct_answer = float(question.get('correct_answer', 0))
            student_ans = float(student_answer)
            
            # Calculate tolerance (0.1% of answer or 0.01, whichever is larger)
            tolerance = max(abs(correct_answer) * 0.001, 0.01)
            
            difference = abs(student_ans - correct_answer)
            is_correct = difference <= tolerance
            
            max_score = question.get('marks', 3)
            
            # Partial credit for close answers
            if is_correct:
                score = max_score
                feedback = f"✅ Correct! (Answer: {correct_answer})"
            elif use_partial_credit and difference <= tolerance * 5:
                # Within 0.5% - give 50% credit
                score = max_score * 0.5
                feedback = f"⚠️ Close! You got partial credit. Correct answer: {correct_answer}"
            else:
                score = 0
                feedback = f"❌ Incorrect. Correct answer: {correct_answer}"
            
            return {
                'score': score,
                'max_score': max_score,
                'is_correct': is_correct,
                'feedback': feedback,
                'correct_answer': correct_answer,
                'grading_method': 'rule_based_numeric'
            }
            
        except (ValueError, TypeError):
            return {
                'score': 0,
                'max_score': question.get('marks', 3),
                'is_correct': False,
                'feedback': '❌ Invalid numeric answer format',
                'correct_answer': question.get('correct_answer', ''),
                'grading_method': 'error'
            }
    
    def _grade_descriptive(self, question: Dict, student_answer: str) -> Dict:
        """Grade descriptive answer using LLM (Gemini Pro for accuracy)"""
        try:
            # Use Gemini Pro for complex grading
            result, was_cached = gemini_client.generate_json(
                task_type=TaskType.GRADING_DESCRIPTIVE,
                prompt_template=PromptTemplates.GRADING_DESCRIPTIVE,
                params={
                    'question': question.get('question_text', ''),
                    'correct_answer': question.get('solution', question.get('correct_answer', '')),
                    'student_answer': student_answer,
                    'max_marks': question.get('marks', 4),
                    'subject': question.get('subject', 'General')
                },
                max_tokens=4096,
                temperature=0.3  # Lower temperature for consistent grading
            )
            
            # Extract grading results
            score = float(result.get('score', 0))
            max_score = float(question.get('marks', 4))
            is_correct = score >= (max_score * 0.6)  # 60% threshold
            
            feedback = result.get('feedback', 'No feedback provided')
            strengths = result.get('strengths', [])
            improvements = result.get('improvements', [])
            
            # Build detailed feedback
            detailed_feedback = f"**Score: {score}/{max_score}**\n\n"
            detailed_feedback += f"{feedback}\n\n"
            
            if strengths:
                detailed_feedback += "**Strengths:**\n"
                for strength in strengths:
                    detailed_feedback += f"- {strength}\n"
                detailed_feedback += "\n"
            
            if improvements:
                detailed_feedback += "**Areas for Improvement:**\n"
                for improvement in improvements:
                    detailed_feedback += f"- {improvement}\n"
            
            return {
                'score': score,
                'max_score': max_score,
                'is_correct': is_correct,
                'feedback': detailed_feedback,
                'correct_answer': question.get('solution', question.get('correct_answer', '')),
                'grading_method': 'llm_based',
                'was_cached': was_cached
            }
            
        except Exception as e:
            print(f"Error in LLM grading: {e}")
            # Fallback to basic keyword matching
            return self._grade_descriptive_fallback(question, student_answer)
    
    def _grade_descriptive_fallback(self, question: Dict, student_answer: str) -> Dict:
        """Fallback grading using keyword matching"""
        correct_answer = question.get('solution', question.get('correct_answer', ''))
        
        # Extract keywords from correct answer (simple approach)
        keywords = re.findall(r'\b\w{4,}\b', correct_answer.lower())
        keywords = list(set(keywords))[:10]  # Top 10 unique keywords
        
        # Check how many keywords are in student answer
        student_lower = student_answer.lower()
        matches = sum(1 for kw in keywords if kw in student_lower)
        
        max_score = question.get('marks', 4)
        score = (matches / len(keywords)) * max_score if keywords else 0
        is_correct = score >= (max_score * 0.6)
        
        feedback = f"Keyword match score: {matches}/{len(keywords)} key concepts found.\n"
        feedback += "This is a basic automated assessment. Please review the solution for complete understanding."
        
        return {
            'score': round(score, 1),
            'max_score': max_score,
            'is_correct': is_correct,
            'feedback': feedback,
            'correct_answer': correct_answer,
            'grading_method': 'keyword_fallback'
        }
    
    def grade_quiz(
        self,
        quiz_id: int,
        answers: Dict[int, str],
        time_taken_minutes: int
    ) -> Dict:
        """
        Grade entire quiz
        
        Args:
            quiz_id: Quiz ID
            answers: Dictionary mapping question_id to student answer
            time_taken_minutes: Time taken to complete quiz
            
        Returns:
            Grading results with overall score and question-wise breakdown
        """
        # Get quiz with questions
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_id, total_questions
                FROM quizzes
                WHERE id = ?
            """, (quiz_id,))
            
            quiz = cursor.fetchone()
            if not quiz:
                raise ValueError(f"Quiz {quiz_id} not found")
            
            quiz = dict(quiz)
            
            # Get questions
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
        
        # Grade each question
        results = []
        total_score = 0
        max_total_score = 0
        correct_count = 0
        
        for question in questions:
            question_id = question['id']
            student_answer = answers.get(question_id, '')
            
            if not student_answer:
                # Unanswered question
                result = {
                    'question_id': question_id,
                    'topic_id': question.get('topic_id'),
                    'student_answer': '',
                    'score': 0,
                    'max_score': question.get('marks', 4),
                    'is_correct': False,
                    'feedback': '❌ Not answered',
                    'grading_method': 'not_answered'
                }
            else:
                result = self.grade_answer(question, student_answer)
                result['question_id'] = question_id
                result['topic_id'] = question.get('topic_id')
                result['student_answer'] = student_answer
            
            results.append(result)
            total_score += result['score']
            max_total_score += result['max_score']
            if result['is_correct']:
                correct_count += 1
        
        # Calculate percentage
        percentage = (total_score / max_total_score * 100) if max_total_score > 0 else 0
        
        # Save quiz attempt
        attempt_id = self._save_quiz_attempt(
            quiz_id=quiz_id,
            user_id=quiz['user_id'],
            total_score=total_score,
            max_score=max_total_score,
            time_taken_minutes=time_taken_minutes,
            results=results
        )
        
        return {
            'attempt_id': attempt_id,
            'quiz_id': quiz_id,
            'total_score': round(total_score, 1),
            'max_score': max_total_score,
            'percentage': round(percentage, 1),
            'correct_count': correct_count,
            'total_questions': len(questions),
            'time_taken_minutes': time_taken_minutes,
            'results': results
        }
    
    def _save_quiz_attempt(
        self,
        quiz_id: int,
        user_id: int,
        total_score: float,
        max_score: float,
        time_taken_minutes: int,
        results: List[Dict]
    ) -> int:
        """Save quiz attempt to database"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert attempt
            cursor.execute("""
                INSERT INTO quiz_attempts
                (quiz_id, user_id, score, max_score, time_taken_minutes,
                 completed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                quiz_id,
                user_id,
                total_score,
                max_score,
                time_taken_minutes,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            attempt_id = cursor.lastrowid
            
            # Calculate percentage and update quiz_attempts
            percentage = (total_score / max_score * 100) if max_score > 0 else 0
            cursor.execute("""
                UPDATE quiz_attempts
                SET percentage = ?
                WHERE id = ?
            """, (percentage, attempt_id))
            
            # Save individual question attempts to attempts table
            for result in results:
                cursor.execute("""
                    INSERT INTO attempts
                    (user_id, quiz_id, topic_id, question_id, 
                     user_answer, correctness, score, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    quiz_id,
                    result['topic_id'],
                    result['question_id'],
                    result['student_answer'],
                    1 if result['is_correct'] else 0,
                    result['score'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            conn.commit()
            
        return attempt_id
