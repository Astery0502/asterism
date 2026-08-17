# Representation Inquiry Module

Status: normative Agent behavior module for target-neutral representation.
Contract: `framework/modules/representation-inquiry/contract.json`

## Purpose

Develop a scientifically meaningful representation problem from an accepted
`TheoreticalAccount` and a user-supplied `PresentationInquirySeed`. The module
defines what a researcher must be able to predict, distinguish, explain,
control, observe, and review before any target-native implementation is chosen.

## Inputs

- `TheoreticalAccount`: the accepted bounded scientific account;
- `PresentationInquirySeed`: one or both of:
  - `PresentationDirection`, the user's desired emphasis or presentation aim;
  - `PresentationQuestionSeed`, a directly supplied question that the Agent may
    retain or refine.

The presentation direction is not automatically the operative presentation
question. A direct question is also a seed, not a forced conclusion. The Agent
may refine either into a question that is answerable through a
scientifically meaningful representation while preserving the user's intent.

## Agent responsibilities

The Agent develops a coherent chain from scientific meaning to reviewable
representation obligations:

1. accepted basis;
2. theory anchor;
3. researcher capability;
4. controlled contrast and held-fixed conditions;
5. observable;
6. expected signature;
7. explanatory bridge;
8. representation;
9. interaction contract;
10. warrant and limits;
11. review probe.

The Agent may revisit earlier links when a proposed observable, contrast, or
interaction does not discriminate the intended scientific mechanism.

## Explanatory outcome

Representation inquiry starts from a change in researcher capability, not an
inventory of page elements. The accepted package states what a researcher
should be able to explain, predict, distinguish, or audit after using the
representation. A list of quantities, controls, plots, or formulas is not by
itself a researcher capability.

The Agent identifies the smallest explanatory chain needed to produce that
capability:

```text
scientific object or state -> mechanism or transformation -> observable consequence
```

The chain need not be spatial or sequential, but its relationships must remain
recognizable in the requirements. When the scientific account concerns an
interface, propagation, balance, decomposition, hierarchy, or evolution, the
requirements preserve that organizing structure instead of reducing it to a
collection of readouts.

An explanatory bridge is part of the representation meaning, not explanatory
prose added after the observables have been chosen. It connects what the
researcher manipulates or compares to why the observed response follows from
the accepted theory.

## Contrasts, defaults, and stress cases

A controlled contrast should isolate the intended mechanism as far as the
scientific problem permits. When several quantities vary together, the package
states why their joint variation remains interpretable or supplies a second
contrast that separates the competing causes.

Defaults and named anchors have explanatory roles:

- the default should normally expose the representative structure needed to
  enter the question;
- limiting, degenerate, singular, or failure states should normally be named
  stress cases rather than accidental entry states; and
- a special state may be the default only when the presentation question is
  specifically about that state and its role is made explicit.

The requirements state the rationale for a consequential default or anchor,
not only its numerical value.

## Quantity meaning

Every quantitative visual or interactive channel must remain locally
decodable. The representation requirements retain the quantity name or symbol
and whether it is dimensional, dimensionless, normalized, transformed, or in
code units. A normalized or transformed quantity retains its defining relation
or reference scale.

This is a target-neutral scientific obligation. A target definition constrains
how a selected view may expose the accepted meaning.

## Output handoff

The module produces a `RepresentationRequirementsPackage` containing:

- `RepresentationIntent`: a concise semantic index and pivotal claim chain;
- `RepresentationRequirements`: the complete authoritative prose obligations;
- `RepresentationInterface`: a concise summary of controls, anchors, views,
  and exports.

The prose requirements are authoritative. Intent and interface records make
important semantics easy for runtimes and target definitions to locate; they do not
replace the complete requirements.

Every pivotal hypothesis has a stable `id` and one or more
`requirement_refs`. These are the minimal links needed for downstream target
coverage and artifact traceability; they do not prescribe the scientific
content of a hypothesis.

## Completion condition

The module is complete when the presentation question, theory anchors,
researcher capabilities, controlled contrasts, observables, expected
signatures, explanatory bridges, interaction meanings, warrants, limits, and
review probes form one coherent target-neutral package. The package must make
clear how its observables and interactions support the declared researcher
capability; mechanically displaying every named quantity is not sufficient.

## Evaluation basis

- fidelity to the accepted scientific account;
- usefulness for the presentation question;
- discriminating power of the controlled contrast;
- clarity of observable and expected signature;
- coherence of the object-mechanism-consequence chain;
- explanatory fitness of defaults and stress cases;
- local interpretability of quantities and interactions;
- explicit warrant and limits;
- reviewability.

Review probes include at least one probe of explanatory or predictive use when
the presentation question asks for understanding. Such a probe asks whether
the representation enables the declared researcher capability; it is distinct
from checking numerical correctness or confirming that a control updates a
view.

## Non-authority

This module does not:

- choose a visualization library;
- choose build-time or browser-time computation;
- choose delivery topology or connectivity;
- rewrite the accepted scientific account;
- infer scientific validity from implementation success.

## Feedback

A problem with the accepted scientific meaning returns to scientific inquiry.
A problem with the question, contrast, observable, explanation, or interaction
semantics remains in representation inquiry. Target limitations are recorded
for target realization rather than silently weakening requirements.
