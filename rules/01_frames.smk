checkpoint extract_frames:
	"""Convert a downloaded video to greyscale PNG frames within configured [t_start, t_end) bounds."""
	wildcard_constraints:
		video = VIDEO_REGEX
	input:
		video_mov = f"{config['paths']['videos_dir']}/{{video}}.MOV"
	output:
		frames_dir = directory(f"{config['paths']['frames_dir']}/{{video}}"),
		manifest_tsv = f"{config['paths']['frames_dir']}/{{video}}.manifest.tsv"
	log:
		f"{config['paths']['logs_dir']}/extract_frames/{{video}}.log"
	benchmark:
		f"{config['paths']['benchmarks_dir']}/extract_frames/{{video}}.tsv"
	params:
		t_start = get_video_t_start,
		t_end = get_video_t_end,
		batch_size = config["parameters"]["frame_batch_size"],
		compress_level = config["parameters"]["png_compress_level"]
	threads: 4
	resources:
		mem_mb = 2000
	conda:
		"../envs/default.yaml"
	script:
		"../scripts/extract_frames.py"
