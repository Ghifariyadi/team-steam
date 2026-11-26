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
- Each "## Section" is one short paragraph, then a "More details" button.
  Put the long text in a block that starts with three colons and the word more, and ends with three colons.
  Inside it, use a numbered list (1. 2. 3.) with one longer paragraph per item.
- Anything in a comment like this one is hidden on the website.
-->

# Irony and toxicity in Steam reviews

Richard, Josh, Ghif

We label 7,365 Steam reviews of Counter-Strike 2, PUBG and GTA V for toxicity mentions, irony, and references to gender or age. Gemini does the labeling from a written codebook, and two human annotators check the codebook first.


> How do literal, mixed and ironic evaluations intersect with gender stereotypes and accounts of harassment, and do reviews that describe toxic communities recommend games less?

## Question and motivation | Question

Steam reviews are a public record of how multiplayer games feel to play: players use them to report harassment, cheating and toxic communities. Irony can flip what a review says, so we ask how toxicity and irony show up in 7,365 reviews of Counter-Strike 2, PUBG and GTA V, and whether the toxic ones recommend the game less.

:::more More details
1. Players use game reviews to report harassment, cheating and toxic communities, so reviews are a public record of how multiplayer spaces feel to the people in them.
2. Irony and sarcasm can reverse what a review says. A "10/10" can be a complaint, so a recommendation and its text do not always agree.
3. Gender and age references show up in reviews as stereotypes, exclusion and self-description. They are what players say about themselves, and nobody verifies them.
4. **Toxicity mention (`harm_mention`):** The review reports, condemns, endorses or expresses insults, threats, discrimination, deliberate disruption or a toxic community. A cheating complaint counts only when it also has one of these. Bugs, pricing complaints and profanity alone do not count.
5. **Irony (`irony`):** A supported ironic reading, including sarcasm: the literal evaluation contrasts with the intended one, or a described outcome mismatches the expectation. Humor or exaggeration alone does not count.
:::

## Data and methods | Data & methods

We use 7,365 public Steam reviews of three games, about 80% of them not in English. Gemini labels each review from a written codebook. The toxic ones get a second check with one added rule, that cheating alone is not toxic, and two humans labeled a 90-review pilot to test the codebook.

:::demo pipeline

:::more More details
1. **Data.** KieranPoc's Kaggle Steam reviews dataset (`weighted_score_above_08.csv`), collected through the Steam reviews API and loaded with `kagglehub`. Each row is one review. We keep three games: Counter-Strike 2 (3,017), PUBG: BATTLEGROUNDS (2,404) and Grand Theft Auto V (1,944), 7,365 reviews in total. About 80% are not in English: Simplified Chinese 2,304, English 1,457, Russian 1,068, Turkish 564, Brazilian Portuguese 406 and Korean 329.
2. **Preparation.** Each review stays in its original language, and labels come from the original text, never from a translation. Empty reviews are skipped (2 of them) instead of getting an invented label. For readers, non-English reviews are also translated into English in a separate column (`translation_en`), and that translation is never sent for labeling.
3. **First pass: labeling.** `gemini-3.5-flash-lite` through Vertex AI at temperature 0. The project codebook is the system prompt, and each review goes in its own request with its game and its Recommended / Not recommended flag. The answer is structured JSON: `harm_mention`, `irony` and `gender_age`, each with a short English reason. The run uses 8 parallel requests, retries on temporary Google errors, and saves every finished label right away, so a re-run skips what is already done.
4. **Second pass: the cheating rule.** The 3,499 reviews labeled toxic in the first pass go back to Gemini with the full codebook plus one added rule, that a cheating complaint alone is not toxicity. Reviews first labeled no are not re-asked, since a narrower rule can only turn a yes into a no. The first-pass labels are kept unchanged and the second pass is saved in separate files.
5. **Third pass: the toxic words.** On the 1,669 reviews still toxic, Gemini quotes up to 3 exact words or phrases that make the review toxic, and gives each a type (insult, identity attack, threat, swearing, sexual harassment, griefing or trolling, toxic community, other), the identity group if it is an identity attack, and who it is aimed at. The types follow common schemes: the Perspective API attributes, Risch and Krestel (2020), and the Fair Play Alliance and ADL framework for online games (2020). A quote counts only if it appears word for word in the review: 96.2% did, and the rest are left out. 1,620 reviews got at least one quote; 49 got none (7 requests failed and the others returned no quote). This pass is saved in separate files too.
6. **Human pilot.** 90 reviews (30 per game), labeled blind by two annotators, with about 10% positive cases. Only 1 of the 90 is not in English. We measured Cohen's kappa between the two annotators to see whether the codebook can be applied the same way by different people.
7. **Trial and next check.** A 10-review trial gave Gemini only reviews where a human had marked toxicity or irony as yes, then compared its labels with the human ones. The next check is a stratified sample of non-English reviews, labeled by a human who reads the language, to test Gemini outside English.
8. **Ethics.** User IDs are left out and only short public review text is shown as examples. Identity claims in reviews are unverified. A yes label means the text says it, not that the reviewer did it or that the event happened.

:::demo labeling

:::demo stats
:::

## Findings

Gemini flagged toxicity in 22.7% of the 7,363 labeled reviews and irony in 25.0%. Counter-Strike 2 has the most of both. Most toxic reviews insult other players, and reviews that do not recommend the game are toxic more often.

:::demo results

:::demo toxic

:::more More details
1. **Gemini labeled every review.** 7,363 of the 7,365 reviews got a label with no failures. The other 2 were empty and skipped. The run took 46 minutes.
2. **Gemini flagged toxicity in 22.7% of the reviews and irony in 25.0%** (1,669 and 1,843 of 7,363). Our first pass flagged toxicity in 47.5% (3,499 reviews), but most of those only complained about cheaters or hackers. We then added one rule to the codebook, that cheating alone is not toxic, and Gemini re-checked those 3,499 reviews. Cheating counts only when the review also has insults, slurs, nationality stereotypes, threats, harassment or deliberate disruption. The re-check turned 1,829 of the 3,499 to no and left 1,669 as yes, and 1 as uncertain. About 1,670 of those changes were reviews that mention cheating. The other 161 were reviews without cheating that Gemini no longer counted as toxic on the second look, often single-word or joke reviews. Irony was not re-checked. Uncertain answers were rare in the first pass: 12 for toxicity and 96 for irony.
3. **Counter-Strike 2 has the most irony.** 32.9% of its reviews are labeled ironic, against about 19% for GTA V and PUBG. On toxicity with the cheating rule, Counter-Strike 2 is highest (27.9%), then PUBG (20.8%) and GTA V (16.8%). The first pass put PUBG and Counter-Strike 2 level near 50%, so the cheating rule moved PUBG the most.
4. **Reviews that do not recommend the game are flagged for toxicity more often:** 28.4% of the 2,369 "Not recommended" reviews, against 19.9% of the 4,994 "Recommended" ones. In the first pass the gap was larger (65.3% against 39.1%). This is an association between Gemini's labels and the recommendation flag, not evidence of cause.
5. **These labels are Gemini's, and they are not checked against humans on this data yet.** The human pilot reviews are much shorter (median 28 characters, against 137 in the full data) and only 9 of the 90 appear in the 7,365, so the pilot's 10% toxicity rate cannot be compared with the full-run rate.
6. **Human agreement on the pilot is high.** Toxicity kappa is 0.845 and irony kappa is 0.903. This was measured before the cheating rule was added.
7. **Gemini matched the human label on 9 of 10 trial reviews for toxicity and on 10 of 10 for irony.** The trial reviews were all human-positive and the codebook was tuned on the same cases, so this is a best case and not an accuracy estimate.

| Game | Reviews labeled | Toxicity yes, first pass | Toxicity yes, with cheating rule | Irony yes |
|---|---:|---:|---:|---:|
| Counter-Strike 2 | 3,017 | 1,505 (49.9%) | 843 (27.9%) | 993 (32.9%) |
| Grand Theft Auto V | 1,944 | 772 (39.7%) | 326 (16.8%) | 383 (19.7%) |
| PUBG: BATTLEGROUNDS | 2,402 | 1,222 (50.9%) | 500 (20.8%) | 467 (19.4%) |
| All three | 7,363 | 3,499 (47.5%) | 1,669 (22.7%) | 1,843 (25.0%) |
Table: Table 1. Gemini's labels by game. "Yes" counts only yes answers, not uncertain ones.

| Check | N | Agreement | Cohen's kappa |
|---|---:|---:|---:|
| Human vs human, toxicity | 89 | 97.8% | 0.845 |
| Human vs human, irony | 83 | 98.8% | 0.903 |
Table: Table 2. Agreement between the two human annotators on the pilot reviews both labeled.
:::

## Interpretation and conclusions | Interpretation

A written codebook lets an LLM label thousands of reviews and give a reason for each, so the labels can be audited one by one. But how we define toxicity changes the answer more than the model does: one extra rule moved the rate from 47.5% to 22.7%. Reviews that do not recommend a game are toxic more often, which is an association, not a cause.

:::more More details
1. **Conclusion.** A written codebook with structured output gives every label a reason, so the labels can be checked one by one. Finished labels are saved as they arrive, so the full run can be paused, resumed and re-checked without paying twice.
2. **Definitions matter.** One extra rule (cheating alone is not toxic) cut the toxicity rate from 47.5% to 22.7%, so the definition changes the result more than the choice of model.
3. **Toxic communities and recommendations.** Reviews that do not recommend the game are toxic more often (28.4% against 19.9%). Reviewers who dislike a game may also be more likely to complain about other players, so this is a link and not a cause.
4. **Not supported: accuracy outside English.** That Gemini is accurate on non-English reviews. That has not been tested yet.
5. That 22.7% of Steam reviews mention toxicity. That is Gemini's rate on these three games, and it has not been validated. It depends on the cheating rule: the first pass without it gave 47.5%.
6. How common toxicity, irony or gender talk is on Steam in general.
7. That toxic communities cause fewer recommendations. Any link between labels and recommendations is an association.
:::

## Limitations

These are Gemini's labels and we have not checked them against humans on this data. About 80% of the reviews are not in English and the codebook was only tested on English. The cheating rule was written after we saw the first results, and we cover only three games.

:::more More details
1. The pilot is small (90 reviews, about 10% positive), so the kappa values are rough.
2. The codebook was checked almost only on English reviews, but about 80% of the data is not English.
3. The Gemini trial used only human-positive reviews and the codebook was tuned on the same cases.
4. The quoted phrases and their types are Gemini's own explanation, not proof of why it decided, and we have not yet checked them against a human (a 30-row spot-check file is ready). 185 reviews (11%) have toxic words aimed only at the developer, which the cheating rule says is not enough on its own, so some of them are probably false positives.
5. The cheating rule was written after we saw the first-pass results, to fit how we want to define toxicity. It changes what the toxicity label means, and we have not checked it against humans.
6. The full-run labels come from Gemini alone. We have not yet compared them with humans on a random sample of these reviews.
7. Labels describe what the text says. They do not verify behavior, identity or events.
8. Three games only, so the results do not cover Steam as a whole.
:::

## Appendix

The code, data files and run instructions are in the GitHub repository, and the notebooks run in the order listed below.

:::more More details
1. **Repository:** [team-steam on GitHub](https://github.com/Ghifariyadi/team-steam)
2. **Environment:** run `uv sync --frozen` from the repository folder.
3. **Run order:** `notebooks/kappa_test.ipynb` (human agreement), then `notebooks/scale_up.ipynb` (10-review trial, then the full run; the plumbing is in `scripts/steam_labeling.py`), then `notebooks/harm_recheck.ipynb` (the cheating rule) and `notebooks/toxic_evidence.ipynb` (the toxic words).
4. **Data access:** the dataset downloads through `kagglehub`. The Gemini calls need your own Google Cloud (Vertex AI) or Gemini API access, set in a local `.env` file that is not committed.

```
git clone https://github.com/Ghifariyadi/team-steam.git
cd team-steam
uv sync --frozen
```

**References**

1. Kowert, R. (2020). Dark participation in games.
2. Van Hee, C., Lefever, E., and Hoste, V. (2018). SemEval-2018 Task 3: Irony detection in English tweets.
3. KieranPoc. Steam reviews dataset, Kaggle.
:::
