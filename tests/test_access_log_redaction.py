from app.core.logging_filters import _redact_url_query


def test_redacts_sensitive_query_params():
    url = "/ws/interview/123?tk=abc.def.ghi&other=1"
    redacted = _redact_url_query(url)
    assert "tk=%2A%2A%2A" in redacted
    assert "other=1" in redacted
    assert "abc.def.ghi" not in redacted


def test_handles_encoded_query_values():
    url = "/ws/interview/123?tk=abc%2Edef%2Dghi"
    redacted = _redact_url_query(url)
    assert "tk=%2A%2A%2A" in redacted
