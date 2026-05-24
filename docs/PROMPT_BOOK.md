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
