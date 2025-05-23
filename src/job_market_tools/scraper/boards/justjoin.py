# src/job_market_tools/scraper/boards/justjoin.py
from datetime import datetime
import requests
from ..resumable import ResumablePagedScraper
from ..base import register_scraper

@register_scraper("justjoin")
class JustJoinScraper(ResumablePagedScraper):
    OFFERS_PAGE_URL = "https://api.justjoin.it/v2/user-panel/offers"
    OFFER_PAGE_URL  = "https://api.justjoin.it/v1/offers/"

    # ---------------------- ResumablePagedScraper hooks ------------------
    def _listing_uid(self, listing):              # ← unique per offer
        return listing["slug"]

    def _listing_published_at(self, listing):
        # API returns ISO-8601 with timezone, e.g. "2025-05-18T07:12:02.123Z"
        return datetime.fromisoformat(listing["publishedAt"].replace("Z", "+00:00"))

    def _total_pages(self):
        resp = requests.get(
            self.OFFERS_PAGE_URL,
            params={"page": 1, "sortBy": "published", "orderBy": "DESC"},
            headers={"Accept": "application/json", "version": "2"}
        )
        resp.raise_for_status()
        return resp.json()["meta"]["totalPages"]

    def _make_offer_payload(self, offer):
        return {
            "job_board_name": "justjoin",
            "company_name":      offer["companyName"],
            "company_country_code": offer["countryCode"],
            "title":             offer["title"],
            "description":       offer["body"],
            "apply_url":         offer["applyUrl"] or f"https://justjoin.it/job-offer/{offer['slug']}",
            "experience_level":  offer["experienceLevel"]["label"],
            "workplace_type":    offer["workplaceType"]["label"],
            "working_time":      offer["workingTime"]["label"],
            "publish_date":      offer["publishedAt"],
            "expire_date":       offer["expiredAt"],
            "categories":        [offer["category"]["name"]],
            "skills_required":   [{"name": s["name"], "level": s.get("level")} for s in offer["requiredSkills"]],
            "skills_optional":   [{"name": s["name"], "level": s.get("level")} for s in offer["niceToHaveSkills"]],
            "languages":         [{"code": l["code"], "level": l.get("level")} for l in offer["languages"]],
            "locations":         [{
                "city": offer["city"],
                "country_code": offer["countryCode"],
                "latitude": offer["latitude"],
                "longitude": offer["longitude"],
                "street": offer["street"],
            }],
            "salaries":          [{
                "currency": sal["currency"],
                "min":      sal["from"] if sal["from"] else -1,
                "max":      sal["to"],
                "is_gross": sal["gross"],
                "unit":     sal["unit"],
                "type":     sal["type"],
            } for sal in offer["employmentTypes"]],
            "raw_json": offer,
        }

    # ---------------------- board-specific fetchers ----------------------
    def fetch_offers_page(self, page: int = 1):
        params  = {"page": page, "sort": "newest"} | self.config.get("params", {})
        headers = {"Accept": "application/json", "version": "2"} | self.config.get("headers", {})
        resp = requests.get(self.OFFERS_PAGE_URL, params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()["data"]

    def fetch_offer_details(self, offer_ids):
        headers = {"Accept": "application/json", "version": "2"} | self.config.get("headers", {})
        out = []
        for oid in offer_ids:
            resp = requests.get(self.OFFER_PAGE_URL + oid, headers=headers)
            resp.raise_for_status()
            out.append(resp.json())
        return out
