rule plot_analysis_figures:
	"""Generate title-free processing, representative fit, and period-vs-amplitude figures."""
	input:
		trajectories_csv = config["paths"]["trajectories_csv"],
		summary_csv = "results/analysis/summary_table.csv",
		diagnostics_json = "results/analysis/diagnostics.json",
		sample_frame_png = f"{config['paths']['frames_dir']}/IMG_1558/IMG_1558_f000000_t0.0000.png",
		background_png = f"{config['paths']['images_dir']}/{config['images'][config['parameters']['background_image_key']]['file']}"
	output:
		fig_procesamiento = "docs/figures/fig_procesamiento_fotograma.png",
		fig_theta_pequena = "docs/figures/fig_theta_pequena.png",
		fig_theta_grande = "docs/figures/fig_theta_grande.png",
		fig_periodo_vs_amplitud = "docs/figures/fig_periodo_vs_amplitud.png"
	log:
		f"{config['paths']['logs_dir']}/plot_analysis_figures.log"
	benchmark:
		f"{config['paths']['benchmarks_dir']}/plot_analysis_figures.tsv"
	threads: 1
	resources:
		mem_mb = 2000
	conda:
		"../envs/default.yaml"
	script:
		"../scripts/plot_analysis_figures.py"


rule analysis_figures_all:
	"""Build all title-free report figures for §2.1, §3.1, and §3.2."""
	input:
		fig_procesamiento = "docs/figures/fig_procesamiento_fotograma.png",
		fig_theta_pequena = "docs/figures/fig_theta_pequena.png",
		fig_theta_grande = "docs/figures/fig_theta_grande.png",
		fig_periodo_vs_amplitud = "docs/figures/fig_periodo_vs_amplitud.png"
