from snakemake.utils import validate


configfile: "config.yaml"


validate(config, schema="workflow/schemas/config.schema.yaml")

VIDEOS: list[str] = list(config["videos"].keys())
VIDEO_REGEX: str = "|".join(VIDEOS)

IMAGES: list[str] = list(config["images"].keys())
IMAGE_FILE_REGEX: str = "|".join(config["images"][k]["file"] for k in IMAGES)

BG_KEY: str = config["parameters"]["background_image_key"]
BACKGROUND_PATH: str = f"{config['paths']['images_dir']}/{config['images'][BG_KEY]['file']}"


include: "rules/00_download.smk"
include: "rules/01_frames.smk"
include: "rules/02_detect.smk"
include: "rules/03_aggregate.smk"


rule all:
	'''Build the unified pendulum trajectories CSV and download active reference images.'''
	input:
		trajectories_csv = config["paths"]["trajectories_csv"],
		reference_images = [
			f"{config['paths']['images_dir']}/{config['images'][img]['file']}"
			for img in IMAGES
		]
