# Product Requirements Document

## 1. Product Summary

AI Agent Debate is a Python implementation of Exercise 02. It runs a structured debate
between two child AI agents under the supervision of a parent judge agent. The project
demonstrates multi-agent orchestration, inter-process communication, context window
engineering, provider abstraction, structured logging, and terminal operation.

The project is designed for course submission. It emphasizes clear architecture, OOP
design, testability, safe API key handling, full debate logs, and compact prompt context.

## 2. Stakeholders

- Student developers: build, run, explain, and submit the project.
- Course grader: verifies the lecture and software-submission requirements.
- Debate operator: chooses the topic, runs the debate, views transcripts, and saves output.
- Future maintainer: can add providers, richer search, UI, or scoring features.

## 3. Goals

- Demonstrate three-agent architecture: judge, pro, con.
- Run pro and con as process-like components using `multiprocessing`.
- Enforce parent-controlled communication through queues.
- Use JSON-serializable messages for IPC.
- Support at least 10 total pings by default.
- Let the user choose a debate topic at runtime.
- Support Gemini, OpenAI, and deterministic mock mode.
- Handle provider quota/key failures without crashing.
- Save full JSONL logs and readable transcript files.
- Implement Select/Write context window engineering.
- Provide tests, linting, docs, and submission artifacts.

## 4. Non-Goals

- The app is not a production debate moderation system.
- Mock mode is not a replacement for final real-LLM evaluation.
- Web search is best-effort and does not guarantee source availability.
- The CLI is intentionally simple; a GUI is optional and outside the required scope.
- The project does not store or manage real API keys beyond reading `.env`.

## 5. Functional Requirements

### FR1: Terminal Operation

The user must be able to run:

```powershell
uv run agent-debate
```

Acceptance criteria:

- Menu includes Run debate, Show last transcript, Save transcript, Validate config, Exit.
- Invalid choices show a clear message.
- The app returns to the menu after each operation unless Exit is selected.

### FR2: Runtime Topic Selection

The user chooses a topic before starting a debate.

Acceptance criteria:

- Pressing Enter uses the configured default topic.
- Custom topics override the default for that run.
- A-or-B topics are reframed into explicit opposing stances.

### FR3: Three Agents

The system includes judge, pro, and con agents.

Acceptance criteria:

- Pro and con run in child processes.
- Judge/orchestrator controls the debate from the parent process.
- Judge produces a final no-tie decision.

### FR4: IPC Through Parent

Child agents must not communicate directly.

Acceptance criteria:

- Message schema rejects `pro -> con` and `con -> pro`.
- MessageRouter rejects direct child-to-child routes.
- All child messages return through the parent queue.

### FR5: Structured Messages

Every process message must be JSON-ready.

Acceptance criteria:

- Messages include round, sender, receiver, type, content, sources, timestamp, metadata.
- JSONL logs store full message dictionaries.
- Unit tests validate schema constraints.

### FR6: Debate Turn-Taking

Only one agent speaks at a time.

Acceptance criteria:

- Orchestrator alternates pro then con for each round.
- Each child receives the opponent previous argument.
- Default `turns_per_side: 5` produces 10 total pings.

### FR7: Context Window Engineering

The system must not send the full transcript on every turn.

Acceptance criteria:

- Full messages are written to logs.
- DebateMemory stores message objects and maintains a compact summary.
- PromptBuilder selects role-relevant context only.

### FR8: Provider Support

The system supports real LLM providers and mock mode.

Acceptance criteria:

- Auto provider mode prefers Gemini when `GEMINI_API_KEY` is valid.
- Auto provider mode uses OpenAI when only `OPENAI_API_KEY` is valid.
- Mock mode runs when no real key exists.
- Provider errors are summarized and can fall back to mock.

### FR9: Logs and Transcript Export

The system saves debate evidence.

Acceptance criteria:

- `logs/debate.jsonl` contains structured messages.
- `logs/transcript.txt` contains the latest readable transcript.
- Menu option 3 exports timestamped transcript archives.

### FR10: Tests and Linting

The project must be easy to verify.

Acceptance criteria:

- `uv run pytest` passes.
- Coverage gate remains at 85 percent or higher.
- `uv run ruff check .` passes.

## 6. Non-Functional Requirements

- Maintainability: OOP modules with small responsibilities.
- Reliability: timeouts, watchdog checks, graceful provider failures.
- Security: `.env` ignored; no secrets committed.
- Usability: clear CLI prompts and concise provider errors.
- Portability: supports UV and plain `requirements.txt`.
- Observability: JSONL logs, readable transcript, metadata for fallback behavior.

## 7. Assignment Constraints

- Must use Python code, not only a manual LLM session.
- Must use OOP design.
- Must use IPC with process-like agents.
- Must use JSON as the communication format.
- Must include timeouts and watchdog behavior.
- Must include tests and Ruff linting.
- Must include terminal operation.
- Must document context window engineering.
- Must not commit API keys.
- Judge must choose a winner; no tie is allowed.

## 8. Risks and Mitigations

- Provider quota failure: summarize the error and fall back to mock mode.
- Search failure: continue debate with empty sources and log the source list.
- Child timeout: raise a clear timeout error.
- Ambiguous topic: frame common A-or-B topics into explicit stances.
- Mock misuse: label mock mode clearly in CLI and README.

## 9. Test Map

- Message schema: `tests/test_messages.py`
- Routing: `tests/test_routing.py`
- Config and topic framing: `tests/test_config.py`
- Provider selection and mock text: `tests/test_llm_and_tools.py`
- Gemini error formatting: `tests/test_gemini_client.py`
- Logging and transcript export: `tests/test_memory_and_logging.py`
- Orchestration: `tests/test_orchestrator.py`
- Watchdog: `tests/test_watchdog.py`
- CLI: `tests/test_cli.py`

## 10. Release Criteria

- Run `uv run pytest`.
- Run `uv run ruff check .`.
- Run a real or mock debate from the terminal.
- Save a transcript export.
- Add screenshots to README if required.
- Confirm `.env` is not tracked.
- Confirm the GitHub repository is accessible to the grader.
