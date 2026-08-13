# Canonical Scientific Investigation Concerns

This reference owns the semantic meaning of the investigation mode. Templates
render these concerns but do not define or expand them.

The initializer uses these concerns during one bounded initialization or
migration. Afterward, selected local files carry the applicable concerns without
depending on this reference or the injector.

## Concern index

- `SCI-PROTOTYPE-FIRST`
- `SCI-SCIENCE-FIRST`
- `SCI-INQUIRY-FREEDOM`
- `SCI-EVIDENCE-STATUS`
- `SCI-MEANING-PRESERVATION`
- `SCI-OUTPUT-REGISTRATION`
- `SCI-SPINE-TESTING`
- `SCI-DURABLE-MEMORY`
- `SCI-GOAL-INTEGRITY`
- `SCI-REVIEW-OUTCOMES`
- `SCI-VERSION-PROVENANCE`
- `SCI-PROPORTIONAL-ESCALATION`

## `SCI-PROTOTYPE-FIRST`

Begin every new scientific direction with the smallest direct prototype that
can answer, distinguish, or sharpen one question. Include only the accepted
basis, direct scientific instrument, relevant observables or outputs,
scientific-spine checks, interpretation, limitations, and next question needed
for that bounded inquiry. Preserve the answer and continue from its scientific
consequence; do not add work merely to make the prototype appear complete. When
unfamiliarity or likely duplication could affect interpretation, briefly inspect
readily available prior practice. Absence of precedent does not block the
prototype.

## `SCI-SCIENCE-FIRST`

Judge work by scientific value rather than procedural volume. A useful
prototype may answer or refine a question, reveal structure or a failure mode,
support a prediction, distinguish explanations, expose uncertainty, create a
useful scientific product, or open the next prototype. A refuted conjecture,
scoped negative result, justified redirection, or sharply defined unresolved
question can be successful.

## `SCI-INQUIRY-FREEDOM`

Within inherited authority and the current charter, let the investigating agent
choose order, recurrence, depth, tools, examples, computations,
representations, and stopping points according to the developing science.
Ground, Predict, Stress, Bound, and Extend are optional lenses, not mandatory
stages or headings.

## `SCI-EVIDENCE-STATUS`

Keep inherited findings, direct observations, derived results, assumptions or
project choices, interpretations or heuristics, and unresolved possibilities
recognizable. Make support proportional to scientific role. Do not describe
numerical evidence as proof, treat uninterpreted tool output as a conclusion, or
claim more confidence than the scientific basis supports.

## `SCI-MEANING-PRESERVATION`

Preserve assumptions, valid regimes, units, coordinates, frames, signs,
normalization, transformations, observation conditions, masks, uncertainty,
and invalid-data meaning when they can alter interpretation. Keep observations,
derived quantities, models, representations, and interpretations distinct.
Never silently alter authoritative source material. Keep inherited authority
and accepted source meaning, direct evidence, and investigation-derived working
contracts distinct. Working contracts are provisional coordination devices,
not established truth; never let one override conflicting evidence or silently
promote it into the accepted basis.

## `SCI-OUTPUT-REGISTRATION`

Treat a generated output as a product only when it must persist because it
materially affects interpretation, supports later prototypes, or will be handed
off. Leave other work in disposable scratch. Use `PRODUCTS.toml` as the sole
investigation-local product registry; other records reference product IDs.
Record only the metadata needed to identify, reproduce, interpret, and retain
each product. Product inputs own dependency edges through `product:`, `source:`,
or `identity:` references. Add checks, interpretation, and limitations only
when material. Raw evidence is immutable; corrections use a new product ID and
may point to the product they supersede.

## `SCI-SPINE-TESTING`

Test only the scientific spine of the current prototype. Use the smallest
checks capable of detecting a failure that would change interpretation:
representative anchors, central identities or limits, material signs or
coordinates, direct cross-checks, decisive sensitivities, central plotted
relationships, and necessary failure conditions. Established dependencies are
not test targets unless their behavior is the governing question. When a
working contract affects interpretation, use the smallest check that could
challenge a claim or detect a material mismatch with a local convention; do not
use a provisional claim as the oracle. Do not defend a working contract with
extra proof, tests, or debugging. Use only what is needed to distinguish
implementation error from scientific failure.

## `SCI-DURABLE-MEMORY`

Use investigation files—not conversation history or scratch work—to preserve
purpose, state, products, decisions, uncertainty, and the next useful move.
Record material scientific changes rather than routine inspection, debugging,
or every command. Permit inheritance before scientific completion when current
understanding and continuation are explicit.

## `SCI-GOAL-INTEGRITY`

Allow the charter to change when science justifies it. Update it to the current
truth and record the evidence and reason in Progress. Do not preserve obsolete
wording for appearance or silently move the goal after seeing a result. When a
material contradiction, repeated failure, or unexplained sensitivity appears,
pause expansion and reconsider the weakest relevant working contract,
assumption, representation, or method. Challenge, reject, or supersede a
contract when the conflict remains, record why in Progress, and revisit only
materially affected results.

## `SCI-REVIEW-OUTCOMES`

Review prototypes and products against the current charter, not process volume.
Process details matter only when they limit interpretation. Use:

- `Achieved` when the current purpose is adequately answered;
- `Partially achieved` when useful progress leaves a material part open;
- `Redirected` when evidence makes another question more valuable; and
- `Inconclusive` when no useful conclusion is supported but the attempted basis
  and unresolved condition are recorded.

## `SCI-VERSION-PROVENANCE`

Use Git, when available—not defensive filesystem copies—for ordinary history
and recovery of tracked investigation files. Never create backup, snapshot,
before-edit, duplicate-tree, or shadow-registry files solely for rollback or
“just in case” safety. Commit only when the user or inherited project authority
permits it. Version history supports inheritance and reversal, not scientific
correctness or simulated activity.

## `SCI-PROPORTIONAL-ESCALATION`

Use bounded prototypes without mandatory phases, gates, or controlled
protocols. Add a working contract only when an investigation-derived claim or
local convention materially affects interpretation and must be reused or
challenged across prototypes or agents. Keep prototype-local assumptions in
Progress; do not use contracts to repeat accepted basis or direct evidence.
Keep one current evidence gate in Progress; add `PHASES.md` only for several
ordered gates. Use a controlled study only when the research question concerns
a process comparison or knowledge boundary, and name the variable being
protected or compared.
