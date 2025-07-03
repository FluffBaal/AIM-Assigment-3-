from fastapi import Request, Response
from typing import Callable, Optional, Dict, Any, List
import time
import logging
import traceback
from datetime import datetime
from collections import deque
import hashlib
import json

logger = logging.getLogger(__name__)

class ErrorTracker:
    """Tracks and categorizes application errors"""
    
    def __init__(self, max_errors: int = 1000):
        self.errors = deque(maxlen=max_errors)
        self.error_counts = {}
        self.error_patterns = {}
        
    def track_error(self, request: Request, error: Exception, duration: float):
        """Track an error occurrence"""
        # Generate error fingerprint
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = traceback.format_exc()
        
        # Create fingerprint for error grouping
        fingerprint = self._generate_fingerprint(error_type, stack_trace)
        
        # Create error record
        error_record = {
            "id": f"{int(time.time() * 1000)}-{len(self.errors)}",
            "timestamp": datetime.utcnow().isoformat(),
            "type": error_type,
            "message": error_message,
            "fingerprint": fingerprint,
            "request": {
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": self._sanitize_headers(dict(request.headers)),
                "client_host": request.client.host if request.client else None,
            },
            "stack_trace": stack_trace,
            "duration_ms": duration * 1000,
        }
        
        # Add to errors list
        self.errors.append(error_record)
        
        # Update counts
        self.error_counts[fingerprint] = self.error_counts.get(fingerprint, 0) + 1
        
        # Update patterns
        if fingerprint not in self.error_patterns:
            self.error_patterns[fingerprint] = {
                "type": error_type,
                "message": error_message,
                "first_seen": datetime.utcnow().isoformat(),
                "last_seen": datetime.utcnow().isoformat(),
                "count": 0,
                "sample_stack": stack_trace,
            }
        else:
            self.error_patterns[fingerprint]["last_seen"] = datetime.utcnow().isoformat()
            self.error_patterns[fingerprint]["count"] = self.error_counts[fingerprint]
        
        # Log the error
        logger.error(
            f"Error tracked: {error_type} - {error_message} "
            f"[{request.method} {request.url.path}] - Duration: {duration * 1000:.2f}ms"
        )
        
    def _generate_fingerprint(self, error_type: str, stack_trace: str) -> str:
        """Generate a fingerprint for error grouping"""
        # Extract meaningful lines from stack trace
        lines = stack_trace.split('\n')
        meaningful_lines = []
        
        for line in lines:
            # Skip framework lines
            if any(skip in line for skip in ['site-packages', 'fastapi', 'starlette', 'uvicorn']):
                continue
            # Include file paths and error messages
            if 'File "' in line or error_type in line:
                meaningful_lines.append(line.strip())
        
        # Create hash from error type and meaningful stack trace lines
        content = f"{error_type}:{':'.join(meaningful_lines[:5])}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive information from headers"""
        sensitive_headers = {'authorization', 'x-api-key', 'cookie', 'set-cookie'}
        sanitized = {}
        
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = value
                
        return sanitized
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of tracked errors"""
        if not self.errors:
            return {
                "total_errors": 0,
                "unique_errors": 0,
                "recent_errors": [],
                "top_errors": [],
            }
        
        # Get top errors by frequency
        top_errors = sorted(
            [
                {
                    "fingerprint": fp,
                    "count": count,
                    "details": self.error_patterns.get(fp, {})
                }
                for fp, count in self.error_counts.items()
            ],
            key=lambda x: x["count"],
            reverse=True
        )[:10]
        
        return {
            "total_errors": len(self.errors),
            "unique_errors": len(self.error_patterns),
            "recent_errors": list(self.errors)[-10:],
            "top_errors": top_errors,
            "error_rate_per_minute": self._calculate_error_rate(),
        }
    
    def _calculate_error_rate(self) -> float:
        """Calculate errors per minute for the last 5 minutes"""
        if not self.errors:
            return 0.0
            
        five_minutes_ago = time.time() - 300
        recent_errors = [
            e for e in self.errors
            if datetime.fromisoformat(e["timestamp"]).timestamp() > five_minutes_ago
        ]
        
        return len(recent_errors) / 5.0
    
    def get_error_details(self, error_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific error"""
        for error in self.errors:
            if error["id"] == error_id:
                return error
        return None
    
    def clear_errors(self):
        """Clear all tracked errors"""
        self.errors.clear()
        self.error_counts.clear()
        self.error_patterns.clear()

# Global error tracker
error_tracker = ErrorTracker()

class ErrorTrackingMiddleware:
    """Middleware for tracking application errors"""
    
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Track the error
            error_tracker.track_error(request, e, duration)
            
            # Re-raise the exception to let error handlers deal with it
            raise