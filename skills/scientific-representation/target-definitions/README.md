# Target Definitions

This directory owns target-specific, declarative expectations consumed by the
target-realization and application-conformance lifecycle stages. Each target
definition may provide a capability catalog, runtime-observation policy, plan
contract, artifact contract, Agent guide, and target-specific validation
extensions.

A target definition does not translate representation requirements or realize
an application. Agent consumer runtimes inject `TargetTranslator` and
`ApplicationRealizer` implementations through the target-neutral ports.

Executable support for these definitions lives in the separate
`scientific_representation_target_definitions` Python package. Core code loads
that package dynamically and must not import a concrete definition statically.
