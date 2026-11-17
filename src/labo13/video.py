from pathlib import Path

import av
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from PIL import Image

from labo13.types import FrameRecord


def is_within_time_bounds(
	t_sec: float,
	t_start: int | None,
	t_end: int | None,
) -> bool:
	"""Return True if t_sec falls within [t_start, t_end) where None means unbounded."""
	if t_start is not None and t_sec < float(t_start):
		return False
	if t_end is not None and t_sec >= float(t_end):
		return False
	return True


def format_frame_stem(video_name: str, frame_index: int, t_sec: float) -> str:
	"""Format illustrative frame stem '{video}_f{index:06d}_t{seconds:.4f}'."""
	stem: str = f"{video_name}_f{frame_index:06d}_t{t_sec:.4f}"
	return stem


def load_image_gray(image_path: Path) -> npt.NDArray[np.uint8]:
	"""Load an image file from disk as a 2D uint8 greyscale array."""
	with Image.open(image_path) as img:
		gray_img: Image.Image = img.convert("L")
		arr: npt.NDArray[np.uint8] = np.asarray(gray_img, dtype=np.uint8)
	return arr


def save_image_gray(frame_gray: npt.NDArray[np.uint8], output_path: Path) -> None:
	"""Save a 2D uint8 greyscale array as a lossless PNG."""
	output_path.parent.mkdir(parents=True, exist_ok=True)
	Image.fromarray(frame_gray, mode="L").save(output_path, format="PNG")


def load_video_frame_gray(video_path: Path, frame_index: int = 0) -> npt.NDArray[np.uint8]:
	"""Decode a single frame by index from video_path as a 2D uint8 greyscale array."""
	with av.open(str(video_path)) as container:
		for idx, frame in enumerate(container.decode(video=0)):
			if idx == frame_index:
				arr: npt.NDArray[np.uint8] = frame.to_ndarray(format="gray")
				return arr
	raise IndexError(f"Frame index {frame_index} out of range for video {video_path}")


def plot_sampled_frames(video_path: Path, frame_indices: list[int]) -> plt.Figure:
	"""Render a vertical stack of sampled greyscale frames from a video."""
	n_panels: int = len(frame_indices)
	fig, axes = plt.subplots(n_panels, 1, figsize=(10, 4 * max(1, n_panels)))
	axes_list: list[plt.Axes] = [axes] if n_panels == 1 else list(axes)

	for ax, sample_idx in zip(axes_list, frame_indices, strict=True):
		frame_gray: npt.NDArray[np.uint8] = load_video_frame_gray(video_path, sample_idx)
		ax.imshow(frame_gray, cmap="gray")
		ax.set_title(f"Frame {sample_idx}")
		ax.axis("off")

	fig.tight_layout()
	return fig


def extract_trimmed_frames_gray(
	video_path: Path,
	video_name: str,
	output_dir: Path,
	t_start: int | None = None,
	t_end: int | None = None,
) -> list[FrameRecord]:
	"""Decode video to greyscale PNG frames within [t_start, t_end) keeping original video time."""
	if t_start is not None and t_end is not None and t_start >= t_end:
		raise ValueError(f"Invalid trim bounds for {video_name}: t_start={t_start} >= t_end={t_end}")

	output_dir.mkdir(parents=True, exist_ok=True)
	records: list[FrameRecord] = []

	with av.open(str(video_path)) as container:
		stream = container.streams.video[0]
		fps: float = float(stream.average_rate) if stream.average_rate is not None else 59.96

		for idx, frame in enumerate(container.decode(video=0)):
			t_sec: float = float(frame.time) if frame.time is not None else float(idx) / fps
			if t_end is not None and t_sec >= float(t_end):
				break
			if not is_within_time_bounds(t_sec=t_sec, t_start=t_start, t_end=t_end):
				continue

			frame_gray: npt.NDArray[np.uint8] = frame.to_ndarray(format="gray")
			stem: str = format_frame_stem(video_name=video_name, frame_index=idx, t_sec=t_sec)
			png_path: Path = output_dir / f"{stem}.png"
			save_image_gray(frame_gray=frame_gray, output_path=png_path)
			records.append(
				FrameRecord(
					video_name=video_name,
					frame_index=idx,
					t_sec=t_sec,
					stem=stem,
					png_path=png_path,
				)
			)

	return records
