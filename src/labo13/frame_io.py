import math
from pathlib import Path

import numpy as np
import numpy.typing as npt
from PIL import Image


def _format_pixel_coord(value: float) -> str:
	"""Format a pixel coordinate as a rounded integer string or 'nan'."""
	if math.isnan(value):
		return "nan"
	return str(int(round(value)))


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
	"""Save a single CSV row 'video_name,t,x,y' (integer pixels, no header) to .txt."""
	output_txt.parent.mkdir(parents=True, exist_ok=True)
	x_str: str = _format_pixel_coord(x_px)
	y_str: str = _format_pixel_coord(y_px)
	line: str = f"{video_name},{t_sec:.4f},{x_str},{y_str}\n"
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


def load_image_gray(image_path: Path) -> npt.NDArray[np.uint8]:
	"""Load an image file from disk as a 2D uint8 greyscale array."""
	with Image.open(image_path) as img:
		if img.mode == "L":
			arr: npt.NDArray[np.uint8] = np.asarray(img, dtype=np.uint8)
			return arr
		gray_img: Image.Image = img.convert("L")
		arr = np.asarray(gray_img, dtype=np.uint8)
	return arr
