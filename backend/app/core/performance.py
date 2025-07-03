"""Performance optimization utilities"""

import asyncio
from functools import wraps
from typing import Any, Callable, TypeVar, ParamSpec
import time
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

from app.middleware.monitoring import log_slow_query

logger = logging.getLogger(__name__)

# Type variables for decorators
P = ParamSpec("P")
T = TypeVar("T")

# Thread pool for CPU-bound operations
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="cpu_worker")

def measure_performance(operation_name: str):
    """Decorator to measure and log performance of operations"""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log slow operations
                if duration > 1.0:
                    log_slow_query(
                        operation_name,
                        duration,
                        {"function": func.__name__, "module": func.__module__}
                    )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Operation {operation_name} failed after {duration:.2f}s: {str(e)}"
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log slow operations
                if duration > 1.0:
                    log_slow_query(
                        operation_name,
                        duration,
                        {"function": func.__name__, "module": func.__module__}
                    )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Operation {operation_name} failed after {duration:.2f}s: {str(e)}"
                )
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class AsyncBatcher:
    """Batch multiple requests to reduce overhead"""
    
    def __init__(self, batch_size: int = 10, timeout: float = 0.1):
        self.batch_size = batch_size
        self.timeout = timeout
        self.pending = []
        self.lock = asyncio.Lock()
        self.process_task = None
        
    async def add(self, item: Any) -> Any:
        """Add item to batch and get result"""
        future = asyncio.Future()
        
        async with self.lock:
            self.pending.append((item, future))
            
            # Start processing if batch is full
            if len(self.pending) >= self.batch_size:
                if self.process_task:
                    self.process_task.cancel()
                self.process_task = asyncio.create_task(self._process_batch())
            # Or schedule processing after timeout
            elif not self.process_task:
                self.process_task = asyncio.create_task(self._wait_and_process())
        
        return await future
    
    async def _wait_and_process(self):
        """Wait for timeout then process batch"""
        await asyncio.sleep(self.timeout)
        await self._process_batch()
    
    async def _process_batch(self):
        """Process current batch"""
        async with self.lock:
            if not self.pending:
                return
            
            batch = self.pending[:]
            self.pending.clear()
            self.process_task = None
        
        # Process batch (override this method in subclasses)
        results = await self.process_items([item for item, _ in batch])
        
        # Set results
        for i, (_, future) in enumerate(batch):
            if not future.done():
                future.set_result(results[i])
    
    async def process_items(self, items: list) -> list:
        """Process batch of items - override in subclasses"""
        raise NotImplementedError

def run_in_thread_pool(func: Callable[P, T]) -> Callable[P, asyncio.Future[T]]:
    """Decorator to run CPU-bound functions in thread pool"""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> asyncio.Future[T]:
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(thread_pool, func, *args, **kwargs)
    
    return wrapper

class ResourcePool:
    """Generic resource pool for connection pooling"""
    
    def __init__(self, create_resource: Callable, max_size: int = 10):
        self.create_resource = create_resource
        self.max_size = max_size
        self.available = []
        self.in_use = set()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        
    def acquire(self, timeout: float = None):
        """Acquire a resource from the pool"""
        with self.condition:
            # Wait for available resource
            while not self.available and len(self.in_use) >= self.max_size:
                if not self.condition.wait(timeout):
                    raise TimeoutError("Failed to acquire resource")
            
            # Get or create resource
            if self.available:
                resource = self.available.pop()
            else:
                resource = self.create_resource()
            
            self.in_use.add(resource)
            return resource
    
    def release(self, resource):
        """Release resource back to pool"""
        with self.condition:
            if resource in self.in_use:
                self.in_use.remove(resource)
                self.available.append(resource)
                self.condition.notify()
    
    def close_all(self):
        """Close all resources"""
        with self.lock:
            for resource in self.available + list(self.in_use):
                if hasattr(resource, 'close'):
                    resource.close()
            self.available.clear()
            self.in_use.clear()

# Lazy loading utilities
class LazyLoader:
    """Lazy load expensive resources"""
    
    def __init__(self, loader_func: Callable[[], T]):
        self.loader_func = loader_func
        self._value = None
        self._loaded = False
        self._lock = threading.Lock()
        
    @property
    def value(self) -> T:
        """Get the lazily loaded value"""
        if not self._loaded:
            with self._lock:
                if not self._loaded:
                    self._value = self.loader_func()
                    self._loaded = True
        return self._value
    
    def reset(self):
        """Reset the loader"""
        with self._lock:
            self._value = None
            self._loaded = False