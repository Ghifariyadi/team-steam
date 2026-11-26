# Richard's labeling workflow (side track)

This folder is Richard's own labeling work. It is **not** the pipeline behind the website or the final presentation.

## Why it exists

Labeling with Gemini was limited by the API: every review is one call, and the daily quota ran out before a full run could finish. Richard's workflow was built to get around that bottleneck by splitting the labeling across teammates, with one batch per person and per game, instead of one machine making every call.

The results in `outputs/gta_v_700/` show the same effect: that run saved each answer as it went and picked up again after the daily quota reset.

## What is here

| Path | What it is |
|---|---|
| `outputs/gta_v_700/` | 700 Gemini labels for GTA V (toxicity and irony), plus the prompt used and a README |
| `scripts/sample_reviews.py` | Draws a reproducible sample from a review pool (fixed seed) |
| `scripts/label_reviews.py` | Labels a sample with Gemini, saves as it goes, and can resume |
| `docs/labeling_setup.md` | Setup guide for teammates |
| `docs/sampling_1000.md` | The 1,000-reviews-per-game plan and the batch commands |

## How it differs from the main project

- Different data: a separate English review pool, not the Kaggle file `weighted_score_above_08.csv` used for the site.
- Different size: 1,000 per game planned, 700 GTA V done, versus 7,365 reviews labeled for the site.
- Labels are model predictions that have not been validated, as the `gta_v_700` README says.

## Running it

The scripts and docs keep their own layout inside this folder, so run every command from `others/richard_label/`, not from the repository root. Review text stays private: put your input files in `data/private/` and do not commit them.
