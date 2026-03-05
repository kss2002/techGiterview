"""
Stateless capability tokens for analysis/interview ownership checks.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import HTTPException

from app.core.config import settings


TOKEN_ALLOWED_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


class TokenValidationError(Exception):
    def __init__(self, reason: str, not_found: bool = False):
        super().__init__(reason)
        self.reason = reason
        self.not_found = not_found


@dataclass(frozen=True)
class TokenKeys:
    active_kid: str
    keys_by_kid: Dict[str, str]


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _json_dumps(data: Dict[str, Any]) -> bytes:
    return json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _normalize_uuid(value: str) -> str:
    return str(uuid.UUID(str(value)))


def _load_keys() -> TokenKeys:
    # token_signing_keys_json format:
    # [{"kid":"k2","secret":"..."},{"kid":"k1","secret":"..."}]
    # or {"k2":"...", "k1":"..."}
    keys_by_kid: Dict[str, str] = {}
    raw = settings.token_signing_keys_json

    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                for kid, secret in parsed.items():
                    if kid and secret:
                        keys_by_kid[str(kid)] = str(secret)
            elif isinstance(parsed, list):
                for item in parsed:
                    if not isinstance(item, dict):
                        continue
                    kid = item.get("kid")
                    secret = item.get("secret")
                    if kid and secret:
                        keys_by_kid[str(kid)] = str(secret)
            else:
                raise TokenValidationError("invalid_keyset_config")
        except TokenValidationError:
            raise
        except Exception as exc:
            raise TokenValidationError("invalid_keyset_config") from exc

        if not keys_by_kid:
            raise TokenValidationError("empty_keyset_config")
    else:
        keys_by_kid = {settings.token_active_kid: settings.secret_key}

    active_kid = settings.token_active_kid if settings.token_active_kid in keys_by_kid else next(iter(keys_by_kid.keys()))
    return TokenKeys(active_kid=active_kid, keys_by_kid=keys_by_kid)


def _sign(header_b64: str, payload_b64: str, secret: str) -> str:
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return _b64url_encode(signature)


def issue_token(
    scope: str,
    ttl_seconds: int,
    analysis_id: Optional[str] = None,
    interview_id: Optional[str] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    keys = _load_keys()
    now = int(time.time())

    claims: Dict[str, Any] = {
        "iss": settings.token_issuer,
        "aud": settings.token_audience,
        "ver": 1,
        "scope": scope,
        "iat": now,
        "nbf": now - 5,
        "exp": now + max(1, int(ttl_seconds)),
    }
    if analysis_id:
        claims["analysis_id"] = _normalize_uuid(analysis_id)
    if interview_id:
        claims["interview_id"] = _normalize_uuid(interview_id)
    if extra_claims:
        claims.update(extra_claims)

    header = {
        "alg": "HS256",
        "typ": "JWT",
        "kid": keys.active_kid,
    }
    header_b64 = _b64url_encode(_json_dumps(header))
    payload_b64 = _b64url_encode(_json_dumps(claims))
    signature_b64 = _sign(header_b64, payload_b64, keys.keys_by_kid[keys.active_kid])

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def _validate_token_shape(token: str) -> None:
    if not token or not isinstance(token, str):
        raise TokenValidationError("missing_token")
    if not TOKEN_ALLOWED_PATTERN.fullmatch(token):
        raise TokenValidationError("invalid_token_chars")
    if token.count(".") != 2:
        raise TokenValidationError("invalid_token_shape")


def verify_token(
    token: str,
    expected_scope: str,
    expected_analysis_id: Optional[str] = None,
    expected_interview_id: Optional[str] = None,
) -> Dict[str, Any]:
    _validate_token_shape(token)
    header_b64, payload_b64, signature_b64 = token.split(".")

    try:
        header = json.loads(_b64url_decode(header_b64).decode("utf-8"))
        claims = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception as exc:
        raise TokenValidationError("decode_failed") from exc

    kid = header.get("kid")
    if not kid:
        raise TokenValidationError("missing_kid")

    keys = _load_keys()
    secret = keys.keys_by_kid.get(str(kid))
    if not secret:
        raise TokenValidationError("unknown_kid")

    expected_sig = _sign(header_b64, payload_b64, secret)
    if not hmac.compare_digest(signature_b64, expected_sig):
        raise TokenValidationError("bad_signature")

    now = int(time.time())
    exp = int(claims.get("exp", 0))
    nbf = int(claims.get("nbf", 0))
    if now >= exp:
        raise TokenValidationError("expired_token")
    if now < nbf:
        raise TokenValidationError("token_not_yet_valid")

    if claims.get("iss") != settings.token_issuer or claims.get("aud") != settings.token_audience:
        raise TokenValidationError("invalid_issuer_or_audience")

    if claims.get("scope") != expected_scope:
        raise TokenValidationError("invalid_scope")

    if expected_analysis_id:
        claim_analysis_id = claims.get("analysis_id")
        if not claim_analysis_id:
            raise TokenValidationError("missing_analysis_claim")
        try:
            if _normalize_uuid(claim_analysis_id) != _normalize_uuid(expected_analysis_id):
                raise TokenValidationError("analysis_mismatch", not_found=True)
        except ValueError as exc:
            raise TokenValidationError("invalid_analysis_claim") from exc

    if expected_interview_id:
        claim_interview_id = claims.get("interview_id")
        if not claim_interview_id:
            raise TokenValidationError("missing_interview_claim")
        try:
            if _normalize_uuid(claim_interview_id) != _normalize_uuid(expected_interview_id):
                raise TokenValidationError("interview_mismatch", not_found=True)
        except ValueError as exc:
            raise TokenValidationError("invalid_interview_claim") from exc

    return claims


def issue_analysis_token(analysis_id: str) -> str:
    return issue_token(
        scope="analysis",
        ttl_seconds=settings.analysis_token_ttl_seconds,
        analysis_id=analysis_id,
    )


def issue_interview_token(analysis_id: str, interview_id: str) -> str:
    return issue_token(
        scope="interview",
        ttl_seconds=settings.interview_token_ttl_seconds,
        analysis_id=analysis_id,
        interview_id=interview_id,
    )


def issue_ws_query_token(analysis_id: str, interview_id: str) -> str:
    ttl = max(30, min(120, int(settings.ws_query_token_ttl_seconds)))
    return issue_token(
        scope="ws-query",
        ttl_seconds=ttl,
        analysis_id=analysis_id,
        interview_id=interview_id,
    )


def parse_ws_subprotocol_token(raw_header: Optional[str]) -> Optional[str]:
    if not raw_header:
        return None

    parts = [part.strip() for part in raw_header.split(",") if part.strip()]
    if "interview.v1" not in parts:
        raise TokenValidationError("missing_interview_protocol")

    auth_parts = [part for part in parts if part.startswith("auth.")]
    if len(auth_parts) != 1:
        raise TokenValidationError("invalid_auth_protocol_count")

    token = auth_parts[0][len("auth."):]
    if not token:
        raise TokenValidationError("empty_auth_protocol_token")
    if not TOKEN_ALLOWED_PATTERN.fullmatch(token):
        raise TokenValidationError("invalid_auth_protocol_token")
    return token


def ws_query_token_from_param(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    token = value.strip()
    if not TOKEN_ALLOWED_PATTERN.fullmatch(token):
        raise TokenValidationError("invalid_query_token")
    return token


def to_http_exception(exc: TokenValidationError) -> HTTPException:
    # 401: token invalid/missing/expired/scope error
    # 404: token valid but ownership mismatch
    if exc.not_found:
        return HTTPException(status_code=404, detail="Resource not found")
    return HTTPException(status_code=401, detail="Unauthorized")
