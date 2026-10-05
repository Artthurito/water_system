from datetime import datetime

from app.domain.enums import RoadStatus


def water_level(install_height_cm: float, distance_cm: float) -> float:
    return max(0.0, install_height_cm - distance_cm)


def moving_average(values: list[float]) -> float:
    if not values:
        raise ValueError("moving_average requires at least one value")

    return sum(values) / len(values)


def classify(level_cm: float, attention_cm: float, avoid_cm: float, blocked_cm: float) -> RoadStatus:
    if level_cm >= blocked_cm:
        return RoadStatus.BLOQUEADA
    if level_cm >= avoid_cm:
        return RoadStatus.EVITAR
    if level_cm >= attention_cm:
        return RoadStatus.ATENCAO

    return RoadStatus.LIVRE


def is_valid_distance(distance_cm: float, install_height_cm: float, tolerance_cm: float) -> bool:
    return 0 < distance_cm <= install_height_cm + tolerance_cm


def is_stale(last_reading_at: datetime, now: datetime, stale_after_seconds: int) -> bool:
    return (now - last_reading_at).total_seconds() > stale_after_seconds
