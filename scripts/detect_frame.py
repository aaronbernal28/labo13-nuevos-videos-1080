from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt

from labo13.detection import compute_bob_centroid
from labo13.io import parse_stem_metadata, save_frame_detection_row
from labo13.video import load_image_gray


if TYPE_CHECKING:
	from snakemake.script import Snakemake

	snakemake: Snakemake


def main() -> None:
	frame_path: Path = Path(snakemake.input.frame_png)
	background_path: Path = Path(snakemake.input.background_png)
	output_txt: Path = Path(snakemake.output.row_txt)

	threshold_low: float = float(snakemake.params.threshold_low)
	threshold_high: float = float(snakemake.params.threshold_high)
	disk_radius: int = int(snakemake.params.disk_radius)
	roi_y_start: int = int(snakemake.params.roi_y_start)
	roi_y_end: int = int(snakemake.params.roi_y_end)
	roi_x_start: int = int(snakemake.params.roi_x_start)
	roi_x_end: int = int(snakemake.params.roi_x_end)

	video_name: str
	_frame_index: int
	t_sec: float
	video_name, _frame_index, t_sec = parse_stem_metadata(frame_path.stem)

	frame_gray: npt.NDArray[np.uint8] = load_image_gray(frame_path)
	background_gray: npt.NDArray[np.uint8] = load_image_gray(background_path)

	x_px: float
	y_px: float
	x_px, y_px = compute_bob_centroid(
		frame_gray=frame_gray,
		background_gray=background_gray,
		threshold_low=threshold_low,
		threshold_high=threshold_high,
		disk_radius=disk_radius,
		roi_y_start=roi_y_start,
		roi_y_end=roi_y_end,
		roi_x_start=roi_x_start,
		roi_x_end=roi_x_end,
	)

	save_frame_detection_row(
		video_name=video_name,
		t_sec=t_sec,
		x_px=x_px,
		y_px=y_px,
		output_txt=output_txt,
	)


if __name__ == "__main__":
	main()
