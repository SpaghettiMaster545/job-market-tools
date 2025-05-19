# src/job_market_tools/scraper/manager.py
from .base import BaseScraper, SCRAPER_REGISTRY

class ScraperManager:
    def __init__(self):
        self._instances: dict[str, BaseScraper] = {}

    def register(self, name: str, **config):
        cls = SCRAPER_REGISTRY.get(name)
        if not cls:
            raise ValueError(f"No scraper registered under '{name}'")
        config.setdefault("name", name)
        self._instances[name] = cls(**config)

    def start(self, name: str, interval: float = 60):
        scraper = self._instances.get(name)
        if not scraper:
            raise ValueError(f"Scraper '{name}' not registered")
        scraper.start(interval)

    def stop(self, name: str):
        scraper = self._instances.get(name)
        if not scraper:
            return
        scraper.stop()

    def status(self, name: str) -> str:
        scraper = self._instances.get(name)
        return scraper.status() if scraper else "not registered"

    def list_scrapers(self) -> list[str]:
        return list(self._instances.keys())
