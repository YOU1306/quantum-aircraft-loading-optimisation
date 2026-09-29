# Mathematics for Judges

## 1. Aircraft loading

Every cargo or baggage item has a weight. Every loading station has a
longitudinal arm: its distance from a chosen aircraft reference point. Placing
weight farther forward or aft changes total moment and therefore longitudinal
centre of gravity (CG).

## 2. Moment and CG

For an item:

\[
\text{moment}=\text{weight}\times\text{arm}
\]

For the complete synthetic aircraft:

\[
M=W_ba_b+\sum_{i,j}w_i a_jx_{ij}
\]

\[
W=W_b+\sum_iw_i
\qquad
CG=M/W
\]

These equations are evaluated independently after every solver run.

## 3. Binary decisions

\(x_{ij}=1\) means item \(i\) is assigned to station \(j\); otherwise it is
zero. Variables are created only for allowed assignments.

Exactly one station must be selected for each item:

\[
\sum_jx_{ij}=1
\]

Each station has a weight limit:

\[
\sum_iw_ix_{ij}\le C_j
\]

The whole manifest is rejected before optimisation if it exceeds the synthetic
payload limit.

## 4. Objective

The selected target CG lies inside the declared CG range. The primary objective
is:

\[
f(x)=
\left(
\frac{M(x)-W\,CG_t}{W(CG_{\max}-CG_{\min})}
\right)^2
\]

For a fixed manifest, \(W\) is constant. Minimising this expression is exactly
the same ordering as minimising squared target-CG deviation. Normalisation
makes QUBO coefficients easier to interpret.

For a manifest change:

\[
f_{\text{late}}(x)=f(x)+
\lambda\frac{\text{number of moved existing items}}
{\text{number of existing items}}
\]

\(\lambda=0.05\) is an **ASSUMPTION**, exposed in code. It is a workflow
preference, not an aerospace constant.

## 5. QUBO

The moment error is linear:

\[
d(x)=c+\sum_k a_kx_k
\]

Squaring it yields:

\[
d(x)^2=c^2+\sum_k(2ca_k+a_k^2)x_k+
\sum_{k<l}2a_ka_lx_kx_l
\]

because \(x_k^2=x_k\) for binary variables. This is quadratic and can be placed
in QUBO form:

\[
\min_x x^TQx+\text{constant}
\]

Qiskit Optimization converts equality and capacity constraints into penalty
terms. Capacity inequalities introduce binary slack variables. The software
reports both assignment-bit count and final QUBO-bit count.

## 6. QAOA and the circuit

Qiskit maps the QUBO to an Ising cost Hamiltonian \(H_C\). QAOA starts from a
superposition and alternates:

\[
e^{-i\gamma_kH_C}
\quad\text{and}\quad
e^{-i\beta_kH_M}
\]

for \(p\) repetitions. COBYLA updates the \(\gamma,\beta\) parameters. The Aer
sampler measures finite-shot bitstrings. Those bits are decoded through the
Qiskit variable names, not by assuming a display bit order.

## 7. Validation

The selected bitstring is converted back into item/station decisions. Separate
code then recalculates:

- assignment completeness;
- allowed stations;
- station weights;
- total payload;
- total moment;
- final CG and range;
- shared objective.

Exact enumeration supplies the known optimum for small cases. QAOA objective
gap is:

\[
\text{gap}=f_{\text{QAOA}}-f_{\text{exact}}
\]

A zero gap on one small run is not quantum advantage. Runtime on a local
simulator is also not equivalent to runtime on quantum hardware.
