"""Second pass on the toxic reviews: cheating vs interpersonal toxicity.

Reads the finished labels (read-only), sends only the harm_mention == "yes" reviews to Gemini
with prompts/harm_subtype.txt, and writes NEW files:
    data/gemini_harm_type_<model>.jsonl   (resumable cache, one line per review)
    data/gemini_harm_type_<model>.csv     (source columns + harm_type + harm_type_reason)

The original files (data/gemini_labels_*.csv, data/gemini_full_*.jsonl) are never written to.
"""
import json
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from google.genai import errors, types

RETRY_CODES = {429, 500, 503, 504}

SCHEMA = {
    "type": "object",
    "properties": {
        "harm_type": {"type": "string", "enum": ["cheating", "interpersonal", "both", "uncertain"]},
        "harm_type_reason": {"type": "string"},
    },
    "required": ["harm_type", "harm_type_reason"],
}


def _payload(row):
    return {"game": row["game"], "review": row["review"], "recommendation": row["recommendation"]}


class SubtypeRun:
    def __init__(self, df_yes, client, model, system, cache_path, temperature=0, workers=8, limit=None,
                 schema=SCHEMA, max_retries=8):
        self.df = df_yes.reset_index(drop=True)
        self.client, self.model, self.system = client, model, system
        self.cache_path, self.temperature, self.workers = cache_path, temperature, workers
        self.limit, self.schema, self.max_retries = limit, schema, max_retries
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
        entry = {"key": row["key"], "harm_type": res["harm_type"], "harm_type_reason": res["harm_type_reason"],
                 "model": self.model}
        with self.lock:   # saved the moment it finishes, so a stopped run loses nothing
            with open(self.cache_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self.done[row["key"]] = entry
        return entry

    def start(self, show=True):
        todo = [r for _, r in self.df.iterrows() if r["key"] not in self.done]
        if self.limit:
            todo = todo[: self.limit]
        total, t0, n = len(todo), time.time(), 0
        print(f"{len(self.df):,} toxic reviews in scope · {len(self.df) - len(todo) if not self.limit else len(self.done):,} already done (skipped) · {total:,} to run now")
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
        """Write source rows + the new columns to a NEW csv. Refuses to overwrite an existing labels file."""
        base = os.path.basename(out_csv)
        assert "harm_type" in base, "out_csv must be a new harm_type file"
        sub = pd.DataFrame(list(self.done.values()))[["key", "harm_type", "harm_type_reason"]]
        out = self.df.merge(sub, on="key", how="left")
        out.to_csv(out_csv, index=False)
        missing = int(out["harm_type"].isna().sum())
        print(f"Saved {len(out):,} rows -> {out_csv}  ({missing:,} toxic reviews not sub-labeled yet)")
        return out
