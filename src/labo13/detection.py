import numpy as np
import numpy.typing as npt
import skimage.measure
import skimage.morphology

from labo13.types import PixelCentroid


def _build_foreground_mask(
	frame_gray: npt.NDArray[np.uint8],
	background_gray: npt.NDArray[np.uint8],
	threshold_low: float,
	threshold_high: float,
	disk_radius: int,
) -> npt.NDArray[np.bool_]:
	"""Subtract background, threshold difference, and apply morphological closing."""
	diff_image: npt.NDArray[np.float64] = background_gray.astype(
		np.float64
	) - frame_gray.astype(np.float64)
	raw_mask: npt.NDArray[np.bool_] = (diff_image > threshold_low) & (
		diff_image < threshold_high
	)
	footprint: npt.NDArray[np.uint8] = skimage.morphology.disk(disk_radius)
	closed_mask: npt.NDArray[np.bool_] = skimage.morphology.closing(raw_mask, footprint)
	return closed_mask


def compute_bob_centroid(
	frame_gray: npt.NDArray[np.uint8],
	background_gray: npt.NDArray[np.uint8],
	threshold_low: float = 100.0,
	threshold_high: float = 200.0,
	disk_radius: int = 2,
) -> PixelCentroid:
	"""Compute bob centroid (x_px, y_px) in pixel coordinates or (nan, nan)."""
	mask: npt.NDArray[np.bool_] = _build_foreground_mask(
		frame_gray=frame_gray,
		background_gray=background_gray,
		threshold_low=threshold_low,
		threshold_high=threshold_high,
		disk_radius=disk_radius,
	)
	labels: npt.NDArray[np.int64] = skimage.measure.label(mask)
	regions = skimage.measure.regionprops(labels)
	if not regions:
		return (float("nan"), float("nan"))

	largest_region = max(regions, key=lambda r: float(r.area))
	y_center: float
	x_center: float
	y_center, x_center = largest_region.centroid
	return (float(x_center), float(y_center))
