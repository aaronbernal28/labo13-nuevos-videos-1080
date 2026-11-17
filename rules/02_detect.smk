rule detect_frame:
	"""Detect pendulum bob centroid for a single greyscale frame and write one CSV row to .txt."""
	wildcard_constraints:
		video = VIDEO_REGEX,
		stem = r".+_f\d{6}_t\d+\.\d{4}"
	input:
		frame_png = f"{config['paths']['frames_dir']}/{{video}}/{{stem}}.png",
		background_png = BACKGROUND_PATH
	output:
		row_txt = f"{config['paths']['frames_dir']}/{{video}}/{{stem}}.txt"
	log:
		f"{config['paths']['logs_dir']}/detect_frame/{{video}}/{{stem}}.log"
	benchmark:
		f"{config['paths']['benchmarks_dir']}/detect_frame/{{video}}/{{stem}}.tsv"
	params:
		threshold_low = config["parameters"]["threshold_low"],
		threshold_high = config["parameters"]["threshold_high"],
		disk_radius = config["parameters"]["morphology_disk_radius"]
	threads: 1
	resources:
		mem_mb = 500
	conda:
		"../envs/default.yaml"
	script:
		"../scripts/detect_frame.py"
