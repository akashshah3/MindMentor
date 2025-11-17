"""
Test script for LLM integration
Tests caching, model selection, and API calls
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.client import gemini_client, generate_lesson, get_hint, explain_concept
from src.llm.models import TaskType, ModelSelector
from src.llm.cache import cache_manager
from src.utils.config import config


def test_config():
    """Test configuration"""
    print("=== Testing Configuration ===")
    print(f"API Key configured: {'✅' if config.GEMINI_API_KEY else '❌'}")
    print(f"Cache enabled: {config.ENABLE_LLM_CACHE}")
    print(f"Cache TTL: {config.CACHE_TTL_DAYS} days")
    print(f"Default model: {config.DEFAULT_MODEL}")
    print()


def test_model_selection():
    """Test model selection logic"""
    print("=== Testing Model Selection ===")
    
    test_cases = [
        (TaskType.GRADING_DESCRIPTIVE, "pro"),
        (TaskType.LESSON_GENERATION, "flash"),
        (TaskType.HINT_GENERATION, "flash_lite"),
    ]
    
    for task_type, expected_tier in test_cases:
        model = ModelSelector.get_model_for_task(task_type)
        tier = ModelSelector.get_model_tier(task_type)
        cost = ModelSelector.estimate_cost_tier(task_type)
        
        status = "✅" if tier == expected_tier else "❌"
        print(f"{status} {task_type.value}:")
        print(f"   Model: {model}")
        print(f"   Tier: {tier} (expected: {expected_tier})")
        print(f"   Cost: {cost}")
    
    print()


def test_simple_generation():
    """Test a simple LLM generation"""
    print("=== Testing Simple Concept Explanation ===")
    
    try:
        explanation, was_cached = explain_concept(
            subject="Physics",
            topic_name="Newton's Laws",
            concept="Newton's First Law of Motion",
            student_context="beginner level"
        )
        
        print(f"Cache status: {'HIT ✅' if was_cached else 'MISS (new generation)'}")
        print(f"\nExplanation:\n{explanation[:300]}...")
        print()
        
        # Try again to test caching
        print("=== Testing Cache (same request again) ===")
        explanation2, was_cached2 = explain_concept(
            subject="Physics",
            topic_name="Newton's Laws",
            concept="Newton's First Law of Motion",
            student_context="beginner level"
        )
        
        print(f"Cache status: {'HIT ✅' if was_cached2 else 'MISS ❌'}")
        print(f"Content matches: {'✅' if explanation == explanation2 else '❌'}")
        print()
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_json_generation():
    """Test JSON generation (lesson)"""
    print("=== Testing JSON Generation (Lesson) ===")
    
    try:
        lesson, was_cached = generate_lesson(
            subject="Physics",
            topic_name="Kinematics",
            chapter_name="Mechanics",
            difficulty="Medium",
            student_level="intermediate",
            force_refresh=True  # Force new generation (old cache was truncated)
        )
        
        print(f"Cache status: {'HIT ✅' if was_cached else 'MISS (new generation)'}")
        print(f"\nLesson structure:")
        print(f"  - Keys: {list(lesson.keys())}")
        
        if 'explanation' in lesson:
            print(f"  - Explanation length: {len(lesson['explanation'])} chars")
        if 'key_points' in lesson:
            print(f"  - Key points: {len(lesson.get('key_points', []))} items")
        if 'examples' in lesson:
            print(f"  - Examples: {len(lesson.get('examples', []))} items")
        
        print()
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_cache_stats():
    """Test cache statistics"""
    print("=== Cache Statistics ===")
    
    # Session stats
    session_stats = gemini_client.get_session_stats()
    print("Session stats:")
    print(f"  - API calls: {session_stats['api_calls']}")
    print(f"  - Cache hits: {session_stats['cache_hits']}")
    print(f"  - Cache misses: {session_stats['cache_misses']}")
    print(f"  - Hit rate: {session_stats['cache_hit_rate_percent']:.1f}%")
    print()
    
    # Overall cache stats
    cache_stats = cache_manager.get_cache_stats()
    print("Overall cache stats:")
    print(f"  - Total entries: {cache_stats['total_entries']}")
    print(f"  - Total accesses: {cache_stats['total_accesses']}")
    print(f"  - Avg accesses per entry: {cache_stats['avg_accesses_per_entry']:.2f}")
    print(f"  - Estimated hit rate: {cache_stats['estimated_hit_rate_percent']:.1f}%")
    
    if cache_stats['by_model']:
        print("\n  By model:")
        for model_stat in cache_stats['by_model']:
            print(f"    - {model_stat['model_used']}: {model_stat['count']} entries, {model_stat['accesses']} accesses")
    
    print()


def main():
    """Run all tests"""
    print("🧪 MindMentor LLM Integration Tests\n")
    print("=" * 60)
    print()
    
    # Test 1: Configuration
    test_config()
    
    if not config.GEMINI_API_KEY:
        print("❌ No API key found. Please set GEMINI_API_KEY in .env")
        return
    
    # Test 2: Model Selection
    test_model_selection()
    
    # Test 3: Simple generation
    success = test_simple_generation()
    if not success:
        print("⚠️  Simple generation failed. Check your API key and network connection.")
        return
    
    # Test 4: JSON generation
    test_json_generation()
    
    # Test 5: Cache stats
    test_cache_stats()
    
    print("=" * 60)
    print("\n✅ All tests completed!")
    print("\n💡 Tips:")
    print("  - Run this test again to see cache hits increase")
    print("  - Check mindmentor.db for cached responses in llm_cache table")
    print("  - Monitor API usage to ensure caching is working")


if __name__ == "__main__":
    main()
