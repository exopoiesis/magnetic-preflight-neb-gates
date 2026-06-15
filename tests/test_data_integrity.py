"""Data-integrity smoke: every bundled JSON parses, and the key result/verdict
artefacts carry the expected top-level structure. CPU-only, stdlib only.
"""
import json
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parent.parent
ALL_JSON = sorted(REPO.glob("data/**/*.json"))


def test_some_data_present():
    assert ALL_JSON, "no data/**/*.json found"


@pytest.mark.parametrize("path", ALL_JSON, ids=lambda p: str(p.relative_to(REPO)))
def test_json_parses(path):
    json.loads(path.read_text(encoding="utf-8"))   # raises on corruption


def test_battery_repro_results_structure():
    f = REPO / "data" / "battery" / "battery_repro_neb_results.json"
    if not f.exists():
        pytest.skip("battery results not present")
    d = json.loads(f.read_text(encoding="utf-8"))
    # a non-empty container of reproduction results
    assert d, "battery reproduction results are empty"
    assert isinstance(d, (list, dict))
