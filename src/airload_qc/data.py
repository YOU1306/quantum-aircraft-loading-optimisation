from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import Aircraft, CargoItem, LoadingScenario, Station


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


def load_aircraft(path: str | Path) -> Aircraft:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    stations = tuple(
        Station(
            id=row["id"],
            name=row["name"],
            arm_m=float(row["arm_m"]),
            max_weight_kg=float(row["max_weight_kg"]),
            classification=row.get("classification", "SYNTHETIC DATA"),
        )
        for row in payload["stations"]
    )
    return Aircraft(
        name=payload["name"],
        basic_weight_kg=float(payload["basic_weight_kg"]),
        basic_arm_m=float(payload["basic_arm_m"]),
        max_payload_kg=float(payload["max_payload_kg"]),
        cg_min_m=float(payload["cg_min_m"]),
        cg_max_m=float(payload["cg_max_m"]),
        target_cg_m=float(payload["target_cg_m"]),
        stations=stations,
        classification=payload.get("classification", "SYNTHETIC DATA"),
    )


def load_manifest(path: str | Path) -> tuple[CargoItem, ...]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        rows = csv.DictReader(handle)
        return tuple(
            CargoItem(
                id=row["id"].strip(),
                description=row["description"].strip(),
                weight_kg=float(row["weight_kg"]),
                allowed_stations=tuple(
                    station.strip()
                    for station in row["allowed_stations"].split("|")
                    if station.strip()
                ),
                classification=row.get("classification", "SYNTHETIC DATA").strip(),
                is_late=row.get("is_late", "false").strip().lower() == "true",
            )
            for row in rows
        )


def demo_scenario(late: bool = False) -> LoadingScenario:
    manifest = "late_manifest.csv" if late else "demo_manifest.csv"
    return LoadingScenario(
        name="Late-change demonstration" if late else "Baseline demonstration",
        aircraft=load_aircraft(DATA_DIR / "demo_aircraft.json"),
        items=load_manifest(DATA_DIR / manifest),
        move_penalty=0.05,
        classification="SYNTHETIC DATA",
    )


def with_prior_assignment(
    scenario: LoadingScenario,
    prior_assignment: dict[str, str],
) -> LoadingScenario:
    return LoadingScenario(
        name=scenario.name,
        aircraft=scenario.aircraft,
        items=scenario.items,
        prior_assignment=prior_assignment,
        move_penalty=scenario.move_penalty,
        classification=scenario.classification,
    )
