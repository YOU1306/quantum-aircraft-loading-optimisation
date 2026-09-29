from __future__ import annotations

import math
from dataclasses import dataclass
from functools import reduce

from .models import LoadingScenario


@dataclass(frozen=True)
class QuboConfig:
    penalty: float | None = None


def variable_name(item_id: str, station_id: str) -> str:
    return f"x__{item_id}__{station_id}"


def decode_variables(
    scenario: LoadingScenario,
    values: dict[str, float],
) -> dict[str, str]:
    """Decode an assignment only when exactly one station bit is selected."""
    assignment: dict[str, str] = {}
    for item in scenario.items:
        selected = [
            station_id
            for station_id in item.allowed_stations
            if values.get(variable_name(item.id, station_id), 0.0) >= 0.5
        ]
        if len(selected) == 1:
            assignment[item.id] = selected[0]
    return assignment


def _capacity_unit_kg(scenario: LoadingScenario) -> float:
    """Find a common 0.1 kg unit to keep QUBO slack registers compact."""
    scaled = [
        round(value * 10)
        for value in [
            *(item.weight_kg for item in scenario.items),
            *(station.max_weight_kg for station in scenario.aircraft.stations),
        ]
    ]
    common = reduce(math.gcd, (abs(value) for value in scaled if value))
    return max(common / 10.0, 0.1)


def objective_upper_bound(scenario: LoadingScenario) -> float:
    """Conservative bound over every binary assignment pattern.

    A unit constraint violation must cost more than any possible improvement
    in the unconstrained objective. The bound deliberately includes invalid
    patterns in which several station bits are selected for one item.
    """
    total_weight = scenario.aircraft.basic_weight_kg + sum(
        item.weight_kg for item in scenario.items
    )
    moment_scale = total_weight * (
        scenario.aircraft.cg_max_m - scenario.aircraft.cg_min_m
    )
    constant_delta = (
        scenario.aircraft.basic_moment_kg_m
        - total_weight * scenario.aircraft.target_cg_m
    )
    maximum_absolute_delta = abs(constant_delta) + sum(
        abs(item.weight_kg * scenario.aircraft.station_by_id(station_id).arm_m)
        for item in scenario.items
        for station_id in item.allowed_stations
    )
    movement_bound = scenario.move_penalty if scenario.prior_assignment else 0.0
    return (maximum_absolute_delta / moment_scale) ** 2 + movement_bound


def effective_penalty(
    scenario: LoadingScenario,
    config: QuboConfig | None = None,
) -> float:
    config = config or QuboConfig()
    minimum = float(math.ceil(objective_upper_bound(scenario)) + 1)
    if config.penalty is None:
        return minimum
    if config.penalty <= objective_upper_bound(scenario):
        raise ValueError(
            f"QUBO penalty {config.penalty} must exceed the conservative "
            f"objective bound {objective_upper_bound(scenario):.6f}."
        )
    return config.penalty


def build_constrained_program(scenario: LoadingScenario):
    """Build the binary quadratic model before inequality-to-QUBO conversion.

    Encoded constraints:
    - exactly one allowed station per item;
    - maximum weight at each station.

    Payload is checked before solving. The CG envelope is checked independently
    after decoding, while target-CG deviation is the quadratic objective.
    """
    from qiskit_optimization import QuadraticProgram

    qp = QuadraticProgram(name="aircraft_loading")
    names: list[str] = []
    coefficients: dict[str, float] = {}
    total_weight = scenario.aircraft.basic_weight_kg + sum(
        item.weight_kg for item in scenario.items
    )
    moment_scale = total_weight * (
        scenario.aircraft.cg_max_m - scenario.aircraft.cg_min_m
    )
    constant_delta = (
        scenario.aircraft.basic_moment_kg_m
        - total_weight * scenario.aircraft.target_cg_m
    )

    for item in scenario.items:
        for station_id in item.allowed_stations:
            name = variable_name(item.id, station_id)
            qp.binary_var(name=name)
            names.append(name)
            coefficients[name] = (
                item.weight_kg * scenario.aircraft.station_by_id(station_id).arm_m
            )

    linear: dict[str, float] = {}
    quadratic: dict[tuple[str, str], float] = {}
    denominator = moment_scale**2
    for index, name_i in enumerate(names):
        a_i = coefficients[name_i]
        linear[name_i] = (2 * constant_delta * a_i + a_i**2) / denominator
        for name_j in names[index + 1 :]:
            quadratic[(name_i, name_j)] = (
                2 * a_i * coefficients[name_j] / denominator
            )

    prior_count = max(1, len(scenario.prior_assignment))
    for item_id, prior_station in scenario.prior_assignment.items():
        for station_id in next(
            item.allowed_stations for item in scenario.items if item.id == item_id
        ):
            if station_id != prior_station:
                name = variable_name(item_id, station_id)
                linear[name] += scenario.move_penalty / prior_count

    qp.minimize(
        constant=(constant_delta**2) / denominator,
        linear=linear,
        quadratic=quadratic,
    )

    for item in scenario.items:
        qp.linear_constraint(
            linear={
                variable_name(item.id, station_id): 1
                for station_id in item.allowed_stations
            },
            sense="==",
            rhs=1,
            name=f"assign_once__{item.id}",
        )

    unit = _capacity_unit_kg(scenario)
    for station in scenario.aircraft.stations:
        station_terms = {
            variable_name(item.id, station.id): round(item.weight_kg / unit)
            for item in scenario.items
            if station.id in item.allowed_stations
        }
        if station_terms:
            qp.linear_constraint(
                linear=station_terms,
                sense="<=",
                rhs=round(station.max_weight_kg / unit),
                name=f"capacity__{station.id}",
            )
    return qp


def build_qubo(
    scenario: LoadingScenario,
    config: QuboConfig | None = None,
):
    from qiskit_optimization.converters import QuadraticProgramToQubo

    config = config or QuboConfig()
    constrained = build_constrained_program(scenario)
    converter = QuadraticProgramToQubo(
        penalty=effective_penalty(scenario, config)
    )
    return converter.convert(constrained)


def qubo_summary(scenario: LoadingScenario, config: QuboConfig | None = None) -> dict:
    config = config or QuboConfig()
    constrained = build_constrained_program(scenario)
    qubo = build_qubo(scenario, config)
    return {
        "assignment_variables": constrained.get_num_binary_vars(),
        "constraints": constrained.get_num_linear_constraints(),
        "qubo_variables_including_slack": qubo.get_num_binary_vars(),
        "qubo_quadratic_terms": len(qubo.objective.quadratic.to_dict()),
        "objective_upper_bound": objective_upper_bound(scenario),
        "penalty": effective_penalty(scenario, config),
        "penalty_basis": "ceil(conservative objective bound) + 1",
    }
