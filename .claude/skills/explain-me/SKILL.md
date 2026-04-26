---
name: explain-me
description: Explains any part of the codebase in plain language and prepares interview-ready answers for live demo Q&A. Use when the user asks "explain this to me", "why does this work", "how do I answer if they ask about X", "walk me through X", or "help me prepare for the demo".
---

# Explain Me

Explain code or design decisions as if answering a TA live — clear, honest, and grounded in the actual code.

## Workflow

### 1. Read before explaining

Always read the actual code before answering. Never explain from memory or assumption. If the question is about a file, read it. If it is about a decision, read the ADR or session notes.

### 2. Explain in three layers

For every explanation, cover all three in order:

1. **What it does** — one sentence, plain language, no jargon
2. **Why it was built this way** — the trade-off or constraint that drove the decision
3. **What breaks if you change it** — the downstream consequence

This mirrors exactly how a TA will probe: they start with "walk me through X", then ask "why did you do it that way?", then ask "what would happen if...?"

### 3. Frame as a live answer

After explaining, produce a 3–5 sentence spoken answer the user can practise out loud. Keep it confident, not defensive. Acknowledge trade-offs honestly — "I chose X because Y; the downside is Z, which I would fix by W."

### 4. Anticipate follow-ups

After the main answer, list 2–3 follow-up questions the TA is likely to ask next. Answer each one briefly.

### 5. Flag gaps

If the code does not match what the documentation says, or if there is a decision the user cannot yet explain, say so clearly. Better to know the gap now than discover it live.

## Triggers

Use this skill when the user asks any of:

- "explain [file / function / component] to me"
- "why did we [do X / choose Y / design it this way]"
- "how do I answer if they ask about [topic]"
- "walk me through [flow / endpoint / pipeline step]"
- "what happens if [condition]"
- "help me prepare for the demo"
- "what will the TA ask about [topic]"

## Tone

- Plain English first, technical terms after
- Never say "it's complicated" — simplify until it is not
- Treat trade-offs as strengths, not weaknesses: knowing the downside shows mastery
- If unsure, say so and show where to look — a TA respects "I would check X" over a confident wrong answer

See [REFERENCE.md](REFERENCE.md) for the full list of sample TA questions and model answers.
