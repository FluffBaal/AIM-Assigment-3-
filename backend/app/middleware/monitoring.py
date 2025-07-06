from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
import logging
from datetime import datetime
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and stores application metrics"""
    
    def __init__(self):
        self.request_count = defaultdict(int)
        self.request_duration = defaultdict(list)
        self.error_count = defaultdict(int)
        self.active_requests = 0
        self.start_time = time.time()
        
    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Record request metrics"""
        key = f"{method}:{path}"
        self.request_count[key] += 1
        self.request_duration[key].append(duration)
        
        if status_code >= 400:
            self.error_count[key] += 1
    
    @property
    def error_rate(self):
        """Calculate current error rate"""
        total_requests = sum(self.request_count.values())
        if total_requests == 0:
            return 0.0
        return sum(self.error_count.values()) / total_requests
    
    def get_metrics(self):
        """Get current metrics"""
        uptime = time.time() - self.start_time
        
        # Calculate averages
        avg_duration = {}
        for key, durations in self.request_duration.items():
            if durations:
                avg_duration[key] = sum(durations) / len(durations)
        
        return {
            "uptime_seconds": uptime,
            "total_requests": sum(self.request_count.values()),
            "active_requests": self.active_requests,
            "request_count": dict(self.request_count),
            "average_duration_ms": {k: v * 1000 for k, v in avg_duration.items()},
            "error_count": dict(self.error_count),
            "error_rate": self.error_rate
        }

# Global metrics collector
metrics_collector = MetricsCollector()

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for request monitoring and metrics collection"""
        
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip monitoring for health endpoints and streaming endpoints
        if request.url.path in ["/health", "/metrics"] or request.url.path.endswith("/stream"):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        metrics_collector.active_requests += 1
        
        # Log request
        logger.info(f"Request started: {request.method} {request.url.path}")
        
        # Add request ID for tracing
        request_id = f"{int(time.time() * 1000)}-{metrics_collector.active_requests}"
        request.state.request_id = request_id
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            metrics_collector.record_request(
                request.method,
                request.url.path,
                response.status_code,
                duration
            )
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration * 1000:.2f}ms"
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Duration: {duration * 1000:.2f}ms"
            )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Record error
            metrics_collector.record_request(
                request.method,
                request.url.path,
                500,
                duration
            )
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"- Error: {str(e)} - Duration: {duration * 1000:.2f}ms"
            )
            
            raise
            
        finally:
            metrics_collector.active_requests -= 1

class PerformanceMonitor:
    """Monitor for tracking performance metrics"""
    
    def __init__(self):
        self.slow_queries = []
        self.memory_usage = []
        self._monitoring_task = None
        
    async def start_monitoring(self):
        """Start background monitoring"""
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
        
    async def stop_monitoring(self):
        """Stop background monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                # Monitor memory usage
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                self.memory_usage.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "memory_mb": memory_mb
                })
                
                # Keep only last hour of data
                if len(self.memory_usage) > 3600:
                    self.memory_usage = self.memory_usage[-3600:]
                
                # Check for high memory usage
                if memory_mb > 500:  # Alert if over 500MB
                    logger.warning(f"High memory usage detected: {memory_mb:.2f}MB")
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {str(e)}")
                await asyncio.sleep(60)

# Global performance monitor
performance_monitor = PerformanceMonitor()

def log_slow_query(query_type: str, duration: float, details: dict = None):
    """Log slow queries for analysis"""
    if duration > 1.0:  # Log queries taking more than 1 second
        performance_monitor.slow_queries.append({
            "timestamp": datetime.utcnow().isoformat(),
            "query_type": query_type,
            "duration_seconds": duration,
            "details": details or {}
        })
        
        # Keep only last 100 slow queries
        if len(performance_monitor.slow_queries) > 100:
            performance_monitor.slow_queries = performance_monitor.slow_queries[-100:]
        
        logger.warning(
            f"Slow query detected: {query_type} took {duration:.2f}s"
        )