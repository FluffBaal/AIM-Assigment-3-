from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import psutil
import platform
from datetime import datetime

from app.api.dependencies import get_api_key
from app.middleware.monitoring import metrics_collector, performance_monitor

router = APIRouter()

@router.get("/metrics")
async def get_metrics(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """Get application metrics"""
    # Basic metrics from collector
    metrics = metrics_collector.get_metrics()
    
    # Add system metrics
    metrics["system"] = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "python_version": platform.python_version(),
        "platform": platform.system()
    }
    
    # Add performance metrics
    metrics["performance"] = {
        "slow_queries_count": len(performance_monitor.slow_queries),
        "recent_slow_queries": performance_monitor.slow_queries[-10:],  # Last 10
        "memory_usage_current_mb": psutil.Process().memory_info().rss / 1024 / 1024
    }
    
    return metrics

@router.get("/metrics/health")
async def health_metrics() -> Dict[str, Any]:
    """Get health metrics (no auth required for monitoring tools)"""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Determine health status
    is_healthy = True
    issues = []
    
    if memory.percent > 90:
        is_healthy = False
        issues.append("High memory usage")
    
    if disk.percent > 90:
        is_healthy = False
        issues.append("Low disk space")
    
    if metrics_collector.error_rate > 0.1:  # More than 10% errors
        is_healthy = False
        issues.append("High error rate")
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "error_rate": metrics_collector.error_rate,
            "active_requests": metrics_collector.active_requests
        },
        "issues": issues
    }

@router.post("/metrics/reset")
async def reset_metrics(api_key: str = Depends(get_api_key)) -> Dict[str, str]:
    """Reset metrics (admin only)"""
    # In production, this should check for admin privileges
    metrics_collector.__init__()
    performance_monitor.slow_queries.clear()
    
    return {"status": "Metrics reset successfully"}