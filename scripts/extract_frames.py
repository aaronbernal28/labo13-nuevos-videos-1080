from pathlib import Path
from typing import TYPE_CHECKING

from labo13.io import save_frame_manifest
from labo13.types import FrameRecord
from labo13.video import extract_trimmed_frames_gray


if TYPE_CHECKING:
	from snakemake.script import Snakemake

	snakemake: Snakemake


def main() -> None:
	video_path: Path = Path(snakemake.input.video_mov)
	frames_dir: Path = Path(snakemake.output.frames_dir)
	manifest_tsv: Path = Path(snakemake.output.manifest_tsv)
	video_name: str = str(snakemake.wildcards.video)

	raw_t_start: int | None = snakemake.params.t_start
	raw_t_end: int | None = snakemake.params.t_end
	t_start: int | None = int(raw_t_start) if raw_t_start is not None else None
	t_end: int | None = int(raw_t_end) if raw_t_end is not None else None

	records: list[FrameRecord] = extract_trimmed_frames_gray(
		video_path=video_path,
		video_name=video_name,
		output_dir=frames_dir,
		t_start=t_start,
		t_end=t_end,
	)
	save_frame_manifest(records=records, manifest_path=manifest_tsv)


if __name__ == "__main__":
	main()
