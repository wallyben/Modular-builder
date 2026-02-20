from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from modules.prospecting.url_fetch import fetch_award_text

_SAMPLE_HTML = """\
<!DOCTYPE html>
<html>
<head>
  <title>Contract Award Notice</title>
  <style>body { font-family: Arial; }</style>
  <script>console.log("ignore me");</script>
</head>
<body>
  <h1>Contract Award Notice</h1>
  <p>Contracting Authority: Cork City Council</p>
  <p>Contract Title: Provision of Cleaning and Facilities Management Services</p>
  <p>Awarded to: CleanPro Ireland Ltd</p>
  <p>Value: EUR 1,200,000</p>
  <p>Award Date: 01 February 2024</p>
  <script>alert("also ignore");</script>
</body>
</html>
"""


def _mock_response(status_code: int = 200, text: str = _SAMPLE_HTML) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    return resp


def test_returns_string_on_200():
    with patch("modules.prospecting.url_fetch.requests.get", return_value=_mock_response()):
        result = fetch_award_text("http://example.com/award")
    assert isinstance(result, str)
    assert len(result) > 0


def test_script_tags_removed():
    with patch("modules.prospecting.url_fetch.requests.get", return_value=_mock_response()):
        result = fetch_award_text("http://example.com/award")
    assert "console.log" not in result
    assert "alert" not in result


def test_style_tags_removed():
    with patch("modules.prospecting.url_fetch.requests.get", return_value=_mock_response()):
        result = fetch_award_text("http://example.com/award")
    assert "font-family" not in result


def test_visible_content_preserved():
    with patch("modules.prospecting.url_fetch.requests.get", return_value=_mock_response()):
        result = fetch_award_text("http://example.com/award")
    assert "Cork City Council" in result
    assert "CleanPro Ireland Ltd" in result
    assert "Cleaning and Facilities Management" in result


def test_raises_on_non_200():
    with patch("modules.prospecting.url_fetch.requests.get", return_value=_mock_response(404)):
        with pytest.raises(RuntimeError, match="HTTP 404"):
            fetch_award_text("http://example.com/missing")


def test_raises_on_500():
    with patch("modules.prospecting.url_fetch.requests.get", return_value=_mock_response(500)):
        with pytest.raises(RuntimeError, match="HTTP 500"):
            fetch_award_text("http://example.com/error")


def test_empty_html_returns_empty_string():
    with patch("modules.prospecting.url_fetch.requests.get", return_value=_mock_response(text="<html></html>")):
        result = fetch_award_text("http://example.com/empty")
    assert isinstance(result, str)


def test_fetched_text_works_with_extract():
    """Integration: cleaned URL text feeds correctly into extract_award_notice."""
    from modules.prospecting.awards_extract import extract_award_notice
    with patch("modules.prospecting.url_fetch.requests.get", return_value=_mock_response()):
        text = fetch_award_text("http://example.com/award")
    notice = extract_award_notice(text)
    assert notice.source == "manual-paste"
    assert notice.winner_name is not None
    assert "CleanPro" in notice.winner_name
