# src/job_market_tools/scraper/base.py
import threading
import time
from abc import ABC, abstractmethod
import traceback

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
        # ─────────── progress / debug output ───────────
        # `verbose` defaults to **True** so you get progress messages
        # out of the box.  Set `verbose=False` when you start a scraper
        # if you want it silent.
        self.verbose: bool = kwargs.get("verbose", True)

# ------------------------------------------------------------------— helpers
    def _log(self, msg: str, *args, **kwargs) -> None:
        """Centralised printf-style debug printer."""
        if not self.verbose:
            return
        name = self.config.get("name", self.__class__.__name__)
        print(f"[{name}] " + msg.format(*args, **kwargs))

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
                # extract the traceback object
                tb = e.__traceback__
                # walk to the last frame in this traceback
                while tb.tb_next:
                    tb = tb.tb_next
                lineno   = tb.tb_lineno
                filename = tb.tb_frame.f_code.co_filename
                funcname = tb.tb_frame.f_code.co_name

                self._log(
                    "ERROR in {func} at {file}:{line}: {err!r}",
                    func=funcname, file=filename, line=lineno, err=e
                )
                # optionally, print full traceback
                traceback.print_exc()
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
        self._log("Started scraper (interval={i}s)", i=interval)

    def stop(self):
        """Signal the loop to stop and wait for thread to finish."""
        if not self._thread:
            return
        self._stop_event.set()
        self._thread.join()
        self._log("Stopped scraper")

    def status(self) -> str:
        return "running" if self._thread and self._thread.is_alive() else "stopped"
