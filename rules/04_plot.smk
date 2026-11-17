rule plot_video_trajectory:
	"""Plot all detected (x, y) points from a video's .txt files over its initial frame PNG."""
	wildcard_constraints:
		video = VIDEO_REGEX
	input:
		frame_txts = collect_video_frame_txts
	output:
		plot_png = f"{config['paths']['plots_dir']}/{{video}}_trajectory.png"
	log:
		f"{config['paths']['logs_dir']}/plot_trajectory/{{video}}.log"
	benchmark:
		f"{config['paths']['benchmarks_dir']}/plot_trajectory/{{video}}.tsv"
	threads: 1
	resources:
		mem_mb = 1000
	conda:
		"../envs/default.yaml"
	script:
		"../scripts/plot_trajectory.py"


rule plot_trajectories:
	"""Generate trajectory overlay plots for all active videos."""
	input:
		plots = [
			f"{config['paths']['plots_dir']}/{video}_trajectory.png"
			for video in VIDEOS
		]
