from snakemake.utils import validate


configfile: "config.yaml"


validate(config, schema="workflow/schemas/config.schema.yaml")


include: "rules/common.smk"
include: "rules/00_download.smk"
include: "rules/01_frames.smk"
include: "rules/02_detect.smk"
include: "rules/03_aggregate.smk"


rule all:
	"""Build the unified pendulum trajectories CSV and download active reference images."""
	input:
		trajectories_csv = config["paths"]["trajectories_csv"],
		reference_images = [
			f"{config['paths']['images_dir']}/{config['images'][img]['file']}"
			for img in IMAGES
		]
