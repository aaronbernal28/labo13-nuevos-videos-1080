import math

import numpy as np
import numpy.typing as npt

from labo13.detection import compute_bob_centroid


def test_compute_bob_centroid_synthetic_disk() -> None:
	bg: npt.NDArray[np.uint8] = np.full((100, 120), 200, dtype=np.uint8)
	frame: npt.NDArray[np.uint8] = bg.copy()
	yy, xx = np.ogrid[:100, :120]
	disk_mask: npt.NDArray[np.bool_] = (xx - 70) ** 2 + (yy - 40) ** 2 <= 8**2
	frame[disk_mask] = 50  # diff = 200 - 50 = 150 (in (100, 200))

	x_px: float
	y_px: float
	x_px, y_px = compute_bob_centroid(frame, bg, 100.0, 200.0, 2)
	assert x_px == 70.0
	assert y_px == 40.0
	assert x_px.is_integer()
	assert y_px.is_integer()


def test_compute_bob_centroid_empty_returns_nan() -> None:
	bg: npt.NDArray[np.uint8] = np.full((64, 64), 200, dtype=np.uint8)
	x_px: float
	y_px: float
	x_px, y_px = compute_bob_centroid(bg, bg, 100.0, 200.0, 2)
	assert math.isnan(x_px)
	assert math.isnan(y_px)
