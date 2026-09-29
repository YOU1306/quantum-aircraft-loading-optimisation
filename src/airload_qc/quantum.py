from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from .models import LoadingScenario, LoadingSolution
from .objective import cg_objective
from .qubo import (
    QuboConfig,
    build_constrained_program,
    decode_variables,
    effective_penalty,
    qubo_summary,
)
from .validation import validate_assignment, validate_scenario


@dataclass(frozen=True)
class QaoaConfig:
    reps: int = 1
    shots: int = 1024
    maxiter: int = 40
    seed: int = 42
    qubo_penalty: float | None = None


def solve_qaoa(
    scenario: LoadingScenario,
    config: QaoaConfig | None = None,
) -> LoadingSolution:
    """Run a genuine QAOA optimization with Qiskit Aer SamplerV2."""
    from qiskit import generate_preset_pass_manager
    from qiskit_aer import AerSimulator
    from qiskit_aer.primitives import SamplerV2
    from qiskit_optimization.algorithms import MinimumEigenOptimizer
    from qiskit_optimization.converters import QuadraticProgramToQubo
    from qiskit_optimization.minimum_eigensolvers import QAOA
    from qiskit_optimization.optimizers import COBYLA
    from qiskit_optimization.utils import algorithm_globals

    config = config or QaoaConfig()
    started = time.perf_counter()
    issues = validate_scenario(scenario)
    if issues:
        return _failed_solution(scenario, "INVALID_INPUT", issues, started, config)

    algorithm_globals.random_seed = config.seed
    backend = AerSimulator(method="statevector")
    sampler = SamplerV2(seed=config.seed, default_shots=config.shots)
    pass_manager = generate_preset_pass_manager(
        optimization_level=1,
        backend=backend,
    )
    optimizer = COBYLA(maxiter=config.maxiter)
    initial_rng = np.random.default_rng(config.seed)
    initial_point = initial_rng.uniform(-np.pi, np.pi, size=2 * config.reps)
    qaoa = QAOA(
        sampler=sampler,
        optimizer=optimizer,
        reps=config.reps,
        initial_point=initial_point,
        pass_manager=pass_manager,
    )
    qubo_config = QuboConfig(penalty=config.qubo_penalty)
    converter = QuadraticProgramToQubo(
        penalty=effective_penalty(scenario, qubo_config)
    )
    solver = MinimumEigenOptimizer(qaoa, converters=converter)

    try:
        result = solver.solve(build_constrained_program(scenario))
    except Exception as exc:
        return _failed_solution(
            scenario,
            "ERROR",
            [f"QAOA execution failed: {type(exc).__name__}: {exc}"],
            started,
            config,
        )

    variable_names = list(result.variable_names)
    feasible_candidates: list[tuple[float, float, dict[str, str], object]] = []
    feasible_probability = 0.0
    for sample in result.samples:
        values = {
            name: float(value) for name, value in zip(variable_names, sample.x)
        }
        assignment = decode_variables(scenario, values)
        feasible, _, balance = validate_assignment(scenario, assignment)
        if feasible:
            objective = cg_objective(scenario, balance, assignment)
            feasible_probability += float(sample.probability)
            feasible_candidates.append(
                (objective, -float(sample.probability), assignment, sample)
            )

    if feasible_candidates:
        objective, neg_probability, assignment, chosen_sample = min(
            feasible_candidates,
            key=lambda value: (value[0], value[1]),
        )
        sample_probability = -neg_probability
    else:
        assignment = decode_variables(scenario, result.variables_dict)
        chosen_sample = None
        sample_probability = 0.0

    feasible, violations, balance = validate_assignment(scenario, assignment)
    runtime = time.perf_counter() - started
    summary = qubo_summary(scenario, qubo_config)
    circuit = qaoa.ansatz
    metadata = {
        **summary,
        "reps": config.reps,
        "shots": config.shots,
        "maxiter": config.maxiter,
        "seed": config.seed,
        "simulator": "Qiskit Aer SamplerV2 (statevector method, shot sampling)",
        "circuit_qubits": circuit.num_qubits if circuit is not None else None,
        "circuit_depth": circuit.decompose(reps=2).depth()
        if circuit is not None
        else None,
        "selected_sample_probability": sample_probability,
        "feasible_sample_probability": feasible_probability,
        "feasible_samples_reported": len(feasible_candidates),
        "qiskit_status": str(result.status),
        "optimal_parameters": _serializable_parameters(
            getattr(result.min_eigen_solver_result, "optimal_point", None)
        ),
        "raw_qaoa_objective": float(result.fval),
    }
    if chosen_sample is not None:
        metadata["selected_sample_qiskit_status"] = str(chosen_sample.status)

    return LoadingSolution(
        method=f"QAOA (p={config.reps})",
        status="FEASIBLE" if feasible else "INFEASIBLE_SAMPLE",
        assignment=assignment,
        total_weight_kg=balance.total_weight_kg,
        total_moment_kg_m=balance.total_moment_kg_m,
        cg_m=balance.cg_m,
        cg_error_m=abs(balance.cg_m - scenario.aircraft.target_cg_m),
        objective=cg_objective(scenario, balance, assignment),
        feasible=feasible,
        violations=violations,
        runtime_s=runtime,
        metadata=metadata,
    )


def _serializable_parameters(value) -> list[float] | None:
    if value is None:
        return None
    return [float(item) for item in value]


def _failed_solution(
    scenario: LoadingScenario,
    status: str,
    violations: list[str],
    started: float,
    config: QaoaConfig,
) -> LoadingSolution:
    return LoadingSolution(
        method=f"QAOA (p={config.reps})",
        status=status,
        assignment={},
        total_weight_kg=scenario.aircraft.basic_weight_kg,
        total_moment_kg_m=scenario.aircraft.basic_moment_kg_m,
        cg_m=scenario.aircraft.basic_arm_m,
        cg_error_m=abs(
            scenario.aircraft.basic_arm_m - scenario.aircraft.target_cg_m
        ),
        objective=float("inf"),
        feasible=False,
        violations=violations,
        runtime_s=time.perf_counter() - started,
        metadata={
            "reps": config.reps,
            "shots": config.shots,
            "maxiter": config.maxiter,
            "seed": config.seed,
        },
    )
