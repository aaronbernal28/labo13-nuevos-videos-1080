import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from labo13.analysis_plots import (
	plot_frame_processing_steps,
	plot_period_vs_amplitude,
	plot_representative_fit,
)
from labo13.pendulum_analysis import (
	PivotCalibration,
	UndampedFitResult,
	build_measured_pivot,
	compute_angular_series,
	fit_undamped_oscillation,
	load_active_trajectories,
)


if TYPE_CHECKING:
	from snakemake.script import Snakemake

	snakemake: Snakemake


def main() -> None:
	trajectories_csv: Path = Path(snakemake.input.trajectories_csv)
	summary_csv: Path = Path(snakemake.input.summary_csv)
	diagnostics_json: Path = Path(snakemake.input.diagnostics_json)
	sample_frame_png: Path = Path(snakemake.input.sample_frame_png)
	background_png: Path = Path(snakemake.input.background_png)

	fig_proc: Path = Path(snakemake.output.fig_procesamiento)
	fig_small: Path = Path(snakemake.output.fig_theta_pequena)
	fig_large: Path = Path(snakemake.output.fig_theta_grande)
	fig_period: Path = Path(snakemake.output.fig_periodo_vs_amplitud)
	log_path: Path = Path(snakemake.log[0])

	summary_df: pd.DataFrame = pd.read_csv(summary_csv)
	diagnostics: dict[str, Any] = json.loads(
		diagnostics_json.read_text(encoding="utf-8")
	)

	cx: float
	cy: float
	cx, cy = plot_frame_processing_steps(
		frame_path=sample_frame_png,
		background_path=background_png,
		output_path=fig_proc,
	)

	df_active: pd.DataFrame = load_active_trajectories(csv_path=trajectories_csv)
	pivot: PivotCalibration = build_measured_pivot(df_active=df_active)

	small_video: str = str(summary_df.iloc[-1]["video_name"])
	large_video: str = str(summary_df.iloc[0]["video_name"])

	df_ang_small: pd.DataFrame = compute_angular_series(
		df_video=df_active[df_active["video_name"] == small_video],
		pivot=pivot,
	)
	fit_small: UndampedFitResult = fit_undamped_oscillation(
		video_name=small_video, df_angular=df_ang_small
	)
	plot_representative_fit(
		df_angular=df_ang_small, fit=fit_small, output_path=fig_small
	)

	df_ang_large: pd.DataFrame = compute_angular_series(
		df_video=df_active[df_active["video_name"] == large_video],
		pivot=pivot,
	)
	fit_large: UndampedFitResult = fit_undamped_oscillation(
		video_name=large_video, df_angular=df_ang_large
	)
	plot_representative_fit(
		df_angular=df_ang_large, fit=fit_large, output_path=fig_large
	)

	t0_exp_s: float = float(diagnostics["reference_period"]["T0_borda_lim_s"])
	t0_teo_s: float = float(diagnostics["length_comparison"]["T0_teo_s"])
	sigma_t0_teo_s: float = float(diagnostics["length_comparison"]["sigma_T0_teo_s"])
	plot_period_vs_amplitude(
		summary_df=summary_df,
		t0_exp_s=t0_exp_s,
		t0_teo_s=t0_teo_s,
		sigma_t0_teo_s=sigma_t0_teo_s,
		output_path=fig_period,
	)

	log_path.parent.mkdir(parents=True, exist_ok=True)
	log_path.write_text(
		f"Generated 4 report figures.\n"
		f"Sample frame centroid ({sample_frame_png.name}): ({cx:.0f}, {cy:.0f}) px\n"
		f"Small take: {small_video} -> {fig_small}\n"
		f"Large take: {large_video} -> {fig_large}\n"
		f"Period vs amplitude -> {fig_period}\n",
		encoding="utf-8",
	)


if __name__ == "__main__":
	main()
