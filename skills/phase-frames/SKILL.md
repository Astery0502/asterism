---
name: phase-frames
description: >
  Use when the user explicitly asks to turn an approved spec, design doc, or requirements document into implementation phase frames. LOAD ONLY when the user explicitly invokes /phase-frames. Do not auto-load for any other reason.
---

# Phase Frames

Frame an approved spec into fixed, ordered implementation phases. Phase frames
shorten the working agent's focus range and check distance without turning the
spec into a conventional implementation plan.

## Input

Use the spec file provided with `/phase-frames`. If no spec file is provided, ask
for it. Explicit invocation with a spec file is permission to edit only the
marked phase-frame section in that spec file.

Do not create a separate artifact or change unrelated spec content. Do not
modify runtime files unless the user separately asks for that work.

## Spec File Update

Append phase frames after the existing spec content using these markers:

```markdown
<!-- phase-frames:start -->
## Implementation Phase Frames

...

<!-- phase-frames:end -->
```

If the markers already exist, replace only the marked section. Preserve the
original spec content above `phase-frames:start`.

The skill must not make a git commit for spec-related changes.

## Phase Model

Generate a fixed and ordered phase sequence. The implementation agent executes
phases one by one in order and should not casually merge, skip, reorder, or
redefine phase boundaries.

Keep work inside each phase flexible. The phase-frame generator frames the spec
into responsibility phases; the working agent determines concrete work after
inspecting the repository and relevant spec context.

Do not preselect exact inspection targets. Do not preselect decision bias. Do
not predict changed files, implementation tasks, or exact completion goals.

## Phase Shape

Each phase is a broad responsibility frame from the spec, not a checklist,
implementation task list, or file operation list.

Use this structure:

```markdown
### Phase N: <Responsibility Name>

Spec focus: <Soft reference to the spec section, theme, or requirement area to
start from. This is orientation, not a limit; full-spec requirements that affect
this responsibility still apply.>

Responsibility frame: <Broad responsibility boundary this phase owns.>

Phase entry: Inspect the repository and relevant spec context before determining
concrete work, applicable constraints, local verification, and practical
decision bias for this phase.

Completion boundary: <When this phase can be marked complete, expressed as a
boundary rather than an exact implementation goal.>

Completion handoff: _Fill this only when the phase is completed: what is
settled, what remains sensitive, and what the next phase should inspect._
```

The implementation agent writes the completion handoff back into the spec file
when the phase completes. Do not add a status marker.

## Guardrails

Reject or self-correct outputs that include:

- checkbox tasks
- numbered implementation steps
- file-by-file operation lists
- exact changed-file predictions
- preselected inspection targets
- preselected decision bias
- rigid task goals inside a phase
- separate logs, ledgers, memory systems, or status trackers
- git commits for spec changes

## Self-Review

Before finishing, review the updated section and fix issues inline:

1. The phase sequence covers the full approved spec.
2. Each phase has a clear responsibility boundary.
3. Phase order is explicit.
4. Phase content leaves internal implementation work to the working agent.
5. The original spec content above the marker was preserved.
6. No generated content became a conventional plan or file-level task list.

Report the spec path and the number of generated phases. Do not start
implementation unless the user explicitly asks.
