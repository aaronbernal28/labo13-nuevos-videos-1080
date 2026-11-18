from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt
import pandas as pd

from labo13.io import build_trajectories_dataframe, parse_stem_metadata
from labo13.video import load_image_gray, plot_trajectory_on_frame


if TYPE_CHECKING:
	from snakemake.script import Snakemake

	snakemake: Snakemake


def main() -> None:
	txt_paths: list[Path] = sorted(
		(Path(p) for p in snakemake.input.frame_txts),
		key=lambda p: parse_stem_metadata(p.stem)[1],
	)
	if not txt_paths:
		raise ValueError("No per-frame .txt files provided to plot_trajectory")

	output_png: Path = Path(snakemake.output.plot_png)
	video_name: str = str(snakemake.wildcards.video)

	initial_png_path: Path = txt_paths[0].with_suffix(".png")
	initial_frame_gray: npt.NDArray[np.uint8] = load_image_gray(initial_png_path)
	df_video: pd.DataFrame = build_trajectories_dataframe(txt_paths=txt_paths)
	df_video["frame_index"] = [parse_stem_metadata(p.stem)[1] for p in txt_paths]

	plot_trajectory_on_frame(
		initial_frame_gray=initial_frame_gray,
		df_video=df_video,
		output_path=output_png,
		video_name=video_name,
	)


if __name__ == "__main__":
	main()
