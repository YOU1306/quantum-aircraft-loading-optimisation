from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from airload_qc.classical import solve_cp_sat, solve_exact
from airload_qc.data import demo_scenario, with_prior_assignment
from airload_qc.quantum import QaoaConfig, solve_qaoa
from airload_qc.reporting import assignment_csv, html_report
from airload_qc.scenarios import run_late_change, run_scaling_benchmark


def main() -> int:
    output_dir = ROOT / "benchmark_results"
    output_dir.mkdir(exist_ok=True)

    scenario = demo_scenario()
    exact = solve_exact(scenario)
    cp_sat = solve_cp_sat(scenario)
    quantum = solve_qaoa(
        scenario,
        QaoaConfig(reps=1, shots=1024, maxiter=40, seed=42),
    )
    late = run_late_change(exact, run_quantum=False)
    scaling = run_scaling_benchmark(
        [2, 3, 4, 5, 6],
        qaoa_max_items=3,
        qaoa_config=QaoaConfig(reps=1, shots=512, maxiter=25, seed=42),
    )

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "result_classification": "EXPERIMENTAL RESULT",
        "input_classification": "SYNTHETIC DATA",
        "baseline": {
            "exact": exact.to_dict(),
            "cp_sat": cp_sat.to_dict(),
            "qaoa": quantum.to_dict(),
        },
        "late_change": {
            "current_loading_still_feasible": late.current_loading_still_feasible,
            "current_loading_violations": late.current_loading_violations,
            "revised_classical": late.revised_classical.to_dict(),
        },
        "scaling_classical": scaling,
        "claims_notice": (
            "These local simulator results do not establish quantum advantage, "
            "hardware speed, fuel savings, certification or operational readiness."
        ),
    }
    (output_dir / "latest_results.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    (output_dir / "latest_report.html").write_text(
        html_report(scenario, [exact, cp_sat, quantum]),
        encoding="utf-8",
    )
    (output_dir / "latest_candidate.csv").write_text(
        assignment_csv(scenario, exact),
        encoding="utf-8",
    )

    print(json.dumps(payload, indent=2))
    return 0 if exact.feasible and cp_sat.feasible and quantum.feasible else 1


if __name__ == "__main__":
    raise SystemExit(main())
