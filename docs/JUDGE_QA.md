# Judge Questions and Defensible Answers

## Why use quantum computing if classical systems already work?

We are not proposing a current replacement. We use a real constrained
assignment problem to measure QAOA against exact and scalable classical
methods. Potential usefulness as model size and complexity grow is the research
question, not a result assumed in advance.

## Does QAOA test every loading configuration at once?

No. The circuit creates and transforms a quantum state, then measurements
sample candidate bitstrings. QAOA does not explicitly enumerate every
placement and does not guarantee the global optimum.

## What does one qubit represent?

Before constraint conversion, one binary assignment variable represents one
allowed item-to-station choice. QUBO conversion adds slack bits for capacity
inequalities, so not every final QUBO bit is a cargo assignment.

## What exactly are you minimizing?

Normalized squared deviation from a selected target longitudinal CG. Since
manifest weight is fixed during one solve, this is equivalent to squared target
moment deviation and is quadratic in the binary variables. Late-change mode
also includes a small preference to avoid moving existing items.

## Is target CG the aerodynamic neutral point?

No. The aerodynamic neutral point is a stability concept and is not the
objective here. Our target is a selected balance target within the synthetic
allowable range.

## Does this prove lower drag or fuel consumption?

No. We do not have a validated aircraft-specific aerodynamic or trim model, so
we make no drag, fuel or cost-saving claim.

## How do you know a quantum result is valid?

We decode the returned assignment and use separate code to recalculate
assignment completeness, allowed positions, station capacities, payload,
moment and CG. An invalid sample is clearly reported as infeasible.

## How do you know the small optimum?

Exact enumeration evaluates every allowed assignment for the small case. It
provides the true optimum and the objective gap for the QAOA result.

## Is the classical comparison fair?

Yes. Exact enumeration is used where practical and OR-Tools CP-SAT is the
scalable baseline. Both receive the same scenario and are evaluated by the same
independent objective. We do not weaken or delay the classical solver.

## Why can QAOA use more qubits than assignment variables?

Capacity constraints are inequalities. Converting them to QUBO introduces
binary slack variables. This overhead is measured and displayed; it is one of
the limitations being studied.

## Why is CG range checked after QAOA instead of fully encoded?

The target-CG objective drives the sample toward the target. We check the hard
CG range independently after decoding. Encoding every inequality as a QUBO
penalty adds slack bits and coefficient-range problems. This hybrid choice is
explicit, and no candidate is called feasible unless it passes the range check.

## What is genuinely quantum in the prototype?

Qiskit builds the QUBO-derived cost Hamiltonian. QAOA runs a parameterised
quantum circuit through Qiskit Aer, measures bitstrings and supplies the
candidate that is decoded into the loading decision. The application records
circuit depth, QUBO size, shots, parameters and simulator.

## Why use a simulator?

It makes the hackathon demo reproducible and independent of internet or queue
availability. Current qubit and noise limits also make only small hardware
tests appropriate. Simulation does not establish hardware speed.

## What do your scaling plots prove?

Only the measured behavior of these implementations on these synthetic local
cases. They do not prove asymptotic quantum advantage. QAOA cases that exceed
the safe demo cap are explicitly marked as not run.

## Is the data real?

No. It is labelled SYNTHETIC DATA and exists to demonstrate the mathematics
and workflow. Operational use would require validated aircraft data, many more
rules, safety assessment, certification and authorised approval.

## Who makes the final loading decision?

A qualified human. The software returns a candidate loading configuration and
validation report; it is not autonomous or approved for operations.
