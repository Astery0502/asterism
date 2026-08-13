---
name: scientific-investigation-injector
description: >
  Create or migrate one durable, self-contained, prototype-first scientific
  investigation under an existing project's investigations directory. Use only
  when the user explicitly invokes $scientific-investigation-injector for a
  consequential scientific question that
  requires persistent provenance, products, decisions, multiple prototypes, or
  handoff across sessions or agents. Do not use for routine analysis, quick
  experiments, literature lookup, debugging, ordinary project exploration, or
  uncertainty that can be resolved within the current task.
disable-model-invocation: true
---

# Scientific Investigation Injector

Initialize or migrate a small scientific-investigation mode in one authorized
`investigations/<investigation-id>/` subtree. Each invocation is a bounded,
one-time setup operation, not ongoing lifecycle management. Treat parent-project
instructions, shared scientific conventions, and source packages as inherited
read-only authority.

## Activation gate

Treat injection as a consequential project-structure decision. Proceed only
when all of these conditions hold:

1. The governing question is scientific rather than routine software work.
2. A durable investigation is justified by at least one active need: multiple
   prototype cycles, persistent evidence and provenance, registered scientific
   products, reusable scientific working contracts, ordered evidence gates,
   cross-session or cross-agent continuation, or a formal handoff.
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

Before initializing or migrating an investigation, read
[`references/framework.md`](references/framework.md) completely. Use
[`references/concern-map.toml`](references/concern-map.toml) to give every
canonical concern one disposition. Route each locally realized concern's
operative rule only to applicable default destinations in the selected payload;
`inherit` and `omit` need no local destination. A destination in an optional
asset applies only when that asset is selected.

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
   `inherit`, or `omit`. Keep a working reason for `replace` and `omit`; persist
   it only when it changes durable scientific meaning.
5. Keep all writes inside the authorized investigation subtree. If a concern
   requires a project-wide change, stop and request separate authority.

The resolution may remain internal for a simple injection. Create a local plan
only when the user requests one, the target already has conflicting authority,
or the mapping is too complex to apply safely in one pass.

## Select payloads

For a new investigation, use these four small core assets:

- [`assets/investigation/AGENTS.md`](assets/investigation/AGENTS.md)
- [`assets/investigation/CHARTER.md`](assets/investigation/CHARTER.md)
- [`assets/investigation/PROGRESS.md`](assets/investigation/PROGRESS.md)
- [`assets/investigation/PRODUCTS.toml`](assets/investigation/PRODUCTS.toml)

Include
[`assets/investigation/REVIEW.md`](assets/investigation/REVIEW.md) only when an
integrated scientific review is part of the current request or task.

Select an optional asset only when its trigger is active in the current request
or task:

- [`assets/optional/CONTRACTS.md`](assets/optional/CONTRACTS.md): a
  investigation-derived claim or local convention materially affects
  interpretation and must be reused or challenged across prototypes or agents.
- [`assets/optional/PHASES.md`](assets/optional/PHASES.md): several ordered
  scientific gates are active.
- [`assets/optional/DECISIONS.md`](assets/optional/DECISIONS.md): binding
  decisions no longer fit cleanly in progress checkpoints.
- [`assets/optional/DATA_PROVENANCE.md`](assets/optional/DATA_PROVENANCE.md):
  external or large data have nontrivial identity or acquisition.
- [`assets/optional/HANDOFF.md`](assets/optional/HANDOFF.md): another
  investigation will inherit a result and its limitations.

The concern map routes concerns within this core-plus-active-optional payload; it
does not select payload files. Do not copy every optional asset or create empty
directories for completeness or hypothetical future needs.

## Instantiate local authority

- Preserve compatible existing investigation content and unrelated user work.
- Replace placeholders with investigation-specific scientific content.
- Remove unused prompts, examples, and optional sections.
- State operative rules directly; never write only “follow the framework.”
- Use the investigation's domain terminology.

After initialization or migration, the selected local files—not this skill or
its assets—govern ordinary investigation work.

## Validate the result

Confirm that:

- every concern in the concern map has a disposition, and each locally realized
  concern is routed only to applicable destinations in the selected payload;
- each mutable datum has one investigation-local owner;
- no unresolved placeholder remains;
- optional records correspond to active concerns;
- investigation-derived working contracts remain separate from accepted basis
  and state their status, scope, and material check;
- the local `AGENTS.md` gives the actual reading order and behavior;
- the current question, prototype, evidence, limitations, products if any, and
  next move can be recovered from local files;
- ordinary work can continue without access to this skill; and
- no file outside the authorized investigation subtree was changed.

Do not build a general software test suite for this skill's output. Perform
structural inspection and any scientific-spine checks required by scientific
work included in the current request.

## Migrate an existing investigation

Treat migration as a bounded reinjection. Compare canonical concerns with
existing local authority, change only affected destinations, preserve scientific
history, and never recopy the whole asset set over populated records.
