# Review Schema

Use this reference to record and present a lifecycle architecture review. `SKILL.md` defines the investigation process; this file defines the vocabulary and output structures.

Apply the schema proportionally. Small repositories may need only a semantic spine, a compact module table, and a short walkthrough.

## Core vocabulary

| Term | Meaning |
|---|---|
| Semantic spine | The smallest evidence-supported model that connects the repository's purpose, authorities, core concepts, transformations, handoffs, outcomes, and feedback. |
| Semantic concept | A domain idea the repository represents or develops. |
| Responsibility | A meaningful unit of work or judgment. |
| Stage | A lifecycle region where responsibility, authority, artifact meaning, or decision context is stable. |
| Authority | The canonical source allowed to establish or revise a fact, decision, or status. |
| Artifact | Information or a result that can be handed off, retained, or consumed. |
| Decision | A choice made by an authority from available evidence or requirements. |
| Contract | The information and guarantees one responsibility exposes to another. |
| Field | A distinct information item carried by an artifact or contract. |
| Status | A statement about one defined dimension of progress, conformance, or review. |
| Feedback | A return path to the responsibility able to resolve a discovered issue. |
| Module | A software boundary implementing one or more related responsibilities. |
| Physical location | The directories, files, entry points, tests, and documents that hold an implementation. |

Keep these distinctions explicit:

- A concept is not automatically a module.
- A module is not automatically a directory.
- An artifact carries information; a status evaluates one dimension of it or its process.
- A producer creates a value; an authority owns its meaning; a consumer uses it.
- A contract describes a boundary; an implementation realizes it.

## Evidence record

Use evidence labels to prevent interpretation from appearing as fact.

| Label | Use |
|---|---|
| Observed | Directly supported by code, documentation, tests, or configuration. |
| Interpreted | A coherent explanation supported by multiple observations. |
| Conflicting | Relevant sources describe incompatible models or behavior. |
| Unresolved | The available evidence does not support a reliable conclusion. |

For material claims, record:

| Claim | Evidence | Label | Scope or limitation |
|---|---|---|---|

## Semantic spine

Use the semantic spine as a revisable working model during investigation. In the final report, present the stabilized model and retain earlier interpretations only when they remain relevant as conflicts or unresolved questions.

Summarize the central idea before listing stages:

```text
Purpose:
Primary outcome:
Primary actors or authorities:
Core concepts:
```

Record lifecycle nodes:

| Stage or responsibility | Purpose | Authority | Input | New artifact or decision | Next consumer |
|---|---|---|---|---|---|

Record lifecycle edges:

| From | To | Handoff | Why it crosses a boundary | Feedback path |
|---|---|---|---|---|

Draw the chain as a graph when branches, loops, parallel work, or event-driven transitions are meaningful.

## Module architecture

| Module | Semantic responsibility | Public surface | Hidden implementation | Owns | Depends on | Used by |
|---|---|---|---|---|---|---|

For each important boundary, explain how it is maintained. Relevant mechanisms may include public types, ports, schemas, package exports, dependency direction, adapters, orchestration, or persistence boundaries.

Review questions:

- Does the module correspond to a meaningful responsibility?
- Is its authority narrower than its implementation convenience?
- Is one responsibility scattered across several owners?
- Are unrelated responsibilities forced into one module?
- Does a target-specific concern define or leak into the core?
- Can the implementation change without changing the public meaning?

## Contract ledger

| Boundary | Producer | Authority | Consumer | Artifact | Required information | Status | Feedback destination |
|---|---|---|---|---|---|---|---|

Review questions:

- Can the consumer continue using only the exposed contract?
- Is required information missing or supplied through hidden coupling?
- Does the contract leak implementation details?
- Does the consumer become a second owner of upstream facts?
- Is feedback routed to the responsibility able to act on it?

## Field and status trace

| Field or status | Meaning | Created by | Authority | Consumers | May change where | Final use |
|---|---|---|---|---|---|---|

For each material item, ask:

1. What distinct fact or judgment does it represent?
2. Which real downstream behavior needs it?
3. Does another field, artifact, or status already express it?
4. Does it combine several meanings under one name or boolean?
5. Is its authority clear throughout its lifetime?
6. What becomes impossible or ambiguous if it is removed?

## Concept-to-path map

| Concept or responsibility | Canonical contract | Implementation | Adapter or target use | Tests | Documentation |
|---|---|---|---|---|---|

Look for:

- more than one canonical location;
- names that conflict with actual responsibility;
- core behavior hidden in an adapter or consumer;
- public contracts mixed with internal mechanics;
- files that cannot be mapped to a meaningful responsibility;
- concepts that have no reliable physical home.

## Light lifecycle walkthrough

State the representative scenario and why it represents the repository's purpose.

| Step | Active responsibility | Input read | Decision or transformation | Artifact or status produced | Next boundary |
|---|---|---|---|---|---|

Conclude with:

- what connected cleanly;
- where meaning or ownership became ambiguous;
- missing or repeated steps;
- information unavailable to the next responsibility;
- feedback that lacks a clear destination.

## Review findings

Use a small vocabulary for broad qualitative findings:

| Finding | Meaning |
|---|---|
| Established | The model is clear and supported by consistent evidence. |
| Ambiguous | More than one interpretation remains plausible. |
| Conflicting | Sources or boundaries express incompatible meanings. |
| Duplicated | Several locations or fields compete to express the same concept. |
| Misplaced | A concept or responsibility resides in an unsuitable boundary. |
| Missing | The lifecycle needs a responsibility or handoff that has no reliable expression. |
| Overdesigned | Complexity has no corresponding responsibility, authority, or consumer need. |

Record material findings as:

| Finding | Evidence | Architectural meaning | Lifecycle effect | Clarification needed |
|---|---|---|---|---|

## Optional architectural coherence evaluation

When the user requests an overall evaluation or improvement direction, synthesize the existing review evidence with this table. Keep the evaluation qualitative, reuse the review finding vocabulary, and mark unsupported judgments as unresolved. Do not treat conformity to a particular architecture style as quality, and do not expand the investigation merely to fill every row.

| Dimension | Evaluation question | Judgment and evidence | Architectural or lifecycle effect | Improvement direction | Confidence or limitation |
|---|---|---|---|---|---|
| Concept integrity and separation | Are core concepts necessary, distinct, cohesive, and owned without scattering or unrelated combination? | | | | |
| Semantic clarity and uniqueness | Do names, facts, decisions, and statuses keep one clear meaning and canonical expression? | | | | |
| Boundary and contract integrity | Can responsibilities collaborate through complete contracts without hidden coupling, authority leakage, or implementation exposure? | | | | |
| Lifecycle continuity and feedback | Can representative paths reach intended outcomes, and can material feedback return to an authority able to act? | | | | |
| Information authority and change reliability | Are the origin, authority, allowed changes, consumers, and final use of important fields and statuses reliable across boundaries? | | | | |
| Semantic-to-physical fidelity | Do modules, contracts, implementations, adapters, tests, and documentation faithfully carry the semantic model? | | | | |
| Evolvability and proportionality | Can responsibilities change locally, and does each abstraction or complexity correspond to a real responsibility or consumer need? | | | | |

## Recommended report shape

1. Repository idea and semantic spine
2. How the current abstraction and modules work
3. Boundary and contract review
4. Field and status lifecycle review
5. Concept-to-path map
6. Light lifecycle walkthrough
7. Established strengths, material findings, and unresolved questions

When requested and supported by the evidence, append the optional architectural coherence evaluation and improvement directions after this report.

Keep explanation and evaluation adjacent. A reader should understand the repository even when no defect is found.
