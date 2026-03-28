"""Tests for kata data integrity and model validation."""

from pathlib import Path

import yaml

from quantum_katas.models.kata import Kata, KataDetail, KataSummary
from quantum_katas.services.kata_registry import (
    get_all_katas,
    get_kata_by_id,
    get_kata_raw,
    reset_cache,
)

KATAS_DIR = Path(__file__).resolve().parent.parent / "src" / "quantum_katas" / "data" / "katas"

REQUIRED_FIELDS = {
    "id",
    "title",
    "description",
    "difficulty",
    "category",
    "template_code",
    "solution_code",
    "validation_code",
}


class TestKataDataIntegrity:
    """Verify that all YAML kata files have required fields and valid data."""

    def setup_method(self):
        reset_cache()

    def test_yaml_files_exist(self):
        yaml_files = list(KATAS_DIR.glob("*.yaml"))
        assert len(yaml_files) == 10, f"Expected 10 kata YAML files, found {len(yaml_files)}"

    def test_all_katas_have_required_fields(self):
        for yaml_file in sorted(KATAS_DIR.glob("*.yaml")):
            raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            for field in REQUIRED_FIELDS:
                assert field in raw, f"{yaml_file.name} is missing required field: {field}"

    def test_difficulty_range(self):
        for yaml_file in sorted(KATAS_DIR.glob("*.yaml")):
            raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            difficulty = raw["difficulty"]
            assert 1 <= difficulty <= 10, f"{yaml_file.name} has invalid difficulty: {difficulty}"

    def test_unique_ids(self):
        ids = []
        for yaml_file in sorted(KATAS_DIR.glob("*.yaml")):
            raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            ids.append(raw["id"])
        assert len(ids) == len(set(ids)), f"Duplicate kata IDs found: {ids}"

    def test_unique_difficulties(self):
        difficulties = []
        for yaml_file in sorted(KATAS_DIR.glob("*.yaml")):
            raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            difficulties.append(raw["difficulty"])
        assert len(difficulties) == len(set(difficulties)), f"Duplicate difficulties: {difficulties}"

    def test_categories_valid(self):
        valid_categories = {"basics", "entanglement", "algorithms"}
        for yaml_file in sorted(KATAS_DIR.glob("*.yaml")):
            raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            assert raw["category"] in valid_categories, f"{yaml_file.name} has invalid category: {raw['category']}"

    def test_hints_are_lists_with_three_items(self):
        for yaml_file in sorted(KATAS_DIR.glob("*.yaml")):
            raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            hints = raw.get("hints", [])
            assert isinstance(hints, list), f"{yaml_file.name}: hints must be a list"
            assert len(hints) == 3, f"{yaml_file.name} should have 3 hints, has {len(hints)}"

    def test_prerequisites_reference_valid_ids(self):
        all_ids = set()
        all_prereqs: dict[str, list[str]] = {}
        for yaml_file in sorted(KATAS_DIR.glob("*.yaml")):
            raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            all_ids.add(raw["id"])
            all_prereqs[raw["id"]] = raw.get("prerequisites", [])

        for kata_id, prereqs in all_prereqs.items():
            for prereq in prereqs:
                assert prereq in all_ids, f"Kata '{kata_id}' references unknown prerequisite: {prereq}"

    def test_template_code_has_placeholder(self):
        for yaml_file in sorted(KATAS_DIR.glob("*.yaml")):
            raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            assert "YOUR CODE HERE" in raw["template_code"], f"{yaml_file.name} template_code missing placeholder"

    def test_first_kata_has_no_prerequisites(self):
        first_file = KATAS_DIR / "01_single_qubit.yaml"
        raw = yaml.safe_load(first_file.read_text(encoding="utf-8"))
        assert raw.get("prerequisites", []) == [], "First kata should have no prerequisites"


class TestKataModel:
    """Tests for the Kata dataclass."""

    def test_kata_creation(self):
        kata = Kata(
            id="test-kata",
            title="Test",
            description="A test kata",
            difficulty=1,
            category="basics",
            template_code="# template",
            solution_code="# solution",
            validation_code="# validation",
            hints=["hint1"],
            prerequisites=[],
            explanation="explanation",
        )
        assert kata.id == "test-kata"
        assert kata.difficulty == 1

    def test_kata_summary(self):
        summary = KataSummary(
            id="test-kata",
            title="Test",
            difficulty=1,
            category="basics",
            prerequisites=[],
        )
        assert summary.id == "test-kata"

    def test_kata_detail_excludes_solution_and_validation(self):
        detail = KataDetail(
            id="test-kata",
            title="Test",
            description="A test kata",
            difficulty=1,
            category="basics",
            template_code="# template",
            hints=["hint1"],
            prerequisites=[],
            explanation="explanation",
        )
        assert not hasattr(detail, "solution_code")
        assert not hasattr(detail, "validation_code")


class TestKataRegistry:
    """Tests for the kata registry service."""

    def setup_method(self):
        reset_cache()

    def test_get_all_katas_returns_ten(self):
        katas = get_all_katas()
        assert len(katas) == 10

    def test_get_all_katas_ordered_by_difficulty(self):
        katas = get_all_katas()
        difficulties = [k.difficulty for k in katas]
        assert difficulties == sorted(difficulties)

    def test_get_kata_by_id_found(self):
        detail = get_kata_by_id("01-single-qubit")
        assert detail is not None
        assert detail.id == "01-single-qubit"
        assert detail.title == "量子ビットの基礎"

    def test_get_kata_by_id_not_found(self):
        detail = get_kata_by_id("nonexistent-kata")
        assert detail is None

    def test_get_kata_raw_includes_solution(self):
        kata = get_kata_raw("01-single-qubit")
        assert kata is not None
        assert kata.solution_code != ""

    def test_get_kata_detail_excludes_solution_and_validation(self):
        detail = get_kata_by_id("01-single-qubit")
        assert detail is not None
        assert not hasattr(detail, "solution_code")
        assert not hasattr(detail, "validation_code")
