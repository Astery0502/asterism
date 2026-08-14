# Framework Handoffs

Agent behavior modules communicate through stable, inspectable artifacts:

```text
ScientificInput + AnalysisQuestion
  -> TheoreticalAccount

TheoreticalAccount + PresentationInquirySeed
  -> RepresentationRequirementsPackage

TheoreticalAccount + RepresentationRequirementsPackage
  + target capabilities + plan and artifact contracts
  -> TargetNativeDecisionPlan + TargetPlanValidationRecord

TheoreticalAccount + RepresentationRequirementsPackage + TargetNativeDecisionPlan
  + ApplicationArtifactContract
  -> ApplicationExecutionRecord + ApplicationArtifact
  + ApplicationManifest + MechanicalEvidence + MechanicalConformanceRecord

accepted artifacts + completed application execution + conformance record
  -> ScientificReviewRecord
```

The authoritative contract for each handoff is colocated with its producing
module. Handoffs are resumable boundaries, not claims that feedback can never
return to an earlier module.
