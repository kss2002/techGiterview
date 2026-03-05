"""
Logging helpers to redact sensitive query params from access logs.
"""

from __future__ import annotations

import logging
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


SENSITIVE_QUERY_KEYS = {"tk", "token", "analysis_token", "interview_token"}


def _redact_url_query(raw_path: str) -> str:
    if "?" not in raw_path:
        return raw_path

    try:
        split = urlsplit(raw_path)
        if not split.query:
            return raw_path

        redacted_pairs = []
        for key, value in parse_qsl(split.query, keep_blank_values=True):
            if key.lower() in SENSITIVE_QUERY_KEYS and value:
                redacted_pairs.append((key, "***"))
            else:
                redacted_pairs.append((key, value))

        new_query = urlencode(redacted_pairs, doseq=True)
        return urlunsplit((split.scheme, split.netloc, split.path, new_query, split.fragment))
    except Exception:
        return raw_path


class UvicornAccessRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        args = getattr(record, "args", None)
        if not isinstance(args, tuple) or len(args) < 5:
            return True

        args_list = list(args)
        path = args_list[2]
        if isinstance(path, str):
            args_list[2] = _redact_url_query(path)
            record.args = tuple(args_list)
        return True


def configure_access_log_redaction() -> None:
    logger = logging.getLogger("uvicorn.access")
    if any(isinstance(f, UvicornAccessRedactionFilter) for f in logger.filters):
        return
    logger.addFilter(UvicornAccessRedactionFilter())
