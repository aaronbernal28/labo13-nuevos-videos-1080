# LABO 13 — Simple pendulum: nonlinear behavior at large angles (1080p videos)

Video tracking of a simple pendulum to study how well the **small-angle (sinusoidal) approximation** holds as the oscillation amplitude grows.

## Links

| Resource | Link |
|---|---|
| Original Colab notebook (source of this repo) | https://colab.research.google.com/drive/1covVbCOVzjUw5jkBTUUZ00v053icBWpg?usp=sharing |
| Simple reference Colab (style example) | https://drive.google.com/file/d/1qCTrCMC7AzwTvXsJM8Y7XEThvcKkU-Gj/view?usp=sharing |
| Raw videos (Google Drive folder) | https://drive.google.com/drive/folders/10VmY2TRLvBIaaMNBjxqX4qjdgOwvmTSv?usp=sharing |

## Repository contents

| File | Description |
|---|---|
| `Copia de [LABO 13] Nuevos Videos 1080.ipynb` | Original Colab notebook, committed **unmodified** as a baseline to be cleaned. |
| `README.md` | This file. |

## Experimental setup (from the original notebook)

| Quantity | Value | Uncertainty |
|---|---|---|
| Pendulum length without base | 0.737 m | ±0.005 m |
| Pendulum length with base | 0.778 m | ±0.005 m |
| Pendulum width | 3.0 mm | ±0.2 mm (caliper) |
| Frame period | 1/59.96 s (~60 fps) | ±1 frame |

- Videos: `.MOV`, 1080p, recorded with a fixed camera.
- A background frame (a frame without the pendulum, or a median frame) is used for background subtraction.

## Objectives

### Stage 1 — Build a single tidy trajectory table (current goal)

Produce **one CSV** containing the bob position for every frame of every video:

```
video_name,t,x,y
IMG_1555.MOV,0.000000,812.4,503.1
IMG_1555.MOV,0.016678,813.0,505.7
...
```

| Column | Type | Meaning |
|---|---|---|
| `video_name` | str | Video file name (identifies the run / amplitude). |
| `t` | float, s | Time since the first analyzed frame (`frame_index / fps`). |
| `x` | float | Horizontal bob-centroid position. |
| `y` | float | Vertical bob-centroid position. |

**Requirements**
- Long (tidy) format: one row per (video, frame).
- `t` comes from the real video frame rate (≈59.96 fps), not an assumed 60.
- Frames where the bob is not detected are left out or set to `NaN` (never filled with a guess).
- Coordinates and units must be documented (pixels with image origin top-left, or meters after calibration). Keep this consistent across all videos.
- The whole table must be reproducible from the raw videos with one command / one notebook run.

> The **detection method** (background subtraction, thresholding, morphology, centroid, etc.) is to be defined by the author. This README only fixes the problem and the output format.

### Stage 2 — Amplitude-dependence analysis (final goal)

Using the CSV, for each video:

1. Find the pivot point and convert `(x, y)` → angle `θ(t)`.
2. Fit two models to `θ(t)`:
   - **Linear (small-angle):** $\ddot\theta + \gamma\dot\theta + \omega_0^2\,\theta = 0$ → damped sinusoid.
   - **Nonlinear:** $\ddot\theta + \gamma\dot\theta + \omega_0^2\,\sin\theta = 0$ (numerical integration).
3. Compare both fits (residuals, χ², estimated `g`, period).

Expected result: **the larger the initial amplitude θ₀, the worse the sinusoidal approximation**, observable as:
- growing residuals / χ² of the linear model compared to the nonlinear one;
- period growing with amplitude, approximately

$$T(\theta_0) \approx T_0\left(1 + \frac{\theta_0^2}{16} + \frac{11\,\theta_0^4}{3072} + \dots\right),\qquad T_0 = 2\pi\sqrt{L/g}.$$

Deliverables: a table per video (θ₀, T, g, χ² of each model) and plots of T vs θ₀ and residuals vs θ₀.

## Roadmap

- [x] Import the original notebook unmodified.
- [ ] Clean the notebook (remove duplicated cells, Colab-only bits, dead code).
- [ ] Stage 1: generate `trajectories.csv` (`video_name, t, x, y`).
- [ ] Stage 2: angle conversion, linear vs nonlinear fits, amplitude analysis.

## Getting the data

Download the videos from the Drive folder above into a local `videos/` directory (not tracked by git).
