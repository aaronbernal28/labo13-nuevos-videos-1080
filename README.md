# LABO 13 — Simple Pendulum: Nonlinear Behavior at Large Angles (1080p)

Reproducible 3-tier **Python + Snakemake** workflow for tracking a simple pendulum across 1080p `.MOV` videos and analyzing the breakdown of the **small-angle (sinusoidal) approximation** as oscillation amplitude increases.

---

## Overview & Scientific Objectives

### Stage 1 — Automated Video Tracking Pipeline (Snakemake)

Convert raw 1080p pendulum videos into a single tidy trajectory table `results/trajectories.csv` (`video_name,t,x,y`):

1. **Parallel Media Acquisition (`download_video`, `download_image`)**: Downloads the 15 active oscillation videos (`IMG_1555.MOV`–`IMG_1569.MOV`) and the shared background frame (`superfotograma.png`) in parallel directly from Google Drive.
2. **Greyscale Frame Extraction & Trimming (`extract_frames` checkpoint)**: Decodes each video via PyAV, filters frames within configured integer-second bounds `[t_start, t_end)` using the container's real presentation timestamp (PTS), converts to 8-bit greyscale, and writes lossless PNGs named `{video}_f{index:06d}_t{seconds:.4f}.png` alongside a per-video manifest TSV (`media/frames/{video}.manifest.tsv`).
3. **Per-Frame Centroid Detection (`detect_frame`)**: Runs **one independent Snakemake job per frame** comparing `{stem}.png` against `superfotograma.png` (background subtraction $\to$ intensity threshold `[threshold_low, threshold_high]` $\to$ morphological closing $\to$ largest connected-component centroid) and writes a single CSV row `video_name,t,x,y` to `{stem}.txt`.
4. **Trajectory Aggregation (`aggregate_csv`)**: Collects all per-frame `.txt` rows resolved through the checkpoint manifests and exports `results/trajectories.csv` sorted deterministically by `(video_name, t)`.

### Stage 2 — Amplitude-Dependence & Nonlinear Regime Analysis (Notebook)

Using `results/trajectories.csv` and the pure physics library (`labo13.physics`):

1. **Cartesian-to-Polar Transformation**: Estimate the equilibrium point $(x_0, y_0)$, convert pixel coordinates $(x, y)$ into meters $(X_m, Y_m)$ and polar angle $\theta(t) = \arctan2(X_m, Y_m)$, and propagate both point-to-point statistical centroid uncertainties ($\sigma_{\theta,\text{stat}}$) and systematic calibration/length uncertainties ($\sigma_{\theta,\text{total}}$).
2. **Model Comparison**: Fit and compare two physical models for $\theta(t)$ across runs of increasing initial amplitude $\theta_0$:
   - **Linear (Small-Angle Harmonic)**: $\ddot\theta + 2\gamma\dot\theta + \omega_0^2\,\theta = 0 \implies \theta(t) = A e^{-\gamma t}\cos(\omega t + \phi) + \theta_{\text{offset}}$
   - **Nonlinear (Exact Restoring Torque)**: $\ddot\theta + 2\gamma\dot\theta + \omega_0^2\,\sin\theta = 0$ integrated numerically via 8th-order Runge-Kutta (`DOP853`).
3. **Anharmonic Period Shift**: Verify that larger initial amplitudes $\theta_0$ degrade the sinusoidal approximation (increasing $\chi^2_{\text{red}}$ and structured residuals in the linear fit) and shift the oscillation period according to the Borda elliptic expansion:

$$T(\theta_0) \approx T_0\left(1 + \frac{\theta_0^2}{16} + \frac{11\,\theta_0^4}{3072} + \dots\right), \qquad T_0 = 2\pi\sqrt{\frac{L}{g}}$$

---

## Experimental Setup & Physical Constants

| Quantity | Symbol | Value | Uncertainty | Notes |
|---|---|---|---|---|
| Pendulum length (without base) | $L_{\text{sin base}}$ | $0.737\text{ m}$ | $\pm 0.005\text{ m}$ | Suspension point to top of bob |
| Pendulum length (with base) | $L_{\text{con base}}$ | $0.778\text{ m}$ | $\pm 0.005\text{ m}$ | Suspension point to bottom of bob |
| Effective center-of-mass length | $L_{\text{CM}}$ | $0.7575\text{ m}$ | $\pm 0.005\text{ m}$ | $\frac{1}{2}(L_{\text{sin base}} + L_{\text{con base}})$ |
| Pendulum width | $w$ | $3.0\text{ mm}$ | $\pm 0.2\text{ mm}$ | Measured with caliper |
| Camera frame period | $\Delta t$ | $1/59.96\text{ s}$ | $\approx 16.68\text{ ms}$ | Fixed 1080p camera (~59.96 fps) |

---

## Links & Data Availability

| Resource | Availability | Link |
|---|---|---|
| Original Colab notebook (baseline) | Public | https://colab.research.google.com/drive/1covVbCOVzjUw5jkBTUUZ00v053icBWpg?usp=sharing |
| Reference Colab example (style guide) | Public | https://drive.google.com/file/d/1qCTrCMC7AzwTvXsJM8Y7XEThvcKkU-Gj/view?usp=sharing |
| Raw videos & images folder (Google Drive) | Public | https://drive.google.com/drive/folders/10VmY2TRLvBIaaMNBjxqX4qjdgOwvmTSv?usp=sharing |

### Google Drive File Inventory (22 Files)

#### Videos (16 `.MOV` Files — 15 Active, 1 Measurement Evidence)

| Config Key | Original Drive Name | Local Target Path | Pipeline Status & Role | Google Drive URL |
|---|---|---|---|---|
| `IMG_1555` | `Copia de IMG_1555.MOV` | `media/raw/videos/IMG_1555.MOV` | Active — oscillation video | https://drive.google.com/file/d/1yiYkiyyFnH82KI7UQBh_dGtKFII0p76R/view?usp=drive_link |
| `IMG_1556` | `Copia de IMG_1556.MOV` | `media/raw/videos/IMG_1556.MOV` | Active — oscillation video | https://drive.google.com/file/d/1Ko_iG_jW-eF3aX8xf-cvqhTFmNtceOSE/view?usp=drive_link |
| `IMG_1557` | `Copia de IMG_1557.MOV` | `media/raw/videos/IMG_1557.MOV` | Active — oscillation video | https://drive.google.com/file/d/1sPhB7ZXdDpAlu3-gkL8NMXjqvmiCZ4vf/view?usp=drive_link |
| `IMG_1558` | `Copia de IMG_1558.MOV` | `media/raw/videos/IMG_1558.MOV` | Active — oscillation video | https://drive.google.com/file/d/11EvlSCqtED3f4dqSZ3tcjMYAoBBoI3_D/view?usp=drive_link |
| `IMG_1559` | `Copia de IMG_1559.MOV` | `media/raw/videos/IMG_1559.MOV` | Active — oscillation video | https://drive.google.com/file/d/1fAx-53cf7GMUyZbGZRhvdtlIEtoU0MX4/view?usp=drive_link |
| `IMG_1560` | `Copia de IMG_1560.MOV` | `media/raw/videos/IMG_1560.MOV` | Active — oscillation video | https://drive.google.com/file/d/1RynR6hOrd2CehShZ23yNl4LZ0phhWTTo/view?usp=drive_link |
| `IMG_1561` | `Copia de IMG_1561.MOV` | `media/raw/videos/IMG_1561.MOV` | Active — oscillation video | https://drive.google.com/file/d/1dUE8vjWjRxv9dS6A6IIJm2_VQwXDBmzP/view?usp=drive_link |
| `IMG_1562` | `Copia de IMG_1562.MOV` | `media/raw/videos/IMG_1562.MOV` | Active — oscillation video | https://drive.google.com/file/d/1FGHw9uC1k9yuTHkOqSoexXQxKgg9-xKz/view?usp=drive_link |
| `IMG_1563` | `Copia de IMG_1563.MOV` | `media/raw/videos/IMG_1563.MOV` | Active — oscillation video | https://drive.google.com/file/d/1iFds9fidJmm_7bCraIAWWR6LcJsTDSc0/view?usp=drive_link |
| `IMG_1564` | `Copia de IMG_1564.MOV` | `media/raw/videos/IMG_1564.MOV` | Active — oscillation video | https://drive.google.com/file/d/16hDMUF1zdKZSXkKT8pUPPzrGAWTtnlkb/view?usp=drive_link |
| `IMG_1565` | `Copia de IMG_1565.MOV` | `media/raw/videos/IMG_1565.MOV` | Active — oscillation video | https://drive.google.com/file/d/16ndBa5GYvaGHjuu1711Ct7iMMoeEpUfh/view?usp=drive_link |
| `IMG_1566` | `Copia de IMG_1566.MOV` | `media/raw/videos/IMG_1566.MOV` | Active — oscillation video | https://drive.google.com/file/d/1BJGQhoKvkviezTdvhw1LzXdSv-LoENst/view?usp=drive_link |
| `IMG_1567` | `Copia de IMG_1567.MOV` | `media/raw/videos/IMG_1567.MOV` | Active — oscillation video | https://drive.google.com/file/d/1y5dY7WYAW8NgpqkZEfVx2DWa6bo5JgIR/view?usp=drive_link |
| `IMG_1568` | `Copia de IMG_1568.MOV` | `media/raw/videos/IMG_1568.MOV` | Active — oscillation video | https://drive.google.com/file/d/1VUcrtZoA1mz7IaMXoH2-2WqOhUlgAti9/view?usp=drive_link |
| `IMG_1569` | `Copia de IMG_1569.MOV` | `media/raw/videos/IMG_1569.MOV` | Active — oscillation video | https://drive.google.com/file/d/1eZCqKr-aIibRBEc1iHHBiQ_NOTzZPzUj/view?usp=drive_link |
| `IMG_1570` | `Copia de IMG_1570.MOV` | `media/raw/videos/IMG_1570.MOV` | Commented out — measurement evidence only | https://drive.google.com/file/d/1z8ZBpSmhMwIGJEqK9fN1YptAB8TFiFXs/view?usp=drive_link |

#### Reference & Background Images (6 Files — Only `superfotograma` Active)

| Config Key | Original Drive Name | Local Target Path | Pipeline Status & Role | Google Drive URL |
|---|---|---|---|---|
| `superfotograma` | `Copia de superfotograma!.png` | `media/raw/images/superfotograma.png` | Active — shared background for subtraction | https://drive.google.com/file/d/1ShYsEFDkAN1E-0kqmVTgIDS4sPruT6MI/view?usp=drive_link |
| `fotograma_1` | `Copia de fotograma_1.png` | `media/raw/images/fotograma_1.png` | Commented out — diagnostic frame snapshot | https://drive.google.com/file/d/19to2iFrK9P6G07SkrLwqDtP1ynoblTEo/view?usp=drive_link |
| `fotograma_100` | `Copia de fotograma_100.png` | `media/raw/images/fotograma_100.png` | Commented out — diagnostic frame snapshot | https://drive.google.com/file/d/1cmgbnIxMP79ELj2D2KjGHmud2Cm2hPXd/view?usp=drive_link |
| `fotograma_200` | `Copia de fotograma_200.png` | `media/raw/images/fotograma_200.png` | Commented out — diagnostic frame snapshot | https://drive.google.com/file/d/1kbLIR8_TYcDvm7I5CpWnNd1bFPHzOj7k/view?usp=drive_link |
| `primer_fotograma_1` | `Copia de primer_fotograma.jpg` | `media/raw/images/primer_fotograma_1.jpg` | Commented out — diagnostic frame snapshot | https://drive.google.com/file/d/16lbQAkDNkBsz2YlzmPsu6qO7hV5b7YhL/view?usp=drive_link |
| `primer_fotograma_2` | `Copia de primer_fotograma.jpg` | `media/raw/images/primer_fotograma_2.jpg` | Commented out — diagnostic frame snapshot | https://drive.google.com/file/d/1lR-8Q0hvlughHIaEoo5EjQnkANZT3nHN/view?usp=drive_link |

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
├── .gitignore                             ← Ignores media/, .snakemake/, .venv/, .env, checkpoints
├── README.md                              ← Project overview, ASCII tree, setup & Snakemake commands
├── envs/
│   └── default.yaml                       ← Conda environment specification for rule portability
├── docs/
│   ├── workflow_plan.md                   ← Initial interview summary plan
│   └── workflow_plan_bis.md               ← Extended convention-compliant implementation plan
├── workflow/
│   └── schemas/
│       └── config.schema.yaml             ← JSON Schema Draft 2020-12 validating config.yaml
├── rules/                                 ← Tier 3: Modular Snakemake rule definitions (*.smk)
│   ├── common.smk                         ← Wildcard constants, parameter getters & checkpoint resolver
│   ├── 00_download.smk                    ← Parallel rules download_video & download_image (gdown)
│   ├── 01_frames.smk                      ← Checkpoint extract_frames (grey PNGs + manifest TSV)
│   ├── 02_detect.smk                      ← Rule detect_frame (parallel 1-job-per-frame centroid TXT)
│   └── 03_aggregate.smk                   ← Rule aggregate_csv (checkpoint aggregation into CSV)
├── scripts/                               ← Tier 2: Thin Snakemake adapter scripts (*.py)
│   ├── download_file.py                   ← Unpacks snakemake -> labo13.io.download_drive_file
│   ├── extract_frames.py                  ← Unpacks snakemake -> labo13.video.extract_trimmed_frames_gray
│   ├── detect_frame.py                    ← Unpacks snakemake -> labo13.detection.compute_bob_centroid
│   └── aggregate_csv.py                   ← Unpacks snakemake -> labo13.io.build_trajectories_dataframe
├── src/                                   ← Tier 1: Pure modular domain library (zero Snakemake coupling)
│   └── labo13/
│       ├── __init__.py                    ← Package exports and version
│       ├── types.py                       ← Dataclasses (FrameRecord, PendulumConstants, HarmonicFitResult)
│       ├── io.py                          ← Per-file Drive download, manifest TSV & TXT/CSV I/O
│       ├── video.py                       ← PyAV decoding, PTS time trimming & greyscale frame I/O
│       ├── detection.py                   ← Foreground segmentation & centroid extraction
│       └── physics.py                     ← Cartesian-to-polar error propagation, harmonic & ODE fits
├── tests/                                 ← Unit tests independent of Snakemake (pytest)
│   ├── test_io.py                         ← Tests TXT row formatting/parsing & CSV sorting
│   ├── test_video.py                      ← Tests integer-second trim predicates & filename formatting
│   └── test_detection.py                  ← Tests synthetic circle centroid & NaN fallback on empty frame
├── notebooks/
│   └── original/
│       └── Copia de [LABO 13] Nuevos Videos 1080.ipynb ← Original unmodified Colab notebook
├── media/                                 ← Gitignored raw media and intermediate frame artifacts
│   ├── raw/
│   │   ├── videos/                        ← Downloaded {video}.MOV files (IMG_1555..IMG_1569)
│   │   └── images/                        ← Downloaded background image (superfotograma.png)
│   └── frames/
│       └── {video}/                       ← {video}_f{index:06d}_t{seconds:.4f}.{png,txt}
└── results/
    └── trajectories.csv                   ← Final tidy table: video_name,t,x,y
```

---

## Key Targets, Rules & Output Formats

| Rule / Checkpoint | Input(s) | Output(s) | Description |
|---|---|---|---|
| `download_video` | Google Drive URL (`config.yaml`) | `media/raw/videos/{video}.MOV` | Downloads each enabled video in parallel via `gdown` |
| `download_image` | Google Drive URL (`config.yaml`) | `media/raw/images/{image_file}` | Downloads `superfotograma.png` (and any enabled image) |
| `extract_frames` *(checkpoint)* | `media/raw/videos/{video}.MOV` | `media/frames/{video}/`, `media/frames/{video}.manifest.tsv` | Extracts trimmed greyscale PNG frames `{video}_f{index:06d}_t{seconds:.4f}.png` |
| `detect_frame` | `media/frames/{video}/{stem}.png`, `media/raw/images/superfotograma.png` | `media/frames/{video}/{stem}.txt` | Runs **1 job per frame** writing a single CSV line `video_name,t,x,y` |
| `aggregate_csv` | All `media/frames/{video}/{stem}.txt` | `results/trajectories.csv` | Concatenates and sorts all per-frame detections by `(video_name, t)` |

### Output CSV Schema (`results/trajectories.csv`)

| Column | Type | Units / Origin | Description |
|---|---|---|---|
| `video_name` | `str` | — | Video identifier matching the key in `config.yaml` (e.g. `IMG_1556`) |
| `t` | `float` | seconds (`s`) | Original video presentation timestamp (PTS) of the frame (not reset to 0 when trimmed) |
| `x` | `float` | pixels (`px`) | Horizontal bob centroid coordinate (origin at top-left image corner; `NaN` if undetected) |
| `y` | `float` | pixels (`px`) | Vertical bob centroid coordinate (origin at top-left image corner; grows downward; `NaN` if undetected) |

---

## Worked Example: One Video & One Frame (Illustrative — Not Run)

The trace below shows how **one video** (`IMG_1556`) and **one frame** (frame `120` at `t = 2.0013 s`) move through the pipeline without executing it on real media.

### 1. Configure `IMG_1556` in `config.yaml`

Keep `IMG_1556` active (comment out other videos while testing) and optionally set integer-second trim bounds:

```yaml
videos:
  IMG_1556:
    file: "IMG_1556.MOV"
    url: "https://drive.google.com/file/d/1Ko_iG_jW-eF3aX8xf-cvqhTFmNtceOSE/view?usp=drive_link"
    t_start: 2
    t_end: 30
```

### 2. Targeted Snakemake Commands for One Video / One Frame

```bash
# Step A: Download only IMG_1556.MOV and superfotograma.png
uv run snakemake media/raw/videos/IMG_1556.MOV media/raw/images/superfotograma.png --cores 2

# Step B: Extract trimmed greyscale PNGs and manifest for IMG_1556
uv run snakemake media/frames/IMG_1556.manifest.tsv --cores 1

# Step C: Run detection for a single frame (1 Snakemake job)
uv run snakemake media/frames/IMG_1556/IMG_1556_f000120_t2.0013.txt --cores 1
```

### Processing an Existing Frame PNG Directly (`IMG_1555_f001371_t22.8500.png`)

In Snakemake, you always request the **output** file you want to produce, not the input `.png`. Given an extracted frame such as `media/frames/IMG_1555/IMG_1555_f001371_t22.8500.png`, its corresponding detection target is `media/frames/IMG_1555/IMG_1555_f001371_t22.8500.txt` (rule `detect_frame`):

```bash
# 1. Dry-run: verify Snakemake only schedules detect_frame (plus download_image if superfotograma.png is missing)
uv run snakemake media/frames/IMG_1555/IMG_1555_f001371_t22.8500.txt -n

# 2. Execute detection for that single frame only
uv run snakemake media/frames/IMG_1555/IMG_1555_f001371_t22.8500.txt --cores 1

# 3. Force re-running only detect_frame on that frame (e.g., after tuning thresholds in config.yaml)
uv run snakemake media/frames/IMG_1555/IMG_1555_f001371_t22.8500.txt --cores 1 --force
```

- Because `media/frames/IMG_1555/IMG_1555_f001371_t22.8500.png` already exists on disk, Snakemake resolves `detect_frame` directly from the `.png` and `media/raw/images/superfotograma.png` without re-running `extract_frames` or processing other frames.
- `--force` (`-f`) re-runs only the final target rule (`detect_frame`) for that `.txt` file, leaving upstream videos and images untouched.

### 3. Artifacts & Illustrative File Contents

| Step / Rule | Generated Artifact | Illustrative Content / Purpose |
|---|---|---|
| `download_video` | `media/raw/videos/IMG_1556.MOV` | Raw 1080p video (~59.96 fps) downloaded from Drive |
| `download_image` | `media/raw/images/superfotograma.png` | Shared static background image for subtraction |
| `extract_frames` | `media/frames/IMG_1556/IMG_1556_f000120_t2.0013.png` | 8-bit greyscale PNG for frame index `120` at PTS `2.0013 s` |
| `extract_frames` | `media/frames/IMG_1556.manifest.tsv` | Index of all extracted frames for `IMG_1556` (see below) |
| `detect_frame` | `media/frames/IMG_1556/IMG_1556_f000120_t2.0013.txt` | Single CSV row without header (see below) |
| `aggregate_csv` | `results/trajectories.csv` | Sorted table combining all `.txt` rows across active videos |
| Logs & Benchmarks | `logs/detect_frame/IMG_1556/IMG_1556_f000120_t2.0013.log`<br/>`benchmarks/detect_frame/IMG_1556/IMG_1556_f000120_t2.0013.tsv` | Per-job execution log and Snakemake runtime/memory metrics |

**Illustrative `media/frames/IMG_1556.manifest.tsv`** (tab-separated):

```tsv
video_name	frame_index	t_sec	stem	png_path
IMG_1556	120	2.0013	IMG_1556_f000120_t2.0013	media/frames/IMG_1556/IMG_1556_f000120_t2.0013.png
IMG_1556	121	2.0180	IMG_1556_f000121_t2.0180	media/frames/IMG_1556/IMG_1556_f000121_t2.0180.png
IMG_1556	122	2.0347	IMG_1556_f000122_t2.0347	media/frames/IMG_1556/IMG_1556_f000122_t2.0347.png
```

**Illustrative `media/frames/IMG_1556/IMG_1556_f000120_t2.0013.txt`** (1 row, no header):

```text
IMG_1556,2.0013,812.400000,503.100000
```

**Illustrative `results/trajectories.csv`** (showing a normal detection and an undetected `nan` frame):

```csv
video_name,t,x,y
IMG_1556,2.001300,812.400000,503.100000
IMG_1556,2.018000,814.125000,504.375000
IMG_1556,2.034700,nan,nan
```

---

## Frame Naming & Incremental Re-Runs

Every extracted frame uses the stem `{video}_f{index:06d}_t{seconds:.4f}`:

- **`{video}`**: Key from `videos:` in `config.yaml` (e.g., `IMG_1556`).
- **`f{index:06d}`**: Zero-padded 0-based frame counter in the original video stream (unchanged when `t_start` changes).
- **`t{seconds:.4f}`**: Container presentation timestamp (PTS) in seconds to 4 decimal places (falls back to `index / fps` only if PTS is absent).

Because frame filenames encode the original index and timestamp, Snakemake handles config edits incrementally:

| Change in `config.yaml` | What Snakemake Re-Runs |
|---|---|
| Expand `[t_start, t_end)` on `IMG_1556` | Re-runs `extract_frames` for `IMG_1556`, then runs `detect_frame` **only** for newly added frames |
| Adjust `threshold_low`, `threshold_high`, or `morphology_disk_radius` | Re-runs `detect_frame` and `aggregate_csv` using existing PNGs (no video re-download or re-decoding) |
| Comment out a video under `videos:` | Excludes that video from `aggregate_csv` without touching remaining videos |

---

## Troubleshooting & Operational Notes

- **Interrupted run lock (`LockException`)**: If a Snakemake execution is interrupted (`Ctrl+C`), clear the directory lock before retrying:
  ```bash
  uv run snakemake --unlock
  ```
- **Google Drive rate limiting during downloads**: All 15 `download_video` rules can run concurrently. If Google Drive throttles parallel requests, download with capped concurrency first (`uv run snakemake -j 2 --until download_video download_image`), then run `uv run snakemake --cores all` for frame extraction and detection.
- **Disk footprint & job scale**: Greyscale 1080p PNGs take roughly 0.5–1 MB per frame (~1,800 frames per 30 s video at 59.96 fps), and `detect_frame` schedules 1 job per frame. Validate trim bounds on a single video before enabling all 15.
- **Undetected frames (`nan,nan`)**: When no connected component passes the threshold window `(threshold_low, threshold_high)`, `compute_bob_centroid` writes `nan,nan` instead of guessing; downstream `labo13.physics` functions drop `NaN` rows explicitly.

---

## Configuration (`config.yaml`)

All experimental paths, detection thresholds, and per-video trim intervals are controlled exclusively through `config.yaml` (validated at startup against `workflow/schemas/config.schema.yaml`):

- **Selecting / Skipping Videos**: Comment out any video block under `videos:` in `config.yaml` to skip downloading and processing that video.
- **Manual Time Trimming (`t_start`, `t_end`)**:
  - Set `t_start` and/or `t_end` to integer seconds (e.g. `t_start: 2`, `t_end: 25`) to restrict frame extraction to $t_{\text{start}} \le t < t_{\text{end}}$.
  - Leave `null` (`t_start: null`, `t_end: null`) for no trimming.
  - Frame filenames (`{video}_f{index:06d}_t{seconds:.4f}.png`) preserve the original frame index and timestamp, so expanding a trim interval only runs `detect_frame` on newly added frames.
- **Segmentation Parameters (`parameters:`)**:
  - `threshold_low: 100.0` — lower bound on background-subtracted intensity (`background - frame`).
  - `threshold_high: 200.0` — upper bound on background-subtracted intensity.
  - `morphology_disk_radius: 2` — disk radius in pixels for `skimage.morphology.closing`.
  - `frame_batch_size: 64` — number of decoded frames buffered before parallel PNG disk flush.
  - `png_compress_level: 1` — lossless PNG zlib compression level (`0` fastest/largest – `9` slowest/smallest).

---

## Tier 1 Domain Library (`src/labo13/`)

| Module | Public Functions & Classes | Responsibility |
|---|---|---|
| `labo13.types` | `FrameRecord`, `PendulumConstants`, `HarmonicFitResult` | Frozen dataclasses for frame metadata, physical constants, and fit results |
| `labo13.io` | `download_drive_file`, `save_frame_manifest`, `load_frame_manifest`, `parse_stem_metadata`, `save_frame_detection_row`, `load_frame_detection_row`, `build_trajectories_dataframe`, `export_trajectories_csv` | Google Drive download, manifest TSV serialization, and per-frame `.txt` / `.csv` I/O |
| `labo13.video` | `is_within_time_bounds`, `format_frame_stem`, `load_image_gray`, `save_image_gray`, `load_video_frame_gray`, `plot_sampled_frames`, `extract_trimmed_frames_gray` | PyAV video decoding, integer-second PTS trimming, and greyscale PNG I/O |
| `labo13.detection` | `compute_bob_centroid` | Background subtraction, thresholding, morphological closing, and largest-region centroid |
| `labo13.physics` | `compute_polar_trajectory`, `compute_harmonic_fit`, `compute_sliding_window_periods`, `compute_ode_trajectory` | Cartesian-to-polar angle conversion with error propagation, 2-stage harmonic fit, and ODE integration |

### Library Quick-Start

```python
import labo13 as l13

frame = l13.load_image_gray("media/frames/IMG_1556/IMG_1556_f000000_t0.0000.png")
x_px, y_px = l13.compute_bob_centroid(frame, l13.load_image_gray("media/raw/images/superfotograma.png"))
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

# 2. Download and extract frames for a single video to inspect trim bounds
uv run snakemake media/frames/IMG_1555.manifest.tsv --cores 4

# 3. Run the full pipeline across all enabled videos using all CPU cores
uv run snakemake --cores all

# 4. Run code quality gates (Ruff, Mypy, Pytest)
uv run ruff check --fix src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/ tests/
uv run pytest -v
```
