"""Validate every TM-Spec artefact: well-formed and carries the core fields.

CPU-only (PyYAML only). The YAML specs live in tm-spec/; the prodromos case
artefacts are TM-Spec-in-JSON under data/cases/*.tm.json. Run: pytest tests/
"""
import json
from pathlib import Path
import yaml
import pytest

REPO = Path(__file__).resolve().parent.parent
YAML_SPECS = sorted(REPO.glob("tm-spec/*.tm.yaml"))
JSON_SPECS = sorted(REPO.glob("data/cases/*.tm.json"))


def test_specs_present():
    assert YAML_SPECS, "no tm-spec/*.tm.yaml found"
    assert JSON_SPECS, "no data/cases/*.tm.json found"


@pytest.mark.parametrize("path", YAML_SPECS, ids=lambda p: p.name)
def test_yaml_spec_core_fields(path):
    d = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert str(d.get("spec", "")).startswith("tm-spec/"), f"{path.name}: bad/missing spec"
    assert d.get("kind"), f"{path.name}: missing kind"
    assert d.get("id"), f"{path.name}: missing id"


@pytest.mark.parametrize("path", JSON_SPECS, ids=lambda p: p.name)
def test_json_case_core_fields(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    assert str(d.get("spec", "")).startswith("tm-spec/"), f"{path.name}: bad/missing spec"
    assert d.get("kind"), f"{path.name}: missing kind"
    assert d.get("id"), f"{path.name}: missing id"


def test_ids_unique():
    ids = []
    for p in YAML_SPECS:
        ids.append(yaml.safe_load(p.read_text(encoding="utf-8")).get("id"))
    for p in JSON_SPECS:
        ids.append(json.loads(p.read_text(encoding="utf-8")).get("id"))
    ids = [i for i in ids if i]
    assert len(ids) == len(set(ids)), f"duplicate spec ids: {[i for i in ids if ids.count(i) > 1]}"
