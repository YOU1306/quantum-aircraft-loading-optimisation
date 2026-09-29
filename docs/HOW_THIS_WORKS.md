# How This Works — Memorize This

Aircraft cargo can be placed in several loading stations. Each choice changes
the aircraft's total moment and centre of gravity, and every station has a
weight limit.

Our software turns each allowed item-to-station choice into a binary decision:
one means “place it here” and zero means “do not.” The objective is to keep CG
close to a selected target while satisfying the loading constraints.

We solve the same synthetic problem three ways:

1. exact enumeration, which proves the optimum for a tiny case;
2. OR-Tools, which is a strong classical optimiser;
3. QAOA through Qiskit, which uses a QUBO-derived quantum cost function.

The QAOA measurement is decoded into a candidate loading configuration. Then
separate code recalculates weight, moment, CG and constraints. This matters
because a quantum heuristic can return a poor or infeasible sample.

We also add late baggage. The software checks whether the current loading still
works and, if needed, searches for a revised candidate while preferring fewer
moves.

We do not claim that quantum is already faster or better. We measure QAOA and
classical results as problem size grows. The project asks where quantum
optimisation may become useful in the future.

All built-in aircraft numbers are synthetic, and a qualified human remains
responsible for any real loading decision.

## Twenty-second version

“We model aircraft cargo placement as a constrained binary optimisation
problem. Qiskit converts it to a QUBO and QAOA samples candidate assignments.
We compare those candidates with exact and OR-Tools solutions, then
independently verify weight, moment, CG and every modeled constraint. We are
testing potential quantum usefulness as the problem grows—not claiming quantum
advantage today.”
