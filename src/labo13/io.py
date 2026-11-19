from pathlib import Path

import gdown
import pandas as pd

from labo13.frame_io import (
	_format_pixel_coord,
	load_frame_detection_row,
	parse_stem_metadata,
	save_frame_detection_row,
)
from labo13.types import FrameRecord


__all__: list[str] = [
	"_format_pixel_coord",
	"build_trajectories_dataframe",
	"download_drive_file",
	"export_trajectories_csv",
	"load_frame_detection_row",
	"load_frame_manifest",
	"parse_stem_metadata",
	"save_frame_detection_row",
	"save_frame_manifest",
]


def download_drive_file(url: str, output_path: Path) -> Path:
	"""Download a single file from a Google Drive sharing link to output_path."""
	output_path.parent.mkdir(parents=True, exist_ok=True)
	downloaded: object = gdown.download(
		url=url,
		output=str(output_path),
		quiet=False,
	)
	if downloaded is None or not output_path.exists():
		raise RuntimeError(
			f"Failed to download Google Drive file from {url} to {output_path}"
		)
	return output_path


def save_frame_manifest(records: list[FrameRecord], manifest_path: Path) -> None:
	"""Write frame metadata records to a TSV manifest file."""
	manifest_path.parent.mkdir(parents=True, exist_ok=True)
	rows: list[dict[str, str | int | float]] = [
		{
			"video_name": rec.video_name,
			"frame_index": rec.frame_index,
			"t_sec": f"{rec.t_sec:.4f}",
			"stem": rec.stem,
			"png_path": str(rec.png_path),
		}
		for rec in records
	]
	df_manifest: pd.DataFrame = pd.DataFrame(
		rows, columns=["video_name", "frame_index", "t_sec", "stem", "png_path"]
	)
	df_manifest.to_csv(manifest_path, sep="\t", index=False)


def load_frame_manifest(manifest_path: Path) -> pd.DataFrame:
	"""Read a per-video frame manifest TSV."""
	df_manifest: pd.DataFrame = pd.read_csv(
		manifest_path,
		sep="\t",
		dtype={
			"video_name": str,
			"frame_index": int,
			"t_sec": float,
			"stem": str,
			"png_path": str,
		},
	)
	return df_manifest


def build_trajectories_dataframe(txt_paths: list[Path]) -> pd.DataFrame:
	"""Aggregate per-frame .txt files into a sorted DataFrame (video_name, t, x, y)."""
	records: list[dict[str, str | float]] = [
		load_frame_detection_row(path) for path in txt_paths
	]
	df_traj: pd.DataFrame = pd.DataFrame(records, columns=["video_name", "t", "x", "y"])
	df_sorted: pd.DataFrame = df_traj.sort_values(
		by=["video_name", "t"], ascending=[True, True], kind="mergesort"
	).reset_index(drop=True)
	df_sorted["x"] = df_sorted["x"].round().astype("Int64")
	df_sorted["y"] = df_sorted["y"].round().astype("Int64")
	return df_sorted


def export_trajectories_csv(df_traj: pd.DataFrame, output_csv: Path) -> None:
	"""Write the aggregated trajectories DataFrame to disk with integer pixel coords."""
	output_csv.parent.mkdir(parents=True, exist_ok=True)
	df_traj.to_csv(output_csv, index=False, float_format="%.4f", na_rep="nan")
