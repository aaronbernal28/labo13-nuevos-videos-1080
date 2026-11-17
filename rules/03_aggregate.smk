rule aggregate_csv:
	"""Concatenate all per-frame .txt detection rows into results/trajectories.csv."""
	input:
		manifests = [
			f"{config['paths']['frames_dir']}/{video}.manifest.tsv"
			for video in VIDEOS
		],
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
	conda:
		"../envs/default.yaml"
	script:
		"../scripts/aggregate_csv.py"
