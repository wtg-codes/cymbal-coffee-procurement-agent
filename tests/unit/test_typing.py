# Copyright 2026 Google LLC

import pytest
from pydantic import ValidationError

from app.app_utils.typing import Feedback


def test_feedback_valid():
    """Feedback model should accept valid score and text."""
    fb = Feedback(score=5, text="Great!")
    assert fb.score == 5
    assert fb.text == "Great!"
    assert fb.log_type == "feedback"
    assert fb.service_name == "cymbal-coffee-procurement-agent"


def test_feedback_float_score():
    """Feedback should accept float scores."""
    fb = Feedback(score=4.5)
    assert fb.score == 4.5


def test_feedback_defaults():
    """Default text should be empty string, IDs should be auto-generated UUIDs."""
    fb = Feedback(score=3)
    assert fb.text == ""
    assert len(fb.user_id) > 0
    assert len(fb.session_id) > 0
    # UUIDs should be different each time
    fb2 = Feedback(score=3)
    assert fb.user_id != fb2.user_id


def test_feedback_service_name_literal():
    """service_name is a Literal and must be cymbal-coffee-procurement-agent."""
    fb = Feedback(score=1)
    assert fb.service_name == "cymbal-coffee-procurement-agent"


def test_feedback_model_dump():
    """model_dump should produce a dict suitable for structured logging."""
    fb = Feedback(score=5, text="test")
    d = fb.model_dump()
    assert "score" in d
    assert "log_type" in d
    assert "service_name" in d
    assert "user_id" in d
    assert "session_id" in d
