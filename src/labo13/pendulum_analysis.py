from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd
from scipy.optimize import curve_fit, least_squares
from scipy.signal import find_peaks


CALIBRATION_VIDEOS: tuple[str, ...] = ("IMG_1555", "IMG_1556", "IMG_1557", "IMG_1558")
EXCLUDED_VIDEOS: frozenset[str] = frozenset({"IMG_1569"})

# Directly measured pivot coordinates on the 4K (3840x2160) frame
MEASURED_PIVOT_X_PX: float = 1960.0
MEASURED_PIVOT_Y_PX: float = 37.0

# Real pendulum length (same L as Fig. 1) and local gravity (Buenos Aires)
LARGO_PENDULO_M: float = 1.072
SIGMA_L_M: float = 0.005
G_REF_M_S2: float = 9.797

DEFAULT_PIVOT_X0: tuple[float, float, float] = (1950.0, 35.0, 1990.0)


@dataclass(frozen=True)
class PivotCalibration:
	xc_px: float
	yc_px: float
	r_px: float
	rms_radial_px: float
	n_points: int


@dataclass(frozen=True)
class UndampedFitResult:
	video_name: str
	n_frames: int
	duracion_s: float
	theta0_rad: float
	sigma_theta0_rad: float
	theta0_deg: float
	sigma_theta0_deg: float
	omega_rad_s: float
	sigma_omega_rad_s: float
	T_s: float
	sigma_T_s: float
	phi_rad: float
	offset_deg: float
	s_res_deg: float
	rms_res_deg: float
	dof: int


@dataclass(frozen=True)
class AmplitudeDecayResult:
	video_name: str
	n_frames: int
	duracion_s: float
	n_cycles: int
	amp_init_deg: float
	amp_final_deg: float
	amp_drop_pct: float


def load_active_trajectories(
	csv_path: Path | str,
	excluded_videos: frozenset[str] = EXCLUDED_VIDEOS,
) -> pd.DataFrame:
	"""Load trajectories CSV and filter out excluded videos."""
	df_all: pd.DataFrame = pd.read_csv(Path(csv_path))
	required_cols: set[str] = {"video_name", "t", "x", "y"}
	missing_cols: set[str] = required_cols - set(df_all.columns)
	if missing_cols:
		raise ValueError(
			f"Missing required columns in trajectories CSV: {sorted(missing_cols)}"
		)

	mask_active: pd.Series[bool] = ~df_all["video_name"].isin(excluded_videos)
	df_active: pd.DataFrame = df_all.loc[mask_active].copy()
	return df_active


def compute_pivot_calibration(
	df_active: pd.DataFrame,
	calibration_videos: tuple[str, ...] = CALIBRATION_VIDEOS,
	x0: tuple[float, float, float] = DEFAULT_PIVOT_X0,
) -> PivotCalibration:
	"""Fit a circular arc (x - xc)^2 + (y - yc)^2 = R^2 over large-swing videos."""
	df_cal: pd.DataFrame = df_active[
		df_active["video_name"].isin(calibration_videos)
	].dropna(subset=["x", "y"])
	if len(df_cal) < 3:
		raise ValueError(
			f"Insufficient points ({len(df_cal)}) for circular-arc pivot calibration"
		)

	x_arr: npt.NDArray[np.float64] = df_cal["x"].to_numpy(dtype=np.float64)
	y_arr: npt.NDArray[np.float64] = df_cal["y"].to_numpy(dtype=np.float64)

	def _circle_residuals(params: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
		xc: float = float(params[0])
		yc: float = float(params[1])
		r_px: float = float(params[2])
		res: npt.NDArray[np.float64] = np.hypot(x_arr - xc, y_arr - yc) - r_px
		return res

	result: Any = least_squares(_circle_residuals, x0=np.array(x0, dtype=np.float64))
	xc_px: float = float(result.x[0])
	yc_px: float = float(result.x[1])
	r_px: float = float(result.x[2])
	rms_radial_px: float = float(np.sqrt(np.mean(np.square(result.fun))))

	return PivotCalibration(
		xc_px=xc_px,
		yc_px=yc_px,
		r_px=r_px,
		rms_radial_px=rms_radial_px,
		n_points=int(len(df_cal)),
	)


def build_measured_pivot(
	df_active: pd.DataFrame,
	xc_px: float = MEASURED_PIVOT_X_PX,
	yc_px: float = MEASURED_PIVOT_Y_PX,
	calibration_videos: tuple[str, ...] = CALIBRATION_VIDEOS,
) -> PivotCalibration:
	"""Construct PivotCalibration from directly measured frame coordinates."""
	df_cal: pd.DataFrame = df_active[
		df_active["video_name"].isin(calibration_videos)
	].dropna(subset=["x", "y"])
	if df_cal.empty:
		return PivotCalibration(
			xc_px=xc_px, yc_px=yc_px, r_px=0.0, rms_radial_px=0.0, n_points=0
		)
	x_arr: npt.NDArray[np.float64] = df_cal["x"].to_numpy(dtype=np.float64)
	y_arr: npt.NDArray[np.float64] = df_cal["y"].to_numpy(dtype=np.float64)
	radii: npt.NDArray[np.float64] = np.hypot(x_arr - xc_px, y_arr - yc_px)
	r_mean: float = float(np.mean(radii))
	rms_radial: float = float(np.sqrt(np.mean(np.square(radii - r_mean))))
	return PivotCalibration(
		xc_px=xc_px,
		yc_px=yc_px,
		r_px=r_mean,
		rms_radial_px=rms_radial,
		n_points=int(len(df_cal)),
	)


def compute_angular_series(
	df_video: pd.DataFrame,
	pivot: PivotCalibration,
) -> pd.DataFrame:
	"""Convert pixel centroids (x, y) to angular series atan2(x - xc, y - yc)."""
	df_v: pd.DataFrame = df_video.dropna(subset=["t", "x", "y"]).sort_values("t").copy()
	if df_v.empty:
		raise ValueError("No valid (t, x, y) rows in video dataframe")

	t_arr: npt.NDArray[np.float64] = df_v["t"].to_numpy(dtype=np.float64)
	dx: npt.NDArray[np.float64] = df_v["x"].to_numpy(dtype=np.float64) - pivot.xc_px
	dy: npt.NDArray[np.float64] = df_v["y"].to_numpy(dtype=np.float64) - pivot.yc_px

	theta_rad: npt.NDArray[np.float64] = np.arctan2(dx, dy)

	df_v["tau"] = t_arr - float(t_arr[0])
	df_v["theta_rad"] = theta_rad
	df_v["theta_deg"] = np.degrees(theta_rad)
	return df_v


def evaluate_undamped_model(
	tau: npt.NDArray[np.float64],
	amplitude: float,
	omega: float,
	phi: float,
	offset: float,
) -> npt.NDArray[np.float64]:
	"""Evaluate undamped harmonic model: A * cos(omega * tau + phi) + offset."""
	out: npt.NDArray[np.float64] = amplitude * np.cos(omega * tau + phi) + offset
	return out


def _estimate_initial_harmonic_params(
	tau: npt.NDArray[np.float64],
	theta: npt.NDArray[np.float64],
) -> tuple[float, float, float, float]:
	"""Estimate (A, omega, phi, offset) via zero-padded FFT and linear least squares."""
	dt: float = float(np.median(np.diff(tau)))
	n_fft: int = 65536
	freqs: npt.NDArray[np.float64] = np.fft.rfftfreq(n_fft, d=dt)
	spectrum: npt.NDArray[np.float64] = np.abs(
		np.fft.rfft(theta - float(np.mean(theta)), n=n_fft)
	)
	mask_band: npt.NDArray[np.bool_] = (freqs >= 0.2) & (freqs <= 1.5)
	band_freqs: npt.NDArray[np.float64] = freqs[mask_band]
	band_spec: npt.NDArray[np.float64] = spectrum[mask_band]
	f_init: float = float(band_freqs[int(np.argmax(band_spec))])
	omega_init: float = 2.0 * float(np.pi) * f_init

	design_matrix: npt.NDArray[np.float64] = np.column_stack(
		[np.cos(omega_init * tau), -np.sin(omega_init * tau), np.ones_like(tau)]
	)
	beta: npt.NDArray[np.float64]
	beta, *_ = np.linalg.lstsq(design_matrix, theta, rcond=None)
	a_init: float = float(np.hypot(beta[0], beta[1]))
	phi_init: float = float(np.arctan2(beta[1], beta[0]))
	offset_init: float = float(beta[2])
	return a_init, omega_init, phi_init, offset_init


def fit_undamped_oscillation(
	video_name: str,
	df_angular: pd.DataFrame,
) -> UndampedFitResult:
	"""Fit undamped sinusoidal model via two-stage empirical-residual double fit.

	Stage 1 performs an unweighted nonlinear least-squares fit (initialized via
	zero-padded FFT and linear least squares) to estimate the empirical per-point
	residual dispersion s_res = sqrt(sum(r^2) / dof). Stage 2 re-fits with
	sigma = s_res and absolute_sigma=True so parameter uncertainties come directly
	from the observed data dispersion without assuming an arbitrary pixel error.
	"""
	t_arr: npt.NDArray[np.float64] = df_angular["t"].to_numpy(dtype=np.float64)
	tau: npt.NDArray[np.float64] = df_angular["tau"].to_numpy(dtype=np.float64)
	theta: npt.NDArray[np.float64] = df_angular["theta_rad"].to_numpy(dtype=np.float64)

	a_init: float
	omega_init: float
	phi_init: float
	offset_init: float
	a_init, omega_init, phi_init, offset_init = _estimate_initial_harmonic_params(
		tau, theta
	)

	# Stage 1: unweighted fit to estimate empirical residual dispersion
	popt_1: npt.NDArray[np.float64]
	popt_1, _ = curve_fit(
		evaluate_undamped_model,
		tau,
		theta,
		p0=[a_init, omega_init, phi_init, offset_init],
		maxfev=20000,
	)
	dof: int = int(len(tau) - 4)
	res_1: npt.NDArray[np.float64] = theta - evaluate_undamped_model(
		tau,
		float(popt_1[0]),
		float(popt_1[1]),
		float(popt_1[2]),
		float(popt_1[3]),
	)
	s_res_rad: float = float(np.sqrt(np.sum(np.square(res_1)) / float(dof)))
	sigma_emp: npt.NDArray[np.float64] = np.full_like(
		theta, max(s_res_rad, 1e-12), dtype=np.float64
	)

	# Stage 2: weighted fit using empirical s_res with absolute_sigma=True
	popt: npt.NDArray[np.float64]
	pcov: npt.NDArray[np.float64]
	popt, pcov = curve_fit(
		evaluate_undamped_model,
		tau,
		theta,
		p0=popt_1,
		sigma=sigma_emp,
		absolute_sigma=True,
		maxfev=20000,
	)
	perr: npt.NDArray[np.float64] = np.sqrt(np.diag(pcov))

	a_fit: float = float(popt[0])
	omega_fit: float = float(popt[1])
	phi_fit: float = float(popt[2])
	offset_fit: float = float(popt[3])

	s_a: float = float(perr[0])
	s_omega: float = float(perr[1])

	if a_fit < 0.0:
		a_fit = -a_fit
		phi_fit = float((phi_fit + np.pi) % (2.0 * np.pi))
	omega_fit = abs(omega_fit)

	t_fit: float = (2.0 * float(np.pi)) / omega_fit
	s_t: float = ((2.0 * float(np.pi)) / (omega_fit**2)) * s_omega

	theta_pred: npt.NDArray[np.float64] = evaluate_undamped_model(
		tau, a_fit, omega_fit, phi_fit, offset_fit
	)
	residuos_rad: npt.NDArray[np.float64] = theta - theta_pred
	s_res_final_rad: float = float(
		np.sqrt(np.sum(np.square(residuos_rad)) / float(dof))
	)

	return UndampedFitResult(
		video_name=video_name,
		n_frames=int(len(tau)),
		duracion_s=float(t_arr[-1] - t_arr[0]),
		theta0_rad=a_fit,
		sigma_theta0_rad=s_a,
		theta0_deg=float(np.degrees(a_fit)),
		sigma_theta0_deg=float(np.degrees(s_a)),
		omega_rad_s=omega_fit,
		sigma_omega_rad_s=s_omega,
		T_s=t_fit,
		sigma_T_s=s_t,
		phi_rad=phi_fit,
		offset_deg=float(np.degrees(offset_fit)),
		s_res_deg=float(np.degrees(s_res_final_rad)),
		rms_res_deg=float(np.degrees(np.std(residuos_rad))),
		dof=dof,
	)


def compute_amplitude_decay(
	video_name: str,
	df_angular: pd.DataFrame,
	min_peak_distance_frames: int = 90,
) -> AmplitudeDecayResult:
	"""Model-free amplitude decay check comparing first vs. last oscillation peaks."""
	t_arr: npt.NDArray[np.float64] = df_angular["t"].to_numpy(dtype=np.float64)
	theta_deg: npt.NDArray[np.float64] = df_angular["theta_deg"].to_numpy(
		dtype=np.float64
	)
	theta_centered: npt.NDArray[np.float64] = theta_deg - float(np.mean(theta_deg))

	pos_peaks: npt.NDArray[np.intp]
	neg_peaks: npt.NDArray[np.intp]
	pos_peaks, _ = find_peaks(theta_centered, distance=min_peak_distance_frames)
	neg_peaks, _ = find_peaks(-theta_centered, distance=min_peak_distance_frames)

	if pos_peaks.size < 2 or neg_peaks.size < 2:
		raise ValueError(
			f"Insufficient oscillation peaks detected for {video_name}: "
			f"pos={pos_peaks.size}, neg={neg_peaks.size}"
		)

	amp_init: float = 0.5 * float(
		theta_centered[pos_peaks[0]] - theta_centered[neg_peaks[0]]
	)
	amp_final: float = 0.5 * float(
		theta_centered[pos_peaks[-1]] - theta_centered[neg_peaks[-1]]
	)
	drop_pct: float = ((amp_init - amp_final) / amp_init) * 100.0
	n_cycles: int = int(min(pos_peaks.size, neg_peaks.size))

	return AmplitudeDecayResult(
		video_name=video_name,
		n_frames=int(len(t_arr)),
		duracion_s=float(t_arr[-1] - t_arr[0]),
		n_cycles=n_cycles,
		amp_init_deg=amp_init,
		amp_final_deg=amp_final,
		amp_drop_pct=drop_pct,
	)


def compute_borda_period(t0_s: float, theta0_rad: float) -> float:
	"""Compute Borda pendulum period T_0 * (1 + theta^2/16 + 11*theta^4/3072)."""
	return t0_s * (1.0 + (theta0_rad**2) / 16.0 + (11.0 * (theta0_rad**4)) / 3072.0)


def build_summary_and_diagnostics(
	undamped_results: list[UndampedFitResult],
	decay_results: list[AmplitudeDecayResult],
	measured_pivot: PivotCalibration,
	fitted_pivot: PivotCalibration | None = None,
	largo_m: float = LARGO_PENDULO_M,
	sigma_l_m: float = SIGMA_L_M,
	g_ref_m_s2: float = G_REF_M_S2,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
	"""Build Toma-indexed summary table, amplitude-decay table, and diagnostics."""
	if not undamped_results:
		raise ValueError("undamped_results cannot be empty")

	# Toma 1 = largest angle ... Toma N = smallest angle
	sorted_desc: list[UndampedFitResult] = sorted(
		undamped_results, key=lambda r: r.theta0_deg, reverse=True
	)
	decay_by_name: dict[str, AmplitudeDecayResult] = {
		r.video_name: r for r in decay_results
	}

	ref: UndampedFitResult = sorted_desc[-1]
	ref_toma_label: str = f"Toma {len(sorted_desc)}"
	t_ref_obs_s: float = ref.T_s
	sigma_t0_ref_s: float = ref.sigma_T_s
	t0_borda_lim_s: float = t_ref_obs_s / (1.0 + (ref.theta0_rad**2) / 16.0)

	t0_teo_s: float = 2.0 * float(np.pi) * float(np.sqrt(largo_m / g_ref_m_s2))
	sigma_t0_teo_s: float = 0.5 * t0_teo_s * (sigma_l_m / largo_m)
	t0_diff_teo_exp_ms: float = (t0_teo_s - t0_borda_lim_s) * 1e3
	t0_z_teo_exp: float = abs(t0_teo_s - t0_borda_lim_s) / float(
		np.hypot(sigma_t0_teo_s, sigma_t0_ref_s)
	)

	l_eff_m: float = g_ref_m_s2 * (t0_borda_lim_s / (2.0 * float(np.pi))) ** 2
	sigma_l_eff_m: float = 2.0 * l_eff_m * (sigma_t0_ref_s / t0_borda_lim_s)

	summary_rows: list[dict[str, Any]] = []
	decay_rows: list[dict[str, Any]] = []

	for idx, res in enumerate(sorted_desc, start=1):
		toma_label: str = f"Toma {idx}"
		delta_t_ms: float = (res.T_s - t0_borda_lim_s) * 1e3
		sigma_delta_t_ms: float = float(np.hypot(res.sigma_T_s, sigma_t0_ref_s) * 1e3)
		three_sigma_delta_t_ms: float = 3.0 * sigma_delta_t_ms
		z_score: float = abs(delta_t_ms) / sigma_delta_t_ms
		compatible_3sigma: bool = bool(z_score <= 3.0)

		t_borda_s: float = compute_borda_period(t0_borda_lim_s, res.theta0_rad)
		delta_t_borda_ms: float = (res.T_s - t_borda_s) * 1e3

		summary_rows.append(
			{
				"toma": toma_label,
				"toma_idx": idx,
				"video_name": res.video_name,
				"n_frames": res.n_frames,
				"duracion_s": res.duracion_s,
				"theta0_deg": res.theta0_deg,
				"sigma_theta0_deg": res.sigma_theta0_deg,
				"T_s": res.T_s,
				"sigma_T_s": res.sigma_T_s,
				"offset_deg": res.offset_deg,
				"s_res_deg": res.s_res_deg,
				"rms_res_deg": res.rms_res_deg,
				"dof": res.dof,
				"delta_T_ms": delta_t_ms,
				"sigma_delta_T_ms": sigma_delta_t_ms,
				"three_sigma_delta_T_ms": three_sigma_delta_t_ms,
				"z_score": z_score,
				"compatible_3sigma": compatible_3sigma,
				"T_borda_s": t_borda_s,
				"delta_T_borda_ms": delta_t_borda_ms,
			}
		)

		if res.video_name in decay_by_name:
			d_res: AmplitudeDecayResult = decay_by_name[res.video_name]
			decay_rows.append(
				{
					"toma": toma_label,
					"toma_idx": idx,
					"video_name": d_res.video_name,
					"n_frames": d_res.n_frames,
					"duracion_s": d_res.duracion_s,
					"theta0_deg": res.theta0_deg,
					"n_cycles": d_res.n_cycles,
					"amp_init_deg": d_res.amp_init_deg,
					"amp_final_deg": d_res.amp_final_deg,
					"amp_drop_pct": d_res.amp_drop_pct,
				}
			)

	summary_df: pd.DataFrame = pd.DataFrame(summary_rows)
	decay_df: pd.DataFrame = pd.DataFrame(decay_rows)

	asc_df: pd.DataFrame = summary_df.sort_values("theta0_deg", ascending=True)
	compatible_df: pd.DataFrame = asc_df[asc_df["compatible_3sigma"]]
	incompatible_df: pd.DataFrame = asc_df[~asc_df["compatible_3sigma"]]

	last_comp_toma: str | None = (
		str(compatible_df.iloc[-1]["toma"]) if not compatible_df.empty else None
	)
	last_comp_theta0: float | None = (
		float(compatible_df.iloc[-1]["theta0_deg"]) if not compatible_df.empty else None
	)
	first_incomp_toma: str | None = (
		str(incompatible_df.iloc[0]["toma"]) if not incompatible_df.empty else None
	)
	first_incomp_theta0: float | None = (
		float(incompatible_df.iloc[0]["theta0_deg"])
		if not incompatible_df.empty
		else None
	)

	borda_devs: npt.NDArray[np.float64] = summary_df["delta_T_borda_ms"].to_numpy(
		dtype=np.float64
	)
	abs_borda_devs: npt.NDArray[np.float64] = np.abs(borda_devs)
	max_borda_idx: int = int(np.argmax(abs_borda_devs))

	decay_summary: dict[str, Any] = {}
	if not decay_df.empty:
		drops_arr: npt.NDArray[np.float64] = decay_df["amp_drop_pct"].to_numpy(
			dtype=np.float64
		)
		min_pos: int = int(np.argmin(drops_arr))
		max_pos: int = int(np.argmax(drops_arr))
		decay_summary = {
			"min_amp_drop_pct": float(drops_arr[min_pos]),
			"min_amp_drop_toma": str(decay_df.iloc[min_pos]["toma"]),
			"max_amp_drop_pct": float(drops_arr[max_pos]),
			"max_amp_drop_toma": str(decay_df.iloc[max_pos]["toma"]),
		}

	rep_takes: dict[str, dict[str, Any]] = {}
	for rep_toma in ("Toma 1", f"Toma {len(sorted_desc)}"):
		sub_df: pd.DataFrame = summary_df[summary_df["toma"] == rep_toma]
		if not sub_df.empty:
			rep_takes[rep_toma] = {
				str(k): (v.item() if hasattr(v, "item") else v)
				for k, v in sub_df.iloc[0].to_dict().items()
			}

	diagnostics: dict[str, Any] = {
		"measured_pivot": asdict(measured_pivot),
		"fitted_circle_crosscheck": asdict(fitted_pivot)
		if fitted_pivot is not None
		else None,
		"reference_period": {
			"toma_ref": ref_toma_label,
			"theta0_ref_deg": ref.theta0_deg,
			"T_ref_obs_s": t_ref_obs_s,
			"T0_borda_lim_s": t0_borda_lim_s,
			"sigma_T0_s": sigma_t0_ref_s,
		},
		"length_comparison": {
			"largo_m": largo_m,
			"sigma_l_m": sigma_l_m,
			"g_ref_m_s2": g_ref_m_s2,
			"T0_teo_s": t0_teo_s,
			"sigma_T0_teo_s": sigma_t0_teo_s,
			"diff_teo_exp_ms": t0_diff_teo_exp_ms,
			"z_teo_exp": t0_z_teo_exp,
			"L_eff_m": l_eff_m,
			"sigma_L_eff_m": sigma_l_eff_m,
		},
		"compatibility_3sigma": {
			"n_total": int(len(summary_df)),
			"n_compatible": int(len(compatible_df)),
			"n_incompatible": int(len(incompatible_df)),
			"last_compatible_toma": last_comp_toma,
			"last_compatible_theta0_deg": last_comp_theta0,
			"first_incompatible_toma": first_incomp_toma,
			"first_incompatible_theta0_deg": first_incomp_theta0,
		},
		"borda_agreement": {
			"max_abs_dev_ms": float(abs_borda_devs[max_borda_idx]),
			"max_abs_dev_toma": str(summary_df.iloc[max_borda_idx]["toma"]),
			"rms_dev_ms": float(np.sqrt(np.mean(np.square(borda_devs)))),
			"mean_dev_ms": float(np.mean(borda_devs)),
		},
		"amplitude_decay_summary": decay_summary,
		"representative_takes": rep_takes,
	}

	return summary_df, decay_df, diagnostics


def _fmt_es(value: float, decimals: int, math_mode: bool = True) -> str:
	"""Format a float with Spanish decimal comma (and no negative zero)."""
	threshold: float = 0.5 * (10.0 ** (-decimals))
	clean_val: float = 0.0 if abs(value) < threshold else value
	sep: str = "{,}" if math_mode else ","
	return f"{clean_val:.{decimals}f}".replace(".", sep)


def format_summary_latex_table(summary_df: pd.DataFrame) -> str:
	"""Format summary DataFrame as an Anexo LaTeX booktabs table (no Comp. column)."""
	caption: str = (
		r"\caption{Resultados del ajuste sinusoidal para las 14 tomas analizadas, "
		r"numeradas en orden decreciente de amplitud angular desde la Toma~1 "
		r"(mayor amplitud) hasta la Toma~14 (menor amplitud). Se reportan la "
		r"amplitud $\theta_0$, el período medido $T$, el desvío "
		r"$\Delta T = T - T_0$ respecto del límite experimental de pequeñas "
		r"oscilaciones $T_0$, la razón $|\Delta T|/\sigma_{\Delta T}$ y el residuo "
		r"frente a la expansión de Borda $T - T_{\text{Borda}}$.}"
	)
	header: str = (
		r"Toma & $\theta_0$ [$^\circ$] & $T$ [s] & $\Delta T$ [ms] & "
		r"$|\Delta T|/\sigma_{\Delta T}$ & $T - T_{\text{Borda}}$ [ms] \\"
	)
	lines: list[str] = [
		r"\begin{table}[htbp]",
		r"\centering",
		caption,
		r"\label{tab:resumen_pendulo}",
		r"\small",
		r"\begin{tabular}{lccccc}",
		r"\toprule",
		header,
		r"\midrule",
	]

	for _, row in summary_df.iterrows():
		toma_str: str = str(row["toma"])
		theta_str: str = (
			f"${_fmt_es(float(row['theta0_deg']), 3)} \\pm "
			f"{_fmt_es(float(row['sigma_theta0_deg']), 3)}$"
		)
		t_str: str = (
			f"${_fmt_es(float(row['T_s']), 5)} \\pm "
			f"{_fmt_es(float(row['sigma_T_s']), 5)}$"
		)
		dt_str: str = (
			f"${_fmt_es(float(row['delta_T_ms']), 2)} \\pm "
			f"{_fmt_es(float(row['sigma_delta_T_ms']), 2)}$"
		)
		z_str: str = _fmt_es(float(row["z_score"]), 1, math_mode=False)
		borda_str: str = f"${_fmt_es(float(row['delta_T_borda_ms']), 2)}$"
		row_tex: str = (
			f"{toma_str} & {theta_str} & {t_str} & {dt_str} & "
			f"{z_str} & {borda_str} \\\\"
		)
		lines.append(row_tex)

	lines.extend(
		[
			r"\bottomrule",
			r"\end{tabular}",
			r"\end{table}",
			"",
		]
	)
	return "\n".join(lines)


def run_pendulum_analysis(
	csv_path: Path | str,
	excluded_videos: frozenset[str] = EXCLUDED_VIDEOS,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], str]:
	"""Run complete pendulum analysis pipeline on trajectories CSV."""
	df_active: pd.DataFrame = load_active_trajectories(
		csv_path=csv_path, excluded_videos=excluded_videos
	)
	measured_pivot: PivotCalibration = build_measured_pivot(df_active=df_active)
	fitted_pivot: PivotCalibration = compute_pivot_calibration(df_active=df_active)

	video_names: list[str] = sorted(str(v) for v in df_active["video_name"].unique())
	undamped_results: list[UndampedFitResult] = []
	decay_results: list[AmplitudeDecayResult] = []

	for video_name in video_names:
		df_video: pd.DataFrame = df_active[df_active["video_name"] == video_name]
		df_angular: pd.DataFrame = compute_angular_series(
			df_video=df_video, pivot=measured_pivot
		)
		undamped: UndampedFitResult = fit_undamped_oscillation(
			video_name=video_name, df_angular=df_angular
		)
		decay: AmplitudeDecayResult = compute_amplitude_decay(
			video_name=video_name, df_angular=df_angular
		)
		undamped_results.append(undamped)
		decay_results.append(decay)

	summary_df: pd.DataFrame
	decay_df: pd.DataFrame
	diagnostics: dict[str, Any]
	summary_df, decay_df, diagnostics = build_summary_and_diagnostics(
		undamped_results=undamped_results,
		decay_results=decay_results,
		measured_pivot=measured_pivot,
		fitted_pivot=fitted_pivot,
	)
	latex_table: str = format_summary_latex_table(summary_df)
	return summary_df, decay_df, diagnostics, latex_table
