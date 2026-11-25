"""Ask Gemini which exact words make a toxic review toxic, and what type each one is.

Input: the reviews that are still toxic after the cheating re-check (read only).
Output (NEW files only):
    data/gemini_toxic_evidence_<model>.jsonl   resumable cache, one line per review
    data/gemini_toxic_evidence_<model>.csv     one row per piece of evidence, with quote_in_review (True/False)

quote_in_review checks that the quoted words really appear in the review text, so an invented quote is caught.
"""
import json
import os
import random
import re
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from google.genai import errors, types

RETRY_CODES = {429, 500, 503, 504}
TYPES = ["identity_attack", "personal_insult", "threat", "profanity", "sexual_harassment",
         "griefing_trolling", "toxic_community", "other"]
GROUPS = ["none", "ethnicity_nationality", "gender", "sexuality", "religion", "age", "disability", "other"]
TARGETS = ["teammate", "opponent", "player_general", "nationality_group", "developer", "other"]

# Plain-English names for the tables (the codes above are only what Gemini returns)
TYPE_LABELS = {
    "identity_attack": "Attack on who someone is (nationality, gender, etc.)",
    "personal_insult": "Insult at a person (skill, brain, character)",
    "threat": "Threat or wishing harm",
    "profanity": "Swearing, not aimed at anyone",
    "sexual_harassment": "Sexual harassment",
    "griefing_trolling": "Griefing or trolling",
    "toxic_community": "Toxic community in general",
    "other": "Other",
}
TARGET_LABELS = {
    "player_general": "Players in general",
    "nationality_group": "A nationality or group",
    "developer": "The developer",
    "teammate": "Teammates",
    "opponent": "Opponents",
    "other": "Other",
}
GROUP_LABELS = {
    "ethnicity_nationality": "Ethnicity or nationality",
    "gender": "Gender",
    "sexuality": "Sexuality",
    "religion": "Religion",
    "age": "Age",
    "disability": "Disability",
    "other": "Other group",
    "none": "(not an identity attack)",
}


def examples(sub, n=2, max_len=60, seed=3):
    """Pick up to n short, readable examples from a table of evidence rows.
    English quotes come first. Other languages are shown with their English meaning."""
    sub = sub[sub["quote"].str.len().between(4, max_len)].drop_duplicates("quote")
    if sub.empty:
        return ""
    eng = sub[sub["language"] == "english"]
    pick = eng.sample(min(n, len(eng)), random_state=seed) if len(eng) >= n else pd.concat(
        [eng, sub.drop(eng.index).sample(min(n - len(eng), len(sub) - len(eng)), random_state=seed)])
    out = []
    for _, r in pick.iterrows():
        out.append(f'"{r["quote"]}"' if r["language"] == "english" else f'"{r["quote"]}" ({r["meaning_en"]})')
    return "  |  ".join(out)


SCHEMA = {
    "type": "object",
    "properties": {
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quote": {"type": "string"},
                    "meaning_en": {"type": "string"},
                    "type": {"type": "string", "enum": TYPES},
                    "identity_group": {"type": "string", "enum": GROUPS},
                    "target": {"type": "string", "enum": TARGETS},
                },
                "required": ["quote", "meaning_en", "type", "identity_group", "target"],
            },
        }
    },
    "required": ["evidence"],
}


def norm(s):
    """Lowercase, unify unicode, drop zero-width characters, collapse whitespace."""
    s = unicodedata.normalize("NFKC", str(s)).lower()
    s = re.sub(r"[​‌‍﻿]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _payload(row):
    return {"game": row["game"], "review": row["review"]}


class EvidenceRun:
    def __init__(self, df, client, model, system, cache_path, temperature=0, workers=8, schema=SCHEMA, max_retries=8):
        self.df = df.reset_index(drop=True)
        self.client, self.model, self.system = client, model, system
        self.cache_path, self.temperature, self.workers = cache_path, temperature, workers
        self.schema, self.max_retries = schema, max_retries
        self.lock = threading.Lock()
        self.done = self._load()
        self.failed, self.retries = {}, 0

    def _load(self):
        out = {}
        if os.path.exists(self.cache_path):
            with open(self.cache_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        e = json.loads(line)
                        out[e["key"]] = e
        return out

    def _call(self, row):
        for attempt in range(self.max_retries):
            try:
                resp = self.client.models.generate_content(
                    model=self.model,
                    contents=json.dumps(_payload(row), ensure_ascii=False),
                    config=types.GenerateContentConfig(
                        system_instruction=self.system, temperature=self.temperature,
                        response_mime_type="application/json", response_schema=self.schema),
                )
                return json.loads(resp.text)
            except errors.APIError as e:
                if e.code not in RETRY_CODES or attempt == self.max_retries - 1:
                    raise
                with self.lock:
                    self.retries += 1
                time.sleep(min(10 * 2 ** attempt, 300) + random.uniform(0, 5))

    def _one(self, row):
        res = self._call(row)
        entry = {"key": row["key"], "evidence": res.get("evidence", []), "model": self.model}
        with self.lock:   # saved the moment it finishes
            with open(self.cache_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self.done[row["key"]] = entry
        return entry

    def start(self, show=True):
        todo = [r for _, r in self.df.iterrows() if r["key"] not in self.done]
        already = len(self.df) - len(todo)
        total, t0, n = len(todo), time.time(), 0
        print(f"{len(self.df):,} reviews in scope · {already:,} already done (skipped) · {total:,} to run now")
        if not total:
            return self
        with ThreadPoolExecutor(self.workers) as ex:
            futs = {ex.submit(self._one, r): r["key"] for r in todo}
            for f in as_completed(futs):
                n += 1
                try:
                    f.result()
                except Exception as e:   # not cached, so a re-run tries it again
                    self.failed[futs[f]] = str(e)[:200]
                if show and (n % 25 == 0 or n == total):
                    el = time.time() - t0
                    rate = n / el if el else 0
                    eta = (total - n) / rate if rate else 0
                    print(f"{n:,}/{total:,} · {rate:.1f} rev/s · ETA {int(eta // 60)}m{int(eta % 60):02d}s · retries {self.retries} · failed {len(self.failed)}")
        print(f"DONE: {n - len(self.failed):,} labeled · {len(self.failed)} failed · {int(time.time() - t0)}s")
        return self

    def export(self, out_csv):
        """One row per piece of evidence. Refuses any file that is not a toxic_evidence file."""
        assert "toxic_evidence" in os.path.basename(out_csv), "out_csv must be a new toxic_evidence file"
        rows = []
        for _, r in self.df.iterrows():
            e = self.done.get(r["key"])
            if e is None:
                continue
            for i, ev in enumerate(e["evidence"], 1):
                rows.append({"key": r["key"], "game": r["game"], "language": r.get("language"), "rank": i,
                             "quote": ev["quote"], "meaning_en": ev["meaning_en"], "type": ev["type"],
                             "identity_group": ev["identity_group"], "target": ev["target"],
                             "quote_in_review": bool(ev["quote"].strip()) and norm(ev["quote"]) in norm(r["review"]),
                             "review": r["review"]})
        out = pd.DataFrame(rows)
        out.to_csv(out_csv, index=False)
        n_rev = len(self.done)
        no_ev = sum(1 for e in self.done.values() if not e["evidence"])
        print(f"Saved {len(out):,} pieces of evidence from {n_rev:,} reviews -> {out_csv}  ({no_ev:,} reviews returned no evidence)")
        return out
