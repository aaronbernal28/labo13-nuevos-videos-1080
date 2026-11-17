from pathlib import Path
import pandas as pd


VIDEOS: list[str] = list(config["videos"].keys())
VIDEO_REGEX: str = "|".join(VIDEOS)

IMAGES: list[str] = list(config["images"].keys())
IMAGE_FILE_REGEX: str = "|".join(config["images"][k]["file"] for k in IMAGES)

BG_KEY: str = config["parameters"]["background_image_key"]
BACKGROUND_PATH: str = f"{config['paths']['images_dir']}/{config['images'][BG_KEY]['file']}"


def get_video_url(wildcards) -> str:
	return str(config["videos"][wildcards.video]["url"])


def get_image_url(wildcards) -> str:
	return next(
		str(v["url"]) for v in config["images"].values() if v["file"] == wildcards.image_file
	)


def get_video_t_start(wildcards) -> int | None:
	return config["videos"][wildcards.video]["t_start"]


def get_video_t_end(wildcards) -> int | None:
	return config["videos"][wildcards.video]["t_end"]


def collect_detected_frame_txts(wildcards) -> list[str]:
	"""Resolve checkpoint manifests to list all expected per-frame .txt files across active videos."""
	txt_files: list[str] = []
	frames_root: str = config["paths"]["frames_dir"]
	for video in VIDEOS:
		ckpt_output = checkpoints.extract_frames.get(video=video).output
		manifest_path: Path = Path(ckpt_output.manifest_tsv)
		df_manifest: pd.DataFrame = pd.read_csv(manifest_path, sep="\t")
		for stem in df_manifest["stem"].astype(str):
			txt_files.append(f"{frames_root}/{video}/{stem}.txt")
	return txt_files


def collect_video_frame_txts(wildcards) -> list[str]:
	"""Resolve checkpoint manifest to list all per-frame .txt files for a single video."""
	frames_root: str = config["paths"]["frames_dir"]
	ckpt_output = checkpoints.extract_frames.get(video=wildcards.video).output
	manifest_path: Path = Path(ckpt_output.manifest_tsv)
	df_manifest: pd.DataFrame = pd.read_csv(manifest_path, sep="\t")
	return [
		f"{frames_root}/{wildcards.video}/{stem}.txt"
		for stem in df_manifest["stem"].astype(str)
	]
