# GTA V: 700 Gemini annotations

This folder contains completed model annotations, not validated human labels or final research findings.

- `gemini_labels_700.csv`: 700 unique case IDs with toxicity and irony labels, English reasons, model name, and UTC annotation timestamps.
- `prompt.txt`: the system instruction used for this run.
- Game: GTA V (Steam app ID 271590).
- Model: `gemini-3.5-flash-lite`; temperature: 0.
- Sampling: 700 reviews selected without replacement using pandas `sample(n=700, random_state=20261118)` after sorting by case ID. The sampling frame is the project's existing English review hash sample, filtered to GTA V, nonblank review text, and unique recommendation IDs, excluding the earlier 90-review pilot IDs.
- Inputs sent to Gemini: game, review text, and recommendation status. Human labels were not supplied.
- Labels: `yes`, `no`, `uncertain` for toxicity mentions and irony. The prompt includes the HW5 clarification that short text without evidence of toxicity is `no`, not automatically `uncertain`.

The original 700 review texts remain local and are not included in this public upload. Retain the local `sample_700.csv` to join annotations by `case_id`; this folder alone is not a complete reproduction package. No API key or `.env` file is included.

The run saved each response incrementally and resumed after the daily API quota reset. Human validation and analysis are still needed before reporting patterns or prevalence. A toxicity mention does not establish actual misconduct or identify the reviewer as its perpetrator.
