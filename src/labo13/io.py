from pathlib import Path

import gdown
import pandas as pd

from labo13.types import FrameRecord


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


def parse_stem_metadata(stem: str) -> tuple[str, int, float]:
	"""Extract (video_name, frame_index, t_sec) from a frame filename stem."""
	prefix_part: str
	t_part: str
	prefix_part, t_part = stem.rsplit("_t", maxsplit=1)
	video_name: str
	idx_part: str
	video_name, idx_part = prefix_part.rsplit("_f", maxsplit=1)
	frame_index: int = int(idx_part)
	t_sec: float = float(t_part)
	return video_name, frame_index, t_sec


def save_frame_detection_row(
	video_name: str,
	t_sec: float,
	x_px: float,
	y_px: float,
	output_txt: Path,
) -> None:
	"""Save a single CSV row 'video_name,t,x,y' (no header) to a per-frame .txt file."""
	output_txt.parent.mkdir(parents=True, exist_ok=True)
	line: str = f"{video_name},{t_sec:.4f},{x_px:.6f},{y_px:.6f}\n"
	output_txt.write_text(line, encoding="utf-8")


def load_frame_detection_row(input_txt: Path) -> dict[str, str | float]:
	"""Parse a single per-frame .txt file into a record dictionary."""
	raw_line: str = input_txt.read_text(encoding="utf-8").strip()
	parts: list[str] = raw_line.split(",")
	if len(parts) != 4:
		raise ValueError(f"Malformed detection row in {input_txt}: {raw_line!r}")
	record: dict[str, str | float] = {
		"video_name": parts[0],
		"t": float(parts[1]),
		"x": float(parts[2]),
		"y": float(parts[3]),
	}
	return record


def build_trajectories_dataframe(txt_paths: list[Path]) -> pd.DataFrame:
	"""Aggregate per-frame .txt files into a sorted DataFrame (video_name, t, x, y)."""
	records: list[dict[str, str | float]] = [
		load_frame_detection_row(path) for path in txt_paths
	]
	df_traj: pd.DataFrame = pd.DataFrame(records, columns=["video_name", "t", "x", "y"])
	df_sorted: pd.DataFrame = df_traj.sort_values(
		by=["video_name", "t"], ascending=[True, True], kind="mergesort"
	).reset_index(drop=True)
	return df_sorted


def export_trajectories_csv(df_traj: pd.DataFrame, output_csv: Path) -> None:
	"""Write the aggregated trajectories DataFrame to disk."""
	output_csv.parent.mkdir(parents=True, exist_ok=True)
	df_traj.to_csv(output_csv, index=False, float_format="%.6f")
