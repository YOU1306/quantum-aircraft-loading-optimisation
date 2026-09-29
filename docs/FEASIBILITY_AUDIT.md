# Technical Feasibility Audit

## Conclusions

### Aircraft loading is suitable for combinatorial optimisation

The decision is discrete: each cargo or baggage item must be assigned to an
allowed station. Assignment count grows combinatorially, while capacity,
compatibility and balance rules restrict feasible choices. This is a valid
optimisation application. It does not imply that classical systems are unable
to solve operational cases.

### QUBO is appropriate for a simplified model

Binary item-to-station variables naturally represent assignments. For a fixed
manifest, total weight is constant and total moment is linear in those
variables. Squared target-CG deviation therefore becomes quadratic. Exactly-one
constraints become quadratic penalties; capacity inequalities require binary
slack variables.

QUBO is less attractive when many detailed loading rules are added. Slack
variables and large penalty ranges increase the qubit count and can make QAOA
harder. The prototype therefore encodes core assignment and capacity rules,
preprocesses disallowed positions, and independently validates all modeled
constraints.

### QAOA is appropriate as an experiment, not a promised improvement

QAOA can act on the Ising Hamiltonian produced from the QUBO and genuinely
participates in selecting candidate assignments. It is suitable for a small
Qiskit demonstration. Present-day simulator cost and hardware limits prevent
an honest claim that it replaces established airline optimisation.

### Correct objective

“Absolute optimal aerodynamic neutral point” is rejected:

- the neutral point is an aerodynamic stability concept;
- it is not calculated by assigning cargo;
- “absolute optimal” is unsupported;
- no aircraft-specific drag or trim model is available.

The implemented objective minimizes normalized squared deviation from a
selected target longitudinal CG. In late-change mode it adds a declared,
secondary movement preference. This is measurable and physically meaningful
for weight-and-balance demonstration, but it is not a fuel or drag prediction.

### CG calculation

The model uses:

\[
CG = \frac{W_b a_b + \sum_i w_i a_{s(i)}}{W_b+\sum_i w_i}
\]

where \(W_b,a_b\) describe the synthetic basic aircraft and \(a_{s(i)}\) is
the arm of the assigned station. The calculation is performed outside every
solver so solver output cannot bypass validation.

### Necessary prototype constraints

- each item assigned exactly once;
- only allowed item/station combinations;
- station weight capacity;
- total payload limit;
- final CG inside the declared range;
- optional movement count after a manifest change.

Real operations require more constraints than this prototype models.

### Baselines

- Exact enumeration establishes the true optimum for small instances.
- OR-Tools CP-SAT is a legitimate scalable classical reference.

Both are given the same scenario and are scored with the same reporting
objective. Classical performance is not weakened.

### Data decision

No operational aircraft dataset is available. The repository uses a clearly
labelled synthetic two-hold demonstrator. It is sufficient to exercise moment,
CG, assignment, capacity, QUBO and late-change logic, but must not be presented
as a real aircraft.

## Primary technical risks and controls

- **QUBO penalty too small:** expose the penalty, validate decoded output and
  test sensitivity.
- **Qubit growth from slack bits:** reduce capacity units by a common divisor
  and cap the live-demo size.
- **QAOA stochastic variation:** use a fixed visible seed and report shots and
  parameters.
- **Bit-order or decode mistake:** decode by Qiskit variable names and test a
  known mapping.
- **Infeasible quantum sample:** independently check it and display violations.
- **Misleading speed comparison:** label measured local runtime and simulator
  context.
- **Synthetic data mistaken as operational:** label the UI, files, reports and
  documentation.
- **Unsupported aerospace claim:** use the target-CG objective and exclude
  fuel or drag claims.
