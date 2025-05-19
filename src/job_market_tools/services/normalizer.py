# src/job_market_tools/services/normalizer.py
from __future__ import annotations

import re
import unicodedata
from typing import Tuple, Optional, List

from django.db import transaction
from django.contrib.postgres.search import TrigramSimilarity
from rapidfuzz import fuzz

from ..db_schema.database import Companies, Skills, OfferCategories
from .lookups import country

# ——————————————————————————————————————————————————————————————
# Shared helpers
# ——————————————————————————————————————————————————————————————
_CORP_SUFFIXES = re.compile(
    r"\b(sa|sp\.? z\.? o\.? o\.?|llc|inc\.?|ltd\.?|gmbh|s\.?r\.?l\.?|pty|co\.?)\b",
    flags=re.IGNORECASE,
)
_WS = re.compile(r"\s+")


def _strip_accents(text: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )


def _clean_name(raw: str) -> str:
    t = _strip_accents(raw)
    t = _CORP_SUFFIXES.sub("", t)        # drop “sp. z o.o.” etc.
    t = re.sub(r"[^\w\s\-]", " ", t)     # punctuation → space
    t = _WS.sub(" ", t)                  # collapse whitespace
    return t.strip().lower()


# ——————————————————————————————————————————————————————————————
# Company
# ——————————————————————————————————————————————————————————————
def normalize_company(raw_name: str, country_code: str | None = None) -> Companies:
    """
    Return a `Companies` instance representing `raw_name`
    (create both the company and the country row if missing).
    """
    cleaned = _clean_name(raw_name)
    if not cleaned:
        raise ValueError("Company name cannot be empty after cleaning")

    country_obj = country(country_code)

    # 1 — candidates from DB
    qs = Companies.objects.annotate(sim=TrigramSimilarity("name", cleaned))
    if country_obj:
        qs = qs.filter(country_code=country_obj)
    qs = qs.filter(sim__gte=0.3).order_by("-sim")[:20]

    # 2 — RapidFuzz re-score
    best: Tuple[Optional[Companies], int] = (None, 0)
    for comp in qs:
        score = fuzz.token_set_ratio(cleaned, _clean_name(comp.name))
        if score > best[1]:
            best = (comp, score)

    if best[0] and best[1] >= 90:
        return best[0]

    # 3 — insert
    with transaction.atomic():
        company, _ = Companies.objects.get_or_create(
            name=raw_name.strip(),
            defaults={"country_code": country_obj},
        )
    return company


# ——————————————————————————————————————————————————————————————
# Skills & categories
# ——————————————————————————————————————————————————————————————
def _generic_normalize(model, raw_name: str, threshold: int = 80):
    cleaned = _clean_name(raw_name)
    qs = (
        model.objects.annotate(sim=TrigramSimilarity("name", cleaned))
        .filter(sim__gte=0.3)
        .order_by("-sim")[:20]
    )

    best: Tuple[Optional[model], int] = (None, 0)
    for obj in qs:
        score = fuzz.token_set_ratio(cleaned, _clean_name(obj.name))
        if score > best[1]:
            best = (obj, score)

    if best[0] and best[1] >= threshold:
        return best[0]

    with transaction.atomic():
        obj, _ = model.objects.get_or_create(name=raw_name.strip())
    return obj


def normalize_skill(raw_skill: str) -> Skills:
    return _generic_normalize(Skills, raw_skill, threshold=80)


def normalize_category(raw_cat: str) -> OfferCategories:
    return _generic_normalize(OfferCategories, raw_cat, threshold=80)
