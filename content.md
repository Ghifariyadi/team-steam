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

[Two or three sentences: what you studied and the main result.]

> How do literal, mixed and ironic evaluations intersect with gender stereotypes and accounts of harassment, and do reviews that describe toxic communities recommend games less?

## Question and motivation | Question

### Social-science motivation
- [Point]
- [Point]
- [Point]

### Key terms
- **[Term]:** [Definition]
- **[Term]:** [Definition]

## Data

- **Source:** KieranPoc's Kaggle Steam reviews dataset
- **Provenance:** Collected via the Steam reviews API
- **Unit of analysis:** One Steam game review
- **Coverage:** Historical English reviews (2012–2023) for Counter-Strike (including CS:GO-era), PUBG and GTA V. Pilot of 300 reviews (100 per game), drawn from a 30,462-review English hash sample with both recommendation labels. Separate supplement of 71 gender/age candidates. Separate helpful-review subset for exploratory toxicity keyword analysis.
- **Access:** Local CSV data accessed via Kaggle

### Ethical considerations
- User IDs omitted; public examples are paraphrased
- Identity claims in reviews are unverified
- Keyword matches are candidate flags, not confirmed categories or prevalence estimates

## Methods

### Preprocessing
1. [Step]
2. [Step]
3. [Step]

### Model and parameters
- [Point]
- [Point]

### Comparisons
- [Point]
- [Point]

### Validation checks
- [Point]
- [Point]

## Findings

- [Main finding]
- [Supporting finding]

![Figure 1. [Caption]](figures/figure-1.png)

| [Group] | [N] | [Estimate] | [95% CI] |
|---|---:|---:|---:|
| [ ] | [ ] | [ ] | [ ] |
| [ ] | [ ] | [ ] | [ ] |
| [ ] | [ ] | [ ] | [ ] |
Table: Table 1. [Caption]

![Figure 2. [Caption]](figures/figure-2.png)

## Interpretation

### Implications
- [Point]
- [Point]

:::note
### Limitations
- [Point]
- [Point]

### Claims the evidence does not support
- [Point]
- [Point]
:::

## Reproducibility

- **Repository:** [team-steam on GitHub](https://github.com/Ghifariyadi/team-steam)
- **Environment:** Run `uv sync --frozen` from the repository folder
- **Run order:** [Notebooks and scripts, in order]
- **Data access:** [How an authorized reader gets the data]

```
git clone https://github.com/Ghifariyadi/team-steam.git
cd team-steam
uv sync --frozen
```

## References

1. [Reference]
2. [Reference]
3. [Reference]
