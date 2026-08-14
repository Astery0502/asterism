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
artifact, and verification decisions are inspectable.

## Evaluation basis

- coverage of accepted requirements;
- fitness of selected target capabilities;
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
an explicit unmet requirement.
