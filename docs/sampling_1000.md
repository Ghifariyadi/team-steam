# Three games, 1,000 reviews each

Use branch `codex/shared-labeling-workflow` until PR #3 is reviewed and merged. In GitHub Desktop: select the branch, Fetch origin, Pull origin if offered, then Open in Visual Studio Code. In the repository terminal run `uv sync --frozen`.

## Easiest route: use the prepared private samples

Richard has prepared these files using the script below. Agree who owns CS:GO and PUBG before starting; game assignments do not require any code edits.

- GTA V: retain the completed 700 results and label only `gta_v_additional_300.csv`.
- CS:GO: `csgo_1000.csv`.
- PUBG: `pubg_1000.csv`.

Each teammate receives their sample privately and puts it in `data/private/`. These contain review text; do not upload them to the public repository. The combined GTA 1,000 input is for analysis, not for rerunning the original 700.

Example for PUBG (replace `pubg_1000` with `csgo_1000` or `gta_v_additional_300` for the other batches):

```sh
uv run python scripts/label_reviews.py --input data/private/pubg_1000.csv --output-dir data/private/pubg_run --check-only
uv run python scripts/label_reviews.py --input data/private/pubg_1000.csv --output-dir data/private/pubg_run --limit 3
uv run python scripts/label_reviews.py --input data/private/pubg_1000.csv --output-dir data/private/pubg_run
```

Enter your own API key at the hidden prompt each time (or set GEMINI_API_KEY in your environment). The third command resumes after the first three saved labels. Use a separate output directory for each batch, especially the GTA additional 300: do not put them in the old 700 output directory. Do not change the shared model or prompt. See [full setup and troubleshooting](labeling_setup.md).

Privately return your `results.csv`, `manifest.json`, and sample CSV to the team. Keep game/batch folder names when sharing: all runs have a file named results.csv. For GTA analysis, concatenate the old 700 and new 300 result files by case_id and verify 1,000 unique IDs; keep the original manifests alongside them.

## Reproduce the sampling yourself

Obtain the same `review_sample.csv` pool and original 90-row `model_inputs.csv` privately. Place them in `data/private`. These are the existing English hash-sampled review pool and pilot IDs, not the entire Steam population. Commands run from the repository root:

```sh
uv run python scripts/sample_reviews.py --pool data/private/review_sample.csv --pilot data/private/model_inputs.csv --appid 730 --n 1000 --output data/private/csgo_1000.csv
uv run python scripts/sample_reviews.py --pool data/private/review_sample.csv --pilot data/private/model_inputs.csv --appid 578080 --n 1000 --output data/private/pubg_1000.csv
```

For GTA, also copy the original `sample_700.csv` to `data/private`:

```sh
uv run python scripts/sample_reviews.py --pool data/private/review_sample.csv --pilot data/private/model_inputs.csv --appid 271590 --n 300 --exclude data/private/sample_700.csv --output data/private/gta_v_additional_300.csv
```

The script filters the game, removes blank reviews and duplicate recommendation IDs, excludes pilot IDs and any explicitly supplied prior sample, sorts by case_id and samples without replacement with seed 20261118. It checks that enough eligible rows remain and refuses to overwrite files. An adjacent `.manifest.json` records game, sample size, seed, eligible count and source/exclusion/sample hashes. Do not resample based on the labels you see.

Keep the existing GTA 700 input and output unchanged. The extra 300 are drawn from the remaining eligible pool; no previous labeling needs to be discarded or repeated.
