from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from airload_qc.classical import solve_cp_sat, solve_exact
from airload_qc.data import demo_scenario, with_prior_assignment
from airload_qc.models import CargoItem, LoadingScenario
from airload_qc.quantum import QaoaConfig, solve_qaoa
from airload_qc.qubo import qubo_summary
from airload_qc.reporting import DISCLAIMER, assignment_csv, html_report
from airload_qc.scenarios import run_late_change, run_scaling_benchmark
from airload_qc.validation import validate_scenario


st.set_page_config(
    page_title="Quantum Aircraft Loading",
    page_icon="✈️",
    layout="wide",
)
st.markdown(
    """
<style>
.block-container{padding-top:1.5rem;max-width:1280px}
.hero{padding:1.4rem 1.7rem;border-radius:18px;
background:linear-gradient(120deg,#25105f,#6c2bd9);color:white;margin-bottom:1rem}
.hero h1{margin:0 0 .35rem;font-size:2rem}.hero p{margin:0;color:#ece6ff}
.label{display:inline-block;padding:.22rem .55rem;border-radius:999px;
font-size:.75rem;font-weight:700;background:#eee8ff;color:#4b20a5;margin-right:.3rem}
.safe{padding:.8rem 1rem;border-left:4px solid #6c2bd9;background:#f7f4ff}
[data-testid="stMetric"]{border:1px solid #e7e3f1;padding:.65rem;border-radius:12px}
</style>
""",
    unsafe_allow_html=True,
)


def initialize() -> None:
    defaults = {
        "scenario": demo_scenario(),
        "exact": None,
        "cp_sat": None,
        "quantum": None,
        "late_result": None,
        "benchmark": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def manifest_frame(scenario: LoadingScenario) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": item.id,
                "description": item.description,
                "weight_kg": item.weight_kg,
                "allowed_stations": "|".join(item.allowed_stations),
                "classification": item.classification,
            }
            for item in scenario.items
        ]
    )


def apply_manifest(frame: pd.DataFrame) -> None:
    items = tuple(
        CargoItem(
            id=str(row["id"]).strip(),
            description=str(row["description"]).strip(),
            weight_kg=float(row["weight_kg"]),
            allowed_stations=tuple(
                value.strip()
                for value in str(row["allowed_stations"]).split("|")
                if value.strip()
            ),
            classification="SYNTHETIC DATA",
        )
        for _, row in frame.iterrows()
    )
    old = st.session_state.scenario
    st.session_state.scenario = LoadingScenario(
        name="User-edited synthetic scenario",
        aircraft=old.aircraft,
        items=items,
        move_penalty=old.move_penalty,
        classification="SYNTHETIC DATA",
    )
    clear_results()


def clear_results() -> None:
    for key in ("exact", "cp_sat", "quantum", "late_result", "benchmark"):
        st.session_state[key] = None


def cg_figure(solution, aircraft):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=solution.cg_m,
            number={"suffix": " m", "valueformat": ".3f"},
            delta={
                "reference": aircraft.target_cg_m,
                "valueformat": ".3f",
                "increasing": {"color": "#6c2bd9"},
                "decreasing": {"color": "#6c2bd9"},
            },
            title={"text": f"{solution.method} longitudinal CG"},
            gauge={
                "axis": {
                    "range": [
                        aircraft.cg_min_m - 0.3,
                        aircraft.cg_max_m + 0.3,
                    ]
                },
                "bar": {"color": "#6c2bd9"},
                "steps": [
                    {
                        "range": [aircraft.cg_min_m, aircraft.cg_max_m],
                        "color": "#dff5e8",
                    }
                ],
                "threshold": {
                    "line": {"color": "#111827", "width": 4},
                    "value": aircraft.target_cg_m,
                },
            },
        )
    )
    fig.update_layout(height=280, margin=dict(l=25, r=25, t=60, b=10))
    return fig


def loading_figure(scenario, solution):
    rows = []
    for item in scenario.items:
        station_id = solution.assignment.get(item.id)
        if station_id:
            station = scenario.aircraft.station_by_id(station_id)
            rows.append((item.id, item.description, item.weight_kg, station.arm_m))
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[station.arm_m for station in scenario.aircraft.stations],
            y=[0] * len(scenario.aircraft.stations),
            mode="markers+text",
            marker={"size": 32, "color": "#d9cef7", "line": {"color": "#5422b8"}},
            text=[station.name for station in scenario.aircraft.stations],
            textposition="bottom center",
            name="Stations",
            hovertemplate="%{text}<br>Arm %{x:.1f} m<extra></extra>",
        )
    )
    for index, (item_id, description, weight, arm) in enumerate(rows):
        fig.add_trace(
            go.Scatter(
                x=[arm],
                y=[0.22 + 0.12 * index],
                mode="markers+text",
                marker={"size": max(18, min(42, weight / 2)), "color": "#6c2bd9"},
                text=[item_id],
                textposition="top center",
                name=item_id,
                hovertemplate=(
                    f"{description}<br>{weight:.1f} kg<br>Arm {arm:.1f} m<extra></extra>"
                ),
            )
        )
    fig.add_vline(
        x=solution.cg_m,
        line_dash="dash",
        line_color="#0b7a47",
        annotation_text=f"CG {solution.cg_m:.3f} m",
    )
    fig.update_layout(
        title="Calculated longitudinal loading",
        xaxis_title="Longitudinal arm (m)",
        yaxis={"visible": False, "range": [-0.15, max(0.8, 0.4 + len(rows) * 0.12)]},
        height=350,
        showlegend=False,
        margin=dict(l=20, r=20, t=55, b=45),
    )
    return fig


def solution_card(solution, scenario):
    status = "✅ Feasible" if solution.feasible else "❌ Not feasible"
    st.subheader(solution.method)
    st.caption(f"{status} · {solution.status} · EXPERIMENTAL RESULT")
    cols = st.columns(4)
    cols[0].metric("CG", f"{solution.cg_m:.4f} m")
    cols[1].metric("Target error", f"{solution.cg_error_m:.4f} m")
    cols[2].metric("Objective", f"{solution.objective:.8f}")
    cols[3].metric("Measured runtime", f"{solution.runtime_s:.3f} s")
    assignment = pd.DataFrame(
        [
            {
                "Item": item.id,
                "Description": item.description,
                "Weight (kg)": item.weight_kg,
                "Candidate station": solution.assignment.get(item.id, "UNASSIGNED"),
            }
            for item in scenario.items
        ]
    )
    st.dataframe(assignment, width="stretch", hide_index=True)
    if solution.violations:
        st.error("\n".join(solution.violations))
    else:
        st.success("Independent check: all modeled constraints are satisfied.")


initialize()
scenario: LoadingScenario = st.session_state.scenario

with st.sidebar:
    st.header("Demo controls")
    if st.button("Reset built-in demo", width="stretch"):
        st.session_state.scenario = demo_scenario()
        clear_results()
        st.rerun()
    st.caption("The QAOA settings below are ASSUMPTIONS, not aircraft data.")
    reps = st.select_slider("QAOA circuit depth (p)", options=[1, 2], value=1)
    shots = st.select_slider("Measurement shots", options=[256, 512, 1024, 2048], value=1024)
    maxiter = st.slider("Classical parameter iterations", 10, 100, 40, 5)
    seed = st.number_input("Reproducibility seed", min_value=0, value=42)
    qaoa_config = QaoaConfig(
        reps=int(reps),
        shots=int(shots),
        maxiter=int(maxiter),
        seed=int(seed),
    )
    st.markdown("---")
    st.markdown("**Evidence labels**")
    st.markdown(
        '<span class="label">SYNTHETIC DATA</span>'
        '<span class="label">ASSUMPTION</span>'
        '<span class="label">EXPERIMENTAL RESULT</span>',
        unsafe_allow_html=True,
    )
    st.caption("No airline, fuel-saving, certification or quantum-advantage claim is made.")

st.markdown(
    """
<div class="hero">
<h1>Quantum-Assisted Aircraft Loading Optimisation</h1>
<p>QAOA research prototype with exact validation and a fair classical comparison.</p>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown(f'<div class="safe">{DISCLAIMER}</div>', unsafe_allow_html=True)

tabs = st.tabs(
    [
        "Dashboard",
        "Aircraft & Manifest",
        "Optimisation",
        "Quantum Analysis",
        "Late Change",
        "Scaling",
        "Export",
    ]
)

with tabs[0]:
    st.subheader("Research question")
    st.write(
        "Can quantum optimisation become useful as aircraft-loading decisions and "
        "constraints increase? The application measures QAOA against honest classical "
        "baselines; it does not assume or claim quantum advantage."
    )
    cols = st.columns(4)
    cols[0].metric("Manifest items", len(scenario.items))
    cols[1].metric("Loading stations", len(scenario.aircraft.stations))
    cols[2].metric("Target CG", f"{scenario.aircraft.target_cg_m:.2f} m")
    cols[3].metric(
        "Allowed CG",
        f"{scenario.aircraft.cg_min_m:.1f}–{scenario.aircraft.cg_max_m:.1f} m",
    )
    st.info(
        "Objective: minimise squared deviation from the selected target CG. "
        "For late changes, a small preference discourages moving existing cargo."
    )
    st.markdown(
        "**Workflow:** manifest → constrained model → QUBO → QAOA/Qiskit → "
        "bitstring decoding → independent CG and constraint checks → comparison."
    )

with tabs[1]:
    st.subheader("Simplified aircraft model")
    st.caption("All built-in values are SYNTHETIC DATA and are not operational.")
    aircraft = scenario.aircraft
    cols = st.columns(3)
    new_target = cols[0].number_input(
        "Target CG (m)", value=float(aircraft.target_cg_m), step=0.1
    )
    new_min = cols[1].number_input(
        "Minimum CG (m)", value=float(aircraft.cg_min_m), step=0.1
    )
    new_max = cols[2].number_input(
        "Maximum CG (m)", value=float(aircraft.cg_max_m), step=0.1
    )
    if st.button("Apply CG settings"):
        try:
            updated_aircraft = replace(
                aircraft,
                target_cg_m=float(new_target),
                cg_min_m=float(new_min),
                cg_max_m=float(new_max),
            )
            st.session_state.scenario = replace(scenario, aircraft=updated_aircraft)
            clear_results()
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
    station_df = pd.DataFrame(
        [
            {
                "Station": station.id,
                "Name": station.name,
                "Arm (m)": station.arm_m,
                "Capacity (kg)": station.max_weight_kg,
                "Classification": station.classification,
            }
            for station in aircraft.stations
        ]
    )
    st.dataframe(station_df, width="stretch", hide_index=True)
    st.subheader("Cargo manifest")
    edited = st.data_editor(
        manifest_frame(scenario),
        num_rows="dynamic",
        width="stretch",
        disabled=["classification"],
        key="manifest_editor",
    )
    if st.button("Validate and apply manifest", type="primary"):
        try:
            apply_manifest(edited)
            issues = validate_scenario(st.session_state.scenario)
            if issues:
                st.error("\n".join(issues))
            else:
                st.success("Manifest accepted.")
            st.rerun()
        except (ValueError, KeyError) as exc:
            st.error(f"Manifest error: {exc}")

with tabs[2]:
    st.subheader("Run the same scenario with quantum and classical methods")
    issues = validate_scenario(scenario)
    if issues:
        st.error("\n".join(issues))
    run_cols = st.columns(3)
    if run_cols[0].button("Run exact verification", type="primary", width="stretch"):
        st.session_state.exact = solve_exact(scenario)
    if run_cols[1].button("Run OR-Tools baseline", width="stretch"):
        st.session_state.cp_sat = solve_cp_sat(scenario)
    if run_cols[2].button("Run QAOA / Qiskit", width="stretch"):
        with st.spinner("Running measured QAOA simulation locally…"):
            st.session_state.quantum = solve_qaoa(scenario, qaoa_config)

    available = [
        solution
        for solution in (
            st.session_state.exact,
            st.session_state.cp_sat,
            st.session_state.quantum,
        )
        if solution is not None
    ]
    for solution in available:
        solution_card(solution, scenario)
        if solution.feasible:
            visual_cols = st.columns(2)
            visual_cols[0].plotly_chart(
                cg_figure(solution, scenario.aircraft),
                width="stretch",
            )
            visual_cols[1].plotly_chart(
                loading_figure(scenario, solution),
                width="stretch",
            )
    if len(available) >= 2:
        comparison = pd.DataFrame(
            [
                {
                    "Method": value.method,
                    "Objective": value.objective,
                    "Runtime (s)": value.runtime_s,
                    "Feasible": value.feasible,
                }
                for value in available
            ]
        )
        st.subheader("Measured comparison")
        st.dataframe(comparison, width="stretch", hide_index=True)
        fig = go.Figure(
            go.Bar(
                x=comparison["Method"],
                y=comparison["Objective"],
                marker_color=["#35128a", "#6c2bd9", "#a985ff"][: len(comparison)],
            )
        )
        fig.update_layout(
            yaxis_title="Common objective (lower is better)",
            height=340,
        )
        st.plotly_chart(fig, width="stretch")

with tabs[3]:
    st.subheader("What the quantum solver actually does")
    summary = qubo_summary(scenario)
    cols = st.columns(4)
    cols[0].metric("Assignment bits", summary["assignment_variables"])
    cols[1].metric("QUBO bits incl. slack", summary["qubo_variables_including_slack"])
    cols[2].metric("Modeled constraints", summary["constraints"])
    cols[3].metric("Penalty", summary["penalty"])
    st.write(
        "Each assignment bit represents one item placed at one allowed station. "
        "Exactly-one and station-capacity constraints are converted into QUBO penalty "
        "terms. QAOA uses the resulting cost Hamiltonian to sample candidate bitstrings."
    )
    st.warning(
        "The allowable CG envelope is checked independently after decoding. "
        "QAOA is heuristic: a sample can be infeasible and no global optimum is guaranteed."
    )
    if st.session_state.quantum:
        metadata = st.session_state.quantum.metadata
        st.json(metadata)
        st.caption(
            "Circuit depth, parameters, simulator, shots and sampling information above "
            "are EXPERIMENTAL RESULTS from this local run."
        )

with tabs[4]:
    st.subheader("Late-manifest-change demonstration")
    st.write(
        "The built-in scenario adds a 20 kg synthetic baggage batch. The current "
        "configuration is checked first; a revised candidate is generated if needed."
    )
    baseline = st.session_state.exact or st.session_state.cp_sat
    if baseline is None:
        st.info("Run exact verification or OR-Tools in the Optimisation tab first.")
    else:
        include_quantum = st.checkbox("Also run QAOA for the changed manifest", value=False)
        if st.button("Add late baggage and re-evaluate", type="primary"):
            with st.spinner("Checking and re-optimising the changed manifest…"):
                st.session_state.late_result = run_late_change(
                    baseline,
                    run_quantum=include_quantum,
                    qaoa_config=qaoa_config,
                )
        late = st.session_state.late_result
        if late:
            if late.current_loading_still_feasible:
                st.success("The provisional late-bag placement remains feasible.")
            else:
                st.error("The provisional placement violates modeled constraints.")
                st.write(late.current_loading_violations)
            changed_scenario = with_prior_assignment(
                demo_scenario(late=True),
                baseline.assignment,
            )
            solution_card(late.revised_classical, changed_scenario)
            if late.revised_quantum:
                solution_card(late.revised_quantum, changed_scenario)

with tabs[5]:
    st.subheader("Scaling experiment")
    st.write(
        "Run synthetic cases with more item-to-station decisions. Values shown here "
        "are measured locally and labelled EXPERIMENTAL RESULT. QAOA is capped to keep "
        "the live demo reliable; larger QUBOs are reported without inventing results."
    )
    sizes = st.multiselect("Item counts", [2, 3, 4, 5, 6], default=[2, 3, 4])
    qaoa_cap = st.selectbox("Run QAOA up to this item count", [2, 3], index=1)
    if st.button("Run scaling benchmark", type="primary", disabled=not sizes):
        with st.spinner("Running exact, CP-SAT and selected QAOA experiments…"):
            st.session_state.benchmark = run_scaling_benchmark(
                sorted(sizes),
                qaoa_max_items=int(qaoa_cap),
                qaoa_config=qaoa_config,
            )
    if st.session_state.benchmark:
        benchmark_df = pd.DataFrame(st.session_state.benchmark)
        st.dataframe(benchmark_df, width="stretch", hide_index=True)
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=benchmark_df["items"],
                y=benchmark_df["exact_runtime_s"],
                mode="lines+markers",
                name="Exact enumeration",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=benchmark_df["items"],
                y=benchmark_df["cp_sat_runtime_s"],
                mode="lines+markers",
                name="OR-Tools CP-SAT",
            )
        )
        qaoa_rows = benchmark_df[benchmark_df["qaoa_run"]]
        if not qaoa_rows.empty:
            fig.add_trace(
                go.Scatter(
                    x=qaoa_rows["items"],
                    y=qaoa_rows["qaoa_runtime_s"],
                    mode="lines+markers",
                    name="QAOA",
                )
            )
        fig.update_layout(
            title="Measured local runtime (not evidence of quantum advantage)",
            xaxis_title="Manifest items",
            yaxis_title="Runtime (seconds)",
            yaxis_type="log",
            height=380,
        )
        st.plotly_chart(fig, width="stretch")
        st.download_button(
            "Download benchmark CSV",
            benchmark_df.to_csv(index=False),
            "scaling_benchmark.csv",
            "text/csv",
        )

with tabs[6]:
    st.subheader("Download calculated results")
    completed = [
        result
        for result in (
            st.session_state.exact,
            st.session_state.cp_sat,
            st.session_state.quantum,
        )
        if result is not None
    ]
    if not completed:
        st.info("Run at least one optimiser to enable result exports.")
    else:
        report = html_report(scenario, completed)
        cols = st.columns(3)
        cols[0].download_button(
            "Download HTML report",
            report,
            "aircraft_loading_report.html",
            "text/html",
            width="stretch",
        )
        preferred = next((value for value in completed if value.feasible), completed[0])
        cols[1].download_button(
            "Download assignment CSV",
            assignment_csv(scenario, preferred),
            "candidate_loading.csv",
            "text/csv",
            width="stretch",
        )
        payload = {
            "scenario": scenario.name,
            "classification": scenario.classification,
            "solutions": [value.to_dict() for value in completed],
            "disclaimer": DISCLAIMER,
        }
        cols[2].download_button(
            "Download machine-readable JSON",
            json.dumps(payload, indent=2),
            "aircraft_loading_results.json",
            "application/json",
            width="stretch",
        )
