---
name: analyze-project-architecture
description: Analyze a software repository by reconstructing its semantic spine, explaining how concepts become modules and boundaries, tracing contracts, fields, statuses, and feedback across the lifecycle, and mapping those concepts back to files. Use when Codex needs a read-only understanding and broad architectural review of a complete or partial repository, especially for unclear ownership, coupling, duplication, missing steps, misplaced concepts, or overdesign.
disable-model-invocation: true
---

# Analyze Project Architecture

Understand a repository by recovering the idea it expresses, then review how faithfully its software structure carries that idea. Treat understanding and evaluation as one evidence-based process.

Read [references/review-schema.md](references/review-schema.md) before recording the review. Use only the schema sections that help explain the repository.

## Principles

- Start from the repository's purpose and domain concepts, not its file inventory.
- Treat stages and modules as meaningful responsibility boundaries, not arbitrary layers.
- Explain how the current design works before evaluating it.
- Follow concepts from their semantic meaning into contracts, code, and physical locations, then verify the model against the code.
- Distinguish observations, supported interpretations, conflicts, and unresolved questions.
- Scale the depth and output to the repository. Do not force a linear lifecycle onto a graph, loop, or event-driven system.
- Keep the review read-only unless the user separately requests changes.

## Workflow

Treat the workflow as iterative. Keep the semantic spine and related architectural interpretations provisional until module, contract, field, physical-structure, and lifecycle evidence support them. When later evidence changes the model, revisit the affected analysis and revalidate its dependent boundaries. Stop iterating when a representative path reaches its intended outcome, material feedback returns to an authority able to act on it, and additional evidence within the stated scope no longer changes the core concepts, authorities, boundaries, or lifecycle; record remaining conflicts and unresolved questions.

### 1. Establish the evidence base

Read the repository instructions, overview documents, architecture or specification files, top-level tree, public entry points, representative implementations, and tests or examples that expose real flows.

Record conflicts between documentation and code instead of silently choosing one. State important scope limits.

### 2. Recover the semantic spine

Describe the repository's central idea in domain language. Identify:

- purpose and intended outcome;
- primary actors or authorities;
- concepts and durable artifacts;
- meaningful transformations and decisions;
- review or acceptance points;
- forward handoffs and feedback paths.

Combine these elements into a lifecycle graph. Include a stage only when responsibility, authority, artifact meaning, or decision context changes.

### 3. Explain abstractions and modules

Map each lifecycle responsibility to the abstractions and modules that implement it. For each important module, explain:

- the concept or responsibility it represents;
- its public surface and hidden implementation;
- the decisions or facts it owns;
- its dependencies and consumers;
- the mechanism that maintains its boundary.

Review whether one responsibility is scattered, multiple unrelated responsibilities are combined, or a downstream target defines the core.

### 4. Trace boundary contracts

For each important edge in the lifecycle graph, identify the producer, semantic authority, consumer, artifact, required information, status, and feedback destination.

Use the contract ledger to determine whether the boundary is complete, whether either side reaches into the other's implementation, and whether ownership remains clear across the handoff.

### 5. Examine fields and statuses

Trace important fields and statuses through their lifecycle. Determine their meaning, origin, authoritative owner, consumers, allowed changes, and final use.

Review whether each item carries distinct information, supports a real downstream need, duplicates another expression, mixes different judgments, or adds complexity without a corresponding responsibility.

### 6. Map concepts to physical structure

Map semantic concepts and responsibilities to public contracts, implementation files, adapters, tests, and documentation.

Use this map to find competing sources of truth, misplaced concepts, hidden core behavior, mixed responsibilities, orphaned files, and meaningful concepts without a reliable home.

### 7. Perform a light lifecycle walkthrough

Choose one representative path and manually follow its inputs, decisions, artifacts, handoffs, statuses, and final review. When useful, follow one feedback path.

Use the walkthrough to reveal missing steps, ambiguous transitions, repeated work, broken ownership, or information that cannot support the next stage. Mark incomplete implementation or insufficient evidence without treating either as an automatic defect.

### 8. Synthesize understanding and review

Report:

1. what the repository is trying to express;
2. how its lifecycle and modules currently work;
3. how well module boundaries carry the semantic boundaries;
4. how contracts, fields, and statuses move through the chain;
5. how concepts are represented in the file structure;
6. what the light walkthrough confirms or exposes;
7. established strengths, material findings, and unresolved questions.

Support findings with repository evidence. Prefer clear qualitative judgments over numeric scores.
