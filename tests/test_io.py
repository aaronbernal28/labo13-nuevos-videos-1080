from pathlib import Path

import pandas as pd

from labo13.io import (
	build_trajectories_dataframe,
	load_frame_detection_row,
	parse_stem_metadata,
	save_frame_detection_row,
)


def test_parse_stem_metadata() -> None:
	video_name: str
	frame_index: int
	t_sec: float
	video_name, frame_index, t_sec = parse_stem_metadata("IMG_1556_f000120_t2.0013")
	assert video_name == "IMG_1556"
	assert frame_index == 120
	assert abs(t_sec - 2.0013) < 1e-6


def test_save_and_build_trajectories_dataframe(tmp_path: Path) -> None:
	txt_b: Path = tmp_path / "IMG_1556_f000002_t0.0334.txt"
	txt_a: Path = tmp_path / "IMG_1556_f000001_t0.0167.txt"
	save_frame_detection_row("IMG_1556", 0.0334, 815.0, 504.0, txt_b)
	save_frame_detection_row("IMG_1556", 0.0167, 812.5, 503.0, txt_a)

	row_a: dict[str, str | float] = load_frame_detection_row(txt_a)
	assert row_a["video_name"] == "IMG_1556"
	assert abs(float(row_a["x"]) - 812.5) < 1e-6

	df_traj: pd.DataFrame = build_trajectories_dataframe([txt_b, txt_a])
	assert list(df_traj.columns) == ["video_name", "t", "x", "y"]
	assert list(df_traj["t"]) == [0.0167, 0.0334]
