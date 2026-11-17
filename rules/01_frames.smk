checkpoint extract_frames:
	'''Convert a downloaded video to greyscale PNG frames within configured [t_start, t_end) bounds.'''
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
		t_start = lambda wildcards: config["videos"][wildcards.video]["t_start"],
		t_end = lambda wildcards: config["videos"][wildcards.video]["t_end"]
	threads: 1
	resources:
		mem_mb = 2000
	script:
		"../scripts/extract_frames.py"
