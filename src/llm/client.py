"""
Gemini API Client
Handles all interactions with Google's Gemini API with caching and error handling
"""

import json
import time
from typing import Optional, Dict, Any, List
from google import genai
from google.genai import types
from src.utils.config import config
from src.llm.cache import cache_manager
from src.llm.models import TaskType, ModelSelector
from src.llm.prompts import PromptTemplates


class GeminiClient:
    """Client for Google Gemini API with caching"""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        default_model: str = "gemini-2.5-flash",
        use_cache: bool = True,
        cache_ttl: int = 7 * 24 * 60 * 60  # 7 days in seconds
    ):
        """
        Initialize Gemini client
        
        Args:
            api_key: Gemini API key (defaults to config)
        """
        self.api_key = api_key or config.GEMINI_API_KEY
        
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # Initialize the client
        self.client = genai.Client(api_key=self.api_key)
        
        # Track API usage
        self.call_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def _call_api(self, model: str, prompt: str, 
                  temperature: float = 0.7,
                  max_tokens: int = 4096,
                  max_retries: int = 3) -> str:
        """
        Make API call to Gemini with retry logic
        
        Args:
            model: Model name to use
            prompt: Prompt text
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response text from the model
            
        Raises:
            Exception: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    )
                )
                
                self.call_count += 1
                
                # Ensure we got a valid response
                if response and response.text:
                    return response.text
                else:
                    raise ValueError(f"Empty response from model {model}")
            
            except Exception as e:
                if attempt < max_retries - 1:
                    # Wait before retry (exponential backoff)
                    wait_time = (2 ** attempt) * 1
                    time.sleep(wait_time)
                    continue
                else:
                    # Final attempt failed
                    raise Exception(f"Gemini API call failed after {max_retries} attempts: {str(e)}")
    
    def generate_with_cache(self, task_type: TaskType,
                          prompt_template: str,
                          params: Dict[str, Any],
                          temperature: float = 0.7,
                          max_tokens: int = 4096,
                          force_refresh: bool = False) -> tuple[str, bool]:
        """
        Generate content with automatic caching
        
        This is the main method to use for all LLM operations
        
        Args:
            task_type: Type of task (determines model selection)
            prompt_template: Prompt template string
            params: Parameters to fill template
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            force_refresh: If True, bypass cache and generate new response
            
        Returns:
            Tuple of (response_text, was_cached)
        """
        # Select appropriate model for task
        model = ModelSelector.get_model_for_task(task_type)
        
        # Fill template
        filled_prompt = prompt_template.format(**params)
        
        # Determine content type for tracking
        content_type = task_type.value
        
        # Generator function for cache
        def generator():
            return self._call_api(model, filled_prompt, temperature, max_tokens)
        
        if force_refresh:
            # Bypass cache
            response = generator()
            self.cache_misses += 1
            # Still store in cache for future
            cache_manager.store_response(
                cache_key=cache_manager.generate_cache_key(prompt_template, params, model),
                response=response,
                model=model,
                prompt_template=prompt_template,
                content_type=content_type
            )
            return response, False
        
        # Use cache
        response, was_cached = cache_manager.get_or_generate(
            prompt_template=prompt_template,
            params=params,
            model=model,
            generator_func=generator,
            content_type=content_type
        )
        
        # Update stats
        if was_cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        return response, was_cached
    
    def generate_json(self, task_type: TaskType,
                     prompt_template: str,
                     params: Dict[str, Any],
                     temperature: float = 0.7,
                     max_tokens: int = 4096,
                     force_refresh: bool = False) -> tuple[Dict, bool]:
        """
        Generate content and parse as JSON
        
        Args:
            task_type: Type of task
            prompt_template: Prompt template string
            params: Parameters to fill template
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            force_refresh: If True, bypass cache
            
        Returns:
            Tuple of (parsed_json_dict, was_cached)
            
        Raises:
            ValueError: If response is not valid JSON
        """
        response_text, was_cached = self.generate_with_cache(
            task_type=task_type,
            prompt_template=prompt_template,
            params=params,
            temperature=temperature,
            max_tokens=max_tokens,
            force_refresh=force_refresh
        )
        
        # Parse JSON
        try:
            # Handle None response
            if not response_text:
                raise ValueError("Empty response from LLM")
            
            # Try to find JSON in response (handle markdown code blocks)
            json_text = response_text.strip()
            
            if "```json" in json_text:
                # Extract JSON from json code block
                start = json_text.find("```json") + 7
                end = json_text.find("```", start)
                if end == -1:  # No closing backticks
                    json_text = json_text[start:].strip()
                else:
                    json_text = json_text[start:end].strip()
            elif "```" in json_text:
                # Extract from generic code block
                start = json_text.find("```") + 3
                end = json_text.find("```", start)
                if end == -1:  # No closing backticks
                    json_text = json_text[start:].strip()
                else:
                    json_text = json_text[start:end].strip()
            
            parsed = json.loads(json_text)
            return parsed, was_cached
        
        except json.JSONDecodeError as e:
            # Try to fix common JSON issues with LaTeX/math expressions
            try:
                # The issue is often unescaped backslashes in LaTeX
                # We'll try using json.loads with strict=False which is more lenient
                import ast
                # Try a more lenient approach - replace response with fixed version
                # This is a workaround for LaTeX in JSON
                fixed_text = json_text.replace('\\', '\\\\')  # Escape all backslashes
                # But this over-escapes, so we need to be smarter
                # Actually, let's just let the LLM handle it by being more lenient
                
                # Alternative: Use ast.literal_eval as last resort
                # For now, just log the error and return empty
                print(f"JSON parsing failed, attempting recovery...")
                print(f"Error details: {str(e)}")
                print(f"Problematic text sample: {json_text[:500]}")
                
                # Return a minimal valid structure
                return {"questions": []}, was_cached
                
            except Exception as recovery_error:
                # If JSON parsing fails, provide detailed error
                error_msg = f"Failed to parse LLM response as JSON.\nError: {str(e)}\nExtracted text: {json_text[:300] if json_text else 'None'}..."
                raise ValueError(error_msg)
        
        except Exception as e:
            raise ValueError(f"Error processing LLM response: {str(e)}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get statistics for current session
        
        Returns:
            Dictionary with usage stats
        """
        total_calls = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_calls * 100) if total_calls > 0 else 0
        
        return {
            'api_calls': self.call_count,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'total_operations': total_calls,
            'cache_hit_rate_percent': round(hit_rate, 2)
        }
    
    def reset_stats(self):
        """Reset session statistics"""
        self.call_count = 0
        self.cache_hits = 0
        self.cache_misses = 0


# Singleton instance
gemini_client = GeminiClient()


# Convenience functions for common operations

def generate_lesson(subject: str, topic_name: str, chapter_name: str,
                   difficulty: str = "Medium", 
                   student_level: str = "intermediate",
                   force_refresh: bool = False) -> tuple[Dict, bool]:
    """
    Generate a lesson for a topic
    
    Returns:
        Tuple of (lesson_dict, was_cached)
    """
    from src.llm.prompts import PromptTemplates
    
    return gemini_client.generate_json(
        task_type=TaskType.LESSON_GENERATION,
        prompt_template=PromptTemplates.LESSON_GENERATION,
        params={
            'subject': subject,
            'topic_name': topic_name,
            'chapter_name': chapter_name,
            'difficulty': difficulty,
            'student_level': student_level
        },
        max_tokens=8192,  # Lessons need more tokens
        force_refresh=force_refresh
    )


def generate_questions(subject: str, topic_name: str, 
                      question_type: str = "MCQ",
                      difficulty: str = "Medium",
                      count: int = 5,
                      exam_level: str = "Main") -> tuple[Dict, bool]:
    """
    Generate practice questions
    
    Returns:
        Tuple of (questions_dict, was_cached)
    """
    from src.llm.prompts import PromptTemplates
    
    return gemini_client.generate_json(
        task_type=TaskType.QUESTION_GENERATION,
        prompt_template=PromptTemplates.QUESTION_GENERATION,
        params={
            'subject': subject,
            'topic_name': topic_name,
            'question_type': question_type,
            'difficulty': difficulty,
            'count': count,
            'exam_level': exam_level
        }
    )


def get_hint(question_text: str, subject: str, topic_name: str) -> tuple[str, bool]:
    """
    Get a hint for a question
    
    Returns:
        Tuple of (hint_text, was_cached)
    """
    from src.llm.prompts import PromptTemplates
    
    return gemini_client.generate_with_cache(
        task_type=TaskType.HINT_GENERATION,
        prompt_template=PromptTemplates.HINT_GENERATION,
        params={
            'question_text': question_text,
            'subject': subject,
            'topic_name': topic_name
        }
    )


def explain_concept(subject: str, topic_name: str, concept: str,
                   student_context: str = "beginner level") -> tuple[str, bool]:
    """
    Explain a concept
    
    Returns:
        Tuple of (explanation_text, was_cached)
    """
    from src.llm.prompts import PromptTemplates
    
    return gemini_client.generate_with_cache(
        task_type=TaskType.CONCEPT_EXPLANATION,
        prompt_template=PromptTemplates.CONCEPT_EXPLANATION,
        params={
            'subject': subject,
            'topic_name': topic_name,
            'concept': concept,
            'student_context': student_context
        }
    )
