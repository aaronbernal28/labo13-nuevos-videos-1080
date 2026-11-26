rule analyze_pendulum:
	"""Run measured-pivot angular conversion, double-fit harmonic analysis, and Borda check."""
	input:
		trajectories_csv = config["paths"]["trajectories_csv"]
	output:
		summary_csv = "results/analysis/summary_table.csv",
		decay_csv = "results/analysis/amplitude_decay.csv",
		diagnostics_json = "results/analysis/diagnostics.json",
		summary_tex = "results/analysis/summary_table.tex"
	log:
		f"{config['paths']['logs_dir']}/analyze_pendulum.log"
	benchmark:
		f"{config['paths']['benchmarks_dir']}/analyze_pendulum.tsv"
	threads: 1
	resources:
		mem_mb = 1000
	conda:
		"../envs/default.yaml"
	script:
		"../scripts/analyze_pendulum.py"


rule analyze_pendulum_all:
	"""Build all quantitative pendulum analysis tables and diagnostics."""
	input:
		summary_csv = "results/analysis/summary_table.csv",
		decay_csv = "results/analysis/amplitude_decay.csv",
		diagnostics_json = "results/analysis/diagnostics.json",
		summary_tex = "results/analysis/summary_table.tex"
