"""
Model selection logic for Gemini API
Chooses the appropriate model based on task complexity to minimize API costs
"""

from enum import Enum
from typing import Dict


class TaskType(Enum):
    """Types of tasks that require LLM"""
    # Complex tasks - Use Gemini 2.5 Pro
    GRADING_DESCRIPTIVE = "grading_descriptive"
    COMPLEX_QUESTION_GEN = "complex_question_gen"
    DETAILED_EXPLANATION = "detailed_explanation"
    
    # Standard tasks - Use Gemini 2.5 Flash
    LESSON_GENERATION = "lesson_generation"
    QUESTION_GENERATION = "question_generation"
    CONCEPT_EXPLANATION = "concept_explanation"
    EXAMPLE_GENERATION = "example_generation"
    
    # Simple tasks - Use Gemini 2.5 Flash Lite
    HINT_GENERATION = "hint_generation"
    SIMPLE_EXPLANATION = "simple_explanation"
    DEFINITION = "definition"
    QUICK_ANSWER = "quick_answer"


class ModelSelector:
    """Selects the appropriate Gemini model based on task requirements."""
    
    # Model configurations
    MODELS = {
        "pro": "gemini-2.5-pro",  # For complex tasks (grading, analysis)
        "flash": "gemini-2.5-flash",  # For standard tasks (lessons, questions)
        "flash_lite": "gemini-2.5-flash-lite",  # For simple tasks (hints, explanations)
    }
    
    # Task type to model mapping
    TASK_TO_MODEL = {
        # Pro tasks (most expensive, use sparingly)
        TaskType.GRADING_DESCRIPTIVE: "pro",
        TaskType.COMPLEX_QUESTION_GEN: "pro",
        TaskType.DETAILED_EXPLANATION: "pro",
        
        # Flash tasks (balanced, default choice)
        TaskType.LESSON_GENERATION: "flash",
        TaskType.QUESTION_GENERATION: "flash",
        TaskType.CONCEPT_EXPLANATION: "flash",
        TaskType.EXAMPLE_GENERATION: "flash",
        
        # Flash Lite tasks (cheapest, use when possible)
        TaskType.HINT_GENERATION: "flash_lite",
        TaskType.SIMPLE_EXPLANATION: "flash_lite",
        TaskType.DEFINITION: "flash_lite",
        TaskType.QUICK_ANSWER: "flash_lite",
    }
    
    @classmethod
    def get_model_for_task(cls, task_type: TaskType) -> str:
        """
        Get the appropriate model name for a task type
        
        Args:
            task_type: Type of task to perform
            
        Returns:
            Model name string
        """
        model_tier = cls.TASK_TO_MODEL.get(task_type, "flash")
        return cls.MODELS[model_tier]
    
    @classmethod
    def get_model_tier(cls, task_type: TaskType) -> str:
        """
        Get the model tier (pro/flash/flash_lite) for a task
        
        Args:
            task_type: Type of task to perform
            
        Returns:
            Model tier string
        """
        return cls.TASK_TO_MODEL.get(task_type, "flash")
    
    @classmethod
    def estimate_cost_tier(cls, task_type: TaskType) -> str:
        """
        Get relative cost tier for a task
        
        Args:
            task_type: Type of task to perform
            
        Returns:
            Cost tier: "high", "medium", or "low"
        """
        tier = cls.get_model_tier(task_type)
        
        if tier == "pro":
            return "high"
        elif tier == "flash":
            return "medium"
        else:
            return "low"
    
    @classmethod
    def get_all_models(cls) -> Dict[str, str]:
        """Get all available models"""
        return cls.MODELS.copy()
    
    @classmethod
    def is_expensive_task(cls, task_type: TaskType) -> bool:
        """
        Check if a task uses the expensive Pro model
        
        Args:
            task_type: Type of task to perform
            
        Returns:
            True if task uses Pro model
        """
        return cls.get_model_tier(task_type) == "pro"


# Convenience function
def select_model(task_type: TaskType) -> str:
    """
    Convenience function to select model for a task
    
    Args:
        task_type: Type of task to perform
        
    Returns:
        Model name string
    """
    return ModelSelector.get_model_for_task(task_type)
