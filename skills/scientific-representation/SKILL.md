---
name: scientific-representation
description: Turn raw scientific literature, equations, formulas, and mathematical-physics descriptions plus a user's presentation direction into a case-specific, interactive, validated standalone Scientific HTML representation. Use when Codex should run the embedded prototype's complete scientific-analysis, representation-requirements, native-planning, implementation, and fast-verification workflow from original scientific material.
disable-model-invocation: true
---

# Scientific Representation

Use the embedded framework runtime as the authority for method, semantics,
target capabilities, and contracts. Use this Skill to coordinate that
authority into one complete Agent workflow.

## Create the workspace

Resolve `<skill-root>` as the directory containing this `SKILL.md`, then create
a writable Prototype copy:

```powershell
python <skill-root>/scripts/create-workspace.py <destination>
```

Perform the case work in that copy. Keep
`<skill-root>/assets/prototype/` as the reusable framework snapshot. The
snapshot intentionally contains no recorded cases, generated products, case
evidence, or case-specific tests.

## Read the authority

Read these files completely and in order from the copied workspace:

1. `AGENTS.md`
2. `modules/scientific-analysis/AGENT-GUIDE.md`
3. `method.json`
4. `adapters/scientific-html/AGENT-GUIDE.md`
5. the capability and contract files referenced by the HTML guide

Let the embedded Prototype define all stage semantics, field shapes, target
contracts, and verification details. Keep this outer Skill responsible only
for routing those authoritative parts into one workflow.

Inspect the current Scientific HTML runtime from the copied workspace:

```powershell
python prototype.py doctor --target scientific-html --json
```

## Execute the method

Accept two distinct inputs:

- the original scientific literature, equations, formulas, or description;
- the user's desired presentation direction.

Preserve them as separate input records. Derive the scientific analysis
question from the source's explanatory problem, then form the scientific
account from that question and the source. Introduce the user's presentation
direction when the Prototype method forms representation intent, requirements,
and interface semantics.

For a new case, perform the scientific analysis, target translation, and
application implementation directly as the Agent:

1. Produce the bounded `TheoreticalAccount` defined by the analysis guide.
2. Convert that account and the presentation direction into target-neutral
   representation requirements.
3. Translate the accepted requirements into an inert Scientific HTML native
   plan.
4. Implement the case-specific model, interaction, views, explanation, and
   standalone product according to the HTML guide and selected capability
   profile.
5. Record the compact evidence required by fast verification.

Place the case under `work/<case>/` and preserve the Prototype boundaries:

```text
input/
  scientific-input.md
  presentation-direction.md
analysis/
  theoretical-account.md
representation/
  representation-intent.json
  representation-requirements.md
  representation-interface.json
targets/scientific-html/
  native-plan.json
application/
  model and build sources
  verification/
  evidence/
  application-manifest.json
  product/index.html
```

## Verify and deliver

Use the embedded Prototype's fast verification route by default. Let its
selected capability profile and work-product gate determine the current checks
and evidence shape.

From the copied workspace, run the Prototype's work-product gate:

```powershell
python adapters/scientific-html/scripts/validate-work-product.py work/<case> --write-receipt
```

Mechanical checks establish implementation conformance; they do not
independently establish scientific review.

Deliver the independently copyable
`work/<case>/application/product/index.html` with a concise account of its
scientific interpretation, interaction semantics, limits, and verification
result.

## Embedded resources

- `assets/prototype/` contains the portable framework runtime without recorded
  cases or generated evidence.
- `scripts/create-workspace.py` creates a clean working copy without modifying
  the embedded snapshot.
