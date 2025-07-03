from fastapi import Request, Response
from typing import Callable, Dict, Optional, Tuple
import time
import hashlib
import json
from datetime import datetime, timedelta
import asyncio
from collections import OrderedDict

class LRUCache:
    """Simple LRU cache implementation"""
    
    def __init__(self, max_size: int = 100):
        self.cache = OrderedDict()
        self.max_size = max_size
        
    def get(self, key: str) -> Optional[Tuple[Dict, float]]:
        """Get item from cache"""
        if key not in self.cache:
            return None
            
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def set(self, key: str, value: Dict, ttl: float):
        """Set item in cache"""
        # Add to cache
        self.cache[key] = (value, time.time() + ttl)
        self.cache.move_to_end(key)
        
        # Remove oldest if over capacity
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
    
    def cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if expiry < current_time
        ]
        
        for key in expired_keys:
            del self.cache[key]

class CachingMiddleware:
    """Middleware for caching GET requests"""
    
    # Endpoints to cache with TTL in seconds
    CACHE_CONFIG = {
        "/api/v1/health": 60,  # 1 minute
        "/api/v1/monitoring/metrics/health": 30,  # 30 seconds
        "/api/v1/pdf": 300,  # 5 minutes for PDF list
    }
    
    def __init__(self, app):
        self.app = app
        self.cache = LRUCache(max_size=1000)
        self.cleanup_task = None
        
    async def __call__(self, request: Request, call_next: Callable):
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Check if endpoint should be cached
        path = request.url.path
        ttl = None
        
        # Check exact match first
        if path in self.CACHE_CONFIG:
            ttl = self.CACHE_CONFIG[path]
        else:
            # Check prefix match for parameterized routes
            for cached_path, cache_ttl in self.CACHE_CONFIG.items():
                if path.startswith(cached_path):
                    ttl = cache_ttl
                    break
        
        if ttl is None:
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get from cache
        cached = self.cache.get(cache_key)
        if cached:
            cached_response, expiry = cached
            if time.time() < expiry:
                # Return cached response
                return Response(
                    content=json.dumps(cached_response["body"]),
                    status_code=cached_response["status_code"],
                    headers={
                        **cached_response["headers"],
                        "X-Cache": "HIT",
                        "X-Cache-Age": str(int(time.time() - (expiry - ttl)))
                    },
                    media_type="application/json"
                )
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses
        if 200 <= response.status_code < 300:
            # Read response body
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk
            
            try:
                body_json = json.loads(body_bytes)
                
                # Cache the response
                cached_response = {
                    "body": body_json,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }
                self.cache.set(cache_key, cached_response, ttl)
                
                # Return new response with cache headers
                return Response(
                    content=body_bytes,
                    status_code=response.status_code,
                    headers={
                        **dict(response.headers),
                        "X-Cache": "MISS",
                        "X-Cache-Control": f"max-age={ttl}"
                    },
                    media_type="application/json"
                )
            except json.JSONDecodeError:
                # Return original response if not JSON
                return Response(
                    content=body_bytes,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type", "text/plain")
                )
        
        return response
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        # Include path, query params, and relevant headers
        key_parts = [
            request.url.path,
            str(sorted(request.query_params.items())),
            request.headers.get("x-api-key", ""),
        ]
        
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def start_cleanup_task(self):
        """Start background cleanup task"""
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self):
        """Stop background cleanup task"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
    
    async def _cleanup_loop(self):
        """Periodically clean up expired cache entries"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                self.cache.cleanup_expired()
            except asyncio.CancelledError:
                break

# Response compression utilities
def should_compress(content_type: str, content_length: int) -> bool:
    """Determine if response should be compressed"""
    # Don't compress small responses
    if content_length < 1024:  # Less than 1KB
        return False
    
    # Compress text-based content types
    compressible_types = [
        "application/json",
        "text/html",
        "text/plain",
        "text/css",
        "application/javascript",
        "application/xml",
    ]
    
    return any(ct in content_type for ct in compressible_types)