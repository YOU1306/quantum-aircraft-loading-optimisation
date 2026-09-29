from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


VALID_CLASSIFICATIONS = {
    "SOURCE",
    "ASSUMPTION",
    "SYNTHETIC DATA",
    "EXPERIMENTAL RESULT",
}


@dataclass(frozen=True)
class Station:
    id: str
    name: str
    arm_m: float
    max_weight_kg: float
    classification: str = "SYNTHETIC DATA"

    def __post_init__(self) -> None:
        if self.arm_m <= 0 or self.max_weight_kg <= 0:
            raise ValueError("Station arm and capacity must be positive.")
        if self.classification not in VALID_CLASSIFICATIONS:
            raise ValueError(f"Unknown data classification: {self.classification}")


@dataclass(frozen=True)
class CargoItem:
    id: str
    description: str
    weight_kg: float
    allowed_stations: tuple[str, ...]
    classification: str = "SYNTHETIC DATA"
    is_late: bool = False

    def __post_init__(self) -> None:
        if self.weight_kg <= 0:
            raise ValueError("Cargo weight must be positive.")
        if not self.allowed_stations:
            raise ValueError("Each cargo item needs at least one allowed station.")
        if self.classification not in VALID_CLASSIFICATIONS:
            raise ValueError(f"Unknown data classification: {self.classification}")


@dataclass(frozen=True)
class Aircraft:
    name: str
    basic_weight_kg: float
    basic_arm_m: float
    max_payload_kg: float
    cg_min_m: float
    cg_max_m: float
    target_cg_m: float
    stations: tuple[Station, ...]
    classification: str = "SYNTHETIC DATA"

    def __post_init__(self) -> None:
        if self.basic_weight_kg <= 0 or self.basic_arm_m <= 0:
            raise ValueError("Basic aircraft weight and arm must be positive.")
        if self.max_payload_kg <= 0:
            raise ValueError("Maximum payload must be positive.")
        if not self.cg_min_m < self.target_cg_m < self.cg_max_m:
            raise ValueError("Target CG must lie strictly inside the CG range.")
        station_ids = [station.id for station in self.stations]
        if len(station_ids) != len(set(station_ids)):
            raise ValueError("Station IDs must be unique.")
        if self.classification not in VALID_CLASSIFICATIONS:
            raise ValueError(f"Unknown data classification: {self.classification}")

    @property
    def basic_moment_kg_m(self) -> float:
        return self.basic_weight_kg * self.basic_arm_m

    def station_by_id(self, station_id: str) -> Station:
        for station in self.stations:
            if station.id == station_id:
                return station
        raise KeyError(f"Unknown station: {station_id}")


@dataclass(frozen=True)
class LoadingScenario:
    name: str
    aircraft: Aircraft
    items: tuple[CargoItem, ...]
    prior_assignment: dict[str, str] = field(default_factory=dict)
    move_penalty: float = 0.05
    classification: str = "SYNTHETIC DATA"

    def __post_init__(self) -> None:
        item_ids = [item.id for item in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("Cargo item IDs must be unique.")
        known_stations = {station.id for station in self.aircraft.stations}
        for item in self.items:
            unknown = set(item.allowed_stations) - known_stations
            if unknown:
                raise ValueError(f"{item.id} uses unknown stations: {sorted(unknown)}")
        if self.move_penalty < 0:
            raise ValueError("Move penalty cannot be negative.")
        if self.classification not in VALID_CLASSIFICATIONS:
            raise ValueError(f"Unknown data classification: {self.classification}")


@dataclass
class LoadingSolution:
    method: str
    status: str
    assignment: dict[str, str]
    total_weight_kg: float
    total_moment_kg_m: float
    cg_m: float
    cg_error_m: float
    objective: float
    feasible: bool
    violations: list[str]
    runtime_s: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
