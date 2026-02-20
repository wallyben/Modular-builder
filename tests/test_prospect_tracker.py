from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import modules.prospecting.tracker as tracker_mod


@pytest.fixture(autouse=True)
def tmp_tracker(tmp_path, monkeypatch):
    """Redirect tracker to a temp file for each test."""
    tmp_file = tmp_path / "outreach.jsonl"
    monkeypatch.setattr(tracker_mod, "_TRACKER_PATH", tmp_file)


def test_ensure_data_dir_creates_parent(tmp_path, monkeypatch):
    nested = tmp_path / "a" / "b" / "outreach.jsonl"
    monkeypatch.setattr(tracker_mod, "_TRACKER_PATH", nested)
    tracker_mod.ensure_data_dir()
    assert nested.parent.exists()


def test_record_outreach_writes_jsonl():
    tracker_mod.record_outreach("Acme FM", "acme@example.com", "drafted", notes="Initial contact")
    records = tracker_mod.list_outreach()
    assert len(records) == 1
    assert records[0]["company_name"] == "Acme FM"
    assert records[0]["status"] == "drafted"


def test_record_multiple_entries():
    tracker_mod.record_outreach("Acme FM", None, "drafted")
    tracker_mod.record_outreach("BetaFM Ltd", None, "sent")
    records = tracker_mod.list_outreach()
    assert len(records) == 2


def test_list_outreach_status_filter():
    tracker_mod.record_outreach("Acme FM", None, "drafted")
    tracker_mod.record_outreach("BetaFM Ltd", None, "sent")
    tracker_mod.record_outreach("GammaFM", None, "drafted")
    drafted = tracker_mod.list_outreach(status_filter="drafted")
    assert len(drafted) == 2
    sent = tracker_mod.list_outreach(status_filter="sent")
    assert len(sent) == 1


def test_list_outreach_empty_when_no_file():
    records = tracker_mod.list_outreach()
    assert records == []


def test_recorded_at_is_present():
    tracker_mod.record_outreach("TestCo", None, "drafted")
    records = tracker_mod.list_outreach()
    assert "recorded_at" in records[0]


def test_notes_stored():
    tracker_mod.record_outreach("TestCo", None, "drafted", notes="Called on 20 Feb")
    records = tracker_mod.list_outreach()
    assert records[0]["notes"] == "Called on 20 Feb"
