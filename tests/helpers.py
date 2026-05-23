from pathlib import Path


def write_test_config(project_root: Path, *, turns: int = 1) -> Path:
    config_dir = project_root / "configs"
    config_dir.mkdir()
    config_path = config_dir / "debate_config.yaml"
    config_path.write_text(
        f"""
topic: "Test debate topic"
turns_per_side: {turns}
language: "English"
agents:
  judge:
    name: "Judge"
    model: "mock-model"
    provider: "mock"
  pro:
    name: "Pro Agent"
    stance: "Support the topic"
    model: "mock-model"
    provider: "mock"
  con:
    name: "Con Agent"
    stance: "Oppose the topic"
    model: "mock-model"
    provider: "mock"
llm:
  provider: "mock"
  timeout_seconds: 5
  max_output_tokens: 100
  temperature: 0.0
  mock_when_no_api_key: true
  fallback_to_mock_on_provider_error: true
web_search:
  enabled: false
  provider: "duckduckgo_html"
  timeout_seconds: 1
  max_results: 1
debate_rules:
  max_words_per_turn: 100
  require_respectful_tone: true
  require_rebuttal: true
  require_sources: false
  no_tie: true
scoring:
  persuasion: 35
  evidence_quality: 25
  factual_correctness: 20
  direct_rebuttal: 20
logging:
  directory: "logs"
  jsonl_file: "debate.jsonl"
  transcript_file: "transcript.txt"
  max_jsonl_lines: 500
  backup_count: 20
watchdog:
  response_timeout_seconds: 10
  restart_attempts: 0
gatekeeper:
  max_calls_per_debate: 10
  max_estimated_input_chars: 10000
""".strip(),
        encoding="utf-8",
    )
    return config_path
