---
name: scientific-representation
description: Use the packaged Scientific Representation project to produce and validate one final scientific work product in a continuous Agent execution.
---

# Scientific Representation

Use the packaged upstream project directly to turn scientific material and
presentation intent into one inspectable, validated work product. Act as the
scientific analyst, representation designer, target realizer, implementer, and
scientific reviewer in one continuous execution. Use lifecycle stages as
scientific responsibilities while keeping the work product a single delivery.

## Inspect the packaged authority

Read `skill-interface.json` and `framework.json`. Follow the referenced
principles, method, pipeline, module guides, module contracts, and selected
target definition. Inspect available targets and runtime readiness with the
packaged project:

```bash
python3 scientific-representation.py method --json
python3 scientific-representation.py targets --json
python3 scientific-representation.py doctor --target <target> --json
```

Use the target definition record to locate its Agent guide, capabilities, plan
contract, artifact contract, and final work-product validator. Do not infer
these resources from this wrapper or maintain a parallel Skill-specific model.

## Produce one final work product

Complete the packaged scientific lifecycle internally before delivering the
result. Create one coherent work-product directory outside the installed Skill.
The directory may contain canonical scientific, representation, plan,
application, evidence, and review records required for inspectability, but they
are parts of one final delivery—not separate Agent responses or interactive
stage checkpoints.

Do not ask the user to provide Python module/class implementations for Agent
roles. Complete the lifecycle without intermediate user-facing checkpoints.
Use the project's canonical records and validators without copying their
semantics into new wrapper files.

## Validate and return

Read `work_product_validator` from the selected target definition and run it on
the completed work product. When supported, request a written receipt. Require
the final validator result to pass before reporting success.

Return only the final work-product location, artifact entry point, validation
receipt, scientific judgment, important limits, and unmet requirements. Do not
surface internal lifecycle records as separate deliverables unless the user
asks to inspect them.
