# Prompt Book

## 1. Purpose

This prompt book documents the prompt strategy used by the AI Agent Debate project. It
explains what each agent receives, what is intentionally excluded, and how topic framing
works. The live templates are assembled in `src/agent_debate/memory.py`.

## 2. Prompt Design Principles

- Keep role instructions explicit.
- Keep debate turns respectful.
- Require direct rebuttal of the opponent previous argument.
- Include only compact selected context.
- Do not send the full transcript to child agents every turn.
- Keep source URLs visible when web search returns evidence.
- Keep judge scoring criteria explicit.
- Require the judge to choose a winner and avoid ties.

## 3. Topic Framing

Runtime topics are processed by `Config.with_topic()` in `src/agent_debate/config.py`.

### A-or-B Topic Example

Input:

```text
What is better sport: pilates or yoga?
```

Framed topic:

```text
Pilates is better than Yoga.
```

Pro stance:

```text
Argue that Pilates is better than Yoga.
```

Con stance:

```text
Argue that Yoga is better than Pilates.
```

### Yes-or-No Topic Example

Input:

```text
Should universities require students to use AI agents in software engineering courses?
```

Framed topic:

```text
Should universities require students to use AI agents in software engineering courses.
```

Pro stance:

```text
Support the proposition.
```

Con stance:

```text
Oppose the proposition.
```

## 4. Child Agent Prompt Template

```text
You are the {role} debate agent. Stance: {stance}.
Topic: {topic}
Rules: {debate_rules}
Running summary: {summary}
Opponent previous argument: {previous_argument_or_none}
Current judge instruction: {instruction}
Web evidence candidates: {evidence_urls}
Write one respectful turn. Explicitly rebut the opponent if present. Include source URLs you rely on.
```

## 5. Child Prompt Fields

- `role`: either `pro` or `con`.
- `stance`: role-specific position generated from the topic.
- `topic`: current debate proposition.
- `rules`: configured debate rules.
- `summary`: compact running summary from DebateMemory.
- `previous_argument`: only the opponent latest argument, not the full transcript.
- `instruction`: judge instruction for the current round.
- `evidence_urls`: best-effort search result URLs.

## 6. Pro Agent Example

```text
You are the pro debate agent. Stance: Argue that Pilates is better than Yoga.
Topic: Pilates is better than Yoga.
Rules: {'max_words_per_turn': 170, 'require_rebuttal': True}
Running summary: Latest con point in round 1: Yoga combines flexibility...
Opponent previous argument: Yoga is more accessible because it needs less equipment.
Current judge instruction: Round 2: present your argument and rebut the prior point.
Web evidence candidates: ['https://example.com/source']
Write one respectful turn. Explicitly rebut the opponent if present. Include source URLs you rely on.
```

## 7. Con Agent Example

```text
You are the con debate agent. Stance: Argue that Yoga is better than Pilates.
Topic: Pilates is better than Yoga.
Rules: {'max_words_per_turn': 170, 'require_rebuttal': True}
Running summary: Latest pro point in round 2: Pilates improves controlled resistance...
Opponent previous argument: Pilates is better for measurable progression.
Current judge instruction: Round 2: present your argument and rebut the prior point.
Web evidence candidates: ['https://example.com/source']
Write one respectful turn. Explicitly rebut the opponent if present. Include source URLs you rely on.
```

## 8. Judge Prompt Template

```text
FINAL DECISION: choose one winner; no tie allowed.
Topic: {topic}
Rules: {debate_rules}
Round: {round_number}
Running summary: {summary}
Latest pro: {latest_pro_argument}
Latest con: {latest_con_argument}
Scoring criteria: {scoring}
Evaluate persuasion, evidence quality, factual correctness, and direct rebuttal.
```

## 9. Judge Scoring Criteria

The default criteria are loaded from `configs/debate_config.yaml`:

- Persuasion: 35
- Evidence quality: 25
- Factual correctness: 20
- Direct rebuttal: 20

The judge must choose a winner. A tie is not allowed.

## 10. Context Window Engineering

The system follows the Select/Write model from the lecture.

Write:

- Full messages are saved in `logs/debate.jsonl`.
- Human transcript is saved in `logs/transcript.txt`.
- DebateMemory keeps full message objects in memory.
- DebateMemory updates a short summary outside the prompt.

Select:

- Child agents receive role, stance, topic, rules, opponent previous argument, summary, instruction, and evidence.
- Judge receives topic, rules, latest arguments, summary, scoring criteria, and round number.

## 11. Provider Behavior

- Gemini: configured through `GEMINI_API_KEY`; default provider for the judge.
- Groq: configured through `GROQ_API_KEY`; default provider for the pro agent.
- Mistral: configured through `MISTRAL_API_KEY`; default provider for the con agent.
- OpenAI: configured through `OPENAI_API_KEY`; optional provider if the config is changed.
- Mock: deterministic dry-run provider for tests, missing keys, and fallback.

Provider errors should not be inserted into agent speech. Fallback reason is stored in
message metadata, and the CLI prints one concise notice.

## 12. Maintenance Rules

When changing prompts:

- update `src/agent_debate/memory.py`,
- update examples in this file,
- update tests if prompt fields change,
- verify context remains compact,
- verify judge still cannot return a tie.

## 13. Project Conversation and User-Requested Prompt Decisions

This section records the important prompt and behavior decisions requested during the
project build. It is included so the submission documents not only the final templates,
but also the reasoning behind the current user experience.

### 13.1 Initial Build Request

User request:

```text
Build me a project in:
C:\Users\Aisha\Desktop\AI\uoh-ay26-ai-agent-debate

Follow the attached files:
- software_submission_guidelines-V3.pdf
- main-v4-Agents-Subagents-Commands.pdf
- HW2_prompt_debate.txt
```

Prompt decision:

- Treat the PDFs and prompt guide as assignment authority.
- Implement three agents: judge, pro, con.
- Use multiprocessing queues for IPC.
- Use JSON messages.
- Include context window engineering.
- Include tests, linting, README, CLI, logs, and config.

### 13.2 Repeated Mock Sentence Problem

User feedback:

```text
WHATS THE POINT OF REPEATING THE SAME SENTENCE?
YOU SHOULD PICK A TOPIC FIRST TO DISCUSS
FIX THIS
```

Observed problem:

- Mock mode repeated the same generic sentence for every round.
- The CLI started a debate without asking the user for a topic.
- Transcript display appended previous runs and looked duplicated.

Prompt and behavior changes:

- CLI now asks for a topic before each debate.
- Pressing Enter uses the default topic.
- Mock provider generates role-specific and round-specific content.
- New debate runs reset the latest transcript.
- Transcript export keeps saved copies separately.

### 13.3 Topic Mismatch Problem

User feedback:

```text
Debate should match the topic, if not default was selected.
```

Example user topic:

```text
What is better sport: pilates or yoga?
```

Observed problem:

- The topic string changed, but mock arguments still discussed AI in education.

Prompt and behavior changes:

- `Config.with_topic()` now frames runtime topics into debate propositions.
- A-or-B topics become explicit opposing stances:
  - Pro: argue for the first option.
  - Con: argue for the second option.
- Mock provider includes topic-specific argument banks for Pilates vs Yoga.
- Generic topics still produce coherent pro/con content.

### 13.4 Transcript Saving Request

User request:

```text
ADD OPTION TO SAVE TRANSCRIPT
```

Behavior change:

- CLI now includes:

```text
3. Save transcript
```

- `DebateLogger.export_transcript()` saves timestamped transcript files:

```text
logs/transcript-YYYYMMDD-HHMMSS.txt
```

Prompt-book relevance:

- Saved transcripts are the human-readable evidence of one complete debate session.
- They should be attached or screenshotted for submission if required.

### 13.5 API Key and Provider Discussion

User question:

```text
what is OPENAI_API_KEY?
how i can know my api?
```

Decision:

- Explain that OpenAI API keys are created from the OpenAI developer platform.
- Do not ask the user to paste secrets into chat.
- Keep `.env` ignored by Git.

Then the user asked for free alternatives because OpenAI required billing.

Prompt and provider decision:

- Add Gemini support through `GEMINI_API_KEY`.
- Keep OpenAI support as optional.
- Use `provider: auto`:
  - Gemini first when `GEMINI_API_KEY` exists.
  - OpenAI second when only `OPENAI_API_KEY` exists.
  - Mock when no real key exists.

### 13.6 Gemini Warning and Quota Handling

Observed user output:

```text
Using LLM provider: gemini
Gemini failed, so this run used mock fallback.
Provider error: Gemini API error: 429 RESOURCE_EXHAUSTED ...
```

Problems:

- Google warning messages cluttered the terminal.
- Gemini quota errors printed a huge JSON payload.
- Fallback notices originally said OpenAI even when Gemini failed.

Prompt and behavior changes:

- Suppress noisy third-party FutureWarning output in CLI and child processes.
- Summarize Gemini quota errors into one readable line.
- Print provider-specific fallback messages:

```text
Gemini failed, so this run used mock fallback.
```

- Store provider fallback details in message metadata instead of injecting them into
  debate speech.

### 13.7 Documentation Expansion Request

User request:

```text
TODO must contain 800-1000 tasks.
Make it more clear... say task clearly and in which file.
Files PLAN, PRD, PROMPT_BOOK should be more professional.
Make them longer and containing more details.
```

Documentation decisions:

- `docs/TODO.md` now contains exactly 900 tasks.
- Every TODO task names the related file or directory.
- `docs/PRD.md` was expanded with stakeholders, functional requirements,
  non-functional requirements, risks, test map, and release criteria.
- `docs/PLAN.md` was expanded with milestones, verification commands, provider plan,
  testing strategy, and submission checklist.
- `docs/PROMPT_BOOK.md` now records prompt templates, context engineering, provider
  behavior, and this conversation-derived decision log.

### 13.8 Commit Strategy Request

User request:

```text
I want to commit changes, but I want to make several commits for better and clearer
commit messages.
```

Commit decision:

- Split commits by concern:
  - scaffolding and config,
  - source implementation,
  - tests,
  - documentation pack.

This improves reviewability and makes the repository history easier for a grader to
understand.
