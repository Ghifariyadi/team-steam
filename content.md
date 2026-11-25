<!--
HOW TO EDIT THIS FILE (the website reads it automatically)

- Edit on GitHub (pencil icon) or locally, then commit to main. The site updates in 1-2 minutes.
- Keep the "## Section" headings: each one becomes a section on the page.
  Optional short name for the bottom menu: "## Question and motivation | Question".
- Write the way you would in a normal doc:
    - bullet points
    **bold**   *italic*   [link text](https://example.com)
    ### Smaller heading
- "- **Label:** text" bullets turn into a neat label/value list.
- Figures:  ![Figure 1. Caption](figures/figure-1.png)
  Put the image file in a "figures" folder. No image yet? It shows a placeholder box.
- Tables:   | A | B |   then   |---|---:|   then rows.  Add a line "Table: caption" right under it.
- A highlighted box:   :::note   ...text...   :::
- Do not publish private data, credentials, or identifying information.
- Anything in a comment like this one is hidden on the website.
-->

# Irony, gender and toxicity in Steam reviews

Richard, Josh, Ghif

We label 7,365 Steam reviews of Counter-Strike 2, PUBG and GTA V for toxicity mentions, irony, and references to gender or age. Gemini does the labeling from a written codebook, and two human annotators check the codebook first. The full run is still in progress, so this page reports the design and the validation so far, not final results.

:::demo labeling

:::demo stats

> How do literal, mixed and ironic evaluations intersect with gender stereotypes and accounts of harassment, and do reviews that describe toxic communities recommend games less?

## Question and motivation | Question

### Social-science motivation
- Players use game reviews to report harassment, cheating and toxic communities, so reviews are a public record of how multiplayer spaces feel to the people in them.
- Irony and sarcasm can reverse what a review says. A "10/10" can be a complaint, so a recommendation and its text do not always agree.
- Gender and age references show up in reviews as stereotypes, exclusion and self-description. They are what players say about themselves, and nobody verifies them.

### Key terms
- **Toxicity mention (`harm_mention`):** The review reports, condemns, endorses or expresses insults, threats, discrimination, deliberate disruption, explicit cheating complaints or a toxic community. Bugs, pricing complaints and profanity alone do not count.
- **Irony (`irony`):** A supported ironic reading, including sarcasm: the literal evaluation contrasts with the intended one, or a described outcome mismatches the expectation. Humor or exaggeration alone does not count.
- **Gender or age (`gender_age`):** An explicit reference to gender or age, including stereotypes, discrimination or self-identification. Identity is never inferred from names, playtime or writing style.

## Data

- **Source:** KieranPoc's Kaggle Steam reviews dataset (`weighted_score_above_08.csv`)
- **Provenance:** Collected via the Steam reviews API
- **Unit of analysis:** One Steam game review
- **Coverage:** 7,365 reviews: Counter-Strike 2 (3,017), PUBG: BATTLEGROUNDS (2,404) and Grand Theft Auto V (1,944). About 80% of them are not in English: Simplified Chinese 2,304, English 1,457, Russian 1,068, Turkish 564, Brazilian Portuguese 406, Korean 329, Spanish 323, German 192, Polish 155, Traditional Chinese 145, other languages about 420.
- **Human-labeled pilot:** 90 reviews (30 per game), labeled blind by two annotators. About 10% were positive cases. Almost all pilot reviews were in English (1 of 90 was not).
- **Access:** Loaded with `kagglehub`; the two annotator files are in `data/`

### Ethical considerations
- User IDs omitted; only short public review text is shown as examples
- Identity claims in reviews are unverified
- A yes label means the text says it, not that the reviewer did it or that the event happened

## Methods

### Preprocessing
1. Load the dataset and keep the three games (7,365 reviews).
2. Keep each review in its original language. Labels come from the original text, never from a translation.
3. Skip empty reviews instead of inventing a label for them.
4. For readers, translate non-English reviews to English into a separate column (`translation_en`). The translation is never sent for labeling.

### Model and parameters
- Model: `gemini-3.5-flash-lite` through Vertex AI, temperature 0.
- The project codebook is the system prompt. Each review goes in a separate request with its game and its Recommended / Not recommended flag.
- Output is structured JSON: `harm_mention` (yes, no, uncertain), `irony` (yes, no, uncertain), `gender_age` (none, gender, age, both, uncertain), and a short English reason for each.
- The run uses 8 parallel requests, retries on temporary Google errors (429, 500, 503, 504) with backoff, and saves every finished label right away. A re-run skips what is already saved.

### Comparisons
- Gemini labels against the human annotators on the pilot cases.
- Label shares by game once the full run finishes.
- Label shares and agreement by language, because the codebook was tested on English first.

### Validation checks
- Two annotators labeled the 90-review pilot blind, and we measured Cohen's kappa between them.
- A 10-review trial gave Gemini only reviews where a human had marked toxicity or irony as yes, then compared its labels with the human ones.
- Next: a stratified sample of non-English reviews, labeled by a human who reads the language, to check Gemini outside English.

## Findings

- **Human agreement on the pilot is high.** Toxicity kappa is 0.845 and irony kappa is 0.903.
- **Gemini matched the human label on 9 of 10 trial reviews for toxicity and on 10 of 10 for irony.** The trial reviews were all human-positive and the codebook was tuned on the same cases, so this is a best case and not an accuracy estimate.
- **The full 7,365-review run is not finished.** Label shares by game and language will be added when it is.

| Check | N | Agreement | Cohen's kappa |
|---|---:|---:|---:|
| Human vs human, toxicity | 89 | 97.8% | 0.845 |
| Human vs human, irony | 83 | 98.8% | 0.903 |
| Gemini vs human, toxicity (trial) | 10 | 90% | not computed |
| Gemini vs human, irony (trial) | 10 | 100% | not computed |
Table: Table 1. Agreement checks so far. Human pairs count the pilot reviews both annotators labeled. The Gemini trial is a non-random sample.

## Interpretation

### Implications
- A written codebook plus structured output makes every label come with a reason, so the labels can be audited one by one.
- Because finished labels are saved as they arrive and a re-run only fills the gaps, the full run can be paused, resumed and re-checked without paying twice.

:::note
### Limitations
- The pilot is small (90 reviews, about 10% positive), so the kappa values are rough.
- The codebook was checked almost only on English reviews, but about 80% of the data is not English.
- The Gemini trial used only human-positive reviews and the codebook was tuned on the same cases.
- Labels describe what the text says. They do not verify behavior, identity or events.
- Three games only, so the results do not cover Steam as a whole.

### Claims the evidence does not support
- That Gemini is accurate on non-English reviews. That has not been tested yet.
- How common toxicity, irony or gender talk is on Steam in general.
- That toxic communities cause fewer recommendations. Any link between labels and recommendations is an association.
:::

## Reproducibility

- **Repository:** [team-steam on GitHub](https://github.com/Ghifariyadi/team-steam)
- **Environment:** Run `uv sync --frozen` from the repository folder
- **Run order:** `notebooks/kappa_test.ipynb` (human agreement), then `notebooks/scale_up.ipynb` (10-review trial, then the full run; the plumbing is in `scripts/steam_labeling.py`)
- **Data access:** The dataset downloads through `kagglehub`. The Gemini calls need your own Google Cloud (Vertex AI) or Gemini API access, set in a local `.env` file that is not committed.

```
git clone https://github.com/Ghifariyadi/team-steam.git
cd team-steam
uv sync --frozen
```

## References

1. Kowert, R. (2020). Dark participation in games.
2. Van Hee, C., Lefever, E., and Hoste, V. (2018). SemEval-2018 Task 3: Irony detection in English tweets.
3. KieranPoc. Steam reviews dataset, Kaggle.
