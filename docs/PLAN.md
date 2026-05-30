# Implementation Plan

## 1. Purpose

This plan describes the current implementation and the remaining verification workflow
for the AI Agent Debate project. It is written for a grader or maintainer who needs to
understand how the code satisfies the assignment requirements.

## 2. Current Architecture Flow

1. `src/agent_debate/cli.py` loads `.env`, reads `configs/debate_config.yaml`, and asks
   the user for a topic.
2. `Config.with_topic()` frames the runtime topic and creates role-specific Pro and Con
   stances.
3. `build_llm_client()` resolves providers by role. The default role mapping is Gemini
   for Judge, Groq for Pro, and OpenAI for Con.
4. `DebateOrchestrator` starts `pro-agent` and `con-agent` as child processes.
5. The parent sends each child a compact instruction through a queue.
6. Each child builds a prompt, optionally gathers web evidence, calls its provider, and
   returns a JSON-ready message.
7. `DebateMemory` stores full message objects and updates a compact running summary.
8. After all rounds finish, the parent starts `judge-agent` as a separate process.
9. `judge-agent` rebuilds memory from serialized message payloads, calls the judge
   provider, and returns a final decision.
10. `DebateLogger` writes JSONL and readable transcript output.
11. The CLI prints the final decision and provider fallback notices when needed.

## 3. Implemented Milestones

### Milestone 1: Project Skeleton

Status: complete.

Implemented files:

- `pyproject.toml`
- `requirements.txt`
- `requirements-dev.txt`
- `configs/debate_config.yaml`
- `src/agent_debate/`
- `tests/`
- `docs/`
- `logs/.gitkeep`
- `results/`
- `.env.example`
- `.gitignore`

### Milestone 2: IPC Foundation

Status: complete.

Implemented files:

- `src/agent_debate/ipc/messages.py`
- `src/agent_debate/ipc/queues.py`
- `tests/test_messages.py`
- `tests/test_routing.py`

Completed behavior:

- JSON-ready message objects.
- Message validation.
- Direct child-to-child route rejection.
- Queue-based routing.

### Milestone 3: Agent Processes and Orchestration

Status: complete.

Implemented files:

- `src/agent_debate/agents/base.py`
- `src/agent_debate/agents/debate_agent.py`
- `src/agent_debate/agents/judge_agent.py`
- `src/agent_debate/orchestration/debate_orchestrator.py`
- `src/agent_debate/orchestration/watchdog.py`
- `tests/test_agents.py`
- `tests/test_judge_agent.py`
- `tests/test_orchestrator.py`
- `tests/test_watchdog.py`

Completed behavior:

- `pro-agent` process.
- `con-agent` process.
- `judge-agent` process for the final decision.
- Parent process supervision and cleanup.
- Watchdog response timeout.

### Milestone 4: Context Engineering

Status: complete.

Implemented files:

- `src/agent_debate/memory.py`
- `docs/PROMPT_BOOK.md`
- `tests/test_memory_and_logging.py`

Completed behavior:

- Write full messages to memory/logs.
- Select compact prompt fields for each role.
- Avoid sending the full transcript on every turn.
- Keep judge scoring criteria explicit.

### Milestone 5: Provider Integration

Status: complete.

Implemented files:

- `src/agent_debate/llm/base.py`
- `src/agent_debate/llm/factory.py`
- `src/agent_debate/llm/gemini_client.py`
- `src/agent_debate/llm/openai_client.py`
- `src/agent_debate/llm/openai_compatible_client.py`
- `src/agent_debate/llm/mock_client.py`
- `tests/test_llm_and_tools.py`
- `tests/test_gemini_client.py`

Completed behavior:

- Gemini provider.
- Groq provider through OpenAI-compatible API behavior.
- OpenAI provider.
- Mistral-compatible provider.
- Mock provider.
- Per-role provider selection.
- Missing-key mock fallback.
- Provider-error mock fallback.
- Concise quota/network error reporting.

### Milestone 6: CLI and Transcript Workflow

Status: complete.

Implemented files:

- `src/agent_debate/cli.py`
- `src/agent_debate/logging_utils/debate_logger.py`
- `tests/test_cli.py`
- `tests/test_memory_and_logging.py`

Completed behavior:

- Run debate.
- Show latest transcript.
- Save timestamped transcript.
- Validate config.
- Print role provider information.
- Print concise fallback notices.

### Milestone 7: Documentation and Results

Status: complete and refreshed.

Implemented files:

- `README.md`
- `docs/PRD.md`
- `docs/PLAN.md`
- `docs/PROMPT_BOOK.md`
- `docs/TODO.md`
- `results/transcript-20260528-004720.txt`
- `results/transcript-20260528-005218.txt`
- `results/transcript-20260528-005609.txt`

Completed behavior:

- README explains implementation details.
- Docs match current three-process design.
- Results folder is described.
- TODO list records completed work and future checks.

## 4. Provider Plan

Current default role providers:

1. Judge uses Gemini: `gemini-2.5-flash`.
2. Pro uses Groq: `llama-3.1-8b-instant`.
3. Con uses OpenAI: `gpt-4.1-mini`.

Supported environment keys:

- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `OPENAI_API_KEY`
- `MISTRAL_API_KEY`

Auto provider mode checks keys in this order when no role override is present:

1. Gemini.
2. Groq.
3. OpenAI.
4. Mistral.
5. Mock.

Provider fallback behavior:

- Missing keys can fall back to mock when `mock_when_no_api_key: true`.
- Provider runtime errors can fall back to mock when `fallback_to_mock_on_provider_error:
  true`.
- Fallback details are stored in message metadata.
- CLI notices are concise and provider-specific.

## 5. Verification Commands

Run from the project root:

```powershell
uv sync --extra dev
uv run ruff check .
uv run pytest
uv run agent-debate
```

Expected results:

- Ruff reports no violations.
- Pytest passes with coverage at or above 85 percent.
- CLI menu opens.
- Debate runs with real providers when keys and quotas are available.
- Debate falls back cleanly to mock when configured providers are unavailable.
- Transcript display and export work.

## 6. Testing Strategy

Unit tests cover:

- Config loading and topic framing.
- Message validation.
- Router validation.
- Provider selection.
- Mock argument generation and scoring.
- Gemini error handling.
- Judge decision formatting.
- Logger reset, transcript read, and transcript export.
- CLI command behavior.
- Watchdog checks.

Integration tests cover:

- Mock debate orchestration.
- Process startup for Pro, Con, and Judge.
- Transcript creation.
- Child process cleanup.

## 7. Results Evidence Plan

The `results/` folder is used for saved transcript examples that can be inspected without
rerunning the app. Current examples cover:

- Default assignment topic.
- A custom sports comparison topic.
- A custom labor-market AI topic.

For submission, keep at least one transcript from a real-provider run if quota and
network access allow it. If only mock fallback is available, clearly explain that the run
demonstrates system behavior but not real LLM quality.

## 8. Submission Checklist

- Confirm `.env` is not tracked.
- Confirm `.env.example` contains placeholders only.
- Run tests and Ruff.
- Save transcript evidence.
- Confirm docs match the current implementation.
- Confirm `results/` contains relevant transcript examples.
- Confirm GitHub repository is accessible to the grader.
- Submit the repository link requested by the course.

## 9. Future Improvements

- Add OpenRouter as another OpenAI-compatible provider.
- Add local LM Studio or Ollama provider support.
- Add Markdown/PDF transcript export.
- Add per-round judge feedback.
- Add richer citation extraction.
- Add a simple web UI while preserving the CLI.
- Add configurable debate order.
- Add stronger evidence validation for source URLs.
