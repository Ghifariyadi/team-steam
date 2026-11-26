# Run Gemini labeling in your own VS Code

For the current 1,000-per-game plan and GTA 300 top-up, start with [sampling and batch commands](sampling_1000.md).

This workflow uses the same prompt, model (`gemini-3.5-flash-lite`), temperature (0), and yes/no/uncertain labels as Richard's completed GTA V 700 run. It labels toxicity and irony together. These are model predictions, not validated human labels.

## 1. Get the shared code

In GitHub Desktop, clone `Ghifariyadi/team-steam` and choose the branch `codex/shared-labeling-workflow` under Current Branch. Click Fetch origin, then Pull origin if offered. Open the whole repository in VS Code. After PR #3 is reviewed and merged, the team can instead use main.

Open Terminal > New Terminal in VS Code (at the repository root) and run:

```sh
uv sync --frozen
```

Use the course setup instructions to install uv if the command is unavailable. No extra dependencies are needed. This script runs in the terminal; a notebook kernel is not required.

## 2. Agree on game assignments and obtain private input

Assignments are not yet finalized. Choose one owner per game to avoid duplicate labeling. GTA V (271590) already has 700 completed labels; do not rerun those unless intentionally validating. Other source game IDs are 730 and 578080.

Create `data/private` in the VS Code Explorer. Obtain your assigned sample privately from Richard, save it as `data/private/my_sample.csv`. Required columns: `case_id`, `game`, `review`, `recommendation`; recommendation must be `Recommended` or `Not recommended`. Never invent or manually replace case IDs.

Alternatively, obtain `review_sample.csv` and the original pilot's `model_inputs.csv` privately from the team's full reproduction package. Put both in `data/private`. For example, to prepare game 578080 (only if assigned to you):

```sh
uv run python scripts/sample_reviews.py --pool data/private/review_sample.csv --pilot data/private/model_inputs.csv --appid 578080 --output data/private/my_sample.csv
```

This samples 1,000 without replacement using seed 20261118, excluding prior pilot IDs. It uses the team's existing English hash-sampled pool, not every Steam review. Retain the exact source pool, pilot file, game ID and command for reproducibility. The script refuses to overwrite an existing sample. Input texts are not supplied by the public result CSV.

## 3. Validate without API calls

```sh
uv run python scripts/label_reviews.py --input data/private/my_sample.csv --output-dir data/private/my_run --check-only
```

## 4. Test three new labels

```sh
uv run python scripts/label_reviews.py --input data/private/my_sample.csv --output-dir data/private/my_run --limit 3
```

Enter **your own** Gemini API key at the hidden terminal prompt; nothing appears while typing. It is not saved. An existing `GEMINI_API_KEY` environment variable is also supported. This script does not read .env. Do not paste keys into code, notebooks, GitHub or chat. Each person needs model access and available quota in their own Google project; another key for the same project may share the same quota.

Inspect `data/private/my_run/results.csv`: there should be three saved rows with labels and reasons. Confirm the input is your assigned game before the full run. Do not change the shared prompt independently.

## 5. Continue or resume

Run the same command **without** `--limit 3`:

```sh
uv run python scripts/label_reviews.py --input data/private/my_sample.csv --output-dir data/private/my_run
```

Completed IDs are skipped and each new result is saved immediately. There is a 15-second pause between requests plus API processing/retry time. Keep the computer awake. Ctrl+C stops the run; rerun the command to continue. Quota errors can stop a run before completion: retain the files and resume when quota is available. Do not change the model simply to bypass an error.

A `manifest.json` records the input hash and prompt/settings; changing them requires a separate output directory. Never run two processes into the same directory. If the computer crashes, remove `data/private/my_run/.running` **only after confirming the earlier process has stopped**. Then resume. If a saved CSV is damaged by a crash, keep a backup and ask for help before modifying it.

## 6. Return results and validate

Privately share `results.csv` and `manifest.json` with the team, with your game ID, sample size, sampling seed and input sample. Keep inputs, credentials and unreviewed outputs in ignored `data/private/`. Check `git status` before any push. The public repository contains code and approved outputs, not credentials or raw private files.

Combine games by `case_id`, check duplicates and missing labels, and report yes/no/uncertain counts separately for each game. Independently human-label a validation sample; assess per-label confusion matrices, precision/recall and agreement before interpreting model label proportions as evidence. Report the sampling frame and model errors, and retain uncertain cases separately.
