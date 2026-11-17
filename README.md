# LABO 13 — Simple Pendulum Nonlinear Behavior at Large Angles (1080p)

Reproducible 3-tier **Python + Snakemake** workflow for tracking a simple pendulum across 1080p videos and evaluating the breakdown of the small-angle sinusoidal approximation as amplitude increases.

---

## Links & Data Sources

| Resource | Link |
|---|---|
| Original Colab notebook | https://colab.research.google.com/drive/1covVbCOVzjUw5jkBTUUZ00v053icBWpg?usp=sharing |
| Reference Colab example | https://drive.google.com/file/d/1qCTrCMC7AzwTvXsJM8Y7XEThvcKkU-Gj/view?usp=sharing |
| Raw videos & images (Google Drive) | https://drive.google.com/drive/folders/10VmY2TRLvBIaaMNBjxqX4qjdgOwvmTSv?usp=sharing |

---

## Project Layout

```text
labo13-nuevos-videos-1080/
├── Snakefile                              ← Pipeline orchestration, schema validation & target rules
├── config.yaml                            ← Central parameters, per-file Drive URLs & video trim bounds
├── pyproject.toml                         ← PEP 621 package metadata, dependencies & mypy config
├── ruff.toml                              ← Ruff linter/formatter config (tab indentation, snakemake builtin)
├── .env.example                           ← Template for optional environment variables (never commit .env)
├── .gitignore                             ← Ignores media/, .snakemake/, .venv/, .env, checkpoints
├── README.md                              ← Project overview, ASCII tree, setup & Snakemake commands
├── docs/
│   ├── workflow_plan.md                   ← Initial interview summary plan
│   └── workflow_plan_bis.md               ← Extended convention-compliant implementation plan
├── workflow/
│   └── schemas/
│       └── config.schema.yaml             ← JSON Schema Draft 2020-12 validating config.yaml
├── rules/                                 ← Tier 3: Modular Snakemake rule definitions (*.smk)
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
│       ├── types.py                       ← Dataclasses (FrameRecord, PendulumConstants) & type aliases
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

## Environment Setup

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

---

## Library Quick-Start

```python
import labo13 as l13

frame = l13.load_image_gray("media/frames/IMG_1556/IMG_1556_f000000_t0.0000.png")
x_px, y_px = l13.compute_bob_centroid(frame, l13.load_image_gray("media/raw/images/superfotograma.png"))
```

---

## Pipeline Execution

```bash
# Validate workflow linting and inspect dry-run DAG
uv run snakemake --lint
uv run snakemake -n

# Execute pipeline across all CPU cores
uv run snakemake --cores all
```
