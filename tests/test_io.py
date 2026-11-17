from pathlib import Path

import pandas as pd

from labo13.io import (
	build_trajectories_dataframe,
	export_trajectories_csv,
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
	txt_nan: Path = tmp_path / "IMG_1556_f000003_t0.0500.txt"
	save_frame_detection_row("IMG_1556", 0.0334, 815.6, 504.2, txt_b)
	save_frame_detection_row("IMG_1556", 0.0167, 812.4, 503.1, txt_a)
	save_frame_detection_row("IMG_1556", 0.0500, float("nan"), float("nan"), txt_nan)

	assert txt_a.read_text(encoding="utf-8").strip() == "IMG_1556,0.0167,812,503"
	assert txt_b.read_text(encoding="utf-8").strip() == "IMG_1556,0.0334,816,504"
	assert txt_nan.read_text(encoding="utf-8").strip() == "IMG_1556,0.0500,nan,nan"

	row_a: dict[str, str | float] = load_frame_detection_row(txt_a)
	assert row_a["video_name"] == "IMG_1556"
	assert int(row_a["x"]) == 812

	df_traj: pd.DataFrame = build_trajectories_dataframe([txt_b, txt_a, txt_nan])
	assert list(df_traj.columns) == ["video_name", "t", "x", "y"]
	assert list(df_traj["t"]) == [0.0167, 0.0334, 0.05]

	csv_out: Path = tmp_path / "trajectories.csv"
	export_trajectories_csv(df_traj, csv_out)
	lines: list[str] = csv_out.read_text(encoding="utf-8").strip().splitlines()
	assert lines == [
		"video_name,t,x,y",
		"IMG_1556,0.0167,812,503",
		"IMG_1556,0.0334,816,504",
		"IMG_1556,0.0500,nan,nan",
	]
