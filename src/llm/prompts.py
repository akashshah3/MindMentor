"""
Prompt templates for LLM interactions
Organized by task type with clear, structured prompts
"""

from typing import Dict, Any


class PromptTemplates:
    """Collection of prompt templates for different tasks"""
    
    # ===== LESSON GENERATION =====
    
    LESSON_GENERATION = """You are an expert JEE tutor teaching {subject} to a student.

Topic: {topic_name}
Chapter: {chapter_name}
Difficulty Level: {difficulty}
Student Level: {student_level}

Provide a comprehensive lesson on this topic. Include:
1. Clear explanation of core concepts
2. Important formulas or principles
3. 2-3 practical examples
4. Common mistakes to avoid
5. Tips for JEE exam

Format your response as JSON with this structure:
{{
    "explanation": "detailed explanation here",
    "key_points": ["point 1", "point 2", ...],
    "formulas": ["formula 1", "formula 2", ...],
    "examples": [
        {{"problem": "...", "solution": "..."}},
        ...
    ],
    "common_mistakes": ["mistake 1", "mistake 2", ...],
    "jee_tips": ["tip 1", "tip 2", ...]
}}

Keep the explanation clear, concise, and suitable for {student_level} level students."""
    
    # ===== CONCEPT EXPLANATION =====
    
    CONCEPT_EXPLANATION = """You are a JEE tutor explaining a concept to a student.

Subject: {subject}
Topic: {topic_name}
Concept to explain: {concept}
Student's current understanding: {student_context}

Provide a clear, step-by-step explanation of this concept. 
Adapt your explanation based on the student's current understanding level.
Use analogies and examples relevant to JEE preparation.

Keep the response focused and under 300 words."""
    
    # ===== QUESTION GENERATION =====
    
    QUESTION_GENERATION = """You are creating JEE practice questions.

Subject: {subject}
Topic: {topic_name}
Question Type: {question_type}
Difficulty: {difficulty}
Number of questions: {count}

Generate {count} {question_type} questions for JEE {exam_level} level.

For MCQ questions, provide:
- Question text
- 4 options (A, B, C, D)
- Correct answer
- Brief explanation

For NUMERIC questions, provide:
- Question text
- Correct numerical answer
- Units (if applicable)
- Brief explanation

For DESCRIPTIVE questions, provide:
- Question text
- Key points that should be in the answer
- Sample answer
- Marking scheme

IMPORTANT: 
- For mathematical expressions, use simple text notation or Unicode symbols instead of LaTeX
- Avoid backslashes in text (they break JSON parsing)
- Use ^ for superscripts (e.g., x^2 instead of x²)
- Use / for fractions (e.g., 1/2 instead of ½)

Format as valid JSON (ensure all strings are properly escaped):
{{
    "questions": [
        {{
            "question_text": "...",
            "type": "{question_type}",
            "options": ["A", "B", "C", "D"],  // for MCQ only
            "correct_answer": "...",
            "explanation": "...",
            "difficulty": "{difficulty}",
            "marks": 4
        }},
        ...
    ]
}}"""
    
    # ===== HINT GENERATION =====
    
    HINT_GENERATION = """A student is stuck on this JEE question:

Question: {question_text}
Subject: {subject}
Topic: {topic_name}

Provide a helpful hint that guides them toward the solution without giving away the answer.
The hint should:
1. Identify the key concept needed
2. Suggest the first step or approach
3. Be encouraging

Keep it brief (2-3 sentences)."""
    
    # ===== ANSWER GRADING (DESCRIPTIVE) =====
    
    GRADING_DESCRIPTIVE = """You are grading a descriptive answer for a JEE question.

Question: {question_text}
Total Marks: {total_marks}
Key Points Expected: {key_points}

Student's Answer:
{student_answer}

Evaluate the student's answer and provide:
1. Points awarded (out of {total_marks})
2. What was correct
3. What was missing or incorrect
4. Specific feedback for improvement

Format as JSON:
{{
    "marks_awarded": <number>,
    "total_marks": {total_marks},
    "correct_points": ["point 1", "point 2", ...],
    "missing_points": ["point 1", "point 2", ...],
    "errors": ["error 1", "error 2", ...],
    "feedback": "constructive feedback here"
}}

Be fair but strict, as JEE grading requires precision."""
    
    # ===== SIMPLE EXPLANATION =====
    
    SIMPLE_EXPLANATION = """Explain this {subject} term in simple words for a JEE student:

Term: {term}
Context: {context}

Provide a brief, clear definition in 2-3 sentences.
Use simple language and include a quick example if helpful."""
    
    # ===== EXAMPLE GENERATION =====
    
    EXAMPLE_GENERATION = """Create a solved example problem for JEE students.

Subject: {subject}
Topic: {topic_name}
Difficulty: {difficulty}
Concept to demonstrate: {concept}

Provide:
1. A clear problem statement
2. Step-by-step solution
3. Final answer with units

Make it relevant to JEE exam patterns.

Format as JSON:
{{
    "problem": "problem statement here",
    "solution_steps": ["step 1", "step 2", ...],
    "final_answer": "answer with units",
    "key_concept": "main concept used"
}}"""
    
    # ===== CHAT/Q&A =====
    
    CHAT_QA = """You are a helpful JEE tutor having a conversation with a student.

Subject Context: {subject}
Topic Context: {topic_name}

Previous conversation:
{conversation_history}

Student's question: {student_question}

Provide a helpful, accurate answer. If the question is unclear, ask for clarification.
Keep your response conversational but informative.
If the question is off-topic, gently redirect to JEE preparation topics."""
    
    
    @classmethod
    def get_template(cls, template_name: str) -> str:
        """
        Get a prompt template by name
        
        Args:
            template_name: Name of the template
            
        Returns:
            Template string
        """
        return getattr(cls, template_name.upper(), "")
    
    @classmethod
    def fill_template(cls, template_name: str, **kwargs) -> str:
        """
        Get and fill a prompt template
        
        Args:
            template_name: Name of the template
            **kwargs: Parameters to fill into template
            
        Returns:
            Filled template string
        """
        template = cls.get_template(template_name)
        return template.format(**kwargs)


# Convenience functions
def get_lesson_prompt(**kwargs) -> str:
    """Get filled lesson generation prompt"""
    return PromptTemplates.fill_template("lesson_generation", **kwargs)


def get_question_prompt(**kwargs) -> str:
    """Get filled question generation prompt"""
    return PromptTemplates.fill_template("question_generation", **kwargs)


def get_grading_prompt(**kwargs) -> str:
    """Get filled grading prompt"""
    return PromptTemplates.fill_template("grading_descriptive", **kwargs)


def get_hint_prompt(**kwargs) -> str:
    """Get filled hint generation prompt"""
    return PromptTemplates.fill_template("hint_generation", **kwargs)


def get_explanation_prompt(**kwargs) -> str:
    """Get filled concept explanation prompt"""
    return PromptTemplates.fill_template("concept_explanation", **kwargs)


def get_chat_prompt(**kwargs) -> str:
    """Get filled chat/Q&A prompt"""
    return PromptTemplates.fill_template("chat_qa", **kwargs)
