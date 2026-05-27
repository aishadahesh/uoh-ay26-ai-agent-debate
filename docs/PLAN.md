# Implementation Plan

## 1. Purpose

This plan explains how the AI Agent Debate project is built, verified, and prepared for
course submission. It is written for maintainers and graders who need to understand the
engineering path, not only the final code.

## 2. Architecture Flow

1. CLI loads configuration and asks for a topic.
2. Provider factory chooses the configured role provider: Gemini, Groq, Mistral, OpenAI, or mock mode.
3. DebateOrchestrator starts pro and con child processes.
4. Judge/orchestrator sends compact instructions through queues.
5. Child agents generate one turn and send JSON messages back to the parent.
6. DebateMemory stores full messages and updates a compact summary.
7. JudgeAgent produces a final no-tie decision.
8. DebateLogger writes JSONL and transcript files.

## 3. Milestones

### Milestone 1: Project Skeleton

- Create `pyproject.toml`.
- Create `src/agent_debate`.
- Add `tests`, `configs`, `docs`, and `logs`.
- Add `.env.example`, `.gitignore`, and requirements files.

Exit criteria:

- Package imports correctly.
- `uv sync --extra dev` succeeds.

### Milestone 2: IPC Foundation

- Implement `Message`.
- Implement route validation.
- Implement `MessageRouter`.
- Test direct child-to-child rejection.

Exit criteria:

- Schema tests pass.
- Routing tests pass.

### Milestone 3: Agents and Orchestration

- Implement `BaseAgent`.
- Implement `DebateAgent`.
- Implement `JudgeAgent`.
- Implement `DebateOrchestrator`.
- Implement `Watchdog`.

Exit criteria:

- Mock end-to-end debate runs.
- Child processes terminate cleanly.

### Milestone 4: Context Engineering

- Implement `DebateMemory`.
- Implement `PromptBuilder`.
- Select compact context per role.
- Write full logs outside prompt context.

Exit criteria:

- Prompt tests prove full transcript is not blindly passed.
- README and Prompt Book document Select/Write behavior.

### Milestone 5: Provider Integration

- Implement provider-neutral LLM contract.
- Implement mock provider.
- Implement Gemini provider.
- Implement Groq, Mistral, and OpenAI-compatible providers.
- Implement provider auto-selection.
- Implement provider fallback metadata.

Exit criteria:

- Provider selection tests pass.
- Provider errors are concise and non-crashing.

### Milestone 6: CLI and Transcript Workflow

- Add terminal menu.
- Add topic selection.
- Add transcript display.
- Add transcript export.
- Add config validation.

Exit criteria:

- CLI tests pass.
- Manual menu smoke test works.

### Milestone 7: Documentation and Submission

- Write README.
- Write PRD.
- Write PLAN.
- Write PROMPT_BOOK.
- Expand TODO backlog.
- Add screenshot placeholders.

Exit criteria:

- Required docs exist.
- Docs match implemented behavior.

## 4. Verification Commands

```powershell
uv sync --extra dev
uv run ruff check .
uv run pytest
uv run agent-debate
```

Expected results:

- Ruff reports no violations.
- Pytest passes with coverage above 85 percent.
- CLI menu opens.
- Debate can run with Gemini, OpenAI, or mock fallback.
- Transcript can be shown and saved.

## 5. Provider Plan

Default role providers:

1. Judge uses Gemini.
2. Pro uses Groq.
3. Con uses OpenAI.

Provider priority in `provider: auto` mode:

1. Gemini if `GEMINI_API_KEY` is present and not a placeholder.
2. Groq if `GROQ_API_KEY` is present and not a placeholder.
3. OpenAI if `OPENAI_API_KEY` is present and not a placeholder.
4. Mistral if `MISTRAL_API_KEY` is present and not a placeholder.
5. Mock mode if no real key exists and mock fallback is enabled.

Provider errors:

- Gemini quota errors are summarized.
- Groq quota errors are summarized.
- Mistral quota errors are summarized.
- OpenAI quota errors are summarized.
- Provider fallback is stored in message metadata.
- Transcript debate content remains clean.

## 6. Testing Strategy

Unit tests cover:

- Message schema validation.
- Routing rules.
- Config loading and topic framing.
- Provider selection.
- Mock provider behavior.
- Gemini error summarization.
- Logging and transcript export.
- CLI menu behavior.
- Watchdog behavior.

Integration tests cover:

- Mock debate orchestration.
- Transcript creation.
- Child process turn-taking.

## 7. Submission Checklist

- Confirm `.env` is not tracked.
- Confirm `.env.example` has placeholders only.
- Save at least one transcript export.
- Capture screenshots of menu, debate run, transcript, tests, and Ruff.
- Confirm GitHub repository is public or shared with the lecturer.
- Submit the same repository link for both pair members if working in pairs.

## 8. Future Improvements

- Add Groq or OpenRouter provider.
- Add local LM Studio provider.
- Add richer source extraction and citation formatting.
- Add configurable debate order.
- Add per-round judge feedback.
- Add transcript export to Markdown and PDF.
