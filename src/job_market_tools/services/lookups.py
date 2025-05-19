# src/job_market_tools/services/lookups.py
"""
Tiny helpers that guarantee a lookup row exists and return the model instance.

Add new helpers here any time you introduce another lookup table.
"""
from __future__ import annotations

import importlib
from typing import Type

from django.db import transaction
from django.db.models import Model

from ..db_schema.database import (           # adjust if you later split models
    Countries,
    Languages,
    LanguageLevels,
    ExperienceLevels,
    WorkplaceTypes,
    WorkingTimes,
    Currencies,
    EmploymentUnits,
    EmploymentTypes,
    JobBoardWebsites,
    SkillLevels
)

# ---------------------------------------------------------------------------
# Generic helper
# ---------------------------------------------------------------------------
def _get_or_create(model: Type[Model], pk_field: str, value: str, **defaults):
    """
    Idempotent fetch-or-insert for any “single-column PK” lookup table.
    """
    kwargs = {pk_field: value}
    with transaction.atomic():
        obj, _ = model.objects.get_or_create(defaults=defaults, **kwargs)  # type: ignore[arg-type]
    return obj


# ---------------------------------------------------------------------------
# Concrete helpers
# ---------------------------------------------------------------------------
# Country -------------------------------------------------------------------
try:
    _pc = importlib.import_module("pycountry")
except ModuleNotFoundError:      # `pycountry` optional
    _pc = None                   # type: ignore[assignment]


def country(code: str | None):
    if not code:
        return None
    code = code.upper()
    name = code
    if _pc:
        try:
            name = _pc.countries.get(alpha_2=code).name  # type: ignore[attr-defined]
        except Exception:
            pass
    return _get_or_create(Countries, "code", code, name=name)


# Language ------------------------------------------------------------------
def language(code: str):
    return _get_or_create(Languages, "code", code.lower(), name=code.lower())


def language_level(level: str | None):
    if level is None:
        return None
    return _get_or_create(LanguageLevels, "level", level.upper())


# Experience / workplace / working time -------------------------------------
def experience_level(level: str):
    return _get_or_create(ExperienceLevels, "level", level.capitalize())


def workplace_type(value: str):
    return _get_or_create(WorkplaceTypes, "type", value.lower())


def working_time(value: str):
    return _get_or_create(WorkingTimes, "type", value.lower())


# Currency / employment units / employment types ----------------------------
def currency(code: str):
    return _get_or_create(Currencies, "code", code.upper(), symbol=code, name=code)


def employment_unit(unit: str):
    return _get_or_create(EmploymentUnits, "unit", unit.lower())


def employment_type(etype: str):
    return _get_or_create(EmploymentTypes, "type", etype.lower())

# Skill levels --------------------------------------------------------------
def skill_level(value: int | None):
    return _get_or_create(SkillLevels, "level", int(value))


# Job-board websites --------------------------------------------------------
def job_board(name: str, website_url: str | None = None):
    """
    Make sure the `job_board_websites` row exists and return it.
    `website_url` is optional – pass it the first time if you have it.
    """
    defaults = {"website_url": website_url or f"https://{name}"}
    return _get_or_create(JobBoardWebsites, "name", name, **defaults)
