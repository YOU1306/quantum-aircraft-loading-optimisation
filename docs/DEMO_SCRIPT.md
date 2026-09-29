# 3–5 Minute Demonstration Script

## 0:00–0:35 — Problem

“Aircraft cargo and baggage can be assigned to loading stations in many ways.
Every placement changes moment and centre of gravity. Existing classical
loading software already works well. Our research question is whether quantum
optimisation may become useful as decisions and constraints grow.”

Show **Dashboard**.

## 0:35–1:00 — Inputs

Open **Aircraft & Manifest**.

“This is a simplified, non-operational aircraft model. Every built-in aircraft
and manifest value is labelled synthetic data. The model still contains the
physics needed for longitudinal balance: weight, arm, moment, CG target, CG
range and station limits.”

## 1:00–2:15 — Solve and validate

Open **Optimisation**. Run exact verification, OR-Tools and QAOA.

“Each binary variable means that an item is placed at an allowed station. We
minimise deviation from the selected target CG. Qiskit converts the model to a
QUBO and QAOA samples candidate solutions. The same case is solved exactly and
with OR-Tools. We independently recalculate weight, moment, CG and every
constraint.”

Point to the actual feasibility, objective and runtime values. Do not memorize
numbers; read the measured values shown by the application.

## 2:15–2:45 — Quantum evidence

Open **Quantum Analysis**.

“This is not a decorative circuit panel. These are the QUBO bit count, QAOA
depth, shot count, parameters, simulator and sample information from the run
that produced the candidate.”

## 2:45–3:35 — Late change

Open **Late Change** and run the scenario.

“Now a late 20-kilogram synthetic baggage batch arrives. The system first checks
the current configuration, then re-optimises the changed manifest while
preferring not to move already loaded items. The output remains a candidate for
human review.”

## 3:35–4:15 — Scaling and conclusion

Show a prepared scaling result or run the quick sizes.

“We increase the number of assignment decisions and measure both approaches.
We do not assume that QAOA wins. Exact enumeration verifies small cases,
OR-Tools is the scalable classical reference, and larger quantum runs are
skipped when they would make the demo unreliable.”

## 4:15–4:40 — Safety and export

Open **Export**.

“The report records the manifest, candidate assignment, CG, objective,
constraints, methods and disclaimer. This is research decision support, not a
certified or autonomous loading system.”

## Demo safety checklist

- Start the app before judges arrive.
- Run the built-in QAOA case once to warm imports and verify the environment.
- Keep the exact and OR-Tools outputs visible if a QAOA rerun takes longer.
- Do not claim simulator runtime represents hardware performance.
- Do not claim fuel savings, drag reduction or quantum advantage.
- Read experimental numbers from the UI; do not use rehearsed values.
