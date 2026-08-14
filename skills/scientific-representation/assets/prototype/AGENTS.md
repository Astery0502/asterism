# Scientific Representation Framework

## Boundary

- Treat this directory as a reusable framework, not a catalog of completed
  scientific cases.
- Keep scientific source material, analysis, case requirements, generated
  applications, and verification evidence under `work/<case>/`.
- Preserve the `TheoreticalAccount` handoff: analysis produces a bounded
  scientific account; representation converts it and the presentation
  question into requirements and an operational interface.
- Keep requirements target-neutral. Put runtime, library, rendering, and
  packaging decisions in the Scientific HTML native plan.
- Keep mechanical conformance separate from scientific review.

## Agent path

Read these files in order:

1. `modules/scientific-analysis/AGENT-GUIDE.md`
2. `method.json`
3. `adapters/scientific-html/AGENT-GUIDE.md`
4. `adapters/scientific-html/capabilities.json`
5. `adapters/scientific-html/plan-contract.json`
6. `adapters/scientific-html/artifact-contract.json`

Inspect local runtime readiness with:

```powershell
python prototype.py doctor --target scientific-html --json
```

Validate a completed work product with:

```powershell
python adapters/scientific-html/scripts/validate-work-product.py work/<case> --write-receipt
```

Do not add a completed case to this framework snapshot. Promote reusable
method, capability, or contract improvements independently from case records.
