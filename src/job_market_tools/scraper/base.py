# src/job_market_tools/scraper/base.py
import threading
import time
from abc import ABC, abstractmethod

SCRAPER_REGISTRY: dict[str, type["BaseScraper"]] = {}

def register_scraper(name: str):
    """Class decorator to register a scraper by name."""
    def decorator(cls):
        SCRAPER_REGISTRY[name] = cls
        return cls
    return decorator

class BaseScraper(ABC):
    """Abstract base: all scrapers must implement start/stop/fetch."""
    def __init__(self, **kwargs):
        self._thread = None
        self._stop_event = threading.Event()
        self.config = kwargs

    @abstractmethod
    def fetch_offers_page(self, page: int = 1):
        """Fetch a page of offers. Must be implemented by subclasses."""
        ...
    
    @abstractmethod
    def fetch_offer_details(self, offer_ids: list[str]):
        """Fetch details for a list of offers. Must be implemented by subclasses."""
        ...

    @abstractmethod
    def loop(self):
        """Main loop for the scraper. Must be implemented by subclasses."""
        ...

    def _run_loop(self, interval: float):
        while not self._stop_event.is_set():
            try:
                self.loop()
            except Exception as e:
                # you could hook in logging here
                print(f"[{self.__class__.__name__}] error: {e}")
            finally:
                time.sleep(interval)

    def start(self, interval: float = 60):
        """Spawn a background thread that fetches every `interval` seconds."""
        if self._thread and self._thread.is_alive():
            print(f"{self.__class__.__name__} already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop, args=(interval,), daemon=False
        )
        self._thread.start()
        print(f"Started {self.__class__.__name__}")

    def stop(self):
        """Signal the loop to stop and wait for thread to finish."""
        if not self._thread:
            return
        self._stop_event.set()
        self._thread.join()
        print(f"Stopped {self.__class__.__name__}")

    def status(self) -> str:
        return "running" if self._thread and self._thread.is_alive() else "stopped"
