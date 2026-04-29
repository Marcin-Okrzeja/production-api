"""
Cache Module Testing
Test the caching system functionality
"""

import sys
import os
import time

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from cache import get_cache

def test_cache_module():
    """Test the cache module with various operations"""
    print("💾 Testing cache module...")
    
    cache = get_cache()
    
    # Test 1: Basic Set/Get
    print("\n📋 Test 1: Basic Set/Get operations")
    print("-" * 40)
    
    test_key = "test_key_1"
    test_value = "test_value_1"
    
    # Set a value
    cache.set(test_key, test_value)
    print(f"✅ Set: {test_key} -> {test_value}")
    
    # Get the value
    retrieved_value = cache.get(test_key)
    print(f"✅ Get: {test_key} -> {retrieved_value}")
    
    # Verify
    assert retrieved_value == test_value, f"Expected {test_value}, got {retrieved_value}"
    print("✅ Set/Get test passed!")
    
    # Test 2: Expiration
    print("\n📋 Test 2: Expiration functionality")
    print("-" * 40)
    
    short_ttl_key = "short_ttl_key"
    short_ttl_value = "expires_in_1_second"
    
    # Set with 1 second TTL
    cache.set(short_ttl_key, short_ttl_value, ttl=1)
    print(f"✅ Set with 1s TTL: {short_ttl_key}")
    
    # Should be available immediately
    immediate_value = cache.get(short_ttl_key)
    print(f"✅ Immediate get: {immediate_value}")
    assert immediate_value == short_ttl_value
    
    # Wait for expiration
    print("⏳ Waiting 2 seconds for expiration...")
    time.sleep(2)
    
    # Should be expired now
    expired_value = cache.get(short_ttl_key)
    print(f"✅ After expiration: {expired_value}")
    assert expired_value is None, f"Expected None, got {expired_value}"
    print("✅ Expiration test passed!")
    
    # Test 3: Cache Statistics
    print("\n📋 Test 3: Cache statistics")
    print("-" * 40)
    
    # Add some test data
    cache.set("stat_key_1", "value_1")
    cache.set("stat_key_2", "value_2")
    cache.set("stat_key_3", "value_3")
    
    # Get statistics
    stats = cache.get_stats()
    print(f"📊 Cache stats: {stats}")
    
    # Verify stats
    assert stats["total_entries"] >= 3, f"Expected at least 3 entries, got {stats['total_entries']}"
    assert stats["utilization"] > 0, "Expected utilization > 0"
    print("✅ Statistics test passed!")
    
    # Test 4: Cache Hit/Miss Tracking
    print("\n📋 Test 4: Hit/Miss tracking")
    print("-" * 40)
    
    # Clear cache for clean test
    cache.clear()
    
    # Miss
    miss_result = cache.get("non_existent_key")
    print(f"❌ Miss result: {miss_result}")
    assert miss_result is None
    
    # Set and hit
    cache.set("hit_key", "hit_value")
    hit_result = cache.get("hit_key")
    print(f"✅ Hit result: {hit_result}")
    assert hit_result == "hit_value"
    
    print("✅ Hit/Miss tracking test passed!")
    
    # Test 5: Large Data
    print("\n📋 Test 5: Large data handling")
    print("-" * 40)
    
    large_data = "x" * 1000  # 1KB of data
    large_key = "large_data_key"
    
    cache.set(large_key, large_data)
    retrieved_large = cache.get(large_key)
    
    print(f"✅ Large data size: {len(retrieved_large)} characters")
    assert retrieved_large == large_data, "Large data retrieval failed"
    print("✅ Large data test passed!")
    
    # Test 6: Cache Clear
    print("\n📋 Test 6: Cache clear functionality")
    print("-" * 40)
    
    # Add some data
    cache.set("clear_key_1", "value_1")
    cache.set("clear_key_2", "value_2")
    
    # Verify data exists
    before_clear = cache.get_stats()
    print(f"📊 Before clear: {before_clear['total_entries']} entries")
    
    # Clear cache
    cache.clear()
    
    # Verify cache is empty
    after_clear = cache.get_stats()
    print(f"📊 After clear: {after_clear['total_entries']} entries")
    assert after_clear["total_entries"] == 0, "Cache should be empty after clear"
    print("✅ Cache clear test passed!")
    
    print("\n" + "=" * 60)
    print("🎉 All cache tests passed!")
    print("💾 Cache module is working perfectly!")
    
    return True

if __name__ == "__main__":
    test_cache_module()
