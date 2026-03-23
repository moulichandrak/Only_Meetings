"""Feedback Handler - retry logic with exponential backoff."""

import asyncio
import logging
from typing import Callable, Any

logger = logging.getLogger("agent.feedback")


class FeedbackHandler:
    """Handles retries with exponential backoff for API calls."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute an async function with retry logic.

        Args:
            func: Async callable to execute
            *args, **kwargs: Arguments to pass to the function

        Returns:
            Result of the function call

        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Attempt {attempt}/{self.max_retries} for {func.__name__}")
                result = await func(*args, **kwargs)
                if attempt > 1:
                    logger.info(f"Succeeded on attempt {attempt}")
                return result

            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt}/{self.max_retries} failed: {str(e)}")

                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)

        error_msg = f"All {self.max_retries} attempts failed. Last error: {str(last_exception)}"
        logger.error(error_msg)
        raise Exception(error_msg)


# Singleton
feedback_handler = FeedbackHandler()
