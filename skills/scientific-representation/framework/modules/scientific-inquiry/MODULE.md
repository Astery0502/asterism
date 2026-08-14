# Scientific Inquiry Module

Status: normative default Agent behavior module for scientific inquiry.
Contract: `framework/modules/scientific-inquiry/contract.json`

This module receives an accepted equation case or supplied
mathematical-physics material together with an analysis question. It produces
the project's native `TheoreticalAccount`, which the representation phase
consumes directly. Within the wider framework, that name denotes the bounded
scientific-account role. Other available scientific-analysis methods may
express an equivalent result differently and use lightweight handoff
preparation before representation.

## 1. Research question

The analysis framework asks:

> Can an agent develop a predictive, structural, and regime-aware
> understanding of an accepted equation, beyond restatement or solution alone?

The desired result is **usable understanding**. A researcher who reads the
account should be able to:

- state the equation's central mechanism;
- anticipate a meaningful qualitative response to a changed term, parameter,
  or condition;
- connect that response to a structural feature;
- recognize where the explanation applies and where it may fail;
- distinguish mathematical consequence, contextual knowledge, and heuristic
  interpretation; and
- see one worthwhile consequence or next question.

Derivation, calculation, examples, and representations serve these abilities.
Their value comes from the understanding they make possible.

## 2. Scope and freedom of inquiry

The theory part receives one read-only accepted equation case or supplied
mathematical-physics input and produces one `TheoreticalAccount`.

The input anchors the equation, notation, context, assumptions, and data.
Within that anchor, the analyst has freedom to choose:

- the order and recurrence of the reasoning questions;
- the examples, limits, counterfactuals, and representations explored;
- the amount of derivation or computation that illuminates the equation;
- the point at which several observations converge on a central relationship;
  and
- the form in which the final understanding is expressed.

The framework supplies lenses for inquiry and qualities for evaluation. It
leaves the route of discovery open.

## 3. Five questions, one evolving inquiry

The five questions are overlapping reasoning operations. They may repeat,
braid together, or redirect attention as understanding develops.

```text
Ground -> Predict <-> Stress -> focus -> Bound -> Extend and compose
```

`focus` names the natural convergence on a central mechanism or relationship.
It may emerge gradually from the surrounding inquiry.

### 3.1 Ground — What is the equation saying?

Ground connects the formal expression to its accepted mathematical and
physical objects:

- the equation and notation;
- mathematical objects and operations;
- the meaning and role of variables and parameters;
- the dimensional, dimensionless, normalized, or code-unit status of
  quantities that may later be compared or visualized;
- the central balance, constraint, or evolution law;
- important term roles;
- domain, coordinate system, and required data; and
- source-supported physical or interpretive meaning.

Ground gives later intuition something definite to refer to. When accepted
context leaves physical meaning open, a mathematical reading can remain exact
while analogies remain exploratory.

When a quantity is normalized or transformed, retain the reference scale or
definition that gives its numerical values meaning. A later representation
should not have to infer whether an unlabeled number is dimensional,
dimensionless, normalized, or expressed in code units.

### 3.2 Predict — What behavior should it create?

Predict develops a qualitative model of what the equation should do before a
complete solution is needed. Prediction may begin tentatively after enough
grounding, change during Stress, and recur when another representation or
example becomes informative.

Type-appropriate expectations may concern:

- propagation or smoothing;
- oscillation, growth, decay, or stability;
- equilibrium, branching, or bifurcation;
- modes, singularities, or asymptotic behavior; or
- sensitivity to parameters, initial data, or boundary data.

A useful prediction gives the analyst a revisable picture of the solution
space and a way to recognize informative contrasts.

### 3.3 Stress — Why this form?

Stress explores examples, counterfactuals, limits, and alternative
representations to discover which relationships organize the behavior. Useful
directions include:

- removing, comparing, or making a term dominant;
- reversing a sign;
- changing derivative order;
- taking a parameter or asymptotic limit;
- examining dimensions, scaling, symmetry, or conservation;
- checking closure; or
- varying initial or boundary data.

Stress can move through several directions before a useful contrast becomes
visible. Productive and unproductive attempts both shape attention. Focus
emerges when one relationship explains more of the observed behavior than its
alternatives.

For a necessity claim, the bounded form is:

> Feature X is necessary for property Y under assumptions A.

The assumptions and the named property give the claim its mathematical reach.

### 3.4 Bound — When is this account valid?

Bound synthesizes the understanding developed through Ground, Predict, and
Stress. It locates that understanding within:

- assumptions and domain;
- required initial, boundary, or auxiliary data;
- closure laws;
- parameter regime and approximation order;
- regularity or solution concept where relevant;
- known failure conditions; and
- unresolved edges.

Three forms of sufficiency offer useful lenses:

- **Mathematical sufficiency:** the equation, domain, assumptions, and data
  adequately specify the mathematical problem.
- **Modeling sufficiency:** the model represents a target phenomenon within a
  declared regime and accuracy.
- **Interpretive sufficiency:** the account explains the selected behavior
  within its intended purpose.

Bound gives the central insight a meaningful range rather than a separate
compliance layer.

### 3.5 Extend — Where does it lead?

Extend draws out a robust consequence, revealing contrast, surprise, or
worthwhile next question. Possible directions include a nearby model, limiting
theory, alternative exact representation, newly exposed uncertainty, or
discriminating observation.

Composition is itself part of inquiry. A better representation, unifying
mechanism, external connection, or new consequence may become visible while
the account is being written. Its value depends on the explanatory work it
performs and the clarity of its mathematical or heuristic status.

## 4. Selective checks

Checks are reasoning instruments within the wider exploration. They are most
informative when they separate live explanations, reveal a hidden condition,
or materially change confidence in the emerging account.

A check may be an exact derivation, counterexample, limiting argument,
dimensional comparison, symbolic computation, numerical exploration, or
another form suited to the question. A formal check becomes interpretable
through a sufficiently clear proposition, assumptions, and relation between
its result and the account.

Several exploratory probes may lead to one illuminating check, several
complementary checks, or a well-defined unresolved edge. The analysis is ready
to compose when its central behavior, structural basis, validity range, and
important uncertainty have become clear enough for the intended account.

## 5. Compact result

`TheoreticalAccount` is a short, reasoned brief that presents what is worth
retaining from the inquiry. A strong account brings together three qualities:

1. **Insight** — a central mechanism and its important qualitative behavior,
   grounded in the symbols and terms needed to understand it.
2. **Basis and bounds** — the examples, contrasts, derivations, or checks that
   make the insight intelligible, together with its assumptions, regime, and
   unresolved edges.
3. **Frontier** — a robust consequence or worthwhile next question.

These qualities can appear in the order and form that best serves the
argument. Detail earns its place by helping the reader understand or trust the
central insight.

The account may contain ideas first discovered during composition. Its
epistemic clarity lets a reader recognize what comes from the accepted case,
what follows mathematically, what draws on wider knowledge, what serves as a
heuristic, and what remains uncertain.

## 6. Epistemic clarity

Epistemic clarity is a reader-facing quality rather than a claim-admission
procedure. It has several dimensions:

- **Source fidelity:** the accepted equation and context remain recognizable
  beside reconstructions and interpretations.
- **Mathematical support:** derivations, examples, and computations support the
  scope of the conclusions drawn from them.
- **Contextual honesty:** relevant wider knowledge is recognizable as context
  rather than a consequence of the accepted equation.
- **Heuristic clarity:** analogies and intuitive pictures communicate their
  exploratory status.
- **Proportional confidence:** the strength of the language matches the
  available mathematical and empirical basis.
- **Visible uncertainty:** unresolved conditions remain part of the account's
  meaning.

Numerical, symbolic, and exact reasoning can each contribute different forms
of insight. Their interpretation establishes what they add to the account.

## 7. Universal questions, type-directed lenses

The five questions are available across equation families. Their emphasis and
subquestions follow the mathematical object and scientific context.

| Equation family | High-value lenses |
| --- | --- |
| Algebraic or constraint system | solution geometry, branches, degeneracy, singular set, identifiability |
| ODE or dynamical system | equilibria, stability, timescales, invariants, stiffness, bifurcations |
| PDE | principal part, type, characteristics, propagation or smoothing, initial and boundary data, weak solutions |
| Variational system | energy or action, stationary points, convexity, symmetry, conserved quantities |
| Eigenvalue or operator problem | spectrum, modes, conditioning, completeness, boundary dependence |
| Stochastic equation | noise interpretation, moments, distribution evolution, stationary states, rare events |

These lenses invite promising directions. The analyst chooses the combination
that reveals the equation most effectively.

## 8. Open evaluation criteria

Evaluation concerns the understanding achieved rather than conformity to one
route. The account can be considered through six open criteria:

- **Qualitative reach:** it makes meaningful behavior or change foreseeable.
- **Structural insight:** it reveals relationships that explain why the
  equation has its form.
- **Boundary awareness:** it gives the insight an intelligible domain, regime,
  and edge.
- **Epistemic clarity:** it communicates the basis and confidence of important
  ideas in proportion to their role.
- **Economy:** its detail supports a coherent central understanding.
- **Fertility:** it opens a worthwhile consequence, representation, or next
  question.

Several analyses may satisfy these criteria through different paths and arrive
at different but compatible accounts. New synthesis during composition can
increase explanatory or generative value. Evaluation considers how well each
idea works within the final account and how responsibly its status is
conveyed.

One case can reveal weaknesses in the framework's use. Generality grows through
comparison across structurally different equation families.
