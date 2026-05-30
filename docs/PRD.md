# Product Requirements Document

## 1. Product Summary

AI Agent Debate is a Python implementation of Exercise 02. It runs a structured,
turn-based debate between three role agents: Pro, Con, and Judge. The current
implementation uses a parent orchestration process plus three agent processes:
`pro-agent`, `con-agent`, and `judge-agent`.

The project demonstrates multiprocessing, inter-process communication, prompt/context
engineering, role-specific LLM provider selection, deterministic fallback behavior,
structured logs, transcript export, and a terminal user interface suitable for course
submission.

## 2. Stakeholders

- Student developer: builds, explains, runs, tests, and submits the repository.
- Course grader: checks assignment requirements, software quality, architecture, and
  evidence.
- Debate operator: chooses a topic, runs the debate, views transcripts, and saves result
  files.
- Future maintainer: can add providers, improve prompts, expand logging, or build a GUI.

## 3. Current Product Scope

The application is a local terminal program. It accepts a topic at runtime, frames the
Pro and Con positions, runs a fixed number of alternating turns, and asks the Judge
process to select one winner.

The current default topic is:

```text
Should universities require students to use AI agents in software engineering courses?
```

The current default turn count is five turns per side, producing ten debate pings before
final judgment.

## 4. Goals

- Demonstrate a three-agent debate architecture.
- Run each agent role in a separate process: Pro, Con, and Judge.
- Keep the parent process responsible for orchestration, routing, memory, logging, and
  cleanup.
- Use queues and JSON-ready message dictionaries for IPC.
- Prevent direct child-to-child communication.
- Support runtime topic selection.
- Support explicit stance framing for A-or-B topics.
- Support Gemini, Groq, OpenAI, Mistral-compatible APIs, and deterministic mock mode.
- Degrade gracefully when API keys are missing or providers fail.
- Save auditable logs and transcripts.
- Use compact prompt context rather than sending full history every turn.
- Provide tests, linting, requirements files, README, and supporting docs.

## 5. Non-Goals

- The app is not a production moderation platform.
- The app is not a chatbot UI or web application.
- Mock mode is not intended to replace a real-provider submission transcript.
- Web search is best-effort and not a guaranteed research engine.
- The project does not store secrets, create API keys, or manage billing.

## 6. Functional Requirements

### FR1: Terminal Menu

The user must be able to run the project with:

```powershell
uv run agent-debate
```

Acceptance criteria:

- Menu options include Run debate, Show last transcript, Save transcript, Validate
  config, and Exit.
- Invalid input returns a clear message.
- The menu repeats after each completed operation.

### FR2: Runtime Topic Selection

Before each debate, the CLI asks for a topic.

Acceptance criteria:

- Pressing Enter uses the default topic.
- Typing a custom topic overrides the default for that run only.
- A-or-B wording is reframed into an explicit proposition and opposing stances.

### FR3: Separate Agent Processes

The system must use process-based agents.

Acceptance criteria:

- `pro-agent` runs as a `multiprocessing.Process`.
- `con-agent` runs as a `multiprocessing.Process`.
- `judge-agent` runs as a `multiprocessing.Process` for the final decision.
- The parent remains a supervisor/router and does not generate debate content.

### FR4: Parent-Controlled IPC

Child agents must not talk directly to each other.

Acceptance criteria:

- `pro -> con` and `con -> pro` messages are invalid.
- `MessageRouter` only routes valid parent-to-child instructions.
- Child responses return to the parent queue.
- The Judge process receives serialized debate memory from the parent.

### FR5: Structured Message Format

Every IPC payload must be JSON-ready.

Acceptance criteria:

- Messages include round, sender, receiver, type, content, sources, timestamp, and
  metadata.
- Messages can be converted to and from dictionaries.
- JSONL logs store the full dictionary representation.

### FR6: Debate Turn-Taking

The debate must run in ordered turns.

Acceptance criteria:

- Pro speaks first in each round.
- Con speaks second in each round.
- Each speaker receives the opponent's previous argument.
- `turns_per_side: 5` produces ten argument messages.

### FR7: Final Judgment

The Judge must produce a no-tie decision.

Acceptance criteria:

- The final message has type `decision`.
- The decision includes a winner and Pro/Con scores.
- A formatting safeguard adds a required verdict if a provider omits the expected
  structure.
- Mock fallback scoring is based on the latest Pro and Con arguments, not a fixed Pro
  win.

### FR8: Provider Support

The system must support multiple LLM providers.

Acceptance criteria:

- Gemini is supported through `GEMINI_API_KEY`.
- Groq is supported through `GROQ_API_KEY`.
- OpenAI is supported through `OPENAI_API_KEY`.
- Mistral-compatible calls are supported through `MISTRAL_API_KEY`.
- Mock mode is available for tests, missing keys, and configured fallback.
- Role-level provider settings override the global provider mode.

### FR9: Logs and Results

The system must preserve debate evidence.

Acceptance criteria:

- `logs/debate.jsonl` contains structured logs for the latest run.
- `logs/transcript.txt` contains the latest readable transcript.
- Menu option 3 exports timestamped transcript files.
- The committed `results/` folder contains representative saved transcripts.

### FR10: Verification

The project must be verifiable locally.

Acceptance criteria:

- `uv run pytest` passes.
- Coverage remains at or above 85 percent.
- `uv run ruff check .` passes.
- Documentation matches the implemented architecture.

## 7. Non-Functional Requirements

- Maintainability: small modules with clear responsibilities.
- Reliability: watchdog checks, queue timeouts, and process cleanup.
- Security: `.env` is ignored and docs use placeholder keys only.
- Usability: readable CLI messages and concise provider failure summaries.
- Portability: UV workflow plus requirements files.
- Observability: JSONL logs, readable transcript, saved results, and fallback metadata.
- Testability: provider behavior and process behavior are covered by tests.

## 8. Assignment Constraints Traceability

- Python implementation: `src/agent_debate/`.
- OOP design: agent, logger, memory, router, client, and orchestrator classes.
- Processes: `multiprocessing.Process` for Pro, Con, and Judge.
- IPC: `multiprocessing.Queue` and JSON-ready `Message` payloads.
- Context engineering: `DebateMemory` and `PromptBuilder`.
- Watchdog: `src/agent_debate/orchestration/watchdog.py`.
- Terminal operation: `src/agent_debate/cli.py`.
- Logs: `src/agent_debate/logging_utils/debate_logger.py`.
- Tests: `tests/`.
- Documentation: `README.md` and `docs/`.

## 9. Results Evidence

The `results/` directory currently includes three saved transcript examples:

- `results/transcript-20260528-004720.txt`: default AI-agents-in-universities debate.
- `results/transcript-20260528-005218.txt`: Ronaldo vs Messi comparison debate.
- `results/transcript-20260528-005609.txt`: AI job replacement debate.

These demonstrate custom topics, multi-round debate behavior, provider/model labels,
transcript persistence, and final judge decisions.

## 10. Risks and Mitigations

- Provider quota or billing failure: summarize the error and fall back to mock when
  configured.
- DNS or network failure: return a concise provider error and use mock fallback where
  enabled.
- Search failure: continue with empty sources.
- Child process hang: watchdog timeout raises a clear error.
- Judge response missing winner/score: formatting safeguard appends a required verdict.
- Mock misuse: CLI and README explain that mock mode is only dry-run behavior.
- Documentation drift: PRD, PLAN, PROMPT_BOOK, TODO, and README are updated together.

## 11. Test Map

- Message schema: `tests/test_messages.py`.
- Routing: `tests/test_routing.py`.
- Config and topic framing: `tests/test_config.py`.
- Provider selection and mock behavior: `tests/test_llm_and_tools.py`.
- Gemini client errors: `tests/test_gemini_client.py`.
- Judge behavior: `tests/test_judge_agent.py`.
- Logging and transcript export: `tests/test_memory_and_logging.py`.
- Orchestration and process checks: `tests/test_orchestrator.py`.
- Watchdog: `tests/test_watchdog.py`.
- CLI: `tests/test_cli.py`.

## 12. Release Criteria

- Run `uv run pytest`.
- Run `uv run ruff check .`.
- Run `uv run agent-debate`.
- Save at least one transcript export.
- Confirm `.env` is not tracked.
- Confirm README and docs describe the current process model.
- Confirm the repository and results are ready for submission.
