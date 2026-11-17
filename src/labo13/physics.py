import numpy as np
import numpy.typing as npt
import pandas as pd
from scipy.integrate import solve_ivp
from scipy.optimize import curve_fit
from scipy.stats import chi2

from labo13.types import HarmonicFitResult, PendulumConstants


def _damped_harmonic_model(
	t: npt.NDArray[np.float64],
	amplitude: float,
	gamma: float,
	omega: float,
	phi: float,
	offset: float,
) -> npt.NDArray[np.float64]:
	"""Evaluate damped harmonic angle model A * exp(-gamma * t) * cos(omega * t + phi) + offset."""
	result: npt.NDArray[np.float64] = (
		amplitude * np.exp(-gamma * t) * np.cos(omega * t + phi) + offset
	)
	return result


def _undamped_harmonic_model(
	t: npt.NDArray[np.float64],
	amplitude: float,
	omega: float,
	phi: float,
	offset: float,
) -> npt.NDArray[np.float64]:
	"""Evaluate undamped harmonic angle model A * cos(omega * t + phi) + offset."""
	result: npt.NDArray[np.float64] = amplitude * np.cos(omega * t + phi) + offset
	return result


def compute_polar_trajectory(
	df_xy: pd.DataFrame,
	constants: PendulumConstants,
	d_real_m: float = 0.0450,
	d_px: float = 52.0,
	sigma_d_px: float = 1.0,
	sigma_x_px: float = 0.5,
	sigma_y_px: float = 0.5,
) -> pd.DataFrame:
	"""Convert Cartesian pixel coordinates (x, y) to polar angle theta(t) with uncertainties."""
	df_polar: pd.DataFrame = df_xy.dropna(subset=["t", "x", "y"]).copy()

	k_m_px: float = d_real_m / d_px
	sigma_k: float = k_m_px * float(
		np.sqrt((constants.sigma_caliper_m / d_real_m) ** 2 + (sigma_d_px / d_px) ** 2)
	)

	x0_px: float = 0.5 * float(df_polar["x"].max() + df_polar["x"].min())
	y0_px: float = float(df_polar["y"].max())

	dx_px: pd.Series = df_polar["x"] - x0_px
	dy_px: pd.Series = y0_px - df_polar["y"]

	length_eff_m: float = constants.length_cm_m
	x_m: pd.Series = dx_px * k_m_px
	y_m: pd.Series = length_eff_m - (dy_px * k_m_px)
	r_m: pd.Series = np.sqrt(x_m**2 + y_m**2)

	df_polar["X_m"] = x_m
	df_polar["Y_m"] = y_m
	df_polar["R_m"] = r_m
	df_polar["theta_rad"] = np.arctan2(x_m, y_m)
	df_polar["theta_deg"] = np.degrees(df_polar["theta_rad"])

	sigma_x_stat: float = k_m_px * sigma_x_px
	sigma_y_stat: float = k_m_px * sigma_y_px
	dtheta_dx: pd.Series = y_m / (r_m**2)
	dtheta_dy: pd.Series = -x_m / (r_m**2)

	df_polar["sigma_theta_stat_rad"] = np.sqrt(
		(dtheta_dx * sigma_x_stat) ** 2 + (dtheta_dy * sigma_y_stat) ** 2
	)

	sigma_x_tot: pd.Series = np.sqrt(sigma_x_stat**2 + (dx_px * sigma_k) ** 2)
	sigma_y_tot: pd.Series = np.sqrt(
		sigma_y_stat**2 + (dy_px * sigma_k) ** 2 + constants.sigma_length_m**2
	)
	df_polar["sigma_theta_total_rad"] = np.sqrt(
		(dtheta_dx * sigma_x_tot) ** 2 + (dtheta_dy * sigma_y_tot) ** 2
	)
	df_polar["sigma_t"] = constants.sigma_frame_s
	return df_polar


def compute_harmonic_fit(
	df_polar: pd.DataFrame,
	constants: PendulumConstants,
	video_name: str = "Experiment",
	damped: bool = True,
) -> HarmonicFitResult:
	"""Perform 2-stage weighted harmonic curve_fit with shutter time-variance propagation."""
	df_fit: pd.DataFrame = df_polar.dropna(
		subset=["t", "theta_rad", "sigma_theta_stat_rad"]
	).copy()
	t_data: npt.NDArray[np.float64] = df_fit["t"].to_numpy(dtype=np.float64)
	y_data: npt.NDArray[np.float64] = df_fit["theta_rad"].to_numpy(dtype=np.float64)
	y_err_stat: npt.NDArray[np.float64] = df_fit["sigma_theta_stat_rad"].to_numpy(dtype=np.float64)

	amp_init: float = 0.5 * float(y_data.max() - y_data.min())
	omega_init: float = float(np.sqrt(9.8 / constants.length_cm_m))
	phi_init: float = 0.0 if float(y_data[0]) > float(np.mean(y_data)) else float(np.pi)
	offset_init: float = float(np.mean(y_data))
	sigma_t_ef: float = 0.25 * constants.sigma_frame_s

	if damped:
		p0_damped: list[float] = [amp_init, 0.003, omega_init, phi_init, offset_init]
		popt_1, _ = curve_fit(
			_damped_harmonic_model,
			t_data,
			y_data,
			p0=p0_damped,
			sigma=y_err_stat,
			absolute_sigma=True,
			maxfev=10000,
		)
		a1, g1, w1, p1, _ = [float(v) for v in popt_1]
		dtheta_dt: npt.NDArray[np.float64] = (
			-a1 * np.exp(-g1 * t_data) * w1 * np.sin(w1 * t_data + p1)
		)
		y_err_ef: npt.NDArray[np.float64] = np.sqrt(y_err_stat**2 + (dtheta_dt * sigma_t_ef) ** 2)
		popt, pcov = curve_fit(
			_damped_harmonic_model,
			t_data,
			y_data,
			p0=popt_1,
			sigma=y_err_ef,
			absolute_sigma=True,
			maxfev=10000,
		)
		perr: npt.NDArray[np.float64] = np.sqrt(np.diag(pcov))
		amp_fit, gamma_fit, omega_fit, phi_fit, offset_fit = [float(v) for v in popt]
		s_amp, s_gamma, s_omega, s_phi, s_offset = [float(v) for v in perr]
		y_pred: npt.NDArray[np.float64] = _damped_harmonic_model(
			t_data, amp_fit, gamma_fit, omega_fit, phi_fit, offset_fit
		)
		n_params: int = 5
	else:
		p0_undamped: list[float] = [amp_init, omega_init, phi_init, offset_init]
		popt_1, _ = curve_fit(
			_undamped_harmonic_model,
			t_data,
			y_data,
			p0=p0_undamped,
			sigma=y_err_stat,
			absolute_sigma=True,
			maxfev=10000,
		)
		a1, w1, p1, _ = [float(v) for v in popt_1]
		dtheta_dt = -a1 * w1 * np.sin(w1 * t_data + p1)
		y_err_ef = np.sqrt(y_err_stat**2 + (dtheta_dt * sigma_t_ef) ** 2)
		popt, pcov = curve_fit(
			_undamped_harmonic_model,
			t_data,
			y_data,
			p0=popt_1,
			sigma=y_err_ef,
			absolute_sigma=True,
			maxfev=10000,
		)
		perr = np.sqrt(np.diag(pcov))
		amp_fit, omega_fit, phi_fit, offset_fit = [float(v) for v in popt]
		s_amp, s_omega, s_phi, s_offset = [float(v) for v in perr]
		gamma_fit, s_gamma = 0.0, 0.0
		y_pred = _undamped_harmonic_model(t_data, amp_fit, omega_fit, phi_fit, offset_fit)
		n_params = 4

	if amp_fit < 0.0:
		amp_fit = -amp_fit
		phi_fit = float((phi_fit + np.pi) % (2.0 * np.pi))
	omega_fit = abs(omega_fit)

	omega0: float = float(np.sqrt(omega_fit**2 + gamma_fit**2))
	sigma_omega0: float = (
		float(np.sqrt((omega_fit * s_omega) ** 2 + (gamma_fit * s_gamma) ** 2)) / omega0
	)
	period_s: float = (2.0 * float(np.pi)) / omega_fit
	sigma_period_s: float = ((2.0 * float(np.pi)) / (omega_fit**2)) * s_omega

	residuals: npt.NDArray[np.float64] = y_data - y_pred
	chi2_val: float = float(np.sum((residuals / y_err_ef) ** 2))
	dof: int = int(len(y_data) - n_params)
	chi2_red: float = chi2_val / float(dof)
	p_val: float = float(1.0 - chi2.cdf(chi2_val, dof))

	length_cm: float = constants.length_cm_m
	g_cm: float = length_cm * (omega0**2)
	sigma_g_cm: float = g_cm * float(
		np.sqrt((constants.sigma_length_m / length_cm) ** 2 + (2.0 * sigma_omega0 / omega0) ** 2)
	)

	return HarmonicFitResult(
		video_name=video_name,
		damped=damped,
		amplitude_rad=amp_fit,
		sigma_amplitude_rad=s_amp,
		gamma_s_inv=gamma_fit,
		sigma_gamma_s_inv=s_gamma,
		omega_rad_s=omega_fit,
		sigma_omega_rad_s=s_omega,
		phi_rad=phi_fit,
		sigma_phi_rad=s_phi,
		offset_rad=offset_fit,
		sigma_offset_rad=s_offset,
		omega0_rad_s=omega0,
		sigma_omega0_rad_s=sigma_omega0,
		period_s=period_s,
		sigma_period_s=sigma_period_s,
		chi2=chi2_val,
		dof=dof,
		chi2_reduced=chi2_red,
		p_value=p_val,
		g_cm_m_s2=g_cm,
		sigma_g_cm_m_s2=sigma_g_cm,
	)


def compute_sliding_window_periods(
	df_polar: pd.DataFrame,
	constants: PendulumConstants,
	video_name: str,
	window_sec: float = 6.0,
	step_sec: float = 2.0,
) -> pd.DataFrame:
	"""Evaluate local period T(theta_0) across sliding time windows of a decaying oscillation."""
	df_clean: pd.DataFrame = df_polar.dropna(
		subset=["t", "theta_rad", "sigma_theta_stat_rad"]
	).copy()
	t_min: float = float(df_clean["t"].min())
	t_max: float = float(df_clean["t"].max())

	rows: list[dict[str, str | float]] = []
	t_start: float = t_min
	while t_start + window_sec <= t_max:
		sub_df: pd.DataFrame = df_clean[
			(df_clean["t"] >= t_start) & (df_clean["t"] <= t_start + window_sec)
		]
		if len(sub_df) >= 15:
			try:
				fit_res: HarmonicFitResult = compute_harmonic_fit(
					df_polar=sub_df,
					constants=constants,
					video_name=f"{video_name}_w",
					damped=False,
				)
				if fit_res.sigma_period_s < 0.02:
					rows.append(
						{
							"video_name": video_name,
							"t_mid_s": t_start + 0.5 * window_sec,
							"theta_max_deg": float(np.degrees(fit_res.amplitude_rad)),
							"theta_max_rad": fit_res.amplitude_rad,
							"period_s": fit_res.period_s,
							"sigma_period_s": fit_res.sigma_period_s,
							"omega_rad_s": fit_res.omega_rad_s,
							"sigma_omega_rad_s": fit_res.sigma_omega_rad_s,
						}
					)
			except Exception:
				pass
		t_start += step_sec

	return pd.DataFrame(rows)


def compute_ode_trajectory(
	t: npt.ArrayLike,
	omega0: float,
	parameters: tuple[float, float, float, float],
	model: str = "seno",
) -> npt.NDArray[np.float64]:
	"""Integrate linear ('lineal') or nonlinear ('seno') damped pendulum ODE starting at t=0."""
	theta_i, v_i, gamma, offset = parameters
	t_arr: npt.NDArray[np.float64] = np.asarray(t, dtype=np.float64)
	if model not in ("lineal", "seno"):
		raise ValueError(f"Unknown pendulum model: {model!r}")

	def rhs(_t_val: float, state: list[float]) -> tuple[float, float]:
		theta_val: float = state[0]
		v_val: float = state[1]
		restoring: float = theta_val if model == "lineal" else float(np.sin(theta_val))
		return (v_val, -2.0 * gamma * v_val - (omega0**2) * restoring)

	sol = solve_ivp(
		rhs,
		(0.0, float(t_arr[-1])),
		[theta_i, v_i],
		t_eval=t_arr,
		method="DOP853",
		rtol=2e-9,
		atol=2e-11,
	)
	if not sol.success or sol.y.shape[1] != len(t_arr):
		raise RuntimeError(f"ODE integration failed: {sol.message}")
	trajectory: npt.NDArray[np.float64] = np.asarray(sol.y[0], dtype=np.float64) + offset
	return trajectory
