# Scientific Review Module

Status: normative Agent behavior module for independent scientific judgment.
Contract: `framework/modules/scientific-review/contract.json`

## Purpose

Judge whether a realized representation is scientifically faithful,
discriminating, bounded, and useful for its accepted presentation question.
Scientific review is independent of mechanical conformance.

## Inputs

- `TheoreticalAccount`;
- `RepresentationRequirementsPackage`;
- `TargetNativeDecisionPlan`;
- a completed `ApplicationExecutionRecord`;
- `ApplicationArtifact`;
- `ApplicationManifest`;
- `MechanicalEvidence`;
- `MechanicalConformanceRecord`.

## Agent responsibilities

- assess fidelity to the accepted scientific account;
- assess whether controlled contrasts and observables discriminate the intended
  mechanism;
- assess whether assumptions, regimes, quantities, and limits remain visible;
- assess whether interactions retain their declared scientific meaning;
- distinguish scientific, representation, target-fit, implementation, and
  evidence concerns;
- direct each concern to the module that owns it.

## Output handoff

- `ScientificReviewRecord`.

The reviewer also returns one explicit judgment label: `accepted`,
`revision_requested`, or `inconclusive`. The label indexes the review record;
it does not replace its scientific basis.

## Completion condition

Review is complete when its judgment, basis, important limits, and any module-
specific feedback are explicit. A mechanical pass does not predetermine the
review outcome.

## Evaluation basis

- faithfulness;
- discrimination;
- boundary visibility;
- epistemic proportionality;
- usefulness;
- traceability to the presentation question.

## Non-authority

Review does not silently modify upstream artifacts or treat successful
execution as sufficient scientific evidence.

## Feedback

- scientific concern to scientific inquiry;
- representation concern to representation inquiry;
- target-fit concern to target realization;
- implementation or evidence concern to application conformance.
