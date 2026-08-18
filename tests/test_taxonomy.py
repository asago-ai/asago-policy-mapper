from pathlib import Path

import pytest

from asago_policy_mapper.taxonomy import load_custom_taxonomy


@pytest.fixture
def valid_taxonomy(tmp_path):
    f = tmp_path / "valid.yaml"
    f.write_text(
        """\
taxonomy:
  id: test-taxonomy
  name: Test Taxonomy

risks:
  - id: test-001
    name: First Risk
    description: >-
      A sufficiently detailed description of the first risk
      for retrieval quality.
    concern: Why this risk matters.
  - id: test-002
    name: Second Risk
    description: >-
      A sufficiently detailed description of the second risk
      for retrieval quality.
  - id: test-003
    name: Third Risk
    description: >-
      A sufficiently detailed description of the third risk
      for retrieval quality.
    risk_type: technical
"""
    )
    return f


def test_valid_load(valid_taxonomy):
    risks = load_custom_taxonomy(valid_taxonomy)
    assert len(risks) == 3
    assert risks[0].id == "test-001"
    assert risks[0].name == "First Risk"
    assert risks[0].isDefinedByTaxonomy == "test-taxonomy"
    assert risks[0].concern == "Why this risk matters."
    assert risks[0].type == "Risk"


def test_taxonomy_attribution(valid_taxonomy):
    risks = load_custom_taxonomy(valid_taxonomy)
    for r in risks:
        assert r.isDefinedByTaxonomy == "test-taxonomy"


def test_concern_defaults_empty(valid_taxonomy):
    risks = load_custom_taxonomy(valid_taxonomy)
    assert risks[1].concern == ""


def test_concern_populated(valid_taxonomy):
    risks = load_custom_taxonomy(valid_taxonomy)
    assert risks[0].concern == "Why this risk matters."


def test_risk_type_populated(valid_taxonomy):
    risks = load_custom_taxonomy(valid_taxonomy)
    assert risks[2].risk_type == "technical"


def test_risk_type_defaults_none(valid_taxonomy):
    risks = load_custom_taxonomy(valid_taxonomy)
    assert risks[0].risk_type is None


def test_missing_taxonomy_block(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text("risks:\n  - id: x\n    name: X\n    description: some description here\n")
    with pytest.raises(ValueError, match="missing the 'taxonomy' block"):
        load_custom_taxonomy(f)


def test_missing_taxonomy_id(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text("taxonomy:\n  name: Test\nrisks:\n  - id: x\n    name: X\n    description: some description here\n")
    with pytest.raises(ValueError, match="taxonomy.id"):
        load_custom_taxonomy(f)


def test_missing_taxonomy_name(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text("taxonomy:\n  id: test\nrisks:\n  - id: x\n    name: X\n    description: some description here\n")
    with pytest.raises(ValueError, match="taxonomy.name"):
        load_custom_taxonomy(f)


def test_missing_risks_key(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text("taxonomy:\n  id: test\n  name: Test\n")
    with pytest.raises(ValueError, match="missing the 'risks' key"):
        load_custom_taxonomy(f)


def test_empty_risks_list(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text("taxonomy:\n  id: test\n  name: Test\nrisks: []\n")
    with pytest.raises(ValueError, match="empty or invalid 'risks' list"):
        load_custom_taxonomy(f)


def test_missing_risk_description(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text("taxonomy:\n  id: test\n  name: Test\nrisks:\n  - id: x\n    name: X\n")
    with pytest.raises(ValueError, match="missing required field 'description'"):
        load_custom_taxonomy(f)


def test_missing_risk_name(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text("taxonomy:\n  id: test\n  name: Test\nrisks:\n  - id: x\n    description: some description here\n")
    with pytest.raises(ValueError, match="missing required field 'name'"):
        load_custom_taxonomy(f)


def test_missing_risk_id(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text("taxonomy:\n  id: test\n  name: Test\nrisks:\n  - name: X\n    description: some description here\n")
    with pytest.raises(ValueError, match="missing required field 'id'"):
        load_custom_taxonomy(f)


def test_empty_description(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text("taxonomy:\n  id: test\n  name: Test\nrisks:\n  - id: x\n    name: X\n    description: ''\n")
    with pytest.raises(ValueError, match="empty or non-string"):
        load_custom_taxonomy(f)


def test_duplicate_risk_ids(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text(
        """\
taxonomy:
  id: test
  name: Test
risks:
  - id: dupe-001
    name: First
    description: A sufficiently long description for the first risk
  - id: dupe-001
    name: Second
    description: A sufficiently long description for the second risk
"""
    )
    with pytest.raises(ValueError, match="Duplicate risk ID 'dupe-001'"):
        load_custom_taxonomy(f)


def test_short_description_warns(tmp_path, caplog):
    f = tmp_path / "short.yaml"
    f.write_text("taxonomy:\n  id: test\n  name: Test\nrisks:\n  - id: x\n    name: X\n    description: Short\n")
    import logging

    with caplog.at_level(logging.WARNING):
        risks = load_custom_taxonomy(f)
    assert len(risks) == 1
    assert "very short description" in caplog.text


def test_builtin_prefix_warns(tmp_path, caplog):
    f = tmp_path / "prefix.yaml"
    f.write_text(
        """\
taxonomy:
  id: test
  name: Test
risks:
  - id: atlas-custom-risk
    name: Custom Risk
    description: A sufficiently long description that uses a built-in prefix
"""
    )
    import logging

    with caplog.at_level(logging.WARNING):
        risks = load_custom_taxonomy(f)
    assert len(risks) == 1
    assert "built-in prefix" in caplog.text


def test_file_not_found():
    with pytest.raises(ValueError, match="not found"):
        load_custom_taxonomy(Path("/nonexistent/taxonomy.yaml"))


def test_invalid_yaml(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text(":\n  - ][invalid yaml")
    with pytest.raises(ValueError, match="Invalid YAML"):
        load_custom_taxonomy(f)


def test_example_file_loads():
    example = Path(__file__).parent.parent / "examples" / "custom-taxonomy-example.yaml"
    if not example.exists():
        pytest.skip("Example file not found")
    risks = load_custom_taxonomy(example)
    assert len(risks) == 5
    assert all(r.isDefinedByTaxonomy == "red-hat-ai-controls" for r in risks)
