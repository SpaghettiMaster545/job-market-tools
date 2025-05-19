# src/job_market_tools/services/offer_ingest.py
"""
Offer ingestion service – *with full-payload logging*.

* Every call to ``create_offer`` is logged at DEBUG level.
* On any ``IntegrityError`` the whole input payload is logged with stack-trace,
  then re-raised.  Same for any other exception.
* The helper ``_location_obj`` still logs its own payload on failure.

Add a logger for ``job_market_tools.services.offer_ingest`` in your
Django ``LOGGING`` settings (console handler is enough) to see the output.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Mapping

from django.db import transaction
from django.db.utils import IntegrityError

from ..db_schema.database import (
    Offers,
    OffersCategories,
    OffersSkills,
    OffersOptionalSkills,
    OffersLanguages,
    OffersLocations,
    OfferSalaries,
    Locations,
)
from .normalizer import normalize_company, normalize_skill, normalize_category
from .lookups import (
    job_board,
    experience_level,
    workplace_type,
    working_time,
    language,
    language_level,
    country,
    currency,
    employment_unit,
    employment_type,
    skill_level,
)

# ──────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────
@transaction.atomic
def create_offer(data: Mapping[str, Any]) -> Offers:  # noqa: C901  (complexity OK)
    """
    Upsert one offer & all related rows.

    *Creates* any missing lookup rows on-the-fly.
    On failure, the full ``data`` payload is logged for easy debugging.
    """
    # record every call (you can mute DEBUG in prod)
    logger.debug("create_offer payload=%s", data)

    try:
        # ----- local helpers -------------------------------------------------
        def _dt(val: str | datetime) -> datetime:
            return val if isinstance(val, datetime) else datetime.fromisoformat(val)

        comp = normalize_company(data["company_name"], data.get("company_country_code"))
        jb = job_board(data["job_board_name"])

        # ----- core Offer row ------------------------------------------------
        offer, _ = Offers.objects.update_or_create(
            job_board_name=jb,
            apply_url=data["apply_url"],
            defaults=dict(
                company=comp,
                title=data["title"],
                description=data.get("description", ""),
                experience_level=experience_level(data["experience_level"]),
                workplace_type=workplace_type(data["workplace_type"]),
                working_time=working_time(data["working_time"]),
                publish_date=_dt(data["publish_date"]),
                expire_date=_dt(data["expire_date"]),
                raw_json=data.get("raw_json") or {},
            ),
        )

        # --------------------------------------------------------------------
        # 1) Categories  (UNIQUE: offer_id, category_name FK)
        # --------------------------------------------------------------------
        OffersCategories.objects.filter(offer=offer).delete()
        seen_cats: set[str] = set()
        for raw in data.get("categories", []):
            cat = normalize_category(raw)
            if cat.name in seen_cats:
                continue
            OffersCategories.objects.create(offer=offer, category_name=cat)
            seen_cats.add(cat.name)

        # --------------------------------------------------------------------
        # 2) Required skills  (UNIQUE: offer_id, skill_name FK)
        # --------------------------------------------------------------------
        OffersSkills.objects.filter(offer=offer).delete()
        seen_req: set[str] = set()
        for sk in data.get("skills_required", []):
            sk_obj = normalize_skill(sk["name"])
            if sk_obj.name in seen_req:
                continue
            OffersSkills.objects.create(
                offer=offer,
                skill_name=sk_obj,
                skill_level=skill_level(sk.get("level")),
            )
            seen_req.add(sk_obj.name)

        # --------------------------------------------------------------------
        # 3) Optional skills  (UNIQUE: offer_id, skill_name FK)
        # --------------------------------------------------------------------
        OffersOptionalSkills.objects.filter(offer=offer).delete()
        seen_opt: set[str] = set()
        for sk in data.get("skills_optional", []):
            sk_obj = normalize_skill(sk["name"])
            if sk_obj.name in seen_opt:
                continue
            OffersOptionalSkills.objects.create(
                offer=offer,
                skill_name=sk_obj,
                skill_level=skill_level(sk.get("level") or 1),
            )
            seen_opt.add(sk_obj.name)

        # --------------------------------------------------------------------
        # 4) Languages  (UNIQUE: offer_id, language_code FK)
        # --------------------------------------------------------------------
        OffersLanguages.objects.filter(offer=offer).delete()
        seen_lang: set[str] = set()
        for lang_rec in data.get("languages", []):
            code = lang_rec["code"].lower()
            if code in seen_lang:
                continue
            OffersLanguages.objects.create(
                offer=offer,
                language_code=language(code),
                language_level=language_level(lang_rec.get("level")),
            )
            seen_lang.add(code)

        # --------------------------------------------------------------------
        # 5) Locations  (UNIQUE: offer_id, location_id FK)
        # --------------------------------------------------------------------
        OffersLocations.objects.filter(offer=offer).delete()
        seen_loc: set[int] = set()
        for loc in data.get("locations", []):
            loc_obj = _location_obj(loc)
            if loc_obj.id in seen_loc:
                continue
            OffersLocations.objects.create(offer=offer, location=loc_obj)
            seen_loc.add(loc_obj.id)

        # --------------------------------------------------------------------
        # 6) Salaries (delete → insert, duplicates allowed)
        # --------------------------------------------------------------------
        OfferSalaries.objects.filter(offer=offer).delete()
        for sal in data.get("salaries", []):
            OfferSalaries.objects.create(
                offer=offer,
                currency=currency(sal["currency"]),
                salary_min=sal["min"],
                salary_max=sal.get("max"),
                is_gross=sal["is_gross"],
                unit=employment_unit(sal["unit"]),
                type=employment_type(sal["type"]),
            )

        return offer

    # ── log & re-raise on IntegrityError ────────────────────────────────────
    except IntegrityError:
        logger.exception("IntegrityError in create_offer | payload=%s", data)
        raise

    # ── catch-all for any other surprises ───────────────────────────────────
    except Exception:
        logger.exception("Unexpected error in create_offer | payload=%s", data)
        raise


# ──────────────────────────────────────────────────────────
# Helper for geo locations – still logs its own payload
# ──────────────────────────────────────────────────────────
def _location_obj(raw: Dict[str, Any]) -> Locations:
    """
    Fetch or create a ``Locations`` instance with defensive logging.
    """
    try:
        return Locations.objects.get_or_create(
            country_code=country(raw.get("country_code")),
            city=raw["city"],
            street=raw.get("street"),
            latitude=raw["latitude"],
            longitude=raw["longitude"],
        )[0]
    except IntegrityError:
        logger.exception("IntegrityError in _location_obj | payload=%s", raw)
        raise
