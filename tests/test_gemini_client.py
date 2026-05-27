from agent_debate.llm.gemini_client import _friendly_gemini_error


def test_friendly_gemini_error_summarizes_quota_payload() -> None:
    error = (
        "429 RESOURCE_EXHAUSTED. Quota exceeded for metric: input_token_count. "
        "Please retry in 40.739s. {'huge': 'payload'}"
    )
    message = _friendly_gemini_error(error, "gemini-2.5-flash")
    assert message.startswith("Gemini quota/rate limit exceeded")
    assert "40.739s" in message
    assert "huge" not in message


def test_friendly_gemini_error_summarizes_unavailable_model() -> None:
    error = (
        "404 NOT_FOUND. This model models/gemini-2.0-flash is no longer available "
        "to new users."
    )
    message = _friendly_gemini_error(error, "gemini-2.0-flash")
    assert message.startswith("Gemini model gemini-2.0-flash is unavailable")
    assert "gemini-2.5-flash" in message
