rule download_video:
	"""Download a single raw .MOV video from Google Drive in parallel."""
	wildcard_constraints:
		video = VIDEO_REGEX
	output:
		file_path = f"{config['paths']['videos_dir']}/{{video}}.MOV"
	log:
		f"{config['paths']['logs_dir']}/download_video/{{video}}.log"
	benchmark:
		f"{config['paths']['benchmarks_dir']}/download_video/{{video}}.tsv"
	params:
		url = get_video_url
	threads: 1
	resources:
		mem_mb = 500
	conda:
		"../envs/default.yaml"
	script:
		"../scripts/download_file.py"


rule download_image:
	"""Download a single reference or background image from Google Drive in parallel."""
	wildcard_constraints:
		image_file = IMAGE_FILE_REGEX
	output:
		file_path = f"{config['paths']['images_dir']}/{{image_file}}"
	log:
		f"{config['paths']['logs_dir']}/download_image/{{image_file}}.log"
	benchmark:
		f"{config['paths']['benchmarks_dir']}/download_image/{{image_file}}.tsv"
	params:
		url = get_image_url
	threads: 1
	resources:
		mem_mb = 500
	conda:
		"../envs/default.yaml"
	script:
		"../scripts/download_file.py"
