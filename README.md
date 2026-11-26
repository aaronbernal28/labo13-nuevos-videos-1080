# LABO 1 — Simple Pendulum: Nonlinear Behavior at Large Angles (4K 60 fps)

Reproducible 3-tier **Python + Snakemake** workflow for tracking a simple pendulum across 4K (`3840x2160`) 60 fps `.MOV` videos and analyzing the breakdown of the **small-angle (sinusoidal) approximation** as oscillation amplitude increases.

## Authors

- **Christian Gustavo Montaño Herrera**
- **Aaron Bernal Huanca**
- **Nazareno Ezequiel Ordiz**

---

## Overview & Scientific Objectives

### Stage 1 — Automated Video Tracking Pipeline (Snakemake)

Convert raw 4K (`3840x2160`) 60 fps pendulum videos into a single tidy trajectory table `results/trajectories.csv` (`video_name,t,x,y`):

1. **Parallel Media Acquisition (`download_video`, `download_image`)**: Downloads the oscillation videos and the shared background frame (`superfotograma.png`) in parallel from Google Drive.
2. **Greyscale Frame Extraction & Trimming (`extract_frames` checkpoint)**: Decodes each video via PyAV, filters frames within configured integer-second bounds `[t_start, t_end)` using the container's presentation timestamp (PTS), converts to 8-bit greyscale, and writes lossless PNGs named `{video}_f{index:06d}_t{seconds:.4f}.png` alongside a per-video manifest TSV (`media/frames/{video}.manifest.tsv`).
3. **Per-Frame Centroid Detection (`detect_frame`)**: Runs **one independent Snakemake job per frame** using `scipy.ndimage` comparing `{stem}.png` against `superfotograma.png` inside the ROI (background subtraction $\to$ intensity threshold `(20, 255)` $\to$ morphological closing with disk $r = 3\text{ px}$ $\to$ morphological opening with disk $r = 6\text{ px}$ to remove the thin string $\to$ largest 8-connected-component centroid) and writes a single CSV row `video_name,t,x,y` to `{stem}.txt`.
4. **Trajectory Aggregation (`aggregate_csv`)**: Collects all per-frame `.txt` rows resolved through the checkpoint manifests and exports `results/trajectories.csv` sorted deterministically by `(video_name, t)`.

### Stage 2 — Amplitude-Dependence & Nonlinear Regime Analysis (Snakemake + Notebook)

Using `results/trajectories.csv` and the pure Tier 1 analysis library (`labo13.pendulum_analysis` and `labo13.analysis_plots`) across the 14 analyzed takes (`Toma 1` at $\theta_0 \approx 56{,}34^\circ$ down to `Toma 14` at $\theta_0 \approx 2{,}17^\circ$):

1. **Angular Reconstruction**: Converts detected centroids $(x, y)$ directly to $\theta(t) = \operatorname{atan2}(x - x_p, y - y_p)$ using the measured 4K suspension point $(x_p, y_p) = (1960,\,37)\text{ px}$ (cross-checked against a circular-arc fit over large-angle takes, yielding $|\Delta\theta_0| \le 0{,}03^\circ$ and $|\Delta T| \le 0{,}005\text{ ms}$).
2. **Two-Stage Empirical-Residual Double Fit**: Fits the undamped sinusoidal model $\theta(\tau) = \theta_0\cos(\omega\tau + \phi) + \theta_{\text{off}}$ initialized via zero-padded FFT and linear least squares. Stage 1 performs an unweighted nonlinear least-squares fit to estimate the empirical per-point residual dispersion $s_{\text{res}} = \sqrt{\sum r_i^2 / (N - 4)}$; Stage 2 re-fits with $\sigma_i = s_{\text{res}}$ (`absolute_sigma=True`) to propagate uncertainties directly from observed data dispersion.
3. **Model-Free Amplitude Decay Check**: Compares first-cycle vs. last-cycle peak-to-peak amplitudes (`scipy.signal.find_peaks`) to quantify amplitude decay across each recording (`1.78%` to `9.50%`) without introducing a damped model.
4. **Small-Angle Breakdown & Borda Expansion**: Compares $T(\theta_0)$ against the small-angle experimental limit $T_0 = (2.07235 \pm 0.00006)\text{ s}$ (compatible at $1.25\sigma$ with the theoretical prediction $T_{0,\text{teo}} = 2\pi\sqrt{L/g} = (2.07841 \pm 0.00485)\text{ s}$ for $L = 1.072\text{ m}$), identifies the $3\sigma$ transition interval $(2.17^\circ,\,3.78^\circ]$, and validates agreement with Borda's second-order expansion ($\text{RMS} = 1.05\text{ ms}$):

$$T(\theta_0) \approx T_0\left(1 + \frac{\theta_0^2}{16} + \frac{11\,\theta_0^4}{3072} + \dots\right), \qquad T_0 = 2\pi\sqrt{\frac{L}{g}}$$

---

## Experimental Setup & Physical Constants

| Quantity | Symbol | Value | Uncertainty | Notes |
|---|---|---|---|---|
| Pendulum length | $L$ | $1.072\text{ m}$ ($107.2\text{ cm}$) | $\pm 0.005\text{ m}$ ($\pm 0.5\text{ cm}$) | Suspension pivot to center of mass of bob |
| Local gravity (Buenos Aires) | $g$ | $9.797\text{ m/s}^2$ | — | Reference value for $T_{0,\text{teo}} = 2\pi\sqrt{L/g}$ |
| Measured suspension pivot | $(x_p, y_p)$ | $(1960,\,37)\text{ px}$ | — | Direct measurement on 4K (`3840x2160`) frame |
| Camera resolution & frame rate | $\text{fps}$ | $60\text{ fps}$ (`3840x2160`) | $\Delta t \approx 16.67\text{ ms}$ | Fixed camera, real-time playback |
| Active analyzed takes | — | $14$ takes (`Toma 1`–`Toma 14`) | — | Ordered from largest ($\theta_0 = 56.34^\circ$) to smallest ($2.17^\circ$) |

---

## Project Layout

```text
labo13-nuevos-videos-1080/
├── Snakefile                              ← Pipeline orchestration, schema validation & target rules
├── config.yaml                            ← Central parameters, per-file Drive URLs & video trim bounds
├── pyproject.toml                         ← PEP 621 package metadata, dependencies & mypy config
├── uv.lock                                ← Locked Python 3.12 dependency versions for uv
├── ruff.toml                              ← Ruff linter/formatter config (tab indentation, snakemake builtin)
├── .env.example                           ← Template for optional environment variables (never commit .env)
├── .gitignore                             ← Ignores media/, docs/, .snakemake/, .venv/, .env, checkpoints
├── README.md                              ← Project overview, ASCII tree, setup & Snakemake commands
├── envs/
│   └── default.yaml                       ← Conda environment specification for rule portability
├── workflow/
│   └── schemas/
│       └── config.schema.yaml             ← JSON Schema Draft 2020-12 validating config.yaml
├── rules/                                 ← Tier 3: Modular Snakemake rule definitions (*.smk)
│   ├── common.smk                         ← Wildcard constants, parameter getters & checkpoint resolver
│   ├── 00_download.smk                    ← Parallel rules download_video & download_image (gdown)
│   ├── 01_frames.smk                      ← Checkpoint extract_frames (grey PNGs + manifest TSV)
│   ├── 02_detect.smk                      ← Rule detect_frame (parallel 1-job-per-frame centroid TXT)
│   ├── 03_aggregate.smk                   ← Rule aggregate_csv (checkpoint aggregation into CSV)
│   ├── 04_plot.smk                        ← Rule plot_video_trajectory (overlay x,y on initial frame)
│   ├── 05_analysis.smk                    ← Rules analyze_pendulum & analyze_pendulum_all (Stage 2)
│   └── 06_figures.smk                     ← Rules plot_analysis_figures & analysis_figures_all (Stage 2)
├── scripts/                               ← Tier 2: Thin Snakemake adapter scripts (*.py)
│   ├── download_file.py                   ← Unpacks snakemake -> labo13.io.download_drive_file
│   ├── extract_frames.py                  ← Unpacks snakemake -> labo13.video.extract_trimmed_frames_gray
│   ├── detect_frame.py                    ← Unpacks snakemake -> labo13.detection.compute_bob_centroid
│   ├── aggregate_csv.py                   ← Unpacks snakemake -> labo13.io.build_trajectories_dataframe
│   ├── plot_trajectory.py                 ← Unpacks snakemake -> labo13.video.plot_trajectory_on_frame
│   ├── analyze_pendulum.py                ← Unpacks snakemake -> labo13.pendulum_analysis.run_pendulum_analysis
│   └── plot_analysis_figures.py           ← Unpacks snakemake -> labo13.analysis_plots (title-free PNGs)
├── src/                                   ← Tier 1: Pure modular domain library (zero Snakemake coupling)
│   └── labo13/
│       ├── __init__.py                    ← Package exports and version
│       ├── types.py                       ← Dataclasses (FrameRecord, PendulumConstants, HarmonicFitResult)
│       ├── io.py                          ← Per-file Drive download, manifest TSV & TXT/CSV I/O
│       ├── frame_io.py                    ← Fast greyscale PNG serialization helpers
│       ├── video.py                       ← PyAV decoding, PTS time trimming & greyscale frame I/O
│       ├── detection.py                   ← scipy.ndimage background subtraction, closing/opening & centroid
│       ├── physics.py                     ← Legacy polar/ODE physics helpers
│       ├── pendulum_analysis.py           ← Measured-pivot conversion, double fit, peak decay & Borda tables
│       └── analysis_plots.py              ← Title-free 300 dpi Matplotlib report figure generators
├── tests/                                 ← Unit tests independent of Snakemake (pytest)
│   ├── test_io.py                         ← Tests TXT row formatting/parsing & CSV sorting
│   ├── test_video.py                      ← Tests integer-second trim predicates & filename formatting
│   ├── test_detection.py                  ← Tests synthetic circle centroid & NaN fallback on empty frame
│   └── test_pendulum_analysis.py          ← Tests pivot fit, double fit, peak decay, Borda & LaTeX table
├── notebooks/
│   ├── colab_pendulum_analysis.ipynb      ← Clean Colab/local Stage 2 analysis notebook aligned with Tier 1
│   ├── debug_frame_detection.ipynb        ← Manual frame-detection inspection notebook
│   └── original/
│       └── Copia de [LABO 13] Nuevos Videos 1080.ipynb ← Original unmodified Colab notebook
├── media/                                 ← Gitignored raw media and intermediate frame artifacts
│   ├── raw/
│   │   ├── videos/                        ← Downloaded {video}.MOV files
│   │   └── images/                        ← Downloaded background image (superfotograma.png)
│   └── frames/
│       └── {video}/                       ← {video}_f{index:06d}_t{seconds:.4f}.{png,txt}
└── results/
    ├── trajectories.csv                   ← Stage 1 tidy table: video_name,t,x,y (60 fps)
    ├── plots/                             ← Per-video trajectory overlays over initial frames
    └── analysis/                          ← Stage 2 verified outputs (summary CSV, decay CSV, JSON, LaTeX)
```

---

## Key Targets, Rules & Output Formats

| Rule / Checkpoint | Input(s) | Output(s) | Description |
|---|---|---|---|
| `download_video` | Google Drive URL (`config.yaml`) | `media/raw/videos/{video}.MOV` | Downloads each enabled video in parallel via `gdown` |
| `download_image` | Google Drive URL (`config.yaml`) | `media/raw/images/{image_file}` | Downloads `superfotograma.png` |
| `extract_frames` *(checkpoint)* | `media/raw/videos/{video}.MOV` | `media/frames/{video}/`, `media/frames/{video}.manifest.tsv` | Extracts trimmed greyscale PNG frames `{video}_f{index:06d}_t{seconds:.4f}.png` |
| `detect_frame` | `media/frames/{video}/{stem}.png`, `media/raw/images/superfotograma.png` | `media/frames/{video}/{stem}.txt` | Runs **1 job per frame** writing a single CSV line `video_name,t,x,y` |
| `aggregate_csv` | All `media/frames/{video}/{stem}.txt` | `results/trajectories.csv` | Concatenates and sorts all per-frame detections by `(video_name, t)` |
| `plot_video_trajectory` | All `media/frames/{video}/{stem}.txt` for `{video}` | `results/plots/{video}_trajectory.png` | Plots all detected `(x, y)` points for `{video}` over its initial frame PNG |
| `analyze_pendulum` | `results/trajectories.csv` | `results/analysis/{summary_table.csv, amplitude_decay.csv, diagnostics.json, summary_table.tex}` | Runs measured-pivot conversion, two-stage double fit, model-free amplitude decay & Borda analysis |
| `plot_analysis_figures` | `results/trajectories.csv`, `results/analysis/{summary_table.csv, diagnostics.json}`, sample frame & background | `docs/figures/fig_{procesamiento_fotograma, theta_pequena, theta_grande, periodo_vs_amplitud}.png` | Generates title-free 300 dpi figures for the report |

### Output CSV Schema (`results/trajectories.csv`)

| Column | Type | Units / Origin | Description |
|---|---|---|---|
| `video_name` | `str` | — | Video identifier matching the key in `config.yaml` (e.g. `IMG_1556`) |
| `t` | `float` | seconds (`s`) | Original video presentation timestamp (PTS) of the frame |
| `x` | `int \| NaN` | pixels (`px`) | Horizontal bob centroid rounded to nearest integer pixel (origin top-left; `nan` if undetected) |
| `y` | `int \| NaN` | pixels (`px`) | Vertical bob centroid rounded to nearest integer pixel (origin top-left; grows downward; `nan` if undetected) |

---

## Configuration (`config.yaml`)

All experimental paths, detection thresholds, and per-video trim intervals are controlled through `config.yaml` (validated at startup against `workflow/schemas/config.schema.yaml`):

- **Selecting / Skipping Videos**: Comment out any video block under `videos:` to skip downloading and processing that video.
- **Manual Time Trimming (`t_start`, `t_end`)**: Integer seconds restricting frame extraction to $t_{\text{start}} \le t < t_{\text{end}}$ (`null` for untrimmed).
- **Detection & Extraction Parameters (`parameters:`)**:
  - `fps: 60` — target extraction frame rate (`1`–`60`).
  - `threshold_low: 20.0`, `threshold_high: 255.0` — intensity window on `background - frame`.
  - `morphology_disk_radius: 3` — disk radius in pixels for `scipy.ndimage.binary_closing`.
  - `morphology_opening_disk_radius: 6` — disk radius in pixels for `scipy.ndimage.binary_opening` (removes the thin suspension string).
  - `roi_y_start: 1180`, `roi_y_end: 2080`, `roi_x_start: 200`, `roi_x_end: 3500` — default 4K region of interest (with per-video override on `IMG_1555`).

---

## Tier 1 Domain Library (`src/labo13/`)

| Module | Public Functions & Classes | Responsibility |
|---|---|---|
| `labo13.types` | `FrameRecord`, `PendulumConstants`, `HarmonicFitResult` | Frozen dataclasses for frame metadata, physical constants, and fit results |
| `labo13.io` | `download_drive_file`, `save_frame_manifest`, `load_frame_manifest`, `parse_stem_metadata`, `save_frame_detection_row`, `load_frame_detection_row`, `build_trajectories_dataframe`, `export_trajectories_csv` | Google Drive download, manifest TSV serialization, and per-frame `.txt` / `.csv` I/O |
| `labo13.video` | `is_within_time_bounds`, `format_frame_stem`, `load_image_gray`, `save_image_gray`, `load_video_frame_gray`, `plot_sampled_frames`, `extract_trimmed_frames_gray` | PyAV video decoding, integer-second PTS trimming, and greyscale PNG I/O |
| `labo13.detection` | `compute_bob_centroid` | `scipy.ndimage` background subtraction, closing (`r=3`), opening (`r=6`), and largest-component centroid |
| `labo13.pendulum_analysis` | `load_active_trajectories`, `build_measured_pivot`, `compute_pivot_calibration`, `compute_angular_series`, `fit_undamped_oscillation`, `compute_amplitude_decay`, `compute_borda_period`, `build_summary_and_diagnostics`, `format_summary_latex_table`, `run_pendulum_analysis` | Stage 2 angular conversion, two-stage empirical-residual double fit, model-free peak decay, Borda comparison, and LaTeX table export |
| `labo13.analysis_plots` | `plot_frame_processing_steps`, `plot_representative_fit`, `plot_period_vs_amplitude` | Title-free 300 dpi Matplotlib report figures |

### Library Quick-Start

```python
from labo13.pendulum_analysis import run_pendulum_analysis

summary_df, decay_df, diagnostics, latex_table = run_pendulum_analysis("results/trajectories.csv")
```

---

## Environment Setup

Python 3.12+ managed with `uv`:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

---

## Pipeline Execution & Quality Gates

```bash
# 1. Validate Snakemake workflow linting and inspect the dry-run DAG
uv run snakemake --lint
uv run snakemake -n

# 2. Run Stage 1 tracking pipeline across all enabled videos
uv run snakemake --cores all

# 3. Run Stage 2 quantitative analysis (tables, decay check, diagnostics JSON, LaTeX table)
uv run snakemake analyze_pendulum_all --cores 1

# 4. Generate Stage 2 title-free report figures
uv run snakemake analysis_figures_all --cores 1

# 5. Run code quality gates (Ruff, Mypy, Pytest)
uv run ruff check --fix src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/labo13/pendulum_analysis.py src/labo13/analysis_plots.py
uv run pytest -v
```
