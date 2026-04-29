"""
Cache module for Production AI API
Response caching with TTL and memory management
"""

import time
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from models import CacheEntry
from config import get_settings


class SimpleCache:
    """In-memory cache with TTL and size limits"""
    
    def __init__(self):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = 1000  # Maximum cache entries
        self.default_ttl = get_settings().cache_ttl
        
    def _generate_key(self, text: str) -> str:
        """Generate cache key from text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[str]:
        """Get cached value if not expired"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if datetime.utcnow() > entry.expires_at:
            del self.cache[key]
            return None
        
        # Update access count
        entry.access_count += 1
        return entry.value
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Set cached value with TTL"""
        # Remove oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            self._cleanup_expired()
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
        
        # Calculate expiration
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            size_bytes=len(value.encode())
        )
        
        self.cache[key] = entry
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries"""
        now = datetime.utcnow()
        expired_keys = [k for k, v in self.cache.items() if v.expires_at < now]
        for key in expired_keys:
            del self.cache[key]
    
    def _evict_oldest(self) -> None:
        """Remove oldest entry"""
        if not self.cache:
            return
        
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].created_at)
        del self.cache[oldest_key]
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self._cleanup_expired()
        
        total_size = sum(entry.size_bytes for entry in self.cache.values())
        avg_access_count = sum(entry.access_count for entry in self.cache.values()) / len(self.cache) if self.cache else 0
        
        return {
            "total_entries": len(self.cache),
            "total_size_bytes": total_size,
            "max_size": self.max_size,
            "utilization": len(self.cache) / self.max_size,
            "average_access_count": avg_access_count
        }


# Global cache instance
cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get global cache instance"""
    return cache


if __name__ == "__main__":
    # Test cache
    print("💾 Testing cache module...")
    
    # Test basic operations
    cache.set("test_key", "test_value", ttl=60)
    value = cache.get("test_key")
    print(f"✅ Set/Get test: {value}")
    
    # Test expiration
    cache.set("expire_key", "expire_value", ttl=1)
    time.sleep(2)
    expired = cache.get("expire_key")
    print(f"✅ Expiration test: {expired is None}")
    
    # Test stats
    stats = cache.get_stats()
    print(f"✅ Cache stats: {stats}")
    
    print("🎉 Cache module working!")
