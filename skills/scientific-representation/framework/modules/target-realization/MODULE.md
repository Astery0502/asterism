# Target Realization Module

Status: normative Agent behavior module for target-native planning.
Contract: `framework/modules/target-realization/contract.json`

## Purpose

Translate an accepted target-neutral representation package into an
inspectable target-native decision plan without changing its scientific
meaning.

## Inputs

- `TheoreticalAccount`, as read-only scientific context;
- `RepresentationRequirementsPackage`;
- `TargetCapabilityCatalog`;
- `RuntimeCapabilityObservation`;
- `TargetPlanContract`, which declares the accepted plan shape;
- `ApplicationArtifactContract`, which constrains the artifact inventory the
  plan must make implementable.

## Agent responsibilities

- select target capabilities that satisfy accepted requirements;
- choose computation timing and method;
- translate controls, interactions, views, dependencies, delivery, and checks
  into target-native decisions;
- choose a target-native visual and interaction grammar that keeps the accepted
  scientific object, mechanism, contrast, and consequence recognizable;
- give each view a distinct explanatory role and avoid views that merely repeat
  the same observable without adding a comparison, relationship, or diagnostic;
- plan the entry state, change encoding, and control-to-response proximity so
  the declared researcher capability is attainable in the realized target;
- preserve the accepted interface snapshot and requirement traceability;
- record conditional or unmet requirements instead of removing them;
- define the artifact inventory and verification plan.

## Output handoff

- `TargetNativeDecisionPlan`.
- `TargetPlanValidationRecord`.

## Completion condition

Planning is complete when every pivotal representation requirement is covered,
conditional, or explicitly unmet; selected capabilities are available in the
target profile; and computation, interaction, view, delivery, dependency,
artifact, and verification decisions are inspectable. Coverage alone is not
completion when the selected target-native grammar obscures the explanatory
relationships accepted upstream.

## Evaluation basis

- coverage of accepted requirements;
- fitness of selected target capabilities;
- fitness of the visual and interaction grammar for the scientific object;
- continuity from control or contrast to observable response;
- non-redundant explanatory roles across views;
- traceability;
- explicit numeric and delivery contracts;
- implementability;
- visible unmet obligations.

## Non-authority

This module does not change scientific claims, rewrite their limits, delete an
inconvenient requirement, or perform scientific review. Access to the
`TheoreticalAccount` does not authorize reinterpretation of it.

## Feedback

Scientific or explanatory problems return to their owning inquiry module. A
target capability mismatch remains here and may lead to a different target or
an explicit unmet requirement. A poor layout, encoding, default presentation,
or target-native interaction remains a target-realization concern even when the
upstream meaning is sound.
