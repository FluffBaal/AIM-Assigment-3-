from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import re
import html
import logging

logger = logging.getLogger(__name__)

class RequestValidator(BaseHTTPMiddleware):
    """Middleware for request validation and sanitization"""
    
    # Patterns for detecting potentially malicious content
    SQL_INJECTION_PATTERN = re.compile(
        r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script|javascript|eval)\b)",
        re.IGNORECASE
    )
    
    XSS_PATTERN = re.compile(
        r"(<script|<iframe|javascript:|onerror=|onload=|onclick=|<img\s+src)",
        re.IGNORECASE
    )
    
    PATH_TRAVERSAL_PATTERN = re.compile(r"\.\./|\.\.\\")
    
    # Maximum sizes
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_STRING_LENGTH = 10000  # Maximum length for string fields
    MAX_ARRAY_LENGTH = 100  # Maximum items in arrays
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip validation for streaming endpoints
        if request.url.path.endswith("/stream"):
            return await call_next(request)
            
        # Check request size
        if request.headers.get("content-length"):
            content_length = int(request.headers.get("content-length", 0))
            if content_length > self.MAX_REQUEST_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request too large"}
                )
        
        # Validate path
        if self.PATH_TRAVERSAL_PATTERN.search(request.url.path):
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid path"}
            )
        
        # For POST/PUT requests, validate body
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Store original body
                body = await request.body()
                
                # Validate content type
                content_type = request.headers.get("content-type", "")
                
                if "application/json" in content_type and body:
                    # Validate JSON body
                    import json
                    try:
                        data = json.loads(body)
                        validated_data = self.validate_json_data(data)
                        
                        # Create new request with validated data
                        async def receive():
                            return {
                                "type": "http.request",
                                "body": json.dumps(validated_data).encode()
                            }
                        
                        request._receive = receive
                    except json.JSONDecodeError:
                        return JSONResponse(
                            status_code=400,
                            content={"detail": "Invalid JSON"}
                        )
                    except ValueError as e:
                        return JSONResponse(
                            status_code=400,
                            content={"detail": str(e)}
                        )
                
            except Exception as e:
                logger.error(f"Request validation error: {str(e)}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid request"}
                )
        
        response = await call_next(request)
        return response
    
    def validate_json_data(self, data, depth=0):
        """Recursively validate and sanitize JSON data"""
        if depth > 10:  # Prevent deep recursion
            raise ValueError("Data structure too deep")
        
        if isinstance(data, dict):
            validated = {}
            for key, value in data.items():
                # Validate key
                if not isinstance(key, str) or len(key) > 100:
                    raise ValueError(f"Invalid key: {key}")
                
                # Sanitize and validate value
                validated[key] = self.validate_json_data(value, depth + 1)
            return validated
        
        elif isinstance(data, list):
            if len(data) > self.MAX_ARRAY_LENGTH:
                raise ValueError(f"Array too long: {len(data)} items")
            
            return [self.validate_json_data(item, depth + 1) for item in data]
        
        elif isinstance(data, str):
            # Check length
            if len(data) > self.MAX_STRING_LENGTH:
                raise ValueError(f"String too long: {len(data)} characters")
            
            # Check for malicious patterns
            if self.SQL_INJECTION_PATTERN.search(data):
                raise ValueError("Potentially malicious SQL content detected")
            
            if self.XSS_PATTERN.search(data):
                raise ValueError("Potentially malicious script content detected")
            
            # Sanitize HTML entities
            return html.escape(data)
        
        elif isinstance(data, (int, float)):
            # Validate numeric ranges
            if isinstance(data, int) and abs(data) > 2**53:
                raise ValueError("Integer out of safe range")
            
            if isinstance(data, float) and (data != data or data == float('inf') or data == float('-inf')):
                raise ValueError("Invalid float value")
            
            return data
        
        elif isinstance(data, bool) or data is None:
            return data
        
        else:
            raise ValueError(f"Invalid data type: {type(data)}")

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and other attacks"""
    # Remove any path components
    filename = filename.replace('\\', '/').split('/')[-1]
    
    # Remove potentially dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = f"{name[:240]}.{ext}" if ext else name[:255]
    
    return filename

def validate_api_key(api_key: str) -> bool:
    """Validate API key format"""
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Check if it matches expected format (e.g., sk-...)
    if not api_key.startswith('sk-') or len(api_key) < 20:
        return False
    
    # Check for valid characters
    if not re.match(r'^sk-[a-zA-Z0-9]+$', api_key):
        return False
    
    return True

def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format"""
    uuid_pattern = re.compile(
        r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(uuid_string))