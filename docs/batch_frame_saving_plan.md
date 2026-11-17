# Plan: Batched Parallel Frame Saving in `extract_frames`

## Goal Description

Downloading the raw `.MOV` videos is fast; the current bottleneck is `extract_frames`, which synchronously compresses and writes each 1080p greyscale PNG (`1920x1080`) one frame at a time on a single thread using PIL's default PNG compression level (`6`).

This change speeds up `extract_trimmed_frames_gray` by buffering decoded frames in **bounded batches** (e.g., `batch_size = 64`) and flushing each batch to disk in parallel across worker threads (PIL's C `zlib` PNG encoder releases the GIL, avoiding cross-process pickling overhead of 2 MB arrays), with configurable fast lossless PNG compression (`png_compress_level = 1`).

**No other workflow stage, rule, file path, or data format changes:**
- `00_download.smk` (`download_video`, `download_image`) — unchanged.
- `02_detect.smk` (`detect_frame` — 1 job per frame) — unchanged.
- `03_aggregate.smk` (`aggregate_csv` — `results/trajectories.csv`) — unchanged.
- Output frame naming (`media/frames/{video}/{video}_f{index:06d}_t{seconds:.4f}.png`) and manifest format (`media/frames/{video}.manifest.tsv`) — unchanged.

---

## Why Batching + Thread Pool + Compression Level Solves the Bottleneck

| Factor | Current Behavior | Proposed Change | Effect |
|---|---|---|---|
| **I/O & PNG Encoding** | Sequential single-frame `Image.save()` in decode loop | Collect `batch_size` frames (`64`), flush batch via `ThreadPoolExecutor(max_workers=workers)` | Overlaps PNG `zlib` compression + disk writes across CPU cores |
| **Memory Footprint** | 1 frame in RAM (~2 MB) | Bounded to `batch_size` frames (~128 MB for 64 × 1080p grey frames) | Prevents OOM on long videos while enabling batch parallelism |
| **PNG Compression** | PIL default `compress_level=6` | Configurable `png_compress_level: 1` (lossless, ~4–6× faster) | Same exact pixel values (`uint8` lossless), drastically lower CPU time |
| **Snakemake Scheduling** | `extract_frames` uses `threads: 1` | `threads: 4` (or `config["parameters"]["extract_threads"]`) | Snakemake budgets CPU cores cleanly across concurrent video jobs |

---

## Proposed Changes

### 1. Configuration & Schema (`config.yaml`, `workflow/schemas/config.schema.yaml`)

#### [MODIFY] [config.yaml](file:///home/aaron/bs/labo13-nuevos-videos-1080/config.yaml)
Add two optional/explicit extraction parameters under `parameters:`:
```yaml
parameters:
  background_image_key: "superfotograma"
  threshold_low: 100.0
  threshold_high: 200.0
  morphology_disk_radius: 2
  frame_batch_size: 64
  png_compress_level: 1
```

#### [MODIFY] [config.schema.yaml](file:///home/aaron/bs/labo13-nuevos-videos-1080/workflow/schemas/config.schema.yaml)
Add schema properties under `parameters.properties` (and `required:`):
- `frame_batch_size`: `type: "integer", minimum: 1`
- `png_compress_level`: `type: "integer", minimum: 0, maximum: 9`

---

### 2. Tier 1 Core Library (`src/labo13/video.py`)

#### [MODIFY] [video.py](file:///home/aaron/bs/labo13-nuevos-videos-1080/src/labo13/video.py)
1. Update `save_image_gray` to accept `compress_level: int = 1`:
   ```python
   def save_image_gray(
   	frame_gray: npt.NDArray[np.uint8],
   	output_path: Path,
   	compress_level: int = 1,
   ) -> None:
   	"""Save a 2D uint8 greyscale array as a lossless PNG."""
   	output_path.parent.mkdir(parents=True, exist_ok=True)
   	Image.fromarray(frame_gray, mode="L").save(
   		output_path, format="PNG", compress_level=compress_level
   	)
   ```
2. Add a small helper `save_frame_batch_gray` that writes a batch of `(npt.NDArray[np.uint8], Path)` pairs in parallel using `concurrent.futures.ThreadPoolExecutor`:
   ```python
   def save_frame_batch_gray(
   	batch: list[tuple[npt.NDArray[np.uint8], Path]],
   	max_workers: int = 4,
   	compress_level: int = 1,
   ) -> None:
   	"""Flush a batch of greyscale frames to disk in parallel."""
   	if not batch:
   		return
   	if max_workers <= 1 or len(batch) == 1:
   		for frame_gray, output_path in batch:
   			save_image_gray(
   				frame_gray=frame_gray,
   				output_path=output_path,
   				compress_level=compress_level,
   			)
   		return
   	with ThreadPoolExecutor(max_workers=max_workers) as executor:
   		futures = [
   			executor.submit(
   				save_image_gray,
   				frame_gray,
   				output_path,
   				compress_level,
   			)
   			for frame_gray, output_path in batch
   		]
   		for future in futures:
   			future.result()
   ```
3. Update `extract_trimmed_frames_gray` with backward-compatible default parameters (`batch_size: int = 64`, `max_workers: int = 4`, `compress_level: int = 1`):
   - Stream decoded frames from PyAV.
   - Append `(frame_gray, png_path)` to `pending_batch` and `FrameRecord` to `records`.
   - Whenever `len(pending_batch) >= batch_size`, call `save_frame_batch_gray(...)` and `pending_batch.clear()`.
   - After the decode loop exits, flush any remaining frames in `pending_batch`.

---

### 3. Tier 2 Adapter & Tier 3 Rule (`scripts/extract_frames.py`, `rules/01_frames.smk`)

#### [MODIFY] [extract_frames.py](file:///home/aaron/bs/labo13-nuevos-videos-1080/scripts/extract_frames.py)
Unpack `snakemake.params.batch_size`, `snakemake.params.compress_level`, and `snakemake.threads`, and pass them to `extract_trimmed_frames_gray`.

#### [MODIFY] [01_frames.smk](file:///home/aaron/bs/labo13-nuevos-videos-1080/rules/01_frames.smk)
Pass `batch_size = config["parameters"]["frame_batch_size"]` and `compress_level = config["parameters"]["png_compress_level"]` in `params:`, and bump `threads: 4` so each `extract_frames` job uses 4 worker threads cleanly.

---

### 4. Unit Tests & Documentation (`tests/test_video.py`, `README.md`)

#### [MODIFY] [test_video.py](file:///home/aaron/bs/labo13-nuevos-videos-1080/tests/test_video.py)
Add unit tests for:
- `save_frame_batch_gray` writing all PNGs in a batch accurately (pixel-identical round-trip via `load_image_gray`).
- `extract_trimmed_frames_gray` with `batch_size=2` on a 5-frame synthetic `.MOV` verifying full batch flushes (`2 + 2`) plus partial trailing batch flush (`1`).

#### [MODIFY] [README.md](file:///home/aaron/bs/labo13-nuevos-videos-1080/README.md)
Document `frame_batch_size` and `png_compress_level` in the Configuration section.

---

## Verification Plan

### Automated Checks (No Real Media Run)
```bash
cd /home/aaron/bs/labo13-nuevos-videos-1080
uv run ruff check --fix src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/ tests/
uv run pytest -v
uv run snakemake --lint
uv run snakemake -n
```
Plus a quick synthetic multi-frame `.MOV` test in `pytest` verifying `batch_size=2` flushes all frames identically without altering filenames, manifest TSV, or downstream `detect_frame` / `aggregate_csv`.
