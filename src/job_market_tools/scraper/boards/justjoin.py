# src/job_market_tools/scraper/justjoin.py
from ..base import BaseScraper, register_scraper
import requests

@register_scraper("justjoin")
class JustJoinScraper(BaseScraper):
    OFFERS_PAGE_URL = "https://api.justjoin.it/v2/user-panel/offers"
    OFFER_PAGE_URL = "https://api.justjoin.it/v1/offers/"

    def fetch_offers_page(self, page: int = 1):
        params = {"page": page} | self.config.get("params", {}).copy()
        headers = {
            "Accept": "application/json",
            "version": "2"
        } | self.config.get("headers", {}).copy()
        print(f"Fetching JustJoin offers page {page} with params: {params} and headers: {headers}\n")
        resp = requests.get(self.OFFERS_PAGE_URL, params=params, headers=headers)
        print(resp.status_code)
        resp.raise_for_status()
        offers = resp.json()
        offers = offers.get("data", [])
        print(f"Fetched offers from JustJoin {offers}\n")
        return offers

    def fetch_offer_details(self, offer_ids: list[str]):
        def fetch_offer(offer_id: str):
            url = self.OFFER_PAGE_URL + offer_id
            headers = {
                "Accept": "application/json",
                "version": "2"
            } | self.config.get("headers", {}).copy()
            print(f"Fetching JustJoin offer details for {offer_id} with headers: {headers}\n")
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()
        for offer_id in offer_ids:
            offer_details = fetch_offer(offer_id)
            print(f"Fetched details for offer {offer_id}: {offer_details}\n")
        return offer_details

    def loop(self):
        # This method would contain the main loop logic for the scraper.
        # For now, we'll just print a message.
        print("Running JustJoin scraper loop")
        offers = self.fetch_offers_page()
        offer_ids = [offer["slug"] for offer in offers]
        print(f"Fetched offer IDs: {offer_ids}")
        offers_details = self.fetch_offer_details(offer_ids)
        print(f"Fetched offer details: {offers_details}")
        print("JustJoin scraper loop completed")
