"""
Circuit breaker implementation for external API resilience.

Provides circuit breaker patterns to prevent cascading failures
when external services (OpenAI, vector databases) become unavailable.
"""

import asyncio
from functools import wraps
from typing import Any, Callable, Optional

import structlog
from pybreaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerListener,
)

logger = structlog.get_logger(__name__)


class CircuitBreakerConfig:
    """Configuration for circuit breakers."""

    # OpenAI API circuit breaker settings
    OPENAI_FAIL_MAX = 5  # Open circuit after 5 failures
    OPENAI_TIMEOUT = 60  # Try again after 60 seconds
    OPENAI_EXPECTED_EXCEPTION = Exception

    # Vector database circuit breaker settings
    VECTORDB_FAIL_MAX = 3  # More aggressive for vector DBs
    VECTORDB_TIMEOUT = 30  # Shorter timeout for vector DBs
    VECTORDB_EXPECTED_EXCEPTION = Exception

    # Elasticsearch circuit breaker settings
    ELASTICSEARCH_FAIL_MAX = 3
    ELASTICSEARCH_TIMEOUT = 30
    ELASTICSEARCH_EXPECTED_EXCEPTION = Exception


class LoggingCircuitBreakerListener(CircuitBreakerListener):
    """Log circuit breaker state transitions and failures."""

    def state_change(self, breaker, old_state, new_state) -> None:
        state = new_state.name
        if state == "open":
            logger.warning(
                "circuit_breaker_opened",
                breaker_name=breaker.name,
                fail_count=breaker.fail_counter,
            )
        elif state == "closed":
            logger.info(
                "circuit_breaker_closed",
                breaker_name=breaker.name,
            )
        elif state == "half-open":
            logger.info(
                "circuit_breaker_half_open",
                breaker_name=breaker.name,
            )


# Initialize circuit breakers for external services
openai_breaker = CircuitBreaker(
    fail_max=CircuitBreakerConfig.OPENAI_FAIL_MAX,
    reset_timeout=CircuitBreakerConfig.OPENAI_TIMEOUT,
    name="openai_api",
    listeners=[LoggingCircuitBreakerListener()],
)

vectordb_breaker = CircuitBreaker(
    fail_max=CircuitBreakerConfig.VECTORDB_FAIL_MAX,
    reset_timeout=CircuitBreakerConfig.VECTORDB_TIMEOUT,
    name="vector_database",
    listeners=[LoggingCircuitBreakerListener()],
)

elasticsearch_breaker = CircuitBreaker(
    fail_max=CircuitBreakerConfig.ELASTICSEARCH_FAIL_MAX,
    reset_timeout=CircuitBreakerConfig.ELASTICSEARCH_TIMEOUT,
    name="elasticsearch",
    listeners=[LoggingCircuitBreakerListener()],
)


def async_circuit_breaker(breaker: CircuitBreaker) -> Callable:
    """
    Decorator for async functions to add circuit breaker protection.

    Args:
        breaker: CircuitBreaker instance to use

    Returns:
        Decorated function with circuit breaker protection

    Example:
        @async_circuit_breaker(openai_breaker)
        async def call_openai_api():
            # API call here
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                breaker.state.before_call(func, *args, **kwargs)
                for listener in breaker.listeners:
                    listener.before_call(breaker, func, *args, **kwargs)

                result = await func(*args, **kwargs)
                breaker.state._handle_success()
                return result

            except CircuitBreakerError:
                logger.warning(
                    "circuit_breaker_blocked_call",
                    breaker_name=breaker.name,
                    function=func.__name__,
                )
                raise
            except Exception as e:
                logger.error(
                    "circuit_breaker_call_failed",
                    breaker_name=breaker.name,
                    function=func.__name__,
                    error=str(e),
                    fail_count=breaker.fail_counter,
                )
                breaker.state._handle_error(e)

        return wrapper

    return decorator


def sync_circuit_breaker(breaker: CircuitBreaker) -> Callable:
    """
    Decorator for sync functions to add circuit breaker protection.

    Args:
        breaker: CircuitBreaker instance to use

    Returns:
        Decorated function with circuit breaker protection
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator


async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """
    Retry an async function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Result of the function call

    Raises:
        Last exception if all retries fail
    """
    last_exception: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(
                    "retry_exhausted",
                    function=func.__name__,
                    attempts=attempt + 1,
                    error=str(e),
                )
                raise

            # Calculate delay with exponential backoff
            delay = min(initial_delay * (exponential_base**attempt), max_delay)

            logger.warning(
                "retry_attempt",
                function=func.__name__,
                attempt=attempt + 1,
                max_retries=max_retries,
                delay=delay,
                error=str(e),
            )

            await asyncio.sleep(delay)

    # Should never reach here, but for type safety
    if last_exception:
        raise last_exception


def get_circuit_breaker_status() -> dict:
    """
    Get status of all circuit breakers.

    Returns:
        Dictionary with circuit breaker states and statistics
    """
    breakers = {
        "openai": openai_breaker,
        "vectordb": vectordb_breaker,
        "elasticsearch": elasticsearch_breaker,
    }

    status = {}
    for name, breaker in breakers.items():
        status[name] = {
            "state": breaker.current_state,
            "fail_counter": breaker.fail_counter,
            "fail_max": breaker.fail_max,
            "reset_timeout": breaker.reset_timeout,
            "is_available": breaker.current_state != "open",
        }

    return status
