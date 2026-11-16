"""
Test cases for data.py (parse_payload validation)
Member 5
"""
import pytest
from deadline_solver.data import parse_payload

def test_parse_payload_duplicate_id():
    payload = {
        "start_date": "2026-11-16",
        "assignments": [
            {"id": "T1", "name": "Math HW", "estimated_hours": 2, "deadline": "2026-11-20"},
            {"id": "T1", "name": "Python Lab", "estimated_hours": 1.5, "deadline": "2026-11-21"}
        ]
    }
    with pytest.raises(ValueError, match="Duplicate task ID"):
        parse_payload(payload)

def test_parse_payload_invalid_dependency():
    payload = {
        "start_date": "2026-11-16",
        "assignments": [
            {"id": "T1", "name": "Essay", "estimated_hours": 3, "deadline": "2026-11-20", "depends_on": ["T99"]}
        ]
    }
    with pytest.raises(ValueError, match="depends on non-existent task id"):
        parse_payload(payload)

def test_parse_payload_negative_hours():
    payload = {
        "start_date": "2026-11-16",
        "assignments": [
            {"id": "T1", "name": "Reading", "estimated_hours": -1, "deadline": "2026-11-20"}
        ]
    }
    with pytest.raises(ValueError, match="estimated_hours must be > 0"):
        parse_payload(payload)
