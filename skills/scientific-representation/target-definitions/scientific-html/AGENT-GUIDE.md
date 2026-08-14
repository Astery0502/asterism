# Scientific HTML Target Definition Guide

## Purpose

Turn an accepted mathematical-physics requirements package into a useful,
interactive HTML product. The requirements establish the scientific meaning;
the agent chooses the implementation that expresses it clearly.

## Read these inputs

1. `analysis/theoretical-account.md` — model, mechanism, assumptions, scope.
2. `representation/representation-intent.json` — presentation question and
   pivotal claim chain.
3. `representation/representation-requirements.md` — complete product meaning.
4. `representation/representation-interface.json` — concise controls, anchors,
   views, and exports.
5. `capabilities.json` and the current `doctor` result — available approaches.
6. `contracts/plan.json` and `contracts/artifact.json` — portable exchange
   shapes.

The prose requirements are authoritative. The intent and interface files are
working summaries that make the key semantics easy to find.

## Realization authority

A host Agent consumer may perform target translation and implementation
directly as one continuous task. Application integrations that need a Python
boundary may instead implement this small interface:

```python
class Realizer:
    realizer_id = "stable-realizer-id"
    target_id = "scientific-html"

    def translate(self, request: TargetPlanningRequest) -> TargetPlanDraft:
        ...

    def implement(
        self,
        request: TargetImplementationRequest,
        output_root: Path,
    ) -> ApplicationDraft:
        ...
```

The host Agent owns the same decisions whether or not a Python object is used.
`translate` records target-native decisions: computation timing, controls,
views, packaging, toolchain profile, expected artifacts, and checks.
`implement` turns those decisions into the application. The same authority may
own both responsibilities; the persisted plan keeps their meanings explicit.
Do not require a Skill user to supply an importable implementation merely to
let the current host Agent exercise this authority.

## Choose an approach

Start from the scientific behavior and choose the smallest suitable profile:

- finite validated states and standard scientific plots:
  `html-plotly-static-v1`;
- small continuous browser formulas: `html-bokeh-customjs-v1`;
- Python/SciPy recalculation in the browser: `html-panel-pyodide-v1`;
- bespoke SVG or Canvas explanation: `html-observable-custom-v1`;
- editable computational exploration: `jupyterlite-exploration-v1`.

These are useful routes, not page templates. The agent may choose layout,
visual grammar, source organization, numerical technique, and interaction
design according to the case. A new capability profile can be added when a
different implementation is a better fit.

## Preserve quantity meaning

The target-neutral quantity meanings are owned by
`framework/modules/representation-inquiry/MODULE.md`. Implement those accepted
meanings in axes, colorbars, controls, numerical readouts, hover values, and
nearby definitions. Treat a colorbar as a quantitative axis rather than
decoration. The native plan records how each selected HTML view exposes the
accepted meaning.

## Practical implementation order

1. Implement the model and observables as ordinary functions.
2. Check the pivotal identity, residual, or comparison on representative
   states.
3. Build the interaction state and views around the presentation question.
4. Confirm that axes, color scales, controls, readouts, and hover values retain
   the accepted quantity meanings.
5. Package the selected HTML topology and write `application-manifest.json`.
6. Open the result in a real browser and record the selected evidence level.

For a build-time product, Python may precompute validated states and browser
code may select among them. For a live-computation product, keep the numerical
method visible in the plan and application source. Both can produce first-class
Scientific HTML products.

## Verification levels

The default verification level is `fast`. It asks for:

- one pivotal numerical identity or residual;
- a fresh browser load with a clean console;
- one interaction that changes the intended observable when controls are present;
- a resolvable entry point and manifest inventory.

Use `verification.level: full` when promoting a durable reference, when the
requirements call for exact anchors or offline closure, or when broader risk
justifies it. Full evidence may cover bounds, defaults, linked views, invalid
states, screenshots, invariants, boundary conditions, assets, and dependency
provenance.

Set `verification.level: full` explicitly for a full reference-product record.

## Result boundary

Mechanical conformance means that the declared product, manifest, scientific
probe, and browser behavior agree. Scientific review remains a separate human
or scientific-analysis judgment. An agent may record useful limitations and
continuation questions in the page without turning the build process into a
formal review board.

If a chosen profile is a poor fit, report the missing capability and select or
add a better route. Preserve the scientific claim and its stated limits while
letting the implementation remain case-specific.
