from pathlib import Path
from typing import TYPE_CHECKING

from labo13.io import download_drive_file


if TYPE_CHECKING:
	from snakemake.script import Snakemake

	snakemake: Snakemake


def main() -> None:
	url: str = str(snakemake.params.url)
	output_path: Path = Path(snakemake.output.file_path)
	download_drive_file(url=url, output_path=output_path)


if __name__ == "__main__":
	main()
