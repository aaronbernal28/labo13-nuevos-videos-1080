from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from labo13.io import build_trajectories_dataframe, export_trajectories_csv


if TYPE_CHECKING:
	from snakemake.script import Snakemake

	snakemake: Snakemake


def main() -> None:
	txt_paths: list[Path] = [Path(p) for p in snakemake.input.frame_txts]
	output_csv: Path = Path(snakemake.output.trajectories_csv)

	df_traj: pd.DataFrame = build_trajectories_dataframe(txt_paths=txt_paths)
	export_trajectories_csv(df_traj=df_traj, output_csv=output_csv)


if __name__ == "__main__":
	main()
