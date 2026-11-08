---
layout: default
title: "Irony, gender and toxicity in Steam reviews"
---

<!--
This website is public. Do not include private data, credentials, identifying
information, or material that you do not have permission to share.
-->

# Irony, gender and toxicity in Steam reviews

**Team:** Richard, Josh, Ghif

[In two or three sentences, state what you studied and the main result.]

## Research question and motivation

**Research question:** How do literal, mixed and ironic evaluations intersect with gender stereotypes and accounts of harassment, and do reviews that describe toxic communities recommend games less?

[Explain why the question matters for social science. Define important terms
and give readers enough context to understand the project.]

## Data

- **Source:** KieranPoc’s Kaggle Steam reviews dataset, collected via the Steam reviews API.
- **Unit of analysis:** One Steam game review.
- **Coverage:** Historical English reviews (2012–2023) for Counter-Strike (including CS:GO-era reviews), PUBG, and GTA V. Pilot of 300 reviews (100 per game), drawn from a 30,462-review English hash sample, including both recommendation labels. Separate supplement of 71 gender/age candidates. A separate helpful-review subset was used for exploratory toxicity keyword analysis.
- **Access and ethics:** Local CSV data accessed via Kaggle. Omit user IDs and paraphrase public examples; identity claims remain unverified. Keyword matches are candidate flags, not confirmed categories or prevalence estimates.

[Describe important collection and cleaning decisions. Do not publish private
or restricted data.]

## Methods

[Explain the analysis in plain language. Name important preprocessing steps,
models, parameters, comparisons, and validation checks. Link to the relevant
notebooks or scripts in the repository.]

## Findings

### Finding 1: [Descriptive title]

[Add a readable figure or table and explain what it shows. Include units,
sample sizes, or evaluation metrics when relevant.]

### Finding 2: [Descriptive title]

[Add another result only if it helps answer the research question.]

## Interpretation and limitations

- **Strongest claim supported:** [What can you conclude from the evidence?]
- **Claim not supported:** [What tempting conclusion should readers avoid?]
- **Important limitations:** [Where can the data or method fail?]
- **Social-science implications:** [Why do the findings matter in context?]

## Reproducibility

- **Repository:** [Link to the project repository.]
- **Environment:** Run `uv sync --frozen` from the repository folder.
- **Run order:** [List the notebooks and scripts in the order a reader should
  run them, or link to the complete run order in the README.]
- **Data access:** [Explain how an authorized reader can obtain or reconstruct
  the data.]

## References

[List data sources, research literature, software, and other material cited on
this page. Include links where appropriate.]
