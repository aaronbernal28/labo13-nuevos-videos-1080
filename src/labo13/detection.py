import math

import numpy as np
import numpy.typing as npt
import scipy.ndimage as ndi

from labo13.types import PixelCentroid


_CONNECTIVITY_8: npt.NDArray[np.int64] = np.ones((3, 3), dtype=np.int64)


def _build_disk_footprint(radius: int) -> npt.NDArray[np.bool_]:
	"""Build an exact Euclidean disk footprint matching skimage.morphology.disk."""
	yy, xx = np.ogrid[-radius : radius + 1, -radius : radius + 1]
	disk: npt.NDArray[np.bool_] = (xx * xx + yy * yy) <= radius * radius
	return disk


def _build_foreground_mask(
	frame_gray: npt.NDArray[np.uint8],
	background_gray: npt.NDArray[np.uint8],
	threshold_low: float,
	threshold_high: float,
	disk_radius: int,
	opening_disk_radius: int = 0,
) -> npt.NDArray[np.bool_]:
	"""Subtract background, threshold, and apply morphological closing/opening."""
	diff_image: npt.NDArray[np.int16] = background_gray.astype(
		np.int16
	) - frame_gray.astype(np.int16)
	low_bound: int = math.floor(threshold_low)
	high_bound: int = math.ceil(threshold_high)
	raw_mask: npt.NDArray[np.bool_] = (diff_image > low_bound) & (
		diff_image < high_bound
	)
	footprint: npt.NDArray[np.bool_] = _build_disk_footprint(disk_radius)
	closed_mask: npt.NDArray[np.bool_] = ndi.binary_closing(
		raw_mask, structure=footprint
	)
	if opening_disk_radius > 0:
		open_footprint: npt.NDArray[np.bool_] = _build_disk_footprint(
			opening_disk_radius
		)
		opened_mask: npt.NDArray[np.bool_] = ndi.binary_opening(
			closed_mask, structure=open_footprint
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

	diff_image: npt.NDArray[np.int16] = background_roi.astype(
		np.int16
	) - frame_roi.astype(np.int16)
	low_bound: int = math.floor(threshold_low)
	high_bound: int = math.ceil(threshold_high)
	raw_mask: npt.NDArray[np.bool_] = (diff_image > low_bound) & (
		diff_image < high_bound
	)
	if not bool(np.any(raw_mask)):
		return (float("nan"), float("nan"))

	closed_mask: npt.NDArray[np.bool_] = ndi.binary_closing(
		raw_mask, structure=_build_disk_footprint(disk_radius)
	)
	labels_closed: npt.NDArray[np.int32]
	num_closed: int
	labels_closed, num_closed = ndi.label(closed_mask, structure=_CONNECTIVITY_8)
	if num_closed == 0:
		return (float("nan"), float("nan"))

	counts: npt.NDArray[np.intp] = np.bincount(labels_closed.ravel())
	counts[0] = 0
	slices: list[tuple[slice, slice] | None] = ndi.find_objects(labels_closed)

	y_center: float = 0.0
	x_center: float = 0.0

	if opening_disk_radius <= 0:
		best_label: int = int(np.argmax(counts))
		sl: tuple[slice, slice] | None = slices[best_label - 1]
		if sl is None:
			return (float("nan"), float("nan"))
		sl_y, sl_x = sl
		ys, xs = np.nonzero(labels_closed[sl_y, sl_x] == best_label)
		y_center = float(ys.mean()) + float(sl_y.start)
		x_center = float(xs.mean()) + float(sl_x.start)
	else:
		open_disk: npt.NDArray[np.bool_] = _build_disk_footprint(opening_disk_radius)
		min_area: int = int(np.count_nonzero(open_disk))
		candidate_labels: npt.NDArray[np.intp] = np.flatnonzero(counts >= min_area)
		if candidate_labels.size == 0:
			return (float("nan"), float("nan"))

		pad: int = opening_disk_radius + 1
		best_area: int = 0
		for lbl_np in candidate_labels:
			lbl_id: int = int(lbl_np)
			cand_sl: tuple[slice, slice] | None = slices[lbl_id - 1]
			if cand_sl is None:
				continue
			sl_y, sl_x = cand_sl
			sub_mask: npt.NDArray[np.bool_] = labels_closed[sl_y, sl_x] == lbl_id
			sub_padded: npt.NDArray[np.bool_] = np.pad(
				sub_mask, pad, mode="constant", constant_values=False
			)
			opened_sub: npt.NDArray[np.bool_] = ndi.binary_opening(
				sub_padded, structure=open_disk
			)
			opened_labels: npt.NDArray[np.int32]
			num_opened: int
			opened_labels, num_opened = ndi.label(opened_sub, structure=_CONNECTIVITY_8)
			if num_opened == 0:
				continue
			opened_counts: npt.NDArray[np.intp] = np.bincount(opened_labels.ravel())
			opened_counts[0] = 0
			top_sub_label: int = int(np.argmax(opened_counts))
			area: int = int(opened_counts[top_sub_label])
			if area > best_area:
				best_area = area
				ys, xs = np.nonzero(opened_labels == top_sub_label)
				y_center = float(ys.mean()) - float(pad) + float(sl_y.start)
				x_center = float(xs.mean()) - float(pad) + float(sl_x.start)

		if best_area == 0:
			return (float("nan"), float("nan"))

	return (
		float(round(x_center + float(roi_x_start))),
		float(round(y_center + float(roi_y_start))),
	)
