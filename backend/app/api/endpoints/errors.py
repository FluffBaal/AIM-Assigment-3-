from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional

from app.api.dependencies import get_api_key
from app.middleware.error_tracking import error_tracker

router = APIRouter()

@router.get("/summary")
async def get_error_summary(
    api_key: str = Depends(get_api_key)
) -> Dict[str, Any]:
    """Get summary of application errors"""
    return error_tracker.get_error_summary()

@router.get("/details/{error_id}")
async def get_error_details(
    error_id: str,
    api_key: str = Depends(get_api_key)
) -> Dict[str, Any]:
    """Get details of a specific error"""
    error = error_tracker.get_error_details(error_id)
    
    if not error:
        raise HTTPException(status_code=404, detail="Error not found")
    
    return error

@router.get("/patterns")
async def get_error_patterns(
    api_key: str = Depends(get_api_key),
    limit: int = Query(default=10, ge=1, le=100)
) -> Dict[str, Any]:
    """Get error patterns grouped by fingerprint"""
    patterns = []
    
    for fingerprint, details in error_tracker.error_patterns.items():
        patterns.append({
            "fingerprint": fingerprint,
            "details": details,
            "count": error_tracker.error_counts.get(fingerprint, 0)
        })
    
    # Sort by count descending
    patterns.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "total_patterns": len(patterns),
        "patterns": patterns[:limit]
    }

@router.post("/clear")
async def clear_errors(
    api_key: str = Depends(get_api_key)
) -> Dict[str, str]:
    """Clear all tracked errors (admin only)"""
    # In production, this should check for admin privileges
    error_tracker.clear_errors()
    
    return {"status": "Errors cleared successfully"}

@router.get("/recent")
async def get_recent_errors(
    api_key: str = Depends(get_api_key),
    limit: int = Query(default=20, ge=1, le=100),
    error_type: Optional[str] = Query(default=None)
) -> Dict[str, Any]:
    """Get recent errors with optional filtering"""
    errors = list(error_tracker.errors)
    
    # Filter by error type if specified
    if error_type:
        errors = [e for e in errors if e["type"] == error_type]
    
    # Get most recent errors
    recent_errors = errors[-limit:]
    recent_errors.reverse()  # Most recent first
    
    return {
        "total": len(errors),
        "limit": limit,
        "errors": recent_errors
    }

@router.get("/stats")
async def get_error_stats(
    api_key: str = Depends(get_api_key)
) -> Dict[str, Any]:
    """Get error statistics"""
    summary = error_tracker.get_error_summary()
    
    # Calculate additional stats
    error_types = {}
    endpoints = {}
    
    for error in error_tracker.errors:
        # Count by error type
        error_type = error["type"]
        error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Count by endpoint
        endpoint = f"{error['request']['method']} {error['request']['path']}"
        endpoints[endpoint] = endpoints.get(endpoint, 0) + 1
    
    return {
        "summary": summary,
        "by_type": error_types,
        "by_endpoint": endpoints,
        "error_rate": {
            "per_minute": summary.get("error_rate_per_minute", 0),
            "per_hour": summary.get("error_rate_per_minute", 0) * 60
        }
    }