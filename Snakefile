from snakemake.utils import validate


configfile: "config.yaml"


validate(config, schema="workflow/schemas/config.schema.yaml")


include: "rules/common.smk"
include: "rules/00_download.smk"
include: "rules/01_frames.smk"
include: "rules/02_detect.smk"
include: "rules/03_aggregate.smk"
include: "rules/04_plot.smk"


rule all:
	"""Build the unified pendulum trajectories CSV, per-video trajectory plots, and reference images."""
	input:
		trajectories_csv = config["paths"]["trajectories_csv"],
		trajectory_plots = [
			f"{config['paths']['plots_dir']}/{video}_trajectory.png"
			for video in VIDEOS
		],
		reference_images = [
			f"{config['paths']['images_dir']}/{config['images'][img]['file']}"
			for img in IMAGES
		]
