"""
LLM Response Caching System
Critical component for API cost control
"""

import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from src.data.db import db
from src.utils.config import config


class CacheManager:
    """Manages LLM response caching"""
    
    @staticmethod
    def generate_cache_key(prompt_template: str, params: Dict[str, Any], 
                          model: str) -> str:
        """
        Generate a unique cache key from prompt template, parameters, and model
        
        Args:
            prompt_template: The prompt template string
            params: Parameters to fill the template
            model: Model name being used
            
        Returns:
            Unique cache key (SHA256 hash)
        """
        # Create a deterministic string from all inputs
        key_data = {
            'template': prompt_template,
            'params': params,
            'model': model
        }
        
        # Convert to JSON string with sorted keys for consistency
        key_string = json.dumps(key_data, sort_keys=True)
        
        # Hash to create fixed-length key
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()
    
    @staticmethod
    def get_cached_response(cache_key: str) -> Optional[str]:
        """
        Retrieve cached LLM response
        
        Args:
            cache_key: Unique cache key
            
        Returns:
            Cached response content, or None if not found
        """
        if not config.ENABLE_LLM_CACHE:
            return None
        
        cache_entry = db.get_from_cache(cache_key)
        
        if cache_entry:
            # Check if cache is still valid (based on TTL)
            created_at = datetime.fromisoformat(cache_entry['created_at'])
            ttl_days = config.CACHE_TTL_DAYS
            
            if datetime.now() - created_at > timedelta(days=ttl_days):
                # Cache expired (though with 7+ days TTL, this is rare)
                return None
            
            return cache_entry['response_content']
        
        return None
    
    @staticmethod
    def store_response(cache_key: str, response: str, model: str,
                      prompt_template: Optional[str] = None,
                      content_type: Optional[str] = None) -> int:
        """
        Store LLM response in cache
        
        Args:
            cache_key: Unique cache key
            response: LLM response content to cache
            model: Model name that generated the response
            prompt_template: Optional prompt template
            content_type: Optional content type (lesson, question, etc.)
            
        Returns:
            Cache entry ID
        """
        if not config.ENABLE_LLM_CACHE:
            return -1
        
        return db.store_in_cache(
            cache_key=cache_key,
            model_used=model,
            response_content=response,
            prompt_template=prompt_template,
            content_type=content_type
        )
    
    @staticmethod
    def get_or_generate(prompt_template: str, params: Dict[str, Any],
                       model: str, generator_func,
                       content_type: Optional[str] = None) -> tuple[str, bool]:
        """
        Get cached response or generate new one
        
        This is the main caching interface that should be used by LLM client
        
        Args:
            prompt_template: Prompt template string
            params: Parameters to fill template
            model: Model to use for generation
            generator_func: Function to call if cache miss (should return response string)
            content_type: Optional content type for tracking
            
        Returns:
            Tuple of (response_content, was_cached)
            where was_cached is True if retrieved from cache, False if generated
        """
        # Generate cache key
        cache_key = CacheManager.generate_cache_key(prompt_template, params, model)
        
        # Try to get from cache
        cached_response = CacheManager.get_cached_response(cache_key)
        
        if cached_response is not None:
            # Cache hit!
            return cached_response, True
        
        # Cache miss - generate new response
        response = generator_func()
        
        # Store in cache
        CacheManager.store_response(
            cache_key=cache_key,
            response=response,
            model=model,
            prompt_template=prompt_template,
            content_type=content_type
        )
        
        return response, False
    
    @staticmethod
    def get_cache_stats() -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats including hit rate
        """
        stats = db.get_cache_stats()
        
        # Calculate cache hit rate (if we have access count data)
        total_accesses = stats['total_accesses']
        total_entries = stats['total_entries']
        
        if total_accesses > 0 and total_entries > 0:
            # Estimate: if average accesses > 1, we had cache hits
            # Hit rate = (total_accesses - total_entries) / total_accesses
            estimated_hits = max(0, total_accesses - total_entries)
            hit_rate = (estimated_hits / total_accesses) * 100
            stats['estimated_hit_rate_percent'] = round(hit_rate, 2)
        else:
            stats['estimated_hit_rate_percent'] = 0.0
        
        return stats
    
    @staticmethod
    def clear_old_cache(days: int = 30) -> int:
        """
        Clear old cache entries
        
        Args:
            days: Clear entries not accessed in this many days
            
        Returns:
            Number of entries deleted
        """
        return db.clear_old_cache(days)


# Singleton instance
cache_manager = CacheManager()
