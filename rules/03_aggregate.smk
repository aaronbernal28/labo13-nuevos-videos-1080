from pathlib import Path
import pandas as pd


def collect_detected_frame_txts(wildcards) -> list[str]:
	'''Resolve checkpoint manifests to list all expected per-frame .txt files across active videos.'''
	txt_files: list[str] = []
	frames_root: str = config["paths"]["frames_dir"]
	for video in VIDEOS:
		ckpt_output = checkpoints.extract_frames.get(video=video).output
		manifest_path: Path = Path(ckpt_output.manifest_tsv)
		df_manifest: pd.DataFrame = pd.read_csv(manifest_path, sep="\t")
		for stem in df_manifest["stem"].astype(str):
			txt_files.append(f"{frames_root}/{video}/{stem}.txt")
	return txt_files


rule aggregate_csv:
	'''Concatenate all per-frame .txt detection rows into results/trajectories.csv.'''
	input:
		frame_txts = collect_detected_frame_txts
	output:
		trajectories_csv = config["paths"]["trajectories_csv"]
	log:
		f"{config['paths']['logs_dir']}/aggregate_csv.log"
	benchmark:
		f"{config['paths']['benchmarks_dir']}/aggregate_csv.tsv"
	threads: 1
	resources:
		mem_mb = 1000
	script:
		"../scripts/aggregate_csv.py"
