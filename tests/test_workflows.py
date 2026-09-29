from __future__ import annotations

import pytest

from airload_qc.classical import solve_exact
from airload_qc.data import demo_scenario
from airload_qc.quantum import QaoaConfig, solve_qaoa
from airload_qc.reporting import assignment_csv, html_report
from airload_qc.scenarios import run_late_change, run_scaling_benchmark


def test_late_change_reaches_target_without_moving_existing_load() -> None:
    baseline = solve_exact(demo_scenario())
    result = run_late_change(baseline, run_quantum=False)
    assert result.revised_classical.feasible
    assert result.revised_classical.cg_m == 10.0
    assert result.revised_classical.metadata["global_optimum_verified"] is True


def test_scaling_benchmark_records_measured_classical_results() -> None:
    rows = run_scaling_benchmark([2, 3], qaoa_max_items=0)
    assert [row["items"] for row in rows] == [2, 3]
    assert all(row["result_classification"] == "EXPERIMENTAL RESULT" for row in rows)
    assert all(row["cp_sat_feasible"] for row in rows)
    assert all(not row["qaoa_run"] for row in rows)


def test_exports_contain_required_safety_and_result_information() -> None:
    scenario = demo_scenario()
    solution = solve_exact(scenario)
    report = html_report(scenario, [solution])
    csv_text = assignment_csv(scenario, solution)
    assert "qualified person" in report
    assert "SYNTHETIC DATA" in report
    assert "Candidate loading configuration" in report
    assert "moment_kg_m" in csv_text


@pytest.mark.quantum
def test_qaoa_runs_and_returns_independently_validated_candidate() -> None:
    solution = solve_qaoa(
        demo_scenario(),
        QaoaConfig(reps=1, shots=256, maxiter=8, seed=7),
    )
    assert solution.status != "ERROR", solution.violations
    assert solution.feasible, solution.violations
    assert solution.metadata["simulator"].startswith("Qiskit Aer")
    assert solution.metadata["circuit_qubits"] >= 4
    assert solution.metadata["shots"] == 256
