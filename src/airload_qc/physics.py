from __future__ import annotations

from dataclasses import dataclass

from .models import LoadingScenario


@dataclass(frozen=True)
class BalanceResult:
    payload_weight_kg: float
    payload_moment_kg_m: float
    total_weight_kg: float
    total_moment_kg_m: float
    cg_m: float
    station_weights_kg: dict[str, float]
    station_moments_kg_m: dict[str, float]


def calculate_balance(
    scenario: LoadingScenario,
    assignment: dict[str, str],
) -> BalanceResult:
    """Calculate longitudinal balance from mass moments.

    CG = total moment / total mass. The basic aircraft is represented by its
    basic weight and arm; each assigned item's moment is weight × station arm.
    """
    item_lookup = {item.id: item for item in scenario.items}
    station_weights = {station.id: 0.0 for station in scenario.aircraft.stations}
    station_moments = {station.id: 0.0 for station in scenario.aircraft.stations}

    payload_weight = 0.0
    payload_moment = 0.0
    for item_id, station_id in assignment.items():
        if item_id not in item_lookup:
            raise KeyError(f"Assignment contains unknown item: {item_id}")
        item = item_lookup[item_id]
        station = scenario.aircraft.station_by_id(station_id)
        moment = item.weight_kg * station.arm_m
        payload_weight += item.weight_kg
        payload_moment += moment
        station_weights[station_id] += item.weight_kg
        station_moments[station_id] += moment

    total_weight = scenario.aircraft.basic_weight_kg + payload_weight
    total_moment = scenario.aircraft.basic_moment_kg_m + payload_moment
    cg = total_moment / total_weight

    return BalanceResult(
        payload_weight_kg=payload_weight,
        payload_moment_kg_m=payload_moment,
        total_weight_kg=total_weight,
        total_moment_kg_m=total_moment,
        cg_m=cg,
        station_weights_kg=station_weights,
        station_moments_kg_m=station_moments,
    )


def count_moves(
    scenario: LoadingScenario,
    assignment: dict[str, str],
) -> int:
    """Count existing items moved away from their prior station."""
    return sum(
        1
        for item_id, previous_station in scenario.prior_assignment.items()
        if item_id in assignment and assignment[item_id] != previous_station
    )
