# m_flow/memory/episodic/llm_call_tracker.py
"""
LLM call tracker - records retry counts and detailed reasons for LLM calls per module.

Features:
- Record LLM call counts per module
- Record retry counts and reasons for each retry
- Provide statistical summaries
- Thread-safe global statistics
"""

from __future__ import annotations

import asyncio
import contextvars
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar
from contextlib import asynccontextmanager

from pydantic import BaseModel
from m_flow.shared.logging_utils import get_logger
from m_flow.llm.LLMGateway import LLMService

logger = get_logger("llm_call_tracker")

T = TypeVar("T", bound=BaseModel)

# Use ContextVar to track current call, ensuring concurrency safety
_current_call_var: contextvars.ContextVar[Optional["LLMCallRecord"]] = contextvars.ContextVar(
    "current_llm_call", default=None
)


@dataclass
class RetryRecord:
    """Single retry record."""

    attempt: int  # Attempt number (1-based)
    error_type: str  # Error type
    error_message: str  # Error message
    timestamp: float  # Timestamp
    duration_ms: float  # Duration of this attempt (ms)


@dataclass
class LLMCallRecord:
    """Single LLM call record."""

    module_name: str  # Module name
    start_time: float  # Start time
    end_time: Optional[float] = None  # End time
    success: bool = False  # Whether successful
    total_attempts: int = 0  # Total attempts
    retries: List[RetryRecord] = field(default_factory=list)  # Retry records
    final_error: Optional[str] = None  # Final error (if failed)
    input_length: int = 0  # Input length
    output_type: Optional[str] = None  # Output type

    @property
    def duration_ms(self) -> float:
        """Total duration (ms)."""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time) * 1000

    @property
    def retry_count(self) -> int:
        """Retry count (excluding first attempt)."""
        return max(0, self.total_attempts - 1)

    def to_log_dict(self) -> Dict[str, Any]:
        """Convert to log dictionary."""
        return {
            "module": self.module_name,
            "success": self.success,
            "total_attempts": self.total_attempts,
            "retry_count": self.retry_count,
            "duration_ms": round(self.duration_ms, 2),
            "input_length": self.input_length,
            "output_type": self.output_type,
            "final_error": self.final_error,
            "retries": [
                {
                    "attempt": r.attempt,
                    "error_type": r.error_type,
                    "error_message": r.error_message[:200] + "..." if len(r.error_message) > 200 else r.error_message,
                    "duration_ms": round(r.duration_ms, 2),
                }
                for r in self.retries
            ]
            if self.retries
            else None,
        }


class LLMCallTracker:
    """
    LLM call tracker - global singleton.

    Usage:
    ```python
    tracker = get_llm_tracker()

    # Method 1: Context manager
    async with tracker.track("facet_generation", text_input):
        result = await LLMService.extract_structured(...)

    # Method 2: Decorator
    @tracker.tracked("entity_selection")
    async def my_llm_call(...):
        ...

    # View statistics
    tracker.print_summary()
    ```
    """

    _instance: Optional["LLMCallTracker"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._records: List[LLMCallRecord] = []
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "LLMCallTracker":
        """Get global singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset (for testing)."""
        if cls._instance:
            cls._instance._records.clear()
        # ContextVar will automatically clean up after task ends, no manual reset needed

    @asynccontextmanager
    async def track(
        self,
        module_name: str,
        text_input: str = "",
        response_model: Optional[Type[BaseModel]] = None,
    ):
        """
        Context manager - track LLM call.

        Args:
            module_name: Module name (e.g., "facet_generation", "entity_selection")
            text_input: LLM input text
            response_model: Response model type

        Example:
            async with tracker.track("facet_generation", text_input, EpisodicWriteDraft):
                result = await LLMService.extract_structured(...)
        """
        record = LLMCallRecord(
            module_name=module_name,
            start_time=time.time(),
            input_length=len(text_input) if text_input else 0,
            output_type=response_model.__name__ if response_model else None,
        )

        # Use ContextVar to set current call, ensuring concurrency safety
        token = _current_call_var.set(record)

        try:
            yield record
            record.success = True
            record.total_attempts = max(1, record.total_attempts)
        except Exception as e:
            record.success = False
            record.final_error = f"{type(e).__name__}: {str(e)[:300]}"
            raise
        finally:
            record.end_time = time.time()
            async with self._lock:
                self._records.append(record)
            _current_call_var.reset(token)

            # Log
            log_data = record.to_log_dict()
            if record.success:
                if record.retry_count > 0:
                    logger.warning(
                        f"[LLM] {module_name} succeeded after {record.retry_count} retries",
                        extra=log_data,
                    )
                else:
                    logger.info(
                        f"[LLM] {module_name} succeeded (first attempt)",
                        extra={"module": module_name, "duration_ms": round(record.duration_ms, 2)},
                    )
            else:
                logger.error(
                    f"[LLM] {module_name} failed after {record.total_attempts} attempts: {record.final_error}",
                    extra=log_data,
                )

    def record_attempt(self, attempt: int, error: Optional[Exception] = None, duration_ms: float = 0):
        """
        Record an attempt (called by retry callback).
        Uses ContextVar to ensure concurrency safety, each async task has its own context.

        Args:
            attempt: Attempt number (1-based)
            error: If failed, record error
            duration_ms: Duration of this attempt
        """
        current_call = _current_call_var.get()
        if current_call is None:
            return

        current_call.total_attempts = attempt

        if error is not None:
            retry_record = RetryRecord(
                attempt=attempt,
                error_type=type(error).__name__,
                error_message=str(error),
                timestamp=time.time(),
                duration_ms=duration_ms,
            )
            current_call.retries.append(retry_record)

            logger.warning(
                f"[LLM] {current_call.module_name} attempt {attempt} failed: "
                f"{type(error).__name__}: {str(error)[:100]}..."
            )

    def get_records(self, module_name: Optional[str] = None) -> List[LLMCallRecord]:
        """Get records."""
        if module_name:
            return [r for r in self._records if r.module_name == module_name]
        return list(self._records)

    def get_summary(self) -> Dict[str, Any]:
        """Get statistical summary."""
        if not self._records:
            return {
                "total_calls": 0,
                "total_success": 0,
                "total_failures": 0,
                "total_retries": 0,
                "total_duration_ms": 0.0,
                "modules": {},
            }

        by_module: Dict[str, List[LLMCallRecord]] = {}
        for r in self._records:
            by_module.setdefault(r.module_name, []).append(r)

        summary = {
            "total_calls": len(self._records),
            "total_success": sum(1 for r in self._records if r.success),
            "total_failures": sum(1 for r in self._records if not r.success),
            "total_retries": sum(r.retry_count for r in self._records),
            "total_duration_ms": round(sum(r.duration_ms for r in self._records), 2),
            "modules": {},
        }

        for module_name, records in by_module.items():
            success_count = sum(1 for r in records if r.success)
            failure_count = sum(1 for r in records if not r.success)
            retry_count = sum(r.retry_count for r in records)
            total_duration = sum(r.duration_ms for r in records)
            avg_duration = total_duration / len(records) if records else 0

            # Collect all retry reasons
            retry_reasons: Dict[str, int] = {}
            for r in records:
                for retry in r.retries:
                    key = retry.error_type
                    retry_reasons[key] = retry_reasons.get(key, 0) + 1

            summary["modules"][module_name] = {
                "calls": len(records),
                "success": success_count,
                "failures": failure_count,
                "retry_count": retry_count,
                "avg_duration_ms": round(avg_duration, 2),
                "retry_reasons": retry_reasons if retry_reasons else None,
            }

        return summary

    def print_summary(self):
        """Print statistical summary to logger."""
        summary = self.get_summary()

        logger.info("=" * 70)
        logger.info("LLM Call Statistics Summary")
        logger.info("=" * 70)

        logger.info("Total calls: %d", summary["total_calls"])
        logger.info(
            "Success: %d, Failures: %d",
            summary["total_success"],
            summary["total_failures"],
        )
        logger.info("Total retries: %d", summary["total_retries"])
        logger.info("Total duration: %.2f ms", summary["total_duration_ms"])

        if summary.get("modules"):
            logger.info("By module:")
            logger.info("-" * 70)
            for module_name, stats in summary["modules"].items():
                logger.info("  [%s]", module_name)
                logger.info(
                    "    Calls: %d, Success: %d, Failures: %d",
                    stats["calls"],
                    stats["success"],
                    stats["failures"],
                )
                logger.info(
                    "    Retries: %d, Avg duration: %.2f ms",
                    stats["retry_count"],
                    stats["avg_duration_ms"],
                )
                if stats.get("retry_reasons"):
                    logger.info("    Retry reasons: %s", stats["retry_reasons"])

        logger.info("=" * 70)

    def log_summary(self):
        """Write statistical summary to log."""
        summary = self.get_summary()
        logger.info(
            f"[LLM Summary] total={summary['total_calls']}, "
            f"success={summary['total_success']}, failures={summary['total_failures']}, "
            f"retries={summary['total_retries']}, duration={summary['total_duration_ms']:.2f}ms"
        )

        for module_name, stats in summary.get("modules", {}).items():
            logger.info(
                f"[LLM Summary] {module_name}: calls={stats['calls']}, "
                f"success={stats['success']}, failures={stats['failures']}, "
                f"retries={stats['retry_count']}, avg_duration={stats['avg_duration_ms']:.2f}ms"
                + (f", retry_reasons={stats['retry_reasons']}" if stats.get("retry_reasons") else "")
            )


def get_llm_tracker() -> LLMCallTracker:
    """Get global LLM tracker."""
    return LLMCallTracker.get_instance()


# -----------------------------
# Helper function: tracked LLM call
# -----------------------------


async def tracked_llm_call(
    module_name: str,
    text_input: str,
    system_prompt: str,
    response_model: Type[T],
    max_retries: int = 3,
    **kwargs,
) -> T:
    """
    Tracked LLM call - wraps LLMService.extract_structured.

    Automatically records:
    - Call count
    - Retry count and reasons
    - Duration
    - Success/failure status

    Args:
        module_name: Module name (for logging and statistics)
        text_input: Input text
        system_prompt: System prompt
        response_model: Pydantic response model
        max_retries: Maximum retry count (default 3)
        **kwargs: Other parameters passed to LLMService

    Returns:
        LLM structured output result

    Example:
        result = await tracked_llm_call(
            module_name="facet_generation",
            text_input=prompt_text,
            system_prompt=system_prompt,
            response_model=EpisodicWriteDraft,
        )
    """
    tracker = get_llm_tracker()

    async with tracker.track(module_name, text_input, response_model):
        attempt = 0
        last_error = None

        while attempt < max_retries:
            attempt += 1
            attempt_start = time.time()

            try:
                result = await LLMService.extract_structured(
                    text_input=text_input,
                    system_prompt=system_prompt,
                    response_model=response_model,
                    **kwargs,
                )
                tracker.record_attempt(attempt)
                return result

            except Exception as e:
                duration_ms = (time.time() - attempt_start) * 1000
                tracker.record_attempt(attempt, error=e, duration_ms=duration_ms)
                last_error = e

                # Some errors should not be retried
                error_str = str(e).lower()
                if any(x in error_str for x in ["not found", "invalid api key", "unauthorized"]):
                    raise

                if attempt >= max_retries:
                    raise

                # Wait before retry
                await asyncio.sleep(min(2**attempt, 30))

        raise last_error or RuntimeError("LLM call failed after retries")
