# claw-code vs auto-sdlc Analysis

## What claw-code IS
- A Rust CLI agent harness (reimplementation of Claude Code) — NOT a multi-agent code generation DAG like auto-sdlc
- Uses 3 external layers: OmX (workflow), clawhip (event router), OmO (multi-agent coordination)
- Focuses on operational reliability: state machines, typed events, failure taxonomy, auto-recovery

## Key Principles from claw-code (applicable to auto-sdlc)
1. **State machine first** — every worker has explicit lifecycle states
2. **Failure taxonomy** — classify failures by type (truncation vs malformed vs schema-echo)
3. **Recovery before escalation** — auto-heal known failure modes before giving up
4. **Typed task packets** — structured tasks, not just prompt blobs
5. **Policy engine** — executable rules for retry/merge/escalation

## auto-sdlc's Three Recurring Failure Modes
1. **JSONDecodeError (Extra data)** — LLM emits trailing text after JSON → FIXED with raw_decode
2. **JSONDecodeError (malformed)** — unescaped quotes/newlines in code strings → PARTIALLY fixed with repair + corrective prompt
3. **review_rejected after 3 cycles** — cross-file imports don't resolve; fixer can't fix in time

## Root Causes
- Delivery plan synthesizes ALL files in ONE LLM call — huge JSON with code embedded as string values
- No structural validation between delivery and review (import resolution, function existence)
- Reviewer catches issues but fixer gets ALL issues at once with ALL files — context overload
- max_retries=2 across the board, no differentiation by failure severity
- Review cycles default to 2, not enough for complex multi-file deliveries

## Planned Improvements
1. Add cross-file import validation before review (catch broken refs early)
2. Increase delivery plan max_retries from 2→4
3. Add file manifest to delivery prompt (explicitly list which files to create)
4. Include cross-reference reminder in delivery prompt
5. Force approval on the last review cycle if issues are minor (style-only)
