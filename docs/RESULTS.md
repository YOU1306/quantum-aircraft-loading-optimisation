# Recorded Local Results

Generated: 2026-09-29 15:14:42 UTC

Input classification: **SYNTHETIC DATA**  
Output classification: **EXPERIMENTAL RESULT**

The machine-readable record is `benchmark_results/latest_results.json`.
Re-run `python scripts/run_experiment.py` to replace these values with a new
measured run.

## Baseline two-item case

The exact solver evaluated four assignments and verified two symmetric global
optima. One candidate places C001 forward and B002 aft:

- total weight: 1100.0 kg;
- total moment: 10,940.0 kg·m;
- CG: 9.94545 m;
- target-CG error: 0.05455 m;
- common objective: 0.0011621901;
- all modeled constraints satisfied.

OR-Tools CP-SAT returned the symmetric candidate, with the same target-CG error
and objective, and reported an optimal status.

QAOA at \(p=1\), 1,024 shots, 40 COBYLA iterations and seed 42 returned the
same feasible candidate as exact enumeration in this run:

- assignment variables: 4;
- QUBO variables including capacity slack: 10;
- QUBO quadratic terms: 34;
- transpiled/decomposed circuit depth reported by the application: 33;
- selected feasible-sample probability: 0.03515625;
- measured local QAOA workflow runtime: approximately 1.63 seconds;
- objective gap from exact: zero for this run.

This single small simulator result does **not** establish quantum advantage,
reliable convergence on larger cases, or hardware performance.

## Late-change case

A 20 kg synthetic late-baggage batch was added. The independently checked
candidate placed the late batch aft without moving the two existing items:

- total weight: 1120.0 kg;
- total moment: 11,200.0 kg·m;
- CG: 10.0000 m;
- objective: 0.0;
- all modeled constraints satisfied;
- exact enumeration checked eight assignments.

This is a result for the synthetic demonstrator only.

## Classical scaling record

Exact enumeration and CP-SAT were run for two through six synthetic items.
Both returned matching objective values in every recorded case. QAOA was
deliberately not run in this saved scaling batch; no missing quantum result is
inferred or fabricated. The Streamlit application can run QAOA for selected
small sizes and records those measurements separately.

## Safe interpretation

The run demonstrates that:

- the QUBO and QAOA path executes through Qiskit Aer;
- a measured QAOA bitstring can be decoded into an aircraft-loading candidate;
- that candidate can be independently validated;
- exact and CP-SAT baselines can evaluate the same scenario;
- a late manifest change can be checked and re-optimised.

It does not demonstrate:

- quantum advantage or faster quantum runtime;
- operational aircraft validity;
- fuel or drag improvement;
- certification, airline deployment or global QAOA reliability.
