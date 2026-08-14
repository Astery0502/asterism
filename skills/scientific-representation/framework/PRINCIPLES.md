# Agent-Centered Framework Principles

Status: Normative

## Agent primacy

The Agent is the primary scientific and representation actor. It develops and
refines questions, selects useful checks and contrasts, synthesizes bounded
scientific understanding, develops representation semantics, and decides when
a result is stable enough to become a handoff.

Python code supports this work through persistence, registry loading, schema
and path validation, extension invocation, and deterministic checks. Python
interfaces do not define scientific reasoning or representation judgment.

## Authority order

When project resources disagree, use this authority order:

1. these Agent-centered principles;
2. the relevant Agent behavior module;
3. the module handoff contract;
4. target-neutral runtime contracts;
5. target-definition contracts;
6. application and consumer code.

## Modules and handoffs

Modules are authority boundaries, not mandatory linear reasoning scripts. An
Agent may iterate, branch, refine a question, or return from review to an
earlier module. A persisted handoff states that a result is stable enough for
another module to consume; it does not forbid later feedback.

Every Agent module declares its purpose, inputs, Agent responsibilities,
output handoff, completion condition, evaluation basis, non-authority, and
feedback destinations.

## Inspectable scientific work

Persisted artifacts record publicly reviewable scientific claims, decisions,
checks, meanings, limits, and evidence. They are shared memory for continuation
and review. They are not an exhaustive transcript of private model reasoning.

## Question development

An initial analysis question or presentation direction may seed inquiry
without fixing its final formulation. An Agent may discover a more informative
question inside the owning module. The accepted handoff must make the question
actually answered and its relation to the supplied input clear.

## Target neutrality

Scientific inquiry and representation inquiry do not select visualization
libraries, browser runtimes, delivery topology, or packaging. Target-native
decisions begin only after an accepted representation requirements package
exists.

## Conformance and review

Execution, numerical residuals, browser checks, and artifact validation may
establish mechanical conformance. They do not establish that a scientific
interpretation is faithful, discriminating, appropriately bounded, or useful.
Scientific review remains an independent Agent judgment.

## Framework development through cases

A case may expose a weakness in a module, handoff, target definition, or
runtime. A case-specific finding becomes framework behavior only after it is
shown to be reusable beyond that case.
