import math
from pathlib import Path

import matplotlib


matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import pandas as pd
import scipy.ndimage as ndi

from labo13.pendulum_analysis import (
	UndampedFitResult,
	compute_borda_period,
	evaluate_undamped_model,
)
from labo13.video import load_image_gray


_CONNECTIVITY_8: npt.NDArray[np.int64] = np.ones((3, 3), dtype=np.int64)


def _disk_footprint(radius: int) -> npt.NDArray[np.bool_]:
	"""Build Euclidean disk footprint matching labo13.detection."""
	yy, xx = np.ogrid[-radius : radius + 1, -radius : radius + 1]
	disk: npt.NDArray[np.bool_] = (xx * xx + yy * yy) <= radius * radius
	return disk


def plot_frame_processing_steps(
	frame_path: Path,
	background_path: Path,
	output_path: Path,
	threshold_low: float = 20.0,
	threshold_high: float = 255.0,
	closing_radius: int = 3,
	opening_radius: int = 6,
	roi_y_start: int = 1180,
	roi_y_end: int = 2080,
	roi_x_start: int = 200,
	roi_x_end: int = 3500,
	crop_half_width: int = 180,
	crop_height_above: int = 220,
	crop_height_below: int = 120,
) -> tuple[float, float]:
	"""Generate title-free 3-panel morphological processing figure for §2.1.

	Panels: (a) thresholded background-subtracted mask, (b) after morphological
	closing (disk r=3 px), (c) after morphological opening (disk r=6 px) and
	largest-component centroid detection.
	"""
	frame_gray: npt.NDArray[np.uint8] = load_image_gray(frame_path)
	bg_gray: npt.NDArray[np.uint8] = load_image_gray(background_path)

	frame_roi: npt.NDArray[np.uint8] = frame_gray[
		roi_y_start:roi_y_end, roi_x_start:roi_x_end
	]
	bg_roi: npt.NDArray[np.uint8] = bg_gray[
		roi_y_start:roi_y_end, roi_x_start:roi_x_end
	]

	diff_image: npt.NDArray[np.int16] = bg_roi.astype(np.int16) - frame_roi.astype(
		np.int16
	)
	low_bound: int = math.floor(threshold_low)
	high_bound: int = math.ceil(threshold_high)
	raw_mask: npt.NDArray[np.bool_] = (diff_image > low_bound) & (
		diff_image < high_bound
	)

	closed_mask: npt.NDArray[np.bool_] = ndi.binary_closing(
		raw_mask, structure=_disk_footprint(closing_radius)
	)
	opened_mask: npt.NDArray[np.bool_] = ndi.binary_opening(
		closed_mask, structure=_disk_footprint(opening_radius)
	)

	labels: npt.NDArray[np.int32]
	num_labels: int
	labels, num_labels = ndi.label(opened_mask, structure=_CONNECTIVITY_8)
	if num_labels == 0:
		raise ValueError(f"No foreground component detected in {frame_path}")

	counts: npt.NDArray[np.intp] = np.bincount(labels.ravel())
	counts[0] = 0
	best_label: int = int(np.argmax(counts))
	final_mask: npt.NDArray[np.bool_] = labels == best_label
	ys, xs = np.nonzero(final_mask)
	cy_roi: float = float(ys.mean())
	cx_roi: float = float(xs.mean())

	cx_full: float = float(round(cx_roi + float(roi_x_start)))
	cy_full: float = float(round(cy_roi + float(roi_y_start)))

	h_roi: int = int(raw_mask.shape[0])
	w_roi: int = int(raw_mask.shape[1])
	x0: int = max(0, int(round(cx_roi)) - crop_half_width)
	x1: int = min(w_roi, int(round(cx_roi)) + crop_half_width)
	y0: int = max(0, int(round(cy_roi)) - crop_height_above)
	y1: int = min(h_roi, int(round(cy_roi)) + crop_height_below)

	extent: tuple[float, float, float, float] = (
		float(x0 + roi_x_start),
		float(x1 + roi_x_start),
		float(y1 + roi_y_start),
		float(y0 + roi_y_start),
	)

	fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6), sharex=True, sharey=True)
	panel_masks: list[npt.NDArray[np.bool_]] = [
		raw_mask[y0:y1, x0:x1],
		closed_mask[y0:y1, x0:x1],
		final_mask[y0:y1, x0:x1],
	]
	panel_tags: list[str] = ["(a)", "(b)", "(c)"]

	for idx, (ax, mask, tag) in enumerate(
		zip(axes, panel_masks, panel_tags, strict=True)
	):
		ax.imshow(mask.astype(np.uint8), cmap="gray", extent=extent, origin="upper")
		ax.text(
			0.04,
			0.94,
			tag,
			transform=ax.transAxes,
			color="white",
			fontsize=11,
			fontweight="bold",
			va="top",
			ha="left",
			bbox={"facecolor": "black", "alpha": 0.65, "pad": 2.5, "edgecolor": "none"},
		)
		ax.set_xlabel("$x$ [px]")
		if idx == 0:
			ax.set_ylabel("$y$ [px]")
		if idx == 2:
			ax.plot(
				cx_full,
				cy_full,
				marker="+",
				markersize=11,
				markeredgewidth=2.0,
				color="#d62728",
				label="Centroide",
			)
			ax.legend(loc="lower right", frameon=True, fontsize=8.5)

	fig.tight_layout()
	output_path.parent.mkdir(parents=True, exist_ok=True)
	fig.savefig(output_path, dpi=300, bbox_inches="tight")
	plt.close(fig)
	return cx_full, cy_full


def plot_representative_fit(
	df_angular: pd.DataFrame,
	fit: UndampedFitResult,
	output_path: Path,
) -> None:
	"""Generate title-free 2-panel sinusoidal fit + residuals figure."""
	t_arr: npt.NDArray[np.float64] = df_angular["t"].to_numpy(dtype=np.float64)
	tau: npt.NDArray[np.float64] = df_angular["tau"].to_numpy(dtype=np.float64)
	theta_deg: npt.NDArray[np.float64] = df_angular["theta_deg"].to_numpy(
		dtype=np.float64
	)

	theta_pred_rad: npt.NDArray[np.float64] = evaluate_undamped_model(
		tau,
		fit.theta0_rad,
		fit.omega_rad_s,
		fit.phi_rad,
		float(np.radians(fit.offset_deg)),
	)
	residuos_deg: npt.NDArray[np.float64] = theta_deg - np.degrees(theta_pred_rad)

	tau_fine: npt.NDArray[np.float64] = np.linspace(0.0, float(tau[-1]), 1400)
	t_fine: npt.NDArray[np.float64] = float(t_arr[0]) + tau_fine
	fit_fine_deg: npt.NDArray[np.float64] = np.degrees(
		evaluate_undamped_model(
			tau_fine,
			fit.theta0_rad,
			fit.omega_rad_s,
			fit.phi_rad,
			float(np.radians(fit.offset_deg)),
		)
	)

	fig, (ax_top, ax_bot) = plt.subplots(
		2,
		1,
		figsize=(8.0, 4.5),
		sharex=True,
		gridspec_kw={"height_ratios": [2.5, 1.1]},
	)
	ax_top.plot(
		t_arr,
		theta_deg,
		"o",
		markersize=2.3,
		color="black",
		alpha=0.55,
		label="Datos experimentales",
	)
	ax_top.plot(
		t_fine,
		fit_fine_deg,
		color="#d62728",
		linewidth=1.5,
		label="Ajuste sinusoidal",
	)
	ax_top.set_ylabel(r"$\theta$ [$^\circ$]")
	ax_top.grid(alpha=0.25)
	ax_top.legend(loc="upper right", fontsize=8.5, frameon=True)

	ax_bot.plot(
		t_arr,
		residuos_deg,
		"o",
		markersize=2.0,
		color="#1f77b4",
		alpha=0.65,
	)
	ax_bot.axhline(0.0, color="black", linestyle="--", linewidth=0.9)
	ax_bot.set_xlabel(r"$t$ [s]")
	ax_bot.set_ylabel(r"Residuo [$^\circ$]")
	ax_bot.grid(alpha=0.25)

	fig.tight_layout()
	output_path.parent.mkdir(parents=True, exist_ok=True)
	fig.savefig(output_path, dpi=300, bbox_inches="tight")
	plt.close(fig)


def plot_period_vs_amplitude(
	summary_df: pd.DataFrame,
	t0_exp_s: float,
	t0_teo_s: float,
	sigma_t0_teo_s: float,
	output_path: Path,
) -> None:
	"""Generate title-free 2-panel T(theta_0) and log-scale Delta T figure."""
	df_asc: pd.DataFrame = summary_df.sort_values("theta0_deg", ascending=True)
	theta_deg: npt.NDArray[np.float64] = df_asc["theta0_deg"].to_numpy(dtype=np.float64)
	sigma_theta_deg: npt.NDArray[np.float64] = df_asc["sigma_theta0_deg"].to_numpy(
		dtype=np.float64
	)
	t_s: npt.NDArray[np.float64] = df_asc["T_s"].to_numpy(dtype=np.float64)
	sigma_t_s: npt.NDArray[np.float64] = df_asc["sigma_T_s"].to_numpy(dtype=np.float64)
	delta_t_ms: npt.NDArray[np.float64] = df_asc["delta_T_ms"].to_numpy(
		dtype=np.float64
	)
	sigma_dt_ms: npt.NDArray[np.float64] = df_asc["sigma_delta_T_ms"].to_numpy(
		dtype=np.float64
	)
	comp_mask: npt.NDArray[np.bool_] = df_asc["compatible_3sigma"].to_numpy(dtype=bool)

	theta_grid_deg: npt.NDArray[np.float64] = np.linspace(0.5, 60.0, 500)
	theta_grid_rad: npt.NDArray[np.float64] = np.radians(theta_grid_deg)
	t_borda_grid: npt.NDArray[np.float64] = np.array(
		[compute_borda_period(t0_exp_s, float(th)) for th in theta_grid_rad],
		dtype=np.float64,
	)
	dt_borda_grid_ms: npt.NDArray[np.float64] = (t_borda_grid - t0_exp_s) * 1e3

	fig, (ax_top, ax_bot) = plt.subplots(
		2,
		1,
		figsize=(8.2, 6.2),
		sharex=True,
		gridspec_kw={"height_ratios": [1.3, 1.2]},
	)

	ax_top.axhspan(
		t0_teo_s - sigma_t0_teo_s,
		t0_teo_s + sigma_t0_teo_s,
		color="#2ca02c",
		alpha=0.14,
		label=r"$T_{0,\mathrm{teo}} = 2\pi\sqrt{L/g} \pm \sigma$",
	)
	ax_top.axhline(
		t0_exp_s,
		color="gray",
		linestyle="--",
		linewidth=1.1,
		label=r"$T_0$ (límite experimental $\theta_0 \to 0$)",
	)
	ax_top.plot(
		theta_grid_deg,
		t_borda_grid,
		color="#ff7f0e",
		linewidth=1.5,
		label=r"Expansión de Borda ($4.^\circ$ orden en $\theta_0$)",
	)
	ax_top.errorbar(
		theta_deg[comp_mask],
		t_s[comp_mask],
		xerr=sigma_theta_deg[comp_mask],
		yerr=sigma_t_s[comp_mask],
		fmt="o",
		markersize=5.5,
		color="#1f77b4",
		capsize=2.5,
		label=r"Compatible con $T_0$ ($|\Delta T| \leq 3\sigma_{\Delta T}$)",
	)
	ax_top.errorbar(
		theta_deg[~comp_mask],
		t_s[~comp_mask],
		xerr=sigma_theta_deg[~comp_mask],
		yerr=sigma_t_s[~comp_mask],
		fmt="s",
		markersize=5.0,
		color="#d62728",
		capsize=2.5,
		label=r"Incompatible con $T_0$ ($|\Delta T| > 3\sigma_{\Delta T}$)",
	)
	ax_top.set_ylabel(r"$T$ [s]")
	ax_top.grid(alpha=0.25)
	ax_top.legend(loc="upper left", fontsize=8.0, frameon=True)

	ax_bot.plot(
		theta_grid_deg,
		dt_borda_grid_ms,
		color="#ff7f0e",
		linewidth=1.5,
		label=r"Predicción de Borda $\Delta T_{\mathrm{Borda}}$",
	)
	ax_bot.errorbar(
		theta_deg[comp_mask],
		delta_t_ms[comp_mask],
		yerr=3.0 * sigma_dt_ms[comp_mask],
		fmt="o",
		markersize=5.5,
		color="#1f77b4",
		capsize=3.0,
		label=r"Compatible (barras $\pm 3\sigma_{\Delta T}$)",
	)
	ax_bot.errorbar(
		theta_deg[~comp_mask],
		delta_t_ms[~comp_mask],
		yerr=3.0 * sigma_dt_ms[~comp_mask],
		fmt="s",
		markersize=5.0,
		color="#d62728",
		capsize=3.0,
		label=r"Incompatible (barras $\pm 3\sigma_{\Delta T}$)",
	)
	ax_bot.set_yscale("log")
	ax_bot.set_ylim(0.05, 300.0)
	ax_bot.set_xlabel(r"Amplitud angular $\theta_0$ [$^\circ$]")
	ax_bot.set_ylabel(r"$\Delta T = T - T_0$ [ms]")
	ax_bot.grid(True, which="both", alpha=0.25)
	ax_bot.legend(loc="upper left", fontsize=8.0, frameon=True)

	fig.tight_layout()
	output_path.parent.mkdir(parents=True, exist_ok=True)
	fig.savefig(output_path, dpi=300, bbox_inches="tight")
	plt.close(fig)
