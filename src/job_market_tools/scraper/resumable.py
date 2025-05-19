# src/job_market_tools/scraper/resumable.py
import math, time
from datetime import datetime, timezone as dt_timezone
from typing import List, Dict
from django.utils import timezone

from ..db_schema.database import(
    Offers,
    ScraperState,
)
from ..services.offer_ingest import create_offer
from .base import BaseScraper

class ResumablePagedScraper(BaseScraper):
    """
    Sub-classes only have to provide three trivial methods:

      * `_listing_uid(raw_listing: dict) -> str`
      * `_listing_published_at(raw_listing: dict) -> datetime`
      * `_total_pages() -> int`

    All the heavy lifting (binary search, resume, monitor) is done here.
    """

    # ------------------------------------------------------------------— helpers
    @staticmethod
    def _aware(dt: datetime) -> datetime:
        """
        Ensure *dt* is timezone-aware (UTC).  Treat naive values as UTC.
        """
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, dt_timezone.utc)
        return dt
    # BOARD IMPLEMENTATION MUST OVERRIDE ↓↓↓
    def _listing_uid(self, listing: Dict) -> str: ...
    def _listing_published_at(self, listing: Dict) -> datetime: ...
    def _total_pages(self) -> int: ...
    # ↑↑↑-----------------------------------------------------------------------

    # Optional: override if detail calls are expensive
    def _need_details(self, listing: Dict) -> bool:
        """Return False if the info in the listing row alone is enough."""
        return True
    # ------------------------------------------------------------------— public API
    def loop(self) -> None:
        if not hasattr(self, "_state"):
            self._state = self._load_state()

        if self._state.mode == "backfill":
            self._run_backfill()
        else:
            self._run_monitor()

    # ------------------------------------------------------------------— state
    def _load_state(self) -> ScraperState:
        jb = self._job_board_obj()                              # JobBoardWebsites row
        state, _ = ScraperState.objects.get_or_create(
            board_name=jb,                                      # ← PK column name
            defaults={                                          # first run
                "last_uid":     "",
                "last_seen_at": self._aware(datetime.min),
                "mode":         "backfill",
                "updated_at":   timezone.now(),
            },
        )
        # --- normalise whatever came from the DB -----------------
        state.last_seen_at = self._aware(state.last_seen_at or datetime.min)
        
        return state

    def _save_state(
        self,
        newest_uid: str,
        published_at: datetime,
        mode: str | None = None,
    ):
        self._state.last_uid     = newest_uid
        self._state.last_seen_at = published_at
        if mode:
            self._state.mode = mode
        self._state.updated_at = timezone.now()
        self._state.save(
            update_fields=["last_uid", "last_seen_at", "mode", "updated_at"]
        )

    def _job_board_obj(self):
        from ..services.lookups import job_board
        return job_board(self.config["name"])

    # ------------------------------------------------------------------— main loops
    # 1) Initial/Resume – binary search to the first page containing duplicates
    def _run_backfill(self):
        self._log("Backfill started – finding oldest unseen offers")
        last_page = self._total_pages()
        self._log("Board reports {p} total pages", p=last_page)
        lo, hi = 1, last_page
        first_dup_page = last_page + 1              # “sentinel” – no dup found yet

        # -------- binary search
        while lo <= hi:
            mid = (lo + hi) // 2
            self._log("Binary-search probe page {p}", p=mid)
            lst = self.fetch_offers_page(mid)
            if self._page_has_duplicates(lst):
                first_dup_page = mid
                hi = mid - 1
            else:
                lo = mid + 1

        # -------- ingest all pages *newer* than the duplicate page
        for page in range(first_dup_page - 1, 0, -1):
            self._log("Ingesting historical page {p}", p=page)
            self._ingest_page(page)

        # we are caught up – flip to monitor mode
        self._save_state(self._state.last_uid, self._state.last_seen_at, mode="monitor")
        self._log("Backfill complete – switching to monitor mode")

    # 2) Regular watch – only page 1 every loop
    def _run_monitor(self):
        self._log("Monitor tick – refreshing page 1")
        lst = self.fetch_offers_page(1)
        newest_published = self._listing_published_at(lst[0])
        newest_uid       = self._listing_uid(lst[0])
        self._log("Newest listing UID={u} published at {t}",
                    u=newest_uid, t=newest_published.isoformat())

        for offer in lst:
            uid = self._listing_uid(offer)
            if self._is_duplicate(uid):
                self._log("Reached duplicate UID={u} – page processed", u=uid)
                break
            self._ingest_single_listing(offer)

        # update the watermark even if no new offers were ingested
        self._save_state(newest_uid, newest_published)

    # ------------------------------------------------------------------— ingestion helpers
    def _page_has_duplicates(self, listings: List[Dict]) -> bool:
        return any(self._is_duplicate(self._listing_uid(l)) for l in listings)

    def _is_duplicate(self, uid: str) -> bool:
        return Offers.objects.filter(raw_json__slug=uid).exists()   # adjust when you store uid

    def _ingest_page(self, page: int):
        for listing in self.fetch_offers_page(page):
            uid = self._listing_uid(listing)
            if self._is_duplicate(uid):
                self._log("Skip duplicate UID={u} on page {p}", u=uid, p=page)
                continue
            self._ingest_single_listing(listing)

    def _ingest_single_listing(self, listing: Dict):
        uid = self._listing_uid(listing)
        self._log("Ingesting UID={u}", u=uid)
        published_at = self._listing_published_at(listing)
        details = listing
        if self._need_details(listing):
            details = self.fetch_offer_details([uid])[0]

        # --------------------- send to ingest service
        create_offer(self._make_offer_payload(details))

        # update in-memory watermark so _save_state has newest values
        if published_at > self._state.last_seen_at:
            self._state.last_uid     = uid
            self._state.last_seen_at = published_at

    # BOARD IMPLEMENTATION MUST OVERRIDE ↓↓↓
    def _make_offer_payload(self, details: Dict) -> Dict:
        """
        Convert the data returned by the board into the dict expected by
        `services.offer_ingest.create_offer`.  Board-specific, so not supplied
        here.
        """
        ...
