"""Kata data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Kata:
    """A single quantum computing kata (exercise).

    Each kata represents one step in the curriculum, containing
    a coding exercise with template, solution, and validation logic.
    """

    id: str
    """Unique identifier, e.g. '01-single-qubit'."""

    title: str
    """Display title, e.g. '量子ビットの基礎'."""

    description: str
    """Kata description in Markdown."""

    difficulty: int
    """Difficulty level from 1 (easiest) to 10 (hardest)."""

    category: str
    """Category: 'basics', 'entanglement', or 'algorithms'."""

    template_code: str
    """Code template with placeholder comments for the learner to fill in."""

    solution_code: str
    """Reference solution code."""

    validation_code: str
    """Code that validates whether the user's submission is correct."""

    hints: list[str] = field(default_factory=list)
    """Progressive hints (up to 3 levels)."""

    prerequisites: list[str] = field(default_factory=list)
    """IDs of prerequisite katas that should be completed first."""

    explanation: str = ""
    """Detailed explanation of the concept in Markdown."""


@dataclass(frozen=True)
class KataSummary:
    """Lightweight kata representation for list endpoints."""

    id: str
    title: str
    difficulty: int
    category: str
    prerequisites: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class KataDetail:
    """Kata detail for the detail endpoint (excludes solution_code and validation_code)."""

    id: str
    title: str
    description: str
    difficulty: int
    category: str
    template_code: str
    hints: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    explanation: str = ""


@dataclass(frozen=True)
class ValidateRequest:
    """Request body for code validation."""

    code: str


@dataclass(frozen=True)
class ValidateResponse:
    """Response body for code validation."""

    passed: bool
    message: str
    stdout: str = ""
    stderr: str = ""
