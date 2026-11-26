# Irony and toxicity in Steam reviews

Final project for COMPSS 211A (UC Berkeley). Website: **https://ghifariyadi.github.io/team-steam/**

## Project overview

- **Research question:** How often do Steam reviews of Counter-Strike 2, PUBG and GTA V mention toxicity or use irony, and can Gemini label them reliably from a written codebook?
- **Team members:** Richard, Josh, Ghif
- **Unit of analysis:** One Steam game review
- **Data source:** KieranPoc's Kaggle Steam reviews dataset (`weighted_score_above_08.csv`), loaded with `kagglehub`. We keep three games: 7,365 reviews (7,363 have text and get a label). About 80% are not in English.
- **Main result:** Gemini flags toxicity in **22.7%** of the reviews (after a rule that cheating complaints alone are not toxic) and irony in **25.0%**. Our first pass, without that rule, gave 47.5% for toxicity, and most of those were complaints about cheaters. Counter-Strike 2 has the most irony (32.9%).
- **Important limitation:** These are Gemini's labels. We checked the codebook with two human annotators on a 90-review pilot (Cohen's kappa 0.845 for toxicity, 0.903 for irony), but we have not checked the full-run labels against humans, and not at all on non-English reviews. The cheating rule was written after we saw the first-pass results.

## Start here

Needs [`uv`](https://docs.astral.sh/uv/) and Python 3.13.

```bash
uv sync --frozen
```

Then select the `.venv` environment as the Python interpreter and notebook kernel in VS Code.

Copy `.env.example` to `.env` and fill in one of the two backends:

- **AI Studio:** `GEMINI_API_KEY=...`
- **Vertex AI:** see **[docs/vertex-ai-setup.md](docs/vertex-ai-setup.md)** for the step-by-step setup.

Never commit `.env`.

## What goes where

```text
.
├── README.md        this file
├── index.html       the project website (GitHub Pages): the summary page, text and numbers are written in the file
├── details.html     full details and backup page (every number, rule and caveat)
├── alt.html         the alternative site; it reads content.md and renders it
├── content.md       the text of alt.html; editing it does not change index.html
├── notebooks/       analysis, in run order (below)
├── scripts/         labeling code the notebooks call
├── prompts/         the codebook and the cheating rule sent to Gemini
├── data/            human labels, Gemini labels and caches
├── docs/            setup notes (Vertex AI)
├── pyproject.toml   Python and package requirements
└── uv.lock          exact versions
```

## Run order

1. `notebooks/kappa_test.ipynb` measures how well the two human annotators agree on the 90-review pilot (`data/blind_labelling_annotator_1.csv` and `_2.csv`).
2. `notebooks/scale_up.ipynb` loads the dataset, tests Gemini on 10 reviews, and labels all reviews (first pass). Its last cells add the toxicity re-label summary. Output: `data/gemini_labels_gemini-3.5-flash-lite.csv`. Every finished label is cached in `data/gemini_full_*.jsonl`, so a re-run skips what is saved and costs nothing.
3. `notebooks/harm_recheck.ipynb` re-asks Gemini about the 3,499 reviews labeled toxic, with the full codebook plus the cheating rule (`prompts/cheating_rule.txt`). Output: `data/gemini_harm_recheck_gemini-3.5-flash-lite.csv` and `.jsonl`. It does not change the first-pass files. Set `SAMPLE = 100` for a quick test, `None` for all.
4. The website numbers come from the two CSVs above and are written into `index.html`, `details.html` and `content.md`.

Scripts: `scripts/steam_labeling.py` runs the labeling (parallel requests, retries, cache). `scripts/harm_recheck.py` runs the toxicity re-check.

### Prompts

- `prompts/codebook_exact.txt` is the system prompt for the first pass.
- `prompts/cheating_rule.txt` is added after the full codebook in the second pass. The codebook itself is unchanged.

## Data and privacy

- **Source and access method:** Kaggle dataset above, collected from the Steam reviews API, loaded with `kagglehub`.
- **Coverage:** Counter-Strike 2 (3,017), PUBG: BATTLEGROUNDS (2,404), Grand Theft Auto V (1,944).
- **What is committed:** the human pilot labels and Gemini's labels (review text, labels and short reasons). User IDs are not included.
- **What stays out of GitHub:** `.env`, API keys, Google Cloud credentials, anything in `data/raw/` or `data/private/`.
- **How to rebuild the data:** run `scale_up.ipynb`. It downloads the Kaggle file itself.
- A yes label means the review text says it, not that the reviewer did it or that the event happened.

## Results and interpretation

| Game | Reviews | Toxicity, first pass | Toxicity, with cheating rule | Irony |
|---|---:|---:|---:|---:|
| Counter-Strike 2 | 3,017 | 49.9% | 27.9% | 32.9% |
| Grand Theft Auto V | 1,944 | 39.7% | 16.8% | 19.7% |
| PUBG: BATTLEGROUNDS | 2,402 | 50.9% | 20.8% | 19.4% |
| All three | 7,363 | 47.5% | 22.7% | 25.0% |

- **Evidence:** `notebooks/scale_up.ipynb` and `notebooks/harm_recheck.ipynb`.
- **Validation:** Two annotators labeled 90 reviews blind (kappa above). Gemini matched the human label on 9 of 10 trial reviews for toxicity and 10 of 10 for irony, but those were all human-positive cases and the codebook was tuned on them, so this is a best case, not an accuracy estimate.
- **Strongest claim supported:** On these three games, with this codebook and rule, Gemini labels about a fifth of reviews as toxic and a quarter as ironic.
- **Claim not supported:** That Gemini is accurate on non-English reviews, or that 22.7% describes Steam as a whole.

## Final project website

The site is `index.html` (the summary) and `details.html` (the full details). Their text and numbers are written directly in the files, so to change them edit the HTML and push to `main`. If a number changes, update it in both files. The alternative version, `alt.html`, reads `content.md` and renders it, so editing `content.md` only changes that page. GitHub Pages updates in 1 to 2 minutes. The site is public, so do not put restricted data or credentials in any of these files.

## Before submitting

- [ ] Every teammate can clone and open the repository.
- [ ] `uv sync --frozen` creates the supported environment.
- [x] The README gives the actual run order.
- [ ] Important notebooks run from top to bottom in a fresh kernel.
- [ ] Scripts can be run from the repository folder with their documented command.
- [ ] The website includes the required research, evidence, interpretation, limitation, reproducibility, and reference sections.
- [ ] Figures and reported values match the notebooks and scripts.
- [ ] The GitHub Pages URL works in a signed-out browser.
- [ ] A PDF snapshot of the website is ready as a presentation backup.
- [x] The data source, exclusions, and sharing limits are documented.
- [ ] No credentials, restricted data, or accidental large files are present.
- [ ] The final contribution of each team member is recorded.

### Project to-do

- [ ] Check Gemini against a human on a random sample of the full run, including non-English reviews.
- [ ] Decide whether to keep or drop the gender and age label (the website still mentions it in the question and the intro).
- [ ] Have a teammate read the 161 non-cheating reviews that changed in the re-check (see `data/gemini_harm_recheck_*.csv`, where `harm_mention_v2` is `no` and the review does not mention cheating).
