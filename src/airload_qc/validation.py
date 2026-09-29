from __future__ import annotations

from .models import LoadingScenario
from .physics import BalanceResult, calculate_balance


def validate_assignment(
    scenario: LoadingScenario,
    assignment: dict[str, str],
) -> tuple[bool, list[str], BalanceResult]:
    """Independently validate assignment completeness and physical constraints."""
    violations: list[str] = []
    expected = {item.id for item in scenario.items}
    assigned = set(assignment)

    missing = sorted(expected - assigned)
    extra = sorted(assigned - expected)
    if missing:
        violations.append(f"Unassigned items: {', '.join(missing)}")
    if extra:
        violations.append(f"Unknown assigned items: {', '.join(extra)}")

    valid_subset = {
        item_id: station_id
        for item_id, station_id in assignment.items()
        if item_id in expected
        and any(station.id == station_id for station in scenario.aircraft.stations)
    }
    if len(valid_subset) != len(assignment):
        violations.append("One or more assignments use an unknown station.")

    item_lookup = {item.id: item for item in scenario.items}
    for item_id, station_id in valid_subset.items():
        if station_id not in item_lookup[item_id].allowed_stations:
            violations.append(f"{item_id} is not allowed in station {station_id}.")

    balance = calculate_balance(scenario, valid_subset)
    if balance.payload_weight_kg > scenario.aircraft.max_payload_kg + 1e-9:
        violations.append(
            f"Payload {balance.payload_weight_kg:.1f} kg exceeds "
            f"{scenario.aircraft.max_payload_kg:.1f} kg."
        )

    for station in scenario.aircraft.stations:
        loaded = balance.station_weights_kg[station.id]
        if loaded > station.max_weight_kg + 1e-9:
            violations.append(
                f"{station.name} load {loaded:.1f} kg exceeds "
                f"{station.max_weight_kg:.1f} kg."
            )

    if not (
        scenario.aircraft.cg_min_m - 1e-9
        <= balance.cg_m
        <= scenario.aircraft.cg_max_m + 1e-9
    ):
        violations.append(
            f"CG {balance.cg_m:.3f} m is outside "
            f"{scenario.aircraft.cg_min_m:.3f}–"
            f"{scenario.aircraft.cg_max_m:.3f} m."
        )

    return not violations, violations, balance


def validate_scenario(scenario: LoadingScenario) -> list[str]:
    """Validate inputs before an optimizer is called."""
    issues: list[str] = []
    payload = sum(item.weight_kg for item in scenario.items)
    if payload > scenario.aircraft.max_payload_kg + 1e-9:
        issues.append(
            f"Manifest payload {payload:.1f} kg exceeds aircraft limit "
            f"{scenario.aircraft.max_payload_kg:.1f} kg."
        )
    for item in scenario.items:
        if item.weight_kg > max(
            scenario.aircraft.station_by_id(station_id).max_weight_kg
            for station_id in item.allowed_stations
        ):
            issues.append(f"{item.id} is too heavy for every allowed station.")
    unknown_prior = set(scenario.prior_assignment) - {item.id for item in scenario.items}
    if unknown_prior:
        issues.append(f"Prior assignment has unknown items: {sorted(unknown_prior)}")
    return issues
