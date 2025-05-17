# src/job_market_tools/__main__.py
from scraper import ScraperManager
import time
import sys

if __name__ == "__main__":
    mgr = ScraperManager()
    mgr.register("justjoin")
    mgr.start("justjoin", 10)

    try:
        # keep the main thread alive so we can Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping scraper…")
        mgr.stop("justjoin")
        sys.exit(0)