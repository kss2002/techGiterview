import json
import uuid

import pytest

from app.core.config import settings
from app.core.session_token import (
    TokenValidationError,
    issue_analysis_token,
    issue_interview_token,
    parse_ws_subprotocol_token,
    to_http_exception,
    verify_token,
)


@pytest.fixture(autouse=True)
def reset_token_settings(monkeypatch):
    monkeypatch.setattr(settings, "token_signing_keys_json", None, raising=False)
    monkeypatch.setattr(settings, "token_active_kid", "default", raising=False)
    monkeypatch.setattr(settings, "secret_key", "test-secret", raising=False)
    monkeypatch.setattr(settings, "token_issuer", "techgiterview", raising=False)
    monkeypatch.setattr(settings, "token_audience", "techgiterview-backend", raising=False)
    monkeypatch.setattr(settings, "analysis_token_ttl_seconds", 1800, raising=False)
    monkeypatch.setattr(settings, "interview_token_ttl_seconds", 10800, raising=False)


def test_analysis_token_roundtrip():
    analysis_id = str(uuid.uuid4())
    token = issue_analysis_token(analysis_id)

    claims = verify_token(
        token=token,
        expected_scope="analysis",
        expected_analysis_id=analysis_id,
    )
    assert claims["analysis_id"] == analysis_id
    assert claims["scope"] == "analysis"


def test_interview_scope_misuse_returns_401():
    analysis_id = str(uuid.uuid4())
    interview_id = str(uuid.uuid4())
    analysis_token = issue_analysis_token(analysis_id)

    with pytest.raises(TokenValidationError) as exc:
        verify_token(
            token=analysis_token,
            expected_scope="interview",
            expected_interview_id=interview_id,
        )

    http_exc = to_http_exception(exc.value)
    assert http_exc.status_code == 401


def test_valid_token_with_ownership_mismatch_returns_404():
    analysis_id = str(uuid.uuid4())
    other_analysis_id = str(uuid.uuid4())
    token = issue_analysis_token(analysis_id)

    with pytest.raises(TokenValidationError) as exc:
        verify_token(
            token=token,
            expected_scope="analysis",
            expected_analysis_id=other_analysis_id,
        )

    http_exc = to_http_exception(exc.value)
    assert http_exc.status_code == 404


def test_secret_rotation_accepts_previous_key(monkeypatch):
    keyset = json.dumps([
        {"kid": "k2", "secret": "new-secret"},
        {"kid": "k1", "secret": "old-secret"},
    ])
    monkeypatch.setattr(settings, "token_signing_keys_json", keyset, raising=False)

    analysis_id = str(uuid.uuid4())
    interview_id = str(uuid.uuid4())

    monkeypatch.setattr(settings, "token_active_kid", "k1", raising=False)
    old_token = issue_interview_token(analysis_id, interview_id)

    monkeypatch.setattr(settings, "token_active_kid", "k2", raising=False)
    claims = verify_token(
        token=old_token,
        expected_scope="interview",
        expected_analysis_id=analysis_id,
        expected_interview_id=interview_id,
    )
    assert claims["interview_id"] == interview_id


def test_invalid_keyset_configuration_fails_closed(monkeypatch):
    monkeypatch.setattr(settings, "token_signing_keys_json", "{not-json", raising=False)

    with pytest.raises(TokenValidationError):
        issue_analysis_token(str(uuid.uuid4()))


def test_ws_subprotocol_parsing_rules():
    token = "abc.def.ghi"
    assert parse_ws_subprotocol_token(f"auth.{token}, interview.v1") == token
    assert parse_ws_subprotocol_token(f"interview.v1, auth.{token}") == token

    with pytest.raises(TokenValidationError):
        parse_ws_subprotocol_token("auth.a,auth.b,interview.v1")

    with pytest.raises(TokenValidationError):
        parse_ws_subprotocol_token(f"auth.{token}")
