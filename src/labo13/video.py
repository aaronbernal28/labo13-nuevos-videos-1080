from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

import av
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
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


def save_image_gray(
	frame_gray: npt.NDArray[np.uint8],
	output_path: Path,
	compress_level: int = 1,
) -> None:
	"""Save a 2D uint8 greyscale array as a lossless PNG."""
	output_path.parent.mkdir(parents=True, exist_ok=True)
	Image.fromarray(frame_gray, mode="L").save(
		output_path, format="PNG", compress_level=compress_level
	)


def save_frame_batch_gray(
	batch: list[tuple[npt.NDArray[np.uint8], Path]],
	max_workers: int = 4,
	compress_level: int = 1,
) -> None:
	"""Flush a batch of greyscale frames to disk in parallel."""
	if not batch:
		return
	if max_workers <= 1 or len(batch) == 1:
		for frame_gray, output_path in batch:
			save_image_gray(
				frame_gray=frame_gray,
				output_path=output_path,
				compress_level=compress_level,
			)
		return

	with ThreadPoolExecutor(max_workers=max_workers) as executor:
		futures: list[Future[None]] = [
			executor.submit(
				save_image_gray,
				frame_gray,
				output_path,
				compress_level,
			)
			for frame_gray, output_path in batch
		]
		for future in futures:
			future.result()


def load_video_frame_gray(
	video_path: Path, frame_index: int = 0
) -> npt.NDArray[np.uint8]:
	"""Decode a single frame by index from video_path as a 2D uint8 greyscale array."""
	with av.open(str(video_path)) as container:
		for idx, frame in enumerate(container.decode(video=0)):
			if idx == frame_index:
				arr: npt.NDArray[np.uint8] = np.asarray(
					frame.to_ndarray(format="gray"), dtype=np.uint8
				)
				return arr
	raise IndexError(f"Frame index {frame_index} out of range for video {video_path}")


def plot_sampled_frames(video_path: Path, frame_indices: list[int]) -> Figure:
	"""Render a vertical stack of sampled greyscale frames from a video."""
	n_panels: int = len(frame_indices)
	fig, axes = plt.subplots(n_panels, 1, figsize=(10, 4 * max(1, n_panels)))
	axes_list: list[Axes] = [axes] if n_panels == 1 else list(axes)

	for ax, sample_idx in zip(axes_list, frame_indices, strict=True):
		frame_gray: npt.NDArray[np.uint8] = load_video_frame_gray(
			video_path, sample_idx
		)
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
	target_fps: int = 60,
	batch_size: int = 64,
	max_workers: int = 4,
	compress_level: int = 1,
) -> list[FrameRecord]:
	"""Decode video to greyscale PNG frames within [t_start, t_end) in batches."""
	if t_start is not None and t_end is not None and t_start >= t_end:
		raise ValueError(
			f"Invalid trim bounds for {video_name}: t_start={t_start} >= t_end={t_end}"
		)
	if not (1 <= target_fps <= 60):
		raise ValueError(f"target_fps must be in [1, 60], got {target_fps}")
	if batch_size < 1:
		raise ValueError(f"batch_size must be >= 1, got {batch_size}")

	frame_step: int = max(1, round(60.0 / float(target_fps)))
	output_dir.mkdir(parents=True, exist_ok=True)
	records: list[FrameRecord] = []
	pending_batch: list[tuple[npt.NDArray[np.uint8], Path]] = []

	with av.open(str(video_path)) as container:
		stream = container.streams.video[0]
		fps: float = (
			float(stream.average_rate) if stream.average_rate is not None else 59.96
		)

		for idx, frame in enumerate(container.decode(video=0)):
			t_sec: float = (
				float(frame.time) if frame.time is not None else float(idx) / fps
			)
			if t_end is not None and t_sec >= float(t_end):
				break
			if not is_within_time_bounds(t_sec=t_sec, t_start=t_start, t_end=t_end):
				continue
			if idx % frame_step != 0:
				continue

			frame_gray: npt.NDArray[np.uint8] = np.asarray(
				frame.to_ndarray(format="gray"), dtype=np.uint8
			)
			stem: str = format_frame_stem(
				video_name=video_name, frame_index=idx, t_sec=t_sec
			)
			png_path: Path = output_dir / f"{stem}.png"
			pending_batch.append((frame_gray, png_path))
			records.append(
				FrameRecord(
					video_name=video_name,
					frame_index=idx,
					t_sec=t_sec,
					stem=stem,
					png_path=png_path,
				)
			)
			if len(pending_batch) >= batch_size:
				save_frame_batch_gray(
					batch=pending_batch,
					max_workers=max_workers,
					compress_level=compress_level,
				)
				pending_batch.clear()

	if pending_batch:
		save_frame_batch_gray(
			batch=pending_batch,
			max_workers=max_workers,
			compress_level=compress_level,
		)
		pending_batch.clear()

	return records


def plot_trajectory_on_frame(
	initial_frame_gray: npt.NDArray[np.uint8],
	df_video: pd.DataFrame,
	output_path: Path,
	video_name: str = "",
) -> Figure:
	"""Plot detected (x, y) trajectory points over the video's initial frame."""
	output_path.parent.mkdir(parents=True, exist_ok=True)
	df_valid: pd.DataFrame = df_video.dropna(subset=["x", "y"])

	fig, ax = plt.subplots(figsize=(12, 7))
	ax.imshow(initial_frame_gray, cmap="gray")
	ax.scatter(
		df_valid["x"].to_numpy(dtype=np.float64),
		df_valid["y"].to_numpy(dtype=np.float64),
		color="C1",
		s=5,
	)
	if video_name:
		ax.set_title(
			f"{video_name} — Trajectory ({len(df_valid)}/{len(df_video)} frames)"
		)
	ax.axis("off")
	fig.tight_layout()
	fig.savefig(output_path, dpi=150, bbox_inches="tight")
	plt.close(fig)
	return fig
