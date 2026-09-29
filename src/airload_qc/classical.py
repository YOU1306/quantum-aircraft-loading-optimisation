from __future__ import annotations

import itertools
import time

from .models import LoadingScenario, LoadingSolution
from .objective import cg_objective
from .physics import count_moves
from .validation import validate_assignment, validate_scenario


def _solution(
    scenario: LoadingScenario,
    method: str,
    assignment: dict[str, str],
    runtime_s: float,
    metadata: dict | None = None,
) -> LoadingSolution:
    feasible, violations, balance = validate_assignment(scenario, assignment)
    return LoadingSolution(
        method=method,
        status="FEASIBLE" if feasible else "INFEASIBLE",
        assignment=assignment,
        total_weight_kg=balance.total_weight_kg,
        total_moment_kg_m=balance.total_moment_kg_m,
        cg_m=balance.cg_m,
        cg_error_m=abs(balance.cg_m - scenario.aircraft.target_cg_m),
        objective=cg_objective(scenario, balance, assignment),
        feasible=feasible,
        violations=violations,
        runtime_s=runtime_s,
        metadata=metadata or {},
    )


def solve_exact(scenario: LoadingScenario) -> LoadingSolution:
    """Enumerate every allowed assignment; intended only for small instances."""
    started = time.perf_counter()
    issues = validate_scenario(scenario)
    if issues:
        return LoadingSolution(
            method="Exact enumeration",
            status="INVALID_INPUT",
            assignment={},
            total_weight_kg=scenario.aircraft.basic_weight_kg,
            total_moment_kg_m=scenario.aircraft.basic_moment_kg_m,
            cg_m=scenario.aircraft.basic_arm_m,
            cg_error_m=abs(
                scenario.aircraft.basic_arm_m - scenario.aircraft.target_cg_m
            ),
            objective=float("inf"),
            feasible=False,
            violations=issues,
            runtime_s=time.perf_counter() - started,
        )

    choices = [item.allowed_stations for item in scenario.items]
    best: LoadingSolution | None = None
    evaluated = 0
    feasible_count = 0
    for station_tuple in itertools.product(*choices):
        evaluated += 1
        assignment = {
            item.id: station for item, station in zip(scenario.items, station_tuple)
        }
        candidate = _solution(scenario, "Exact enumeration", assignment, 0.0)
        if not candidate.feasible:
            continue
        feasible_count += 1
        if best is None or candidate.objective < best.objective - 1e-12:
            best = candidate

    runtime = time.perf_counter() - started
    if best is None:
        return LoadingSolution(
            method="Exact enumeration",
            status="INFEASIBLE",
            assignment={},
            total_weight_kg=scenario.aircraft.basic_weight_kg,
            total_moment_kg_m=scenario.aircraft.basic_moment_kg_m,
            cg_m=scenario.aircraft.basic_arm_m,
            cg_error_m=abs(
                scenario.aircraft.basic_arm_m - scenario.aircraft.target_cg_m
            ),
            objective=float("inf"),
            feasible=False,
            violations=["No feasible assignment exists."],
            runtime_s=runtime,
            metadata={"assignments_evaluated": evaluated, "feasible_assignments": 0},
        )

    best.runtime_s = runtime
    best.metadata.update(
        {
            "assignments_evaluated": evaluated,
            "feasible_assignments": feasible_count,
            "global_optimum_verified": True,
        }
    )
    return best


def solve_cp_sat(
    scenario: LoadingScenario,
    time_limit_s: float = 10.0,
) -> LoadingSolution:
    """Solve a scalable integer model with OR-Tools CP-SAT.

    The integer objective is the squared target-moment deviation plus the same
    normalized movement preference used by the shared reporting objective.
    """
    from ortools.sat.python import cp_model

    started = time.perf_counter()
    issues = validate_scenario(scenario)
    if issues:
        invalid = solve_exact(scenario)
        invalid.method = "OR-Tools CP-SAT"
        return invalid

    # Demo data uses one-decimal-compatible values; scaling preserves exactness.
    scale = 10
    model = cp_model.CpModel()
    variables: dict[tuple[str, str], cp_model.IntVar] = {}
    for item in scenario.items:
        for station_id in item.allowed_stations:
            variables[(item.id, station_id)] = model.new_bool_var(
                f"x__{item.id}__{station_id}"
            )
        model.add(
            sum(variables[(item.id, station_id)] for station_id in item.allowed_stations)
            == 1
        )

    for station in scenario.aircraft.stations:
        terms = []
        for item in scenario.items:
            key = (item.id, station.id)
            if key in variables:
                terms.append(round(item.weight_kg * scale) * variables[key])
        model.add(sum(terms) <= round(station.max_weight_kg * scale))

    total_weight = scenario.aircraft.basic_weight_kg + sum(
        item.weight_kg for item in scenario.items
    )
    basic_moment = round(scenario.aircraft.basic_moment_kg_m * scale)
    cargo_moment_terms = [
        round(
            next(item.weight_kg for item in scenario.items if item.id == item_id)
            * scenario.aircraft.station_by_id(station_id).arm_m
            * scale
        )
        * variable
        for (item_id, station_id), variable in variables.items()
    ]
    cargo_abs_bound = sum(abs(term) for term in [
        round(item.weight_kg * max(
            scenario.aircraft.station_by_id(s).arm_m
            for s in item.allowed_stations
        ) * scale)
        for item in scenario.items
    ])
    total_moment = model.new_int_var(
        basic_moment, basic_moment + cargo_abs_bound, "total_moment"
    )
    model.add(total_moment == basic_moment + sum(cargo_moment_terms))
    model.add(total_moment >= round(total_weight * scenario.aircraft.cg_min_m * scale))
    model.add(total_moment <= round(total_weight * scenario.aircraft.cg_max_m * scale))

    target = round(total_weight * scenario.aircraft.target_cg_m * scale)
    max_deviation = basic_moment + cargo_abs_bound + abs(target)
    deviation = model.new_int_var(0, max_deviation, "target_moment_deviation")
    model.add_abs_equality(deviation, total_moment - target)
    squared = model.new_int_var(0, max_deviation**2, "squared_deviation")
    model.add_multiplication_equality(squared, [deviation, deviation])

    moves = []
    for item_id, prior_station in scenario.prior_assignment.items():
        key = (item_id, prior_station)
        if key in variables:
            moved = model.new_bool_var(f"moved__{item_id}")
            model.add(moved + variables[key] == 1)
            moves.append(moved)
    movement_coefficient = round(
        scenario.move_penalty
        * (total_weight * (scenario.aircraft.cg_max_m - scenario.aircraft.cg_min_m) * scale) ** 2
        / max(1, len(scenario.prior_assignment))
    )
    model.minimize(squared + movement_coefficient * sum(moves))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = 1
    status = solver.solve(model)
    runtime = time.perf_counter() - started
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return LoadingSolution(
            method="OR-Tools CP-SAT",
            status="INFEASIBLE" if status == cp_model.INFEASIBLE else "NO_SOLUTION",
            assignment={},
            total_weight_kg=scenario.aircraft.basic_weight_kg,
            total_moment_kg_m=scenario.aircraft.basic_moment_kg_m,
            cg_m=scenario.aircraft.basic_arm_m,
            cg_error_m=abs(
                scenario.aircraft.basic_arm_m - scenario.aircraft.target_cg_m
            ),
            objective=float("inf"),
            feasible=False,
            violations=["No feasible assignment was returned."],
            runtime_s=runtime,
            metadata={"cp_sat_status": solver.status_name(status)},
        )

    assignment = {}
    for item in scenario.items:
        for station_id in item.allowed_stations:
            if solver.value(variables[(item.id, station_id)]):
                assignment[item.id] = station_id
                break
    result = _solution(
        scenario,
        "OR-Tools CP-SAT",
        assignment,
        runtime,
        {
            "cp_sat_status": solver.status_name(status),
            "global_optimum_verified": status == cp_model.OPTIMAL,
            "moves": count_moves(scenario, assignment),
        },
    )
    return result
