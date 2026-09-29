from __future__ import annotations

from .models import LoadingScenario
from .physics import BalanceResult, count_moves


def cg_objective(
    scenario: LoadingScenario,
    balance: BalanceResult,
    assignment: dict[str, str],
) -> float:
    """Common objective used to compare every solver.

    The CG error is normalized by the allowable CG span. A late-change move
    penalty is added per existing item, so its scale remains understandable.
    """
    cg_span = scenario.aircraft.cg_max_m - scenario.aircraft.cg_min_m
    normalized_error = (
        (balance.cg_m - scenario.aircraft.target_cg_m) / cg_span
    ) ** 2
    prior_count = max(1, len(scenario.prior_assignment))
    movement_cost = (
        scenario.move_penalty * count_moves(scenario, assignment) / prior_count
    )
    return normalized_error + movement_cost


def target_moment_kg_m(scenario: LoadingScenario) -> float:
    total_weight = scenario.aircraft.basic_weight_kg + sum(
        item.weight_kg for item in scenario.items
    )
    return total_weight * scenario.aircraft.target_cg_m
