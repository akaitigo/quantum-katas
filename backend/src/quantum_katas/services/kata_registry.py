"""Kata registry service — loads and provides access to kata definitions.

Reads YAML files from the data/katas/ directory and provides
lookup methods for the kata catalog.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from quantum_katas.models.kata import Kata, KataDetail, KataSummary

logger = logging.getLogger(__name__)

_KATAS_DIR = Path(__file__).resolve().parent.parent / "data" / "katas"

_kata_cache: dict[str, Kata] | None = None


def _load_katas() -> dict[str, Kata]:
    """Load all kata YAML files from the data directory.

    Returns a dict keyed by kata id, sorted by difficulty.
    """
    katas: dict[str, Kata] = {}
    yaml_files = sorted(_KATAS_DIR.glob("*.yaml"))

    if not yaml_files:
        logger.warning("No kata YAML files found in %s", _KATAS_DIR)
        return katas

    for yaml_file in yaml_files:
        raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        kata = Kata(
            id=raw["id"],
            title=raw["title"],
            description=raw["description"],
            difficulty=raw["difficulty"],
            category=raw["category"],
            template_code=raw["template_code"],
            solution_code=raw["solution_code"],
            validation_code=raw["validation_code"],
            hints=raw.get("hints", []),
            prerequisites=raw.get("prerequisites", []),
            explanation=raw.get("explanation", ""),
        )
        katas[kata.id] = kata

    logger.info("Loaded %d katas", len(katas))
    return katas


def _get_cache() -> dict[str, Kata]:
    """Get or initialize the kata cache."""
    global _kata_cache  # noqa: PLW0603
    if _kata_cache is None:
        _kata_cache = _load_katas()
    return _kata_cache


def get_all_katas() -> list[KataSummary]:
    """Return a list of all katas as summaries, ordered by difficulty."""
    cache = _get_cache()
    return [
        KataSummary(
            id=kata.id,
            title=kata.title,
            difficulty=kata.difficulty,
            category=kata.category,
            prerequisites=list(kata.prerequisites),
        )
        for kata in sorted(cache.values(), key=lambda k: k.difficulty)
    ]


def get_kata_by_id(kata_id: str) -> KataDetail | None:
    """Return a single kata detail by ID (excludes solution_code)."""
    cache = _get_cache()
    kata = cache.get(kata_id)
    if kata is None:
        return None
    return KataDetail(
        id=kata.id,
        title=kata.title,
        description=kata.description,
        difficulty=kata.difficulty,
        category=kata.category,
        template_code=kata.template_code,
        validation_code=kata.validation_code,
        hints=list(kata.hints),
        prerequisites=list(kata.prerequisites),
        explanation=kata.explanation,
    )


def get_kata_raw(kata_id: str) -> Kata | None:
    """Return the full kata (including solution_code) for internal use."""
    cache = _get_cache()
    return cache.get(kata_id)


def reset_cache() -> None:
    """Clear the kata cache (useful for testing)."""
    global _kata_cache  # noqa: PLW0603
    _kata_cache = None
