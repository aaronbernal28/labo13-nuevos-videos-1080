import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from labo13.pendulum_analysis import run_pendulum_analysis


if TYPE_CHECKING:
	from snakemake.script import Snakemake

	snakemake: Snakemake


def main() -> None:
	trajectories_csv: Path = Path(snakemake.input.trajectories_csv)
	summary_csv: Path = Path(snakemake.output.summary_csv)
	decay_csv: Path = Path(snakemake.output.decay_csv)
	diagnostics_json: Path = Path(snakemake.output.diagnostics_json)
	summary_tex: Path = Path(snakemake.output.summary_tex)
	log_path: Path = Path(snakemake.log[0])

	summary_df: pd.DataFrame
	decay_df: pd.DataFrame
	diagnostics: dict[str, Any]
	latex_table: str
	summary_df, decay_df, diagnostics, latex_table = run_pendulum_analysis(
		csv_path=trajectories_csv
	)

	for out_path in (summary_csv, decay_csv, diagnostics_json, summary_tex, log_path):
		out_path.parent.mkdir(parents=True, exist_ok=True)

	summary_df.to_csv(summary_csv, index=False)
	decay_df.to_csv(decay_csv, index=False)
	diagnostics_json.write_text(
		json.dumps(diagnostics, indent=2, ensure_ascii=False) + "\n",
		encoding="utf-8",
	)
	summary_tex.write_text(latex_table, encoding="utf-8")

	ref: dict[str, Any] = diagnostics["reference_period"]
	pivot: dict[str, Any] = diagnostics["measured_pivot"]
	length_cmp: dict[str, Any] = diagnostics["length_comparison"]
	log_lines: list[str] = [
		f"Analyzed {len(summary_df)} active takes from {trajectories_csv}",
		f"Measured pivot: xc={pivot['xc_px']:.1f} px, yc={pivot['yc_px']:.1f} px, "
		f"R_mean={pivot['r_px']:.2f} px",
		f"T0 (Borda limit from {ref['toma_ref']}): "
		f"{ref['T0_borda_lim_s']:.5f} +/- {ref['sigma_T0_s']:.5f} s",
		f"T0_teo (L={length_cmp['largo_m'] * 100:.1f} cm): "
		f"{length_cmp['T0_teo_s']:.5f} +/- {length_cmp['sigma_T0_teo_s']:.5f} s "
		f"(z={length_cmp['z_teo_exp']:.2f})",
	]
	log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
	main()
