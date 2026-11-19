import importlib
from types import ModuleType
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
	from labo13.detection import compute_bob_centroid
	from labo13.frame_io import (
		load_frame_detection_row,
		load_image_gray,
		parse_stem_metadata,
		save_frame_detection_row,
	)
	from labo13.io import (
		build_trajectories_dataframe,
		download_drive_file,
		export_trajectories_csv,
		load_frame_manifest,
		save_frame_manifest,
	)
	from labo13.physics import (
		compute_harmonic_fit,
		compute_ode_trajectory,
		compute_polar_trajectory,
		compute_sliding_window_periods,
	)
	from labo13.types import (
		FrameRecord,
		HarmonicFitResult,
		PendulumConstants,
		PixelCentroid,
		VideoName,
	)
	from labo13.video import (
		extract_trimmed_frames_gray,
		format_frame_stem,
		is_within_time_bounds,
		load_video_frame_gray,
		plot_sampled_frames,
		plot_trajectory_on_frame,
		save_frame_batch_gray,
		save_image_gray,
	)


_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
	"FrameRecord": ("labo13.types", "FrameRecord"),
	"HarmonicFitResult": ("labo13.types", "HarmonicFitResult"),
	"PendulumConstants": ("labo13.types", "PendulumConstants"),
	"PixelCentroid": ("labo13.types", "PixelCentroid"),
	"VideoName": ("labo13.types", "VideoName"),
	"build_trajectories_dataframe": ("labo13.io", "build_trajectories_dataframe"),
	"compute_bob_centroid": ("labo13.detection", "compute_bob_centroid"),
	"compute_harmonic_fit": ("labo13.physics", "compute_harmonic_fit"),
	"compute_ode_trajectory": ("labo13.physics", "compute_ode_trajectory"),
	"compute_polar_trajectory": ("labo13.physics", "compute_polar_trajectory"),
	"compute_sliding_window_periods": (
		"labo13.physics",
		"compute_sliding_window_periods",
	),
	"download_drive_file": ("labo13.io", "download_drive_file"),
	"export_trajectories_csv": ("labo13.io", "export_trajectories_csv"),
	"extract_trimmed_frames_gray": ("labo13.video", "extract_trimmed_frames_gray"),
	"format_frame_stem": ("labo13.video", "format_frame_stem"),
	"is_within_time_bounds": ("labo13.video", "is_within_time_bounds"),
	"load_frame_detection_row": ("labo13.frame_io", "load_frame_detection_row"),
	"load_frame_manifest": ("labo13.io", "load_frame_manifest"),
	"load_image_gray": ("labo13.frame_io", "load_image_gray"),
	"load_video_frame_gray": ("labo13.video", "load_video_frame_gray"),
	"parse_stem_metadata": ("labo13.frame_io", "parse_stem_metadata"),
	"plot_sampled_frames": ("labo13.video", "plot_sampled_frames"),
	"plot_trajectory_on_frame": ("labo13.video", "plot_trajectory_on_frame"),
	"save_frame_batch_gray": ("labo13.video", "save_frame_batch_gray"),
	"save_frame_detection_row": ("labo13.frame_io", "save_frame_detection_row"),
	"save_frame_manifest": ("labo13.io", "save_frame_manifest"),
	"save_image_gray": ("labo13.video", "save_image_gray"),
}


__all__: list[str] = [
	"FrameRecord",
	"HarmonicFitResult",
	"PendulumConstants",
	"PixelCentroid",
	"VideoName",
	"build_trajectories_dataframe",
	"compute_bob_centroid",
	"compute_harmonic_fit",
	"compute_ode_trajectory",
	"compute_polar_trajectory",
	"compute_sliding_window_periods",
	"download_drive_file",
	"export_trajectories_csv",
	"extract_trimmed_frames_gray",
	"format_frame_stem",
	"is_within_time_bounds",
	"load_frame_detection_row",
	"load_frame_manifest",
	"load_image_gray",
	"load_video_frame_gray",
	"parse_stem_metadata",
	"plot_sampled_frames",
	"plot_trajectory_on_frame",
	"save_frame_batch_gray",
	"save_frame_detection_row",
	"save_frame_manifest",
	"save_image_gray",
]


def __getattr__(name: str) -> Any:
	if name in _LAZY_IMPORTS:
		module_name: str
		attr_name: str
		module_name, attr_name = _LAZY_IMPORTS[name]
		module: ModuleType = importlib.import_module(module_name)
		value: Any = getattr(module, attr_name)
		globals()[name] = value
		return value
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
