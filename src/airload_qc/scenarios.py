from __future__ import annotations

from dataclasses import dataclass

from .classical import solve_cp_sat, solve_exact
from .data import demo_scenario, with_prior_assignment
from .models import Aircraft, CargoItem, LoadingScenario, LoadingSolution, Station
from .quantum import QaoaConfig, solve_qaoa
from .qubo import qubo_summary
from .validation import validate_assignment


@dataclass
class LateChangeResult:
    baseline: LoadingSolution
    current_loading_still_feasible: bool
    current_loading_violations: list[str]
    revised_classical: LoadingSolution
    revised_quantum: LoadingSolution | None


def run_late_change(
    baseline: LoadingSolution,
    run_quantum: bool = False,
    qaoa_config: QaoaConfig | None = None,
) -> LateChangeResult:
    changed = with_prior_assignment(demo_scenario(late=True), baseline.assignment)
    provisional_assignment = dict(baseline.assignment)
    provisional_assignment["L003"] = "AFT"
    still_feasible, violations, _ = validate_assignment(
        changed,
        provisional_assignment,
    )
    revised_classical = solve_exact(changed)
    revised_quantum = solve_qaoa(changed, qaoa_config) if run_quantum else None
    return LateChangeResult(
        baseline=baseline,
        current_loading_still_feasible=still_feasible,
        current_loading_violations=violations,
        revised_classical=revised_classical,
        revised_quantum=revised_quantum,
    )


def scaling_scenario(item_count: int) -> LoadingScenario:
    """Create a labelled synthetic family with an increasing decision count."""
    if item_count < 2:
        raise ValueError("Scaling scenarios require at least two items.")
    weights = [20.0, 40.0, 60.0]
    items = tuple(
        CargoItem(
            id=f"I{index + 1:02d}",
            description=f"Synthetic load unit {index + 1}",
            weight_kg=weights[index % len(weights)],
            allowed_stations=("FWD", "AFT"),
            classification="SYNTHETIC DATA",
        )
        for index in range(item_count)
    )
    payload = sum(item.weight_kg for item in items)
    station_capacity = max(100.0, payload)
    aircraft = Aircraft(
        name=f"Synthetic scaling model ({item_count} items)",
        basic_weight_kg=1000.0,
        basic_arm_m=10.0,
        max_payload_kg=payload + 20.0,
        cg_min_m=9.2,
        cg_max_m=10.8,
        target_cg_m=10.0,
        stations=(
            Station("FWD", "Forward hold", 7.0, station_capacity),
            Station("AFT", "Aft hold", 13.0, station_capacity),
        ),
        classification="SYNTHETIC DATA",
    )
    return LoadingScenario(
        name=f"Synthetic {item_count}-item scaling case",
        aircraft=aircraft,
        items=items,
        classification="SYNTHETIC DATA",
    )


def run_scaling_benchmark(
    sizes: list[int],
    qaoa_max_items: int = 3,
    qaoa_config: QaoaConfig | None = None,
) -> list[dict]:
    """Run measured local experiments; QAOA is capped to protect demo reliability."""
    rows: list[dict] = []
    for size in sizes:
        scenario = scaling_scenario(size)
        exact = solve_exact(scenario)
        cp_sat = solve_cp_sat(scenario)
        summary = qubo_summary(scenario)
        common = {
            "items": size,
            "assignment_variables": summary["assignment_variables"],
            "qubo_variables": summary["qubo_variables_including_slack"],
            "data_classification": "SYNTHETIC DATA",
            "result_classification": "EXPERIMENTAL RESULT",
            "exact_objective": exact.objective,
            "exact_runtime_s": exact.runtime_s,
            "cp_sat_objective": cp_sat.objective,
            "cp_sat_runtime_s": cp_sat.runtime_s,
            "cp_sat_feasible": cp_sat.feasible,
        }
        if size <= qaoa_max_items:
            quantum = solve_qaoa(scenario, qaoa_config)
            common.update(
                {
                    "qaoa_run": True,
                    "qaoa_objective": quantum.objective,
                    "qaoa_runtime_s": quantum.runtime_s,
                    "qaoa_feasible": quantum.feasible,
                    "qaoa_gap": quantum.objective - exact.objective
                    if quantum.feasible
                    else None,
                }
            )
        else:
            common.update(
                {
                    "qaoa_run": False,
                    "qaoa_objective": None,
                    "qaoa_runtime_s": None,
                    "qaoa_feasible": None,
                    "qaoa_gap": None,
                }
            )
        rows.append(common)
    return rows
