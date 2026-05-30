from agent_debate.llm.mock_client import MockLLMClient
from agent_debate.tools.web_search import WebSearchTool


def test_mock_client_generates_role_and_round_specific_text() -> None:
    client = MockLLMClient()
    pro = client.complete(
        "You are the pro debate agent. Stance: Argue that Pilates is better than Yoga.\n"
        "Topic: Pilates is better than Yoga.\nCurrent judge instruction: Round 2:",
        model="mock",
        timeout=1,
    )
    con = client.complete(
        "You are the con debate agent. Stance: Argue that Yoga is better than Pilates.\n"
        "Topic: Pilates is better than Yoga.\nCurrent judge instruction: Round 2:",
        model="mock",
        timeout=1,
    )
    assert "Pro round 2" in pro.content
    assert "Con round 2" in con.content
    assert "Pilates" in pro.content
    assert "Yoga" in con.content
    assert "software" not in pro.content.lower()
    assert pro.content != con.content


def test_mock_client_generates_default_topic_specific_text() -> None:
    client = MockLLMClient()
    pro = client.complete(
        "You are the pro debate agent. Stance: Support the proposition.\n"
        "Topic: Should universities require students to use AI agents in software "
        "engineering courses.\nCurrent judge instruction: Round 1:",
        model="mock",
        timeout=1,
    )
    con = client.complete(
        "You are the con debate agent. Stance: Oppose the proposition.\n"
        "Topic: Should universities require students to use AI agents in software "
        "engineering courses.\nCurrent judge instruction: Round 1:",
        model="mock",
        timeout=1,
    )
    assert "AI agents" in pro.content
    assert "fundamentals" in con.content
    assert "the proposition better satisfies" not in pro.content


def test_mock_judge_scores_latest_arguments_not_fixed_pro_win() -> None:
    client = MockLLMClient()
    result = client.complete(
        "FINAL DECISION: choose one winner; no tie allowed.\n"
        "Topic: Test topic\n"
        "Latest pro: brief claim.\n"
        "Latest con: Addressing the opponent directly, this argument gives specific "
        "evidence because privacy, access, testing, risk, criteria, and rebuttal all "
        "matter for the selected topic.\n"
        "Scoring criteria: {'persuasion': 35}",
        model="mock",
        timeout=1,
    )
    assert "Winner: Con Agent" in result.content
    assert "Score: Pro 62, Con" in result.content


def test_web_search_disabled_returns_no_sources() -> None:
    assert WebSearchTool(enabled=False, timeout=0.1, max_results=1).search("anything") == []


def test_web_search_parses_html_results(monkeypatch) -> None:
    class Response:
        text = '<a rel="nofollow" class="result__a" href="https://example.com">Example</a>'

        def raise_for_status(self) -> None:
            return None

    class Requests:
        @staticmethod
        def get(url, timeout, headers):
            return Response()

    monkeypatch.setitem(__import__("sys").modules, "requests", Requests)
    results = WebSearchTool(enabled=True, timeout=0.1, max_results=1).search("query")
    assert results[0].url == "https://example.com"
