---
name: intake
description: >
  Use when a user explicitly invokes /intake for a rough, unclear, under-structured,
  or role-ambiguous request before any downstream work begins.
  LOAD ONLY when the user explicitly invokes /intake. Do not auto-load for any other reason.
---

# Intake

## Overview

Intake is prompt refinement before work begins. It turns a rough request into one stronger downstream prompt by identifying the work type, assigning a fitting agent role, preserving the user's intent, adding missing structure, and stopping.

It improves the prompt; it does not solve execution. Do not implement, route, invoke another skill, create a plan, inspect code by default, or make changes.

## When to Use

Use only when `/intake` is explicitly invoked and the request is:

- rough, unclear, or under-structured
- missing role, output, constraints, or success criteria
- mixing possible work types
- not ready to hand to a downstream agent or workflow

Do not use for:

- implementation, debugging, refactoring, testing, or review work
- requests that already identify task, artifact, constraints, and success criteria
- routing, planning, or execution decomposition

If explicitly invoked on a request that is already clear, lightly polish the prompt and stop.

## Work Types And Roles

Pick one dominant `WORK_TYPE` and one concise `AGENT_ROLE`.

| `WORK_TYPE` | Default `AGENT_ROLE` |
|---|---|
| `coding` | Senior engineer |
| `research` | Careful researcher |
| `analysis` | Analyst |
| `writing` | Editor |
| `planning` | Planner |
| `debugging` | Debugger |
| `decision-framing` | Strategist |

If multiple work types are plausible, choose the dominant one and preserve the ambiguity in `Missing ingredients handled`. Do not expand the taxonomy unless the user explicitly asks.

## Implementation

### Phase 1: Prompt Diagnosis

Read the user's request and classify:

- `WORK_TYPE`
- `AGENT_ROLE`
- user goal
- target output
- stated constraints
- missing prompt ingredients
- whether clarification is required

Clarification should be rare. Ask one question only if the missing information would materially change the polished prompt. If clarification is required, ask the question and stop. After the user answers, rerun the diagnosis.

If information is incomplete but usable, carry uncertainty forward.

### Phase 2: Prompt Polishing

Emit the diagnosis and one polished prompt.

The polished prompt should include:

- role, task, and context
- constraints and expected output
- success criteria and important ambiguities

The polished prompt must not include:

- tool calls
- step-by-step implementation
- a forced next workflow or current-agent execution instructions

Hard stop after output. Do not execute, route, invoke another skill, inspect files, or make code changes.

## Output Template

```text
--- Prompt Diagnosis ---
WORK_TYPE: <coding | research | analysis | writing | planning | debugging | decision-framing>
AGENT_ROLE: <one concise role>
User goal: <goal>
Target output: <artifact/result>
Constraints: <stated constraints, or none>
Missing ingredients handled: <assumptions or preserved ambiguities>

--- Polished Prompt ---
<one strong downstream prompt>

Stop here. Do not execute, route, invoke another skill, or make code changes.
```

## Common Mistakes

| Mistake | Correction |
|---|---|
| Treating intake as execution prep with implementation steps | Produce a better prompt, not a plan or task list. |
| Routing to another skill after polishing | Stop after the polished prompt; the user chooses what happens next. |
| Asking broad discovery questions | Ask only one question when the answer would materially change the prompt. |
| Expanding the work type taxonomy too early | Pick the dominant listed type and preserve ambiguity in the diagnosis. |
| Inspecting files or code by default | Use only context the user supplied unless they ask for work outside intake. |
| Writing a generic prompt that loses the user's wording | Preserve the user's intent, constraints, and uncertainty. |
