import uuid

import pytest

from app.api.questions import QuestionResponse, _save_questions_to_db
import app.api.questions as questions_module


class _FakeResult:
    rowcount = 1


class _FakeConnection:
    def __init__(self):
        self.calls = []
        self.committed = False

    def execute(self, statement, params=None):
        self.calls.append((statement, params or {}))
        return _FakeResult()

    def commit(self):
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeEngine:
    def __init__(self):
        self.conn = _FakeConnection()

    def connect(self):
        return self.conn


@pytest.mark.asyncio
async def test_save_questions_uses_bound_parameters(monkeypatch):
    fake_engine = _FakeEngine()
    monkeypatch.setattr(questions_module, "engine", fake_engine)

    safe_id = str(uuid.uuid4())
    malicious_id = "bad-id'); DROP TABLE interview_questions;--"
    questions = [
        QuestionResponse(
            id=safe_id,
            type="technical",
            question="safe question",
            difficulty="medium",
        ),
        QuestionResponse(
            id=malicious_id,
            type="technical",
            question="unsafe question",
            difficulty="medium",
        ),
    ]

    await _save_questions_to_db(str(uuid.uuid4()), questions)

    statements = [str(call[0]) for call in fake_engine.conn.calls]
    delete_calls = [
        call for call in fake_engine.conn.calls
        if "DELETE FROM interview_questions WHERE analysis_id = :analysis_id" in str(call[0])
    ]
    insert_calls = [
        call for call in fake_engine.conn.calls
        if "INSERT INTO interview_questions" in str(call[0])
    ]

    assert len(delete_calls) == 1
    assert len(insert_calls) == 2

    # SQL 본문에 악의적 값이 직접 삽입되지 않고 바인딩 파라미터로 전달되는지 확인
    assert malicious_id not in " ".join(statements)
    assert any(call[1]["id"] == safe_id for call in insert_calls)
    assert any(call[1]["id"] == malicious_id for call in insert_calls)
    assert fake_engine.conn.committed is True
