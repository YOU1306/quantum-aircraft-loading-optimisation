from __future__ import annotations

import csv
import html
import io
from datetime import datetime, timezone

from .models import LoadingScenario, LoadingSolution


DISCLAIMER = (
    "Research and education prototype only. All aircraft and manifest values in "
    "the built-in demo are SYNTHETIC DATA. A qualified person must independently "
    "verify and approve any operational aircraft loading."
)


def assignment_csv(
    scenario: LoadingScenario,
    solution: LoadingSolution,
) -> str:
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(
        [
            "item_id",
            "description",
            "weight_kg",
            "station",
            "arm_m",
            "moment_kg_m",
            "data_classification",
        ]
    )
    for item in scenario.items:
        station_id = solution.assignment.get(item.id, "")
        station = (
            scenario.aircraft.station_by_id(station_id) if station_id else None
        )
        writer.writerow(
            [
                item.id,
                item.description,
                item.weight_kg,
                station_id,
                station.arm_m if station else "",
                item.weight_kg * station.arm_m if station else "",
                item.classification,
            ]
        )
    return stream.getvalue()


def html_report(
    scenario: LoadingScenario,
    solutions: list[LoadingSolution],
) -> str:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    solution_sections = "\n".join(
        _solution_html(scenario, solution) for solution in solutions
    )
    manifest_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(item.id)}</td>"
        f"<td>{html.escape(item.description)}</td>"
        f"<td>{item.weight_kg:.1f}</td>"
        f"<td>{html.escape(', '.join(item.allowed_stations))}</td>"
        f"<td>{html.escape(item.classification)}</td>"
        "</tr>"
        for item in scenario.items
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Aircraft Loading Optimisation Report</title>
<style>
body{{font-family:Arial,sans-serif;max-width:980px;margin:40px auto;color:#172033}}
h1,h2{{color:#35128a}} .badge{{background:#eee7ff;padding:4px 8px;border-radius:12px}}
table{{border-collapse:collapse;width:100%;margin:12px 0 28px}}
th,td{{border:1px solid #d7d9e0;padding:8px;text-align:left}}
th{{background:#f4f1ff}} .ok{{color:#08783e}} .bad{{color:#b42318}}
.notice{{border-left:5px solid #6c35de;background:#f7f4ff;padding:12px}}
</style>
</head>
<body>
<h1>Quantum-Assisted Aircraft Loading Optimisation</h1>
<p><strong>Scenario:</strong> {html.escape(scenario.name)}</p>
<p><strong>Generated:</strong> {timestamp} UTC</p>
<p><span class="badge">{html.escape(scenario.classification)}</span></p>
<div class="notice">{html.escape(DISCLAIMER)}</div>
<h2>Aircraft and limits</h2>
<table>
<tr><th>Model</th><th>Basic weight</th><th>Target CG</th><th>CG range</th><th>Classification</th></tr>
<tr><td>{html.escape(scenario.aircraft.name)}</td>
<td>{scenario.aircraft.basic_weight_kg:.1f} kg</td>
<td>{scenario.aircraft.target_cg_m:.3f} m</td>
<td>{scenario.aircraft.cg_min_m:.3f}–{scenario.aircraft.cg_max_m:.3f} m</td>
<td>{html.escape(scenario.aircraft.classification)}</td></tr>
</table>
<h2>Manifest</h2>
<table>
<tr><th>ID</th><th>Description</th><th>Weight (kg)</th><th>Allowed stations</th><th>Classification</th></tr>
{manifest_rows}
</table>
{solution_sections}
</body>
</html>"""


def _solution_html(
    scenario: LoadingScenario,
    solution: LoadingSolution,
) -> str:
    assignment_rows = "\n".join(
        f"<tr><td>{html.escape(item.id)}</td>"
        f"<td>{html.escape(solution.assignment.get(item.id, 'UNASSIGNED'))}</td></tr>"
        for item in scenario.items
    )
    violations = (
        "<ul>"
        + "".join(f"<li>{html.escape(value)}</li>" for value in solution.violations)
        + "</ul>"
        if solution.violations
        else "None"
    )
    css = "ok" if solution.feasible else "bad"
    return f"""
<h2>{html.escape(solution.method)}</h2>
<p class="{css}"><strong>{html.escape(solution.status)}</strong></p>
<table>
<tr><th>Total weight</th><th>Total moment</th><th>CG</th><th>CG error</th><th>Objective</th><th>Runtime</th></tr>
<tr><td>{solution.total_weight_kg:.1f} kg</td>
<td>{solution.total_moment_kg_m:.1f} kg·m</td>
<td>{solution.cg_m:.4f} m</td>
<td>{solution.cg_error_m:.4f} m</td>
<td>{solution.objective:.8f}</td>
<td>{solution.runtime_s:.4f} s</td></tr>
</table>
<h3>Candidate loading configuration</h3>
<table><tr><th>Item</th><th>Station</th></tr>{assignment_rows}</table>
<p><strong>Constraint violations:</strong> {violations}</p>
"""
