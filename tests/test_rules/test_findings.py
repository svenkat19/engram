import pytest

from engram.rules.findings import Finding, FindingType


def test_finding_is_frozen():
    f = Finding(FindingType.TOUCHES_PATH, "src/auth/jwt.py")
    with pytest.raises(AttributeError):
        f.value = "other"  # type: ignore[misc]


def test_finding_equality():
    a = Finding(FindingType.TOUCHES_PATH, "src/auth/jwt.py")
    b = Finding(FindingType.TOUCHES_PATH, "src/auth/jwt.py")
    assert a == b


def test_finding_default_confidence():
    f = Finding(FindingType.REFERENCES_ISSUE, "321")
    assert f.confidence == 1.0
