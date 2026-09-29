# Official QuantumXpo Abstract Text

## Project Title

Quantum-Assisted Decision Support for Aircraft Loading Optimisation

## Problem Statement

Aircraft cargo and baggage loading involves many possible ways to assign items
to loading stations while keeping weight and centre-of-gravity (CG) limits
satisfied. Last-minute baggage, cargo changes or weight changes can require the
loading to be reassessed quickly. Existing systems already solve these problems
using classical optimisation. This project explores whether quantum
optimisation can become useful as the number of loading decisions and
constraints increases.

## Proposed Solution

Build a quantum-assisted decision-support prototype that finds feasible
cargo-to-station assignments while keeping CG close to a selected target. The
problem is converted into a QUBO and solved using QAOA with Qiskit. Results are
compared with a classical optimiser as problem size increases. The system also
re-evaluates the loading after a manifest change. A qualified human remains
responsible for final approval.

## Key Features

- QUBO model for cargo-to-station assignment
- QAOA implemented using Qiskit
- CG and weight constraint checking
- Exact verification for small problems
- Fair classical optimisation comparison
- Scaling test as problem size increases
- Late baggage/cargo change handling
- Loading and CG visualisation
- Human-in-the-loop decision support

## How It Works

1. Import a manifest and simplified, non-operational aircraft model.
2. Validate weights, stations and loading rules.
3. Create assignment variables and the QUBO.
4. Run QAOA using a Qiskit simulator.
5. Solve the same problem using a classical optimiser.
6. Calculate weight, moment and CG independently.
7. Compare feasibility, solution quality and runtime.
8. Display the recommended candidate loading configuration.
9. Re-evaluate after a manifest change.

## Quantum Simulation

QAOA will run on a Qiskit simulator for small loading problems. Its solutions
will be compared with exact and classical methods using feasibility, CG error,
objective value and runtime. The problem size will then be increased to study
how both approaches behave as the number of loading decisions grows. Results
will be measured rather than assuming quantum advantage.

## Quantum Circuit / Algorithm

Quantum Approximate Optimisation Algorithm (QAOA)

The loading problem is converted into a QUBO and mapped to a quantum cost
Hamiltonian. QAOA uses a parameterised quantum circuit to search for low-cost
loading configurations. Qiskit is used to construct and simulate the circuit,
and measured results are converted back into loading decisions.

QAOA does not guarantee the global optimum or enumerate every possible
placement. Solutions are independently checked against the loading constraints.

## IBM Quantum Platform / Tool

- Qiskit: quantum circuit and simulation
- Qiskit Optimization: QUBO and QAOA workflow
- Qiskit Aer: local quantum simulation
- IBM Quantum Runtime: optional future hardware testing
- OR-Tools: classical optimisation comparison
- Streamlit: interactive decision-support interface

## Expected Impact

An explainable prototype for applying quantum optimisation to aircraft loading.
The project will test whether QAOA can produce feasible, near-optimal loading
solutions and how its performance changes as the problem grows. Classical
optimisation will provide a fair reference. The prototype is intended as
decision support, not a replacement for certified aircraft-loading systems.

## Future Scope

Test larger loading problems and more complex constraint models as quantum
hardware improves. Explore hybrid quantum-classical methods, stronger
constraint handling and additional late-loading scenarios. Future
aircraft-specific models and operational deployment would require validated
data, independent safety assessment, certification and authorised human
approval.

## Team Name

PQP
