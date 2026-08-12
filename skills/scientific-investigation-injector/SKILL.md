---
name: scientific-investigation-injector
description: >
  Create or migrate one durable, self-contained, prototype-first scientific
  investigation under an existing project's investigations directory. Use only
  when the user explicitly invokes $scientific-investigation-injector for a
  consequential scientific question that
  requires persistent provenance, outputs, decisions, multiple prototypes, or
  handoff across sessions or agents. Do not use for routine analysis, quick
  experiments, literature lookup, debugging, ordinary project exploration, or
  uncertainty that can be resolved within the current task.
disable-model-invocation: true
---

# Scientific Investigation Injector

Inject a small scientific-investigation mode into one authorized
`investigations/<investigation-id>/` subtree. Treat parent-project instructions,
shared scientific conventions, and source packages as inherited read-only
authority.

## Activation gate

Treat injection as a consequential project-structure decision. Proceed only
when all of these conditions hold:

1. The governing question is scientific rather than routine software work.
2. A durable investigation is justified by at least one active need: multiple
   prototype cycles, persistent evidence and provenance, registered scientific
   outputs, stable scientific meaning, ordered evidence gates, cross-session or
   cross-agent continuation, or a formal handoff.
3. The user explicitly invokes `$scientific-investigation-injector` and
   authorizes its target investigation subtree.

Scientific uncertainty or general authorization to investigate is not
sufficient. Without explicit skill invocation and a target subtree, do not
inject files; continue with ordinary scientific work or ask the user to invoke
the skill if durable infrastructure appears warranted.

Do not activate this skill for exploratory conversation, a one-off calculation
or plot, a small hypothesis check that fits the current task, literature or web
research, ordinary debugging, general planning, or work that does not need
durable investigation-local authority.

## Load the semantic source

Before resolving or writing an investigation, read
[`references/framework.md`](references/framework.md) completely. Use
[`references/concern-map.toml`](references/concern-map.toml) to verify that every
canonical concern has one disposition and destination.

Do not copy either reference into the investigation. Do not leave canonical IDs
in ordinary runtime prose.

## Resolve the injection

1. Inspect inherited project instructions and the target investigation, if it
   already exists.
2. Identify the scientific purpose, governing question, accepted basis, and
   smallest direct prototype from the user request and available context.
3. Infer local specialization when it is safe. Ask the user only when a choice
   materially changes scientific purpose, authority, or interpretation.
4. Give every canonical concern one disposition: `create`, `merge`, `replace`,
   `inherit`, or `omit`. Record a reason for `replace` and `omit`.
5. Keep all writes inside the authorized investigation subtree. If a concern
   requires a project-wide change, stop and request separate authority.

The resolution may remain internal for a simple injection. Create a local plan
only when the user requests one, the target already has conflicting authority,
or the mapping is too complex to apply safely in one pass.

## Select payloads

Create or merge these assets for a new investigation:

- [`assets/investigation/AGENTS.md`](assets/investigation/AGENTS.md)
- [`assets/investigation/CHARTER.md`](assets/investigation/CHARTER.md)
- [`assets/investigation/PROGRESS.md`](assets/investigation/PROGRESS.md)
- [`assets/investigation/PRODUCTS.toml`](assets/investigation/PRODUCTS.toml)

Create
[`assets/investigation/REVIEW.md`](assets/investigation/REVIEW.md) only when an
integrated scientific review begins.

Select an optional asset only when its trigger is active:

- [`assets/optional/CONTRACTS.md`](assets/optional/CONTRACTS.md): stable
  scientific meaning must survive several prototypes or agents.
- [`assets/optional/PHASES.md`](assets/optional/PHASES.md): several ordered
  scientific gates are active.
- [`assets/optional/DECISIONS.md`](assets/optional/DECISIONS.md): binding
  decisions no longer fit cleanly in progress checkpoints.
- [`assets/optional/DATA_PROVENANCE.md`](assets/optional/DATA_PROVENANCE.md):
  external or large data have nontrivial identity or acquisition.
- [`assets/optional/HANDOFF.md`](assets/optional/HANDOFF.md): another
  investigation will inherit a result and its limitations.

Do not copy every optional asset. Do not create empty directories for
completeness.

## Instantiate local authority

- Preserve compatible existing investigation content and unrelated user work.
- Replace placeholders with investigation-specific scientific content.
- Remove unused prompts, examples, and optional sections.
- State operative rules directly; never write only “follow the framework.”
- Use the investigation's domain terminology.

After injection, the local files—not this skill or its assets—govern ordinary
investigation work.

## Validate the result

Confirm that:

- every concern in the concern map is inherited, injected, specialized, or
  deliberately omitted;
- each concern has one inherited or investigation-local owner;
- no unresolved placeholder remains;
- optional records correspond to active concerns;
- the local `AGENTS.md` gives the actual reading order and behavior;
- the current question, prototype, evidence, limitations, outputs, and next move
  can be recovered from local files;
- ordinary work can continue without access to this skill; and
- no file outside the authorized investigation subtree was changed.

Do not build a general software test suite for this skill's output. Perform
structural inspection and the investigation's own scientific-spine checks.

## Migrate an existing investigation

Treat migration as a bounded reinjection. Compare canonical concerns with
existing local authority, change only affected destinations, preserve scientific
history, and never recopy the whole asset set over populated records.
