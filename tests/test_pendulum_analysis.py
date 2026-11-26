import numpy as np
import numpy.typing as npt
import pandas as pd

from labo13.pendulum_analysis import (
	AmplitudeDecayResult,
	PivotCalibration,
	UndampedFitResult,
	build_summary_and_diagnostics,
	compute_amplitude_decay,
	compute_angular_series,
	compute_borda_period,
	compute_pivot_calibration,
	evaluate_undamped_model,
	fit_undamped_oscillation,
	format_summary_latex_table,
)


def test_compute_pivot_calibration_synthetic_arc() -> None:
	xc_true: float = 1960.0
	yc_true: float = 37.0
	r_true: float = 1985.0
	angles: npt.NDArray[np.float64] = np.linspace(-0.8, 0.8, 200)
	x_vals: npt.NDArray[np.float64] = xc_true + r_true * np.sin(angles)
	y_vals: npt.NDArray[np.float64] = yc_true + r_true * np.cos(angles)

	df_cal: pd.DataFrame = pd.DataFrame(
		{
			"video_name": ["IMG_1555"] * len(angles),
			"t": np.linspace(0.0, 10.0, len(angles)),
			"x": x_vals,
			"y": y_vals,
		}
	)

	pivot: PivotCalibration = compute_pivot_calibration(
		df_active=df_cal,
		calibration_videos=("IMG_1555",),
	)
	assert abs(pivot.xc_px - xc_true) < 1e-6
	assert abs(pivot.yc_px - yc_true) < 1e-6
	assert abs(pivot.r_px - r_true) < 1e-6
	assert pivot.rms_radial_px < 1e-6
	assert pivot.n_points == 200


def test_compute_angular_series_and_double_fit() -> None:
	pivot: PivotCalibration = PivotCalibration(
		xc_px=1960.0,
		yc_px=37.0,
		r_px=1985.0,
		rms_radial_px=0.0,
		n_points=100,
	)
	t_arr: npt.NDArray[np.float64] = np.arange(0.0, 20.0, 1.0 / 60.0)
	t_true_s: float = 2.08
	omega_true: float = 2.0 * float(np.pi) / t_true_s
	theta0_true: float = float(np.radians(15.0))
	phi_true: float = 0.4
	offset_true: float = float(np.radians(0.2))

	theta_true: npt.NDArray[np.float64] = evaluate_undamped_model(
		t_arr, theta0_true, omega_true, phi_true, offset_true
	)
	rng: np.random.Generator = np.random.default_rng(42)
	x_vals: npt.NDArray[np.float64] = (
		pivot.xc_px
		+ pivot.r_px * np.sin(theta_true)
		+ rng.normal(0.0, 0.5, size=len(t_arr))
	)
	y_vals: npt.NDArray[np.float64] = (
		pivot.yc_px
		+ pivot.r_px * np.cos(theta_true)
		+ rng.normal(0.0, 0.5, size=len(t_arr))
	)
	df_video: pd.DataFrame = pd.DataFrame(
		{"video_name": "SYNTH_UNDAMPED", "t": t_arr + 2.0, "x": x_vals, "y": y_vals}
	)

	df_ang: pd.DataFrame = compute_angular_series(df_video=df_video, pivot=pivot)
	assert "theta_rad" in df_ang.columns
	assert abs(float(df_ang["tau"].iloc[0])) < 1e-12

	fit: UndampedFitResult = fit_undamped_oscillation(
		video_name="SYNTH_UNDAMPED", df_angular=df_ang
	)
	assert abs(fit.theta0_deg - 15.0) < 0.05
	assert abs(fit.T_s - t_true_s) < 5e-4
	assert fit.dof == len(t_arr) - 4
	assert fit.s_res_deg < 0.05
	assert fit.sigma_T_s > 0.0


def test_compute_amplitude_decay_model_free() -> None:
	tau: npt.NDArray[np.float64] = np.arange(0.0, 20.0, 1.0 / 60.0)
	omega_true: float = 2.0 * float(np.pi) / 2.08
	gamma_true: float = 0.005
	theta_deg: npt.NDArray[np.float64] = (
		20.0 * np.exp(-gamma_true * tau) * np.cos(omega_true * tau)
	)
	df_ang: pd.DataFrame = pd.DataFrame(
		{"t": tau + 1.0, "tau": tau, "theta_deg": theta_deg}
	)

	decay: AmplitudeDecayResult = compute_amplitude_decay(
		video_name="SYNTH_DECAY", df_angular=df_ang
	)
	assert decay.n_cycles >= 8
	assert decay.amp_init_deg > decay.amp_final_deg
	assert 7.0 < decay.amp_drop_pct < 11.0


def test_borda_limit_toma_indexing_and_anexo_latex() -> None:
	t0_true: float = 2.07235
	theta_small_deg: float = 2.0
	theta_large_deg: float = 30.0
	t_small: float = compute_borda_period(t0_true, float(np.radians(theta_small_deg)))
	t_large: float = compute_borda_period(t0_true, float(np.radians(theta_large_deg)))

	u_small: UndampedFitResult = UndampedFitResult(
		video_name="IMG_1568",
		n_frames=800,
		duracion_s=13.5,
		theta0_rad=float(np.radians(theta_small_deg)),
		sigma_theta0_rad=1e-5,
		theta0_deg=theta_small_deg,
		sigma_theta0_deg=0.001,
		omega_rad_s=2.0 * float(np.pi) / t_small,
		sigma_omega_rad_s=1e-4,
		T_s=t_small,
		sigma_T_s=6e-5,
		phi_rad=0.0,
		offset_deg=0.0,
		s_res_deg=0.01,
		rms_res_deg=0.01,
		dof=796,
	)
	u_large: UndampedFitResult = UndampedFitResult(
		video_name="IMG_1555",
		n_frames=1200,
		duracion_s=20.0,
		theta0_rad=float(np.radians(theta_large_deg)),
		sigma_theta0_rad=1e-4,
		theta0_deg=theta_large_deg,
		sigma_theta0_deg=0.01,
		omega_rad_s=2.0 * float(np.pi) / t_large,
		sigma_omega_rad_s=2e-4,
		T_s=t_large,
		sigma_T_s=1e-4,
		phi_rad=0.0,
		offset_deg=0.0,
		s_res_deg=0.5,
		rms_res_deg=0.5,
		dof=1196,
	)
	d_small: AmplitudeDecayResult = AmplitudeDecayResult(
		video_name="IMG_1568",
		n_frames=800,
		duracion_s=13.5,
		n_cycles=6,
		amp_init_deg=2.02,
		amp_final_deg=1.98,
		amp_drop_pct=1.98,
	)
	pivot: PivotCalibration = PivotCalibration(1960.0, 37.0, 1985.0, 9.5, 4600)

	summary_df: pd.DataFrame
	decay_df: pd.DataFrame
	diagnostics: dict[str, object]
	summary_df, decay_df, diagnostics = build_summary_and_diagnostics(
		undamped_results=[u_small, u_large],
		decay_results=[d_small],
		measured_pivot=pivot,
	)

	assert list(summary_df["toma"]) == ["Toma 1", "Toma 2"]
	assert bool(summary_df.iloc[0]["compatible_3sigma"]) is False
	assert bool(summary_df.iloc[1]["compatible_3sigma"]) is True
	assert abs(float(summary_df.iloc[0]["delta_T_borda_ms"])) < 1e-3
	assert len(decay_df) == 1
	assert "length_comparison" in diagnostics

	tex: str = format_summary_latex_table(summary_df)
	assert r"\toprule" in tex
	assert "Toma 1" in tex
	assert "Toma 2" in tex
	assert "IMG" not in tex
	assert "Comp." not in tex
	assert "2{,}000" in tex
