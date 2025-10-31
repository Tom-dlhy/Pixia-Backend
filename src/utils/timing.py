"""
Minimal timing utility for performance tracing.

Provides a context manager to measure and log execution time of code blocks.
"""

import logging
import time

logger = logging.getLogger(__name__)


class Timer:
    """
    Context manager for measuring execution time.
    """

    def __init__(self, label: str):
        """
        Initialize timer with label.

        Args:
            label: Description of the operation being timed
        """
        self.label = label
        self.start_time = None
        self.elapsed = None

    def __enter__(self):
        """Start timing on context entry."""
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        """Log elapsed time on context exit."""
        if self.start_time is None:
            return
        else:
            self.elapsed = time.time() - self.start_time
        logger.info(f"⏱️  {self.label}: {self.elapsed:.2f}s")

    def get_elapsed(self) -> float:
        """
        Get elapsed time in seconds.

        Returns current elapsed time or 0.0 if timer not started.

        Returns:
            Elapsed time in seconds
        """
        if self.start_time is None:
            return 0.0
        return self.elapsed or (time.time() - self.start_time)
