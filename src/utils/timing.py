import time
import logging

logger = logging.getLogger(__name__)


class Timer:
    """Context manager pour mesurer le temps d'exécution."""

    def __init__(self, label: str):
        self.label = label
        self.start_time = None
        self.elapsed = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.elapsed = time.time() - self.start_time
        logger.info(f"⏱️  {self.label}: {self.elapsed:.2f}s")

    def get_elapsed(self) -> float:
        """Retourne le temps écoulé en secondes."""
        if self.start_time is None:
            return 0.0
        return self.elapsed or (time.time() - self.start_time)
