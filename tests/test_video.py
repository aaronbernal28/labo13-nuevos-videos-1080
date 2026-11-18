from pathlib import Path

import av
import numpy as np
import numpy.typing as npt
import pandas as pd
import pytest

from labo13.types import FrameRecord
from labo13.video import (
	extract_trimmed_frames_gray,
	format_frame_stem,
	is_within_time_bounds,
	load_image_gray,
	plot_trajectory_on_frame,
	save_frame_batch_gray,
)


def test_is_within_time_bounds() -> None:
	assert is_within_time_bounds(5.0, None, None) is True
	assert is_within_time_bounds(1.99, 2, 10) is False
	assert is_within_time_bounds(2.0, 2, 10) is True
	assert is_within_time_bounds(10.0, 2, 10) is False


def test_format_frame_stem() -> None:
	stem: str = format_frame_stem("IMG_1555", 42, 0.7005)
	assert stem == "IMG_1555_f000042_t0.7005"


def test_save_frame_batch_gray_round_trip(tmp_path: Path) -> None:
	frames: list[tuple[npt.NDArray[np.uint8], Path]] = []
	for idx in range(5):
		arr: npt.NDArray[np.uint8] = np.full((16, 20), idx * 40, dtype=np.uint8)
		frames.append((arr, tmp_path / f"frame_{idx}.png"))

	save_frame_batch_gray(batch=frames, max_workers=2, compress_level=1)

	for idx, (expected, png_path) in enumerate(frames):
		assert png_path.exists(), f"Missing frame {idx}"
		loaded: npt.NDArray[np.uint8] = load_image_gray(png_path)
		assert np.array_equal(loaded, expected)


def test_extract_trimmed_frames_gray_batched(tmp_path: Path) -> None:
	video_path: Path = tmp_path / "synthetic.MOV"
	with av.open(str(video_path), mode="w") as container:
		stream = container.add_stream("mpeg4", rate=10)
		stream.width = 32
		stream.height = 24
		stream.pix_fmt = "yuv420p"
		for idx in range(5):
			gray: npt.NDArray[np.uint8] = np.full((24, 32), idx * 40, dtype=np.uint8)
			rgb: npt.NDArray[np.uint8] = np.stack([gray, gray, gray], axis=-1)
			vframe = av.VideoFrame.from_ndarray(rgb, format="rgb24")
			for packet in stream.encode(vframe):
				container.mux(packet)
		for packet in stream.encode():
			container.mux(packet)

	out_dir: Path = tmp_path / "frames"
	records: list[FrameRecord] = extract_trimmed_frames_gray(
		video_path=video_path,
		video_name="SYNTH",
		output_dir=out_dir,
		t_start=None,
		t_end=None,
		batch_size=2,
		max_workers=2,
		compress_level=1,
	)
	assert len(records) == 5
	for rec in records:
		assert rec.png_path.exists()


def test_plot_trajectory_on_frame(tmp_path: Path) -> None:
	initial_frame: npt.NDArray[np.uint8] = np.full((60, 80), 200, dtype=np.uint8)
	df_video: pd.DataFrame = pd.DataFrame(
		{
			"video_name": ["IMG_1556", "IMG_1556", "IMG_1556"],
			"frame_index": [120, 121, 122],
			"t": [2.0, 2.0167, 2.0334],
			"x": pd.Series([20, 21, pd.NA], dtype="Int64"),
			"y": pd.Series([30, 31, pd.NA], dtype="Int64"),
		}
	)
	out_png: Path = tmp_path / "IMG_1556_trajectory.png"
	plot_trajectory_on_frame(
		initial_frame_gray=initial_frame,
		df_video=df_video,
		output_path=out_png,
		video_name="IMG_1556",
	)
	assert out_png.exists()
	assert out_png.stat().st_size > 0


def test_extract_trimmed_frames_gray_subsampled_fps(tmp_path: Path) -> None:
	video_path: Path = tmp_path / "synthetic6.MOV"
	with av.open(str(video_path), mode="w") as container:
		stream = container.add_stream("mpeg4", rate=10)
		stream.width = 32
		stream.height = 24
		stream.pix_fmt = "yuv420p"
		for idx in range(6):
			gray: npt.NDArray[np.uint8] = np.full((24, 32), idx * 30, dtype=np.uint8)
			rgb: npt.NDArray[np.uint8] = np.stack([gray, gray, gray], axis=-1)
			vframe = av.VideoFrame.from_ndarray(rgb, format="rgb24")
			for packet in stream.encode(vframe):
				container.mux(packet)
		for packet in stream.encode():
			container.mux(packet)

	out_dir: Path = tmp_path / "frames_30fps"
	records: list[FrameRecord] = extract_trimmed_frames_gray(
		video_path=video_path,
		video_name="SYNTH",
		output_dir=out_dir,
		target_fps=30,
		batch_size=2,
		max_workers=2,
	)
	assert [r.frame_index for r in records] == [0, 2, 4]

	with pytest.raises(ValueError, match="target_fps"):
		extract_trimmed_frames_gray(
			video_path=video_path,
			video_name="SYNTH",
			output_dir=out_dir,
			target_fps=61,
		)
