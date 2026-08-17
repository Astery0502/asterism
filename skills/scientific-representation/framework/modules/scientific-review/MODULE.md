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
- assess whether the realized entry state exposes the representative structure
  or clearly identifies why a special state is the intended starting point;
- assess whether the main representation makes the accepted scientific object,
  mechanism, and observable consequence intelligibly connected;
- assess whether a researcher can use the representation to perform the
  declared explanatory, predictive, discriminating, or auditing capability;
- assess whether each major view contributes distinct understanding rather
  than restating the same quantity in another form;
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
review outcome. Correct formulas, responsive controls, visible limits, and
passing evidence do not by themselves justify acceptance when the declared
researcher capability is not attained.

## Evaluation basis

- faithfulness;
- discrimination;
- explanatory and predictive use;
- intelligibility of the object-mechanism-consequence chain;
- fitness of the entry state and controlled contrast;
- non-redundancy of major views;
- boundary visibility;
- epistemic proportionality;
- usefulness;
- traceability to the presentation question.

## Non-authority

Review does not silently modify upstream artifacts or treat successful
execution as sufficient scientific evidence.

When the presentation question asks for understanding, review includes a
fresh-reader probe: judge the primary representation before relying on extended
explanatory prose, then use the prose to evaluate precision and boundaries. A
result that is correct only after reconstructing its mechanism from scattered
readouts and notes should normally receive `revision_requested`.

## Feedback

- scientific concern to scientific inquiry;
- representation concern to representation inquiry;
- target-fit concern to target realization;
- implementation or evidence concern to application conformance.
