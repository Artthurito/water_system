from datetime import datetime, timedelta, timezone

import pytest

from app.domain.enums import RoadStatus
from app.modules.analysis.utils import classify, is_stale, is_valid_distance, moving_average, water_level


def test_water_level_is_height_minus_distance():
  assert water_level(20.0, 14.0) == 6.0


def test_water_level_is_never_negative():
  assert water_level(20.0, 22.5) == 0.0


def test_moving_average_of_single_value():
  assert moving_average([4.0]) == 4.0


def test_moving_average_of_five_values():
  assert moving_average([0.0, 0.0, 0.0, 0.0, 10.0]) == 2.0


def test_moving_average_rejects_empty_list():
  with pytest.raises(ValueError):
    moving_average([])


@pytest.mark.parametrize(
  ("level", "expected"),
  [
    (0.0, RoadStatus.LIVRE),
    (1.99, RoadStatus.LIVRE),
    (2.0, RoadStatus.ATENCAO),
    (4.99, RoadStatus.ATENCAO),
    (5.0, RoadStatus.EVITAR),
    (7.99, RoadStatus.EVITAR),
    (8.0, RoadStatus.BLOQUEADA),
    (15.0, RoadStatus.BLOQUEADA),
  ],
)
def test_classify_ranges_and_exact_edges(level, expected):
  assert classify(level, attention_cm=2.0, avoid_cm=5.0, blocked_cm=8.0) == expected


@pytest.mark.parametrize(
  ("distance", "expected"),
  [(0.0, False), (-1.0, False), (0.1, True), (20.0, True), (25.0, True), (25.01, False)],
)
def test_is_valid_distance(distance, expected):
  assert is_valid_distance(distance, install_height_cm=20.0, tolerance_cm=5.0) is expected


def test_reading_older_than_threshold_is_stale():
  now = datetime(2026, 10, 5, 18, 0, tzinfo=timezone.utc)

  assert is_stale(now - timedelta(seconds=121), now, 120) is True


def test_reading_exactly_at_threshold_is_not_stale():
  now = datetime(2026, 10, 5, 18, 0, tzinfo=timezone.utc)

  assert is_stale(now - timedelta(seconds=120), now, 120) is False
