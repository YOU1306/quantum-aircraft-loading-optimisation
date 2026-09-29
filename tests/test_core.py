from __future__ import annotations

import math

from airload_qc.classical import solve_cp_sat, solve_exact
from airload_qc.data import demo_scenario, with_prior_assignment
from airload_qc.objective import cg_objective
from airload_qc.physics import calculate_balance, count_moves
from airload_qc.qubo import build_constrained_program, build_qubo, decode_variables
from airload_qc.validation import validate_assignment, validate_scenario


def test_moment_and_cg_calculation() -> None:
    scenario = demo_scenario()
    assignment = {"C001": "FWD", "B002": "AFT"}
    result = calculate_balance(scenario, assignment)
    assert result.payload_weight_kg == 100
    assert result.payload_moment_kg_m == 940
    assert result.total_weight_kg == 1100
    assert result.total_moment_kg_m == 10940
    assert math.isclose(result.cg_m, 10940 / 1100)


def test_constraint_checking_detects_station_overload() -> None:
    scenario = demo_scenario(late=True)
    assignment = {"C001": "FWD", "B002": "FWD", "L003": "FWD"}
    feasible, violations, _ = validate_assignment(scenario, assignment)
    assert not feasible
    assert any("exceeds" in violation for violation in violations)


def test_incomplete_assignment_is_rejected() -> None:
    scenario = demo_scenario()
    feasible, violations, _ = validate_assignment(scenario, {"C001": "FWD"})
    assert not feasible
    assert any("Unassigned items" in violation for violation in violations)


def test_objective_is_zero_at_target_cg() -> None:
    scenario = demo_scenario(late=True)
    assignment = {"C001": "FWD", "B002": "AFT", "L003": "AFT"}
    balance = calculate_balance(scenario, assignment)
    assert balance.cg_m == 10.0
    assert cg_objective(scenario, balance, assignment) == 0.0


def test_move_penalty_counts_only_changed_existing_items() -> None:
    scenario = with_prior_assignment(
        demo_scenario(late=True),
        {"C001": "FWD", "B002": "AFT"},
    )
    unchanged = {"C001": "FWD", "B002": "AFT", "L003": "AFT"}
    changed = {"C001": "AFT", "B002": "FWD", "L003": "AFT"}
    assert count_moves(scenario, unchanged) == 0
    assert count_moves(scenario, changed) == 2


def test_exact_solver_verifies_known_optimum() -> None:
    solution = solve_exact(demo_scenario())
    assert solution.feasible
    assert solution.metadata["global_optimum_verified"] is True
    assert solution.metadata["assignments_evaluated"] == 4
    assert math.isclose(solution.cg_error_m, 0.0545454545, rel_tol=1e-8)


def test_cp_sat_matches_exact_objective() -> None:
    scenario = demo_scenario()
    exact = solve_exact(scenario)
    cp_sat = solve_cp_sat(scenario)
    assert cp_sat.feasible
    assert math.isclose(cp_sat.objective, exact.objective, abs_tol=1e-12)


def test_qubo_generation_and_decode() -> None:
    scenario = demo_scenario()
    constrained = build_constrained_program(scenario)
    qubo = build_qubo(scenario)
    assert constrained.get_num_binary_vars() == 4
    assert constrained.get_num_linear_constraints() == 4
    assert qubo.get_num_binary_vars() > constrained.get_num_binary_vars()
    values = {
        "x__C001__FWD": 1,
        "x__C001__AFT": 0,
        "x__B002__FWD": 0,
        "x__B002__AFT": 1,
    }
    assert decode_variables(scenario, values) == {"C001": "FWD", "B002": "AFT"}
    ambiguous = dict(values)
    ambiguous["x__C001__AFT"] = 1
    assert "C001" not in decode_variables(scenario, ambiguous)


def test_demo_scenario_is_valid() -> None:
    assert validate_scenario(demo_scenario()) == []
