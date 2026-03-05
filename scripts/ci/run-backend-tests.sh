#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PYTHONPATH=src/backend uv run pytest \
  tests/test_session_token_security.py \
  tests/test_question_sql_safety.py \
  tests/test_access_log_redaction.py \
  tests/test_github_analyzer.py \
  tests/test_integration.py \
  tests/test_content_based_questions.py \
  tests/test_dynamic_weights_system.py \
  tests/run_content_questions_test.py \
  tests/test_integration_performance.py \
  -q
