# Quantum-Assisted Decision Support for Aircraft Loading Optimisation

A working hackathon prototype that models a simplified aircraft-loading problem,
solves it with QAOA through Qiskit, compares the same problem with honest
classical methods, and independently checks every returned loading
configuration.

> **Safety and data notice:** This is a research and education prototype, not an
> operational aircraft-loading system. The built-in aircraft and manifest are
> **SYNTHETIC DATA** and do not describe a certificated aircraft or airline
> configuration. A qualified person remains responsible for operational
> verification and approval.

## Research question

Existing aircraft-loading systems already use effective classical
optimisation. This project does **not** claim that quantum computing currently
beats those systems. It measures whether QAOA can return feasible,
near-optimal candidates and studies how quantum and classical methods behave as
the number of loading decisions increases.

## What the prototype does

- loads an editable synthetic aircraft and cargo manifest;
- calculates weight, moment and longitudinal centre of gravity (CG);
- models item-to-station decisions with binary variables;
- builds a constrained quadratic model and converts it to a QUBO;
- runs genuine QAOA with Qiskit and Qiskit Aer;
- solves the same scenario by exact enumeration and OR-Tools CP-SAT;
- independently checks assignment, capacity, payload and CG constraints;
- reports objective value, feasibility and measured local runtime;
- adds late baggage, rechecks the loading and generates a revised candidate;
- runs small scaling experiments without assuming quantum advantage;
- exports HTML, CSV and JSON results;
- provides a local Streamlit interface with no internet dependency.

## Quick start

### Windows: prepared environment

Double-click `START_DEMO.bat`.

### Command line

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
streamlit run app.py
```

Open the local address shown by Streamlit, normally
`http://localhost:8501`.

## Three-minute workflow

1. Open **Dashboard** and state the research question.
2. Open **Aircraft & Manifest** to show the labelled synthetic inputs.
3. Open **Optimisation** and run:
   - exact verification;
   - OR-Tools baseline;
   - QAOA / Qiskit.
4. Compare feasibility, objective, CG and measured runtime.
5. Open **Quantum Analysis** to show QUBO size, circuit depth, shots and
   simulator metadata from the actual run.
6. Open **Late Change**, add the built-in late baggage batch and re-optimise.
7. Open **Export** and download the calculated report.

For a presentation-safe path, run exact and OR-Tools first. QAOA uses only the
local simulator and the built-in case is intentionally small.

## Mathematical model

### Decision variables

For item \(i\) and allowed station \(j\):

\[
x_{ij} =
\begin{cases}
1 & \text{if item } i \text{ is assigned to station } j \\
0 & \text{otherwise}
\end{cases}
\]

Each item is assigned exactly once:

\[
\sum_{j \in A_i}x_{ij}=1
\]

Station capacity is:

\[
\sum_i w_i x_{ij}\le C_j
\]

Disallowed item/station combinations are not created as variables.

### Weight, moment and CG

\[
M = M_\text{basic} + \sum_{i,j} w_i a_j x_{ij}
\]

\[
W = W_\text{basic} + \sum_i w_i
\qquad
CG = \frac{M}{W}
\]

For a fixed manifest, \(W\) is constant. Therefore minimizing squared target
moment error is equivalent to minimizing squared target-CG error:

\[
\left(\frac{M-W\,CG_\text{target}}
{W(CG_\text{max}-CG_\text{min})}\right)^2
\]

The denominator only normalizes the number. In a late-change run, the objective
adds a small, declared preference for keeping an existing item at its current
station.

This objective is **not** an aerodynamic neutral point, drag model or fuel
saving calculation. Those claims require aircraft-specific validated data that
this project does not have.

### QUBO

The target-moment expression is linear in binary variables; squaring it
produces linear and pairwise quadratic terms. Qiskit Optimization converts the
exactly-one and capacity constraints into QUBO penalties, adding binary slack
variables for inequalities.

The demo uses a declared penalty of 20. The software exposes QUBO variable and
constraint counts and validates the decoded result. Penalty sensitivity should
be included in any final experimental discussion.

The allowable CG envelope is independently checked after decoding. This is
deliberate: encoding every operational rule as a QUBO penalty can increase
qubit count and coefficient range. A candidate outside the range is reported
as infeasible.

### QAOA

The QUBO is mapped to a cost Hamiltonian. QAOA alternates cost and mixer
operations for depth \(p\), while COBYLA updates circuit parameters. The
application uses:

- `qiskit_optimization.minimum_eigensolvers.QAOA`;
- Qiskit V2 primitives;
- `qiskit_aer.primitives.SamplerV2`;
- an Aer statevector simulation method with finite shot sampling;
- a fixed, visible random seed for reproducibility.

Measured bitstrings are decoded into item-to-station assignments and then
checked by code that is independent of the QUBO penalties.

QAOA is a heuristic. It does not enumerate every assignment and does not
guarantee the global optimum.

## Classical baselines

1. **Exact enumeration** tests every allowed assignment for small cases. It
   establishes the true optimum and validates QAOA-sized instances.
2. **OR-Tools CP-SAT** represents the same assignment, capacity, CG and
   late-movement conditions with integer constraints. It is not intentionally
   weakened and is the more scalable classical reference.

Every solver is reported using the same independently calculated objective.

## Data classifications

All important numbers are labelled by one of:

- **SOURCE** — copied from an identified external source;
- **ASSUMPTION** — a chosen modelling or algorithm setting;
- **SYNTHETIC DATA** — invented solely for this non-operational demonstration;
- **EXPERIMENTAL RESULT** — produced by an actual local run.

The repository currently contains no aircraft operational data. Built-in
weights, arms, capacities and CG limits are **SYNTHETIC DATA**. QAOA depth,
shots, seed, penalty and move preference are **ASSUMPTIONS**. Objective values,
runtime, circuit depth and returned configurations become **EXPERIMENTAL
RESULTS** only when the software runs.

## Architecture

```text
app.py                         Streamlit presentation layer
src/airload_qc/
  models.py                    Typed domain objects
  data.py                      JSON/CSV loading and demo scenarios
  physics.py                   Independent moment and CG calculation
  validation.py                Input and solution constraint checks
  objective.py                 Shared solver-comparison objective
  classical.py                 Exact enumeration and OR-Tools CP-SAT
  qubo.py                      Binary model and QUBO conversion
  quantum.py                   Qiskit Aer QAOA execution and decoding
  scenarios.py                 Late-change and scaling experiments
  reporting.py                 HTML, CSV and JSON-ready exports
data/                          Labelled synthetic demo inputs
tests/                         Unit, integration and quantum tests
docs/                          Mathematics, demo and judge material
```

Scientific logic is separate from the UI. A different frontend can call the
same tested modules.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The suite checks:

- mass moment and CG;
- assignment completeness;
- capacity violations;
- objective values and movement penalties;
- known exact optimum;
- CP-SAT agreement;
- constrained model and QUBO generation;
- bitstring decoding;
- late-change workflow;
- scaling records;
- report exports;
- a real local QAOA execution.

## Limitations

- The model is longitudinal and does not model lateral balance, contour,
  structural floor loading, dangerous goods, loading sequence, fuel burn or
  full regulatory rules.
- The data is synthetic.
- QUBO slack variables increase qubit requirements quickly.
- Statevector simulation cost grows exponentially with qubit count.
- Simulator runtime is not comparable to hardware runtime or classical
  production performance.
- Small experiments cannot establish quantum advantage.
- QAOA can return a suboptimal or infeasible sample.
- No certification, operational integration or airline validation is claimed.

## Repository and submission assets

- Technical audit: `docs/FEASIBILITY_AUDIT.md`
- Judge-friendly mathematics: `docs/MATHEMATICS.md`
- Demonstration script: `docs/DEMO_SCRIPT.md`
- Judge questions and answers: `docs/JUDGE_QA.md`
- Official abstract text: `docs/SUBMISSION_TEXT.md`
- Non-programmer explanation: `docs/HOW_THIS_WORKS.md`

## Current Qiskit API basis

The implementation follows Qiskit Optimization's V2-primitives approach:

- [Qiskit Optimization: Minimum Eigen Optimizer](https://qiskit-community.github.io/qiskit-optimization/tutorials/03_minimum_eigen_optimizer.html)
- [Qiskit Optimization 0.7 migration guide](https://qiskit-community.github.io/qiskit-optimization/migration/03_migration_guide_to_v0.7.html)

These links document `StatevectorSampler`/SamplerV2-era QAOA and the pass
manager requirement for non-statevector V2 primitives.

## License

Hackathon and educational use. Add the team's chosen open-source license before
publishing if required by the event.
