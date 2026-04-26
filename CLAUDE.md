# CLAUDE.md

## 1. Think Before Coding

Before implementing anything:
- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If something is unclear, stop and ask. Don't guess.

## 2. Simplicity First

- Minimum code that solves the problem. Nothing extra.
- No abstractions for single-use code.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

## 3. Surgical Changes

- Touch only what the task requires.
- Don't refactor or "improve" adjacent code.
- Match existing style.
- Every changed line must trace directly to the request.

## 4. Goal-Driven Execution

Turn tasks into verifiable steps:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
```

State a brief plan before multi-step tasks. Verify each step before moving to the next.

## 5. Project Context

- Session tracker files live in `planing-and-sessions/session-0N.md`
- Implementation plan is in `plans/modelserve-plan.md`
- PRD is in `plans/modelserve-prd.md`
- Work through sessions in order — check off items as they're completed
- `data/` is gitignored — never commit CSV files
