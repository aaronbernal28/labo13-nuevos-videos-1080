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
	opening_disk_radius: int = 0,
) -> npt.NDArray[np.bool_]:
	"""Subtract background, threshold, and apply morphological closing/opening."""
	diff_image: npt.NDArray[np.float64] = background_gray.astype(
		np.float64
	) - frame_gray.astype(np.float64)
	raw_mask: npt.NDArray[np.bool_] = (diff_image > threshold_low) & (
		diff_image < threshold_high
	)
	footprint: npt.NDArray[np.uint8] = skimage.morphology.disk(disk_radius)
	closed_mask: npt.NDArray[np.bool_] = skimage.morphology.closing(raw_mask, footprint)
	if opening_disk_radius > 0:
		open_footprint: npt.NDArray[np.uint8] = skimage.morphology.disk(
			opening_disk_radius
		)
		opened_mask: npt.NDArray[np.bool_] = skimage.morphology.opening(
			closed_mask, open_footprint
		)
		return opened_mask
	return closed_mask


def compute_bob_centroid(
	frame_gray: npt.NDArray[np.uint8],
	background_gray: npt.NDArray[np.uint8],
	threshold_low: float = 20.0,
	threshold_high: float = 255.0,
	disk_radius: int = 3,
	roi_y_start: int = 0,
	roi_y_end: int | None = None,
	roi_x_start: int = 0,
	roi_x_end: int | None = None,
	opening_disk_radius: int = 0,
) -> PixelCentroid:
	"""Compute bob centroid (x_px, y_px) rounded to integer pixels or (nan, nan)."""
	y_end: int = int(frame_gray.shape[0]) if roi_y_end is None else roi_y_end
	x_end: int = int(frame_gray.shape[1]) if roi_x_end is None else roi_x_end
	frame_roi: npt.NDArray[np.uint8] = frame_gray[roi_y_start:y_end, roi_x_start:x_end]
	background_roi: npt.NDArray[np.uint8] = background_gray[
		roi_y_start:y_end, roi_x_start:x_end
	]
	mask: npt.NDArray[np.bool_] = _build_foreground_mask(
		frame_gray=frame_roi,
		background_gray=background_roi,
		threshold_low=threshold_low,
		threshold_high=threshold_high,
		disk_radius=disk_radius,
		opening_disk_radius=opening_disk_radius,
	)
	labels: npt.NDArray[np.int64] = skimage.measure.label(mask)
	regions = skimage.measure.regionprops(labels)
	if not regions:
		return (float("nan"), float("nan"))

	largest_region = max(regions, key=lambda r: float(r.area))
	y_center: float
	x_center: float
	y_center, x_center = largest_region.centroid
	return (
		float(round(x_center + float(roi_x_start))),
		float(round(y_center + float(roi_y_start))),
	)
