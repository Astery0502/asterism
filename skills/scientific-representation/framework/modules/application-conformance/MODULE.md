# Application Conformance Module

Status: normative Agent behavior module for implementation and mechanical evidence.
Contract: `framework/modules/application-conformance/contract.json`

## Purpose

Materialize an accepted target-native plan and establish whether the declared
implementation, artifacts, and mechanical checks conform to that plan.

## Input

- `TheoreticalAccount` and `RepresentationRequirementsPackage` as read-only
  traceability context;
- `TargetNativeDecisionPlan` as the implementation authority;
- `ApplicationArtifactContract` as the declared output and evidence envelope.

## Agent responsibilities

- implement the accepted computation, interaction, views, and delivery plan;
- preserve requirement and plan traceability;
- execute declared numerical, behavioral, browser, and artifact checks;
- record mechanical evidence and implementation failures;
- publish the declared application artifact inventory.

## Output handoff

- `ApplicationExecutionRecord`;
- `ApplicationArtifact`;
- `ApplicationManifest`;
- `MechanicalEvidence`;
- `MechanicalConformanceRecord`.

An execution failure completes this module with an execution record and a
failed conformance record. It does not fabricate a manifest and is not
admitted to scientific review.

## Completion condition

The module is complete when the implementation result and all evidence records
required by the selected target contract are present, resolvable, and report
their conformance status.

## Evaluation basis

- agreement with the accepted native plan;
- artifact closure;
- identity and requirement traceability;
- declared numerical tolerances;
- interaction and browser behavior;
- dependency provenance.

## Non-authority

This module does not weaken upstream requirements to obtain a pass, infer
scientific validity from execution success, or replace scientific review.

## Feedback

Implementation and evidence defects remain in this module. Target-plan defects
return to target realization. Scientific or representation concerns return to
their owning inquiry module.
