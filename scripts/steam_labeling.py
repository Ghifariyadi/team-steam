"""Scale-up labeling helpers for notebooks/scale_up.ipynb (section 4).

Keeps the notebook short: all the plumbing (resume-from-cache, parallel requests, retries,
the live progress panel, export) lives here. The notebook only sets the options and calls
`LabelRun(...).start()` / `.export()`.

How it behaves
- Every finished review is appended to data/gemini_full_<model>.jsonl right away.
- Re-running skips anything already stored (looked up by row index + a hash of game/review).
- A review that still fails after the retries is logged, shown in the panel, and retried on re-run.
- Empty reviews are skipped (no label is invented for them).
"""
import hashlib
import html
import json
import os
import queue
import random
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from google.genai import errors, types
from IPython.display import HTML, Image, display

RETRY_CODES = {429, 500, 503, 504}

# --------------------------------------------------------------------------- panel styling
_CSS = """
<style>
.sr{--surface:#191919;--panel:#242424;--line:#343434;--tx:#efefef;--tx2:#9c9c9c;--blue:#338ced;--blue-lt:#6aabf1;--orange:#e76624;--neutral:#5f5f5f;--crit:#dc3c3d;--good:#0aac23;--warn:#fbb315;
 font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--surface);color:var(--tx);border:1px solid var(--line);border-radius:18px;padding:22px 24px;max-width:980px;box-sizing:border-box;line-height:1.35}
.sr *{box-sizing:border-box}
.sr-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap}
.sr-title{font-size:15px;font-weight:600}
.sr-sub{font-size:12px;color:var(--tx2);margin-top:3px}
.sr-chip{display:inline-flex;align-items:center;gap:8px;font-size:11px;font-weight:700;letter-spacing:.07em;padding:6px 12px;border-radius:999px;border:1px solid var(--line);background:var(--panel)}
.sr-dot{width:9px;height:9px;border-radius:50%;background:var(--blue)}
.sr-run .sr-dot{animation:sr-blink 1.1s ease-in-out infinite}
.sr-done .sr-dot{background:var(--good)}
.sr-warn .sr-dot{background:var(--crit)}
.sr-pause .sr-dot{background:var(--warn)}
.sr-hero{display:flex;align-items:baseline;gap:14px;margin:20px 0 12px;flex-wrap:wrap}
.sr-pct{font-size:50px;font-weight:700;line-height:1;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.sr-of{font-size:13px;color:var(--tx2);font-variant-numeric:tabular-nums}
.sr-bar{height:14px;border-radius:999px;background:var(--panel);overflow:hidden}
.sr-fill{height:100%;border-radius:999px;background:var(--blue);transition:width .45s ease}
.sr-run .sr-fill{background:linear-gradient(90deg,var(--blue) 0%,var(--blue-lt) 50%,var(--blue) 100%);background-size:220% 100%;animation:sr-shine 1.7s linear infinite}
.sr-bar.thin{height:8px;margin-top:8px}
.sr-stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:18px 0 6px}
.sr-stat{background:var(--panel);border-radius:12px;padding:11px 13px}
.sr-k{font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--tx2)}
.sr-v{font-size:19px;font-weight:600;margin-top:3px;font-variant-numeric:tabular-nums;white-space:nowrap}
.sr-v small{font-size:11px;font-weight:500;color:var(--tx2)}
.sr-h{font-size:12px;font-weight:600;margin:22px 0 9px;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}
.sr-h span{font-weight:400;color:var(--tx2)}
.sr-tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(24px,1fr));gap:3px}
.sr-t{aspect-ratio:1;border-radius:6px;background:var(--panel);position:relative;overflow:hidden}
.sr-t i{position:absolute;left:0;right:0;bottom:0;background:var(--blue);display:block}
.sr-t.full i{height:100%}
.sr-t.part.live i{animation:sr-pulse 1.1s ease-in-out infinite}
.sr-t.bad{background:var(--crit);color:#fff;font:700 12px/24px sans-serif;text-align:center}
.sr-legend{display:flex;gap:16px;flex-wrap:wrap;font-size:11px;color:var(--tx2);margin-top:9px}
.sr-legend b{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.sr-cols{display:grid;grid-template-columns:1fr 1fr;gap:26px}
.sr-row{margin-bottom:12px}
.sr-rowh{display:flex;justify-content:space-between;font-size:12px;margin-bottom:6px;font-variant-numeric:tabular-nums}
.sr-rowh span{color:var(--tx2)}
.sr-stack{display:flex;height:12px;border-radius:999px;overflow:hidden;background:var(--panel)}
.sr-stack div{height:100%;border-left:2px solid var(--surface);transition:width .45s ease}
.sr-stack div:first-child{border-left:0}
.sr-key{display:flex;gap:14px;flex-wrap:wrap;font-size:11px;color:var(--tx2);margin-top:6px;font-variant-numeric:tabular-nums}
.sr-key b{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}
.sr-feed{display:flex;flex-direction:column;gap:6px}
.sr-item{display:grid;grid-template-columns:54px 1fr auto;gap:12px;align-items:center;background:var(--panel);border-radius:10px;padding:8px 12px;font-size:12px}
.sr-game{font-size:10.5px;font-weight:700;letter-spacing:.05em;color:var(--tx2)}
.sr-txt{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sr-badges{display:flex;gap:6px;font-size:11px;color:var(--tx2);white-space:nowrap}
.sr-badges span{display:inline-flex;align-items:center;gap:5px;border:1px solid var(--line);border-radius:999px;padding:2px 8px}
.sr-badges b{width:7px;height:7px;border-radius:50%;display:inline-block}
.sr-note{font-size:12px;color:var(--tx2);margin-top:14px}
@keyframes sr-blink{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes sr-shine{from{background-position:200% 0}to{background-position:-20% 0}}
@keyframes sr-pulse{0%,100%{opacity:1}50%{opacity:.55}}
@media (prefers-reduced-motion:reduce){.sr *{animation:none!important;transition:none!important}}
@media (max-width:720px){.sr-stats{grid-template-columns:repeat(2,1fr)}.sr-cols{grid-template-columns:1fr}}
</style>
"""

_SHORT = {"Counter-Strike 2": "CS2", "PUBG: BATTLEGROUNDS": "PUBG", "Grand Theft Auto V": "GTA V"}
_COLOR = {"yes": "var(--blue)", "uncertain": "var(--orange)", "no": "var(--neutral)"}


# --------------------------------------------------------------------------- small helpers
def _fmt_clock(s):
    s = int(s)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def _fmt_eta(s):
    if s is None:
        return "calculating…"
    if s < 60:
        return f"~{int(s)} s"
    if s < 3600:
        return f"~{int(round(s / 60))} min"
    return f"~{int(s // 3600)}h {int(s % 3600 // 60):02d}m"


def _jsonable(x):
    return x.item() if hasattr(x, "item") else x


def _clean_row(row):
    r = row.copy()
    if "recommendation" not in r.index and "voted_up" in r.index:
        r["voted_up"] = bool(r["voted_up"])      # numpy bool -> plain bool so json.dumps works
    return r


def _review_ok(row):
    return isinstance(row["review"], str) and row["review"].strip() != ""


def _key(idx, row):
    # row index + short hash of game/review: if the dataset ever changes, old cache entries stop matching
    h = hashlib.sha1(f'{row["game"]}|{row["review"]}'.encode("utf-8")).hexdigest()[:8]
    return f"{idx}-{h}"


def _mix_block(title, counts):
    total = sum(counts.values()) or 1
    segs = "".join(f'<div style="width:{100 * counts[k] / total:.2f}%;background:{_COLOR[k]}"></div>' for k in ("yes", "uncertain", "no"))
    key = "".join(f'<span><b style="background:{_COLOR[k]}"></b>{k} {counts[k]:,}</span>' for k in ("yes", "uncertain", "no"))
    return (f'<div class="sr-row"><div class="sr-rowh">{title}<span>{sum(counts.values()):,} labeled</span></div>'
            f'<div class="sr-stack">{segs}</div><div class="sr-key">{key}</div></div>')


def _badge(label, v):
    return f'<span><b style="background:{_COLOR.get(v, "var(--neutral)")}"></b>{label} {html.escape(str(v))}</span>'


# --------------------------------------------------------------------------- the run
class LabelRun:
    def __init__(self, df, client, model, system, schema, temperature, make_payload,
                 batch_size=100, workers=8, limit=None, data_dir="../data",
                 backoff_base=10, backoff_max=300):
        self.client, self.model, self.system, self.schema = client, model, system, schema
        self.temperature, self.make_payload = temperature, make_payload
        self.batch_size, self.workers = batch_size, workers
        self.backoff_base, self.backoff_max = backoff_base, backoff_max
        self.backend = "Vertex AI" if os.environ.get("USE_VERTEX") == "1" else "AI Studio"

        tag = model.replace("/", "_")
        self.cache_path = f"{data_dir}/gemini_full_{tag}.jsonl"          # one line per finished review
        self.err_path = f"{data_dir}/gemini_full_{tag}_errors.jsonl"     # failures, for the record
        self.labels_path = f"{data_dir}/gemini_labels_{tag}.csv"         # export()

        self.jobs = [{"pos": pos, "idx": idx, "key": _key(idx, row), "game": row["game"], "row": _clean_row(row)}
                     for pos, (idx, row) in enumerate(df.iterrows())]
        if limit:
            self.jobs = self.jobs[:limit]

        # lookup: what is already stored? (those reviews get skipped, so nothing is paid for twice)
        self.results = {}
        if os.path.exists(self.cache_path):
            with open(self.cache_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        e = json.loads(line)
                        self.results[e["key"]] = e
        already = sum(1 for j in self.jobs if j["key"] in self.results)

        self.net = {"retries": 0, "waiting": 0}
        self.net_lock = threading.Lock()
        print(f"{self.backend} · {model}")
        print(f"{len(self.jobs):,} reviews in scope · {already:,} already labeled in {self.cache_path} (skipped) · "
              f"{len(self.jobs) - already:,} to go")

    # ----- one request, with retries (silent: the panel shows the retry count)
    def _label(self, row, max_retries=8):
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=json.dumps(self.make_payload(row), ensure_ascii=False),
                    config=types.GenerateContentConfig(
                        system_instruction=self.system,
                        temperature=self.temperature,
                        response_mime_type="application/json",
                        response_schema=self.schema,
                    ),
                )
                if not response.text:
                    raise ValueError("empty response (blocked by a safety filter, or no text returned)")
                return json.loads(response.text)
            except errors.APIError as e:
                if e.code not in RETRY_CODES or attempt == max_retries - 1:
                    raise
                wait = min(self.backoff_base * 2 ** attempt, self.backoff_max) + random.uniform(0, self.backoff_base / 2)
                with self.net_lock:
                    self.net["retries"] += 1
                    self.net["waiting"] += 1
                try:
                    time.sleep(wait)
                finally:
                    with self.net_lock:
                        self.net["waiting"] -= 1

    # ----- bookkeeping for the panel
    def _reset_state(self):
        bs = self.batch_size
        self.n_batches = (len(self.jobs) + bs - 1) // bs
        self.b_total, self.b_done, self.b_fail = [0] * self.n_batches, [0] * self.n_batches, [0] * self.n_batches
        self.games = sorted({j["game"] for j in self.jobs})
        self.g_total, self.g_done = {g: 0 for g in self.games}, {g: 0 for g in self.games}
        self.mix = {"harm_mention": {"yes": 0, "uncertain": 0, "no": 0}, "irony": {"yes": 0, "uncertain": 0, "no": 0}}
        self.state = {"done": 0, "skipped": 0}
        self.recent, self.stamps, self.failed = deque(maxlen=4), deque(), {}
        for j in self.jobs:
            self.b_total[j["pos"] // bs] += 1
            self.g_total[j["game"]] += 1
        for j in self.jobs:                                   # what the cache already covers
            if j["key"] in self.results:
                self._register(j, self.results[j["key"]], fresh=False)

    def _register(self, job, entry, fresh):
        b = job["pos"] // self.batch_size
        self.state["done"] += 1
        self.b_done[b] += 1
        self.g_done[job["game"]] += 1
        if entry.get("status") == "skipped_empty":
            self.state["skipped"] += 1
            return
        for fld in self.mix:
            v = entry.get(fld)
            self.mix[fld][v] = self.mix[fld].get(v, 0) + 1
        if fresh:
            self.recent.appendleft(entry | {"_review": job["row"]["review"]})
            self.stamps.append(time.time())

    # ----- the live panel
    def _render(self, status):
        now = time.time()
        elapsed = now - self.t_start
        while self.stamps and now - self.stamps[0] > 30:
            self.stamps.popleft()
        rate = len(self.stamps) / max(min(30.0, elapsed), 1e-9) if self.stamps else 0.0
        total, done, n_fail = len(self.jobs), self.state["done"], len(self.failed)
        remaining = max(total - done - n_fail, 0)
        pct = 100.0 * done / total if total else 100.0
        eta = None if (remaining and rate <= 0) else (remaining / rate if remaining else 0)

        if status == "RUNNING":
            cls, chip = "sr-run", "RUNNING"
        elif status == "PAUSED":
            cls, chip = "sr-pause", "PAUSED · re-run the cell to resume"
        elif n_fail:
            cls, chip = "sr-warn", f"! DONE · {n_fail} failed"
        else:
            cls, chip = "sr-done", "✓ DONE"

        live = "live" if status == "RUNNING" else ""

        def ph(period):   # the panel is re-drawn on every refresh; tying the animation phase to the clock keeps it smooth
            return f"animation-delay:-{now % period:.2f}s"

        tiles = []
        for b in range(self.n_batches):
            d, f, t = self.b_done[b], self.b_fail[b], self.b_total[b]
            tip = f"Batch {b + 1}: {d}/{t} ({100 * d // t}%)" + (f" · {f} failed" if f else "")
            if f and d + f == t:
                tiles.append(f'<div class="sr-t bad" title="{tip}">!</div>')
            elif d == t:
                tiles.append(f'<div class="sr-t full" title="{tip}"><i></i></div>')
            elif d:
                tiles.append(f'<div class="sr-t part {live}" title="{tip}"><i style="height:{100 * d / t:.0f}%;{ph(1.1)}"></i></div>')
            else:
                tiles.append(f'<div class="sr-t" title="{tip}"></div>')

        active = next((b for b in range(self.n_batches) if self.b_done[b] + self.b_fail[b] < self.b_total[b]), None)
        if active is None:
            cur_label, cur_pct = "All batches finished", 100.0
        else:
            cur_pct = 100.0 * self.b_done[active] / self.b_total[active]
            cur_label = f"Batch {active + 1} of {self.n_batches} · {self.b_done[active]}/{self.b_total[active]} · {cur_pct:.0f}%"

        game_rows = "".join(
            f'<div class="sr-row"><div class="sr-rowh">{html.escape(g)}<span>{self.g_done[g]:,} / {self.g_total[g]:,}</span></div>'
            f'<div class="sr-bar thin" style="margin-top:0"><div class="sr-fill" style="width:{100 * self.g_done[g] / max(self.g_total[g], 1):.1f}%"></div></div></div>'
            for g in self.games)

        feed = "".join(
            f'<div class="sr-item"><div class="sr-game">{_SHORT.get(e["game"], e["game"][:6])}</div>'
            f'<div class="sr-txt">{html.escape(" ".join(str(e["_review"]).split())[:140])}</div>'
            f'<div class="sr-badges">{_badge("toxicity", e.get("harm_mention"))}{_badge("irony", e.get("irony"))}</div></div>'
            for e in self.recent) or '<div class="sr-note">Waiting for the first results…</div>'

        waiting = f' <small>({self.net["waiting"]} waiting)</small>' if self.net["waiting"] else ""
        bad = '<span style="color:var(--crit)">! </span>' if n_fail else ""
        skipped = f'<div class="sr-note">{self.state["skipped"]} review(s) skipped (empty text).</div>' if self.state["skipped"] else ""
        return f"""{_CSS}
<div class="sr {cls}">
 <div class="sr-head">
  <div><div class="sr-title">Steam review labeling</div><div class="sr-sub">{html.escape(self.model)} · {self.backend} · {self.workers} workers · batches of {self.batch_size}</div></div>
  <div class="sr-chip"><i class="sr-dot" style="{ph(1.1)}"></i>{chip}</div>
 </div>
 <div class="sr-hero"><div class="sr-pct">{pct:.1f}%</div><div class="sr-of">{done:,} of {total:,} reviews labeled</div></div>
 <div class="sr-bar"><div class="sr-fill" style="width:{pct:.2f}%;{ph(1.7)}"></div></div>
 <div class="sr-stats">
  <div class="sr-stat"><div class="sr-k">Speed</div><div class="sr-v">{rate:.1f} <small>rev/s</small></div></div>
  <div class="sr-stat"><div class="sr-k">Time left</div><div class="sr-v">{_fmt_eta(eta) if remaining else "—"}</div></div>
  <div class="sr-stat"><div class="sr-k">Elapsed</div><div class="sr-v">{_fmt_clock(elapsed)}</div></div>
  <div class="sr-stat"><div class="sr-k">Retries (503/429)</div><div class="sr-v">{self.net["retries"]:,}{waiting}</div></div>
  <div class="sr-stat"><div class="sr-k">Failed</div><div class="sr-v">{bad}{n_fail:,}</div></div>
 </div>
 <div class="sr-h">Batches <span>{cur_label}</span></div>
 <div class="sr-tiles">{"".join(tiles)}</div>
 <div class="sr-bar thin"><div class="sr-fill" style="width:{cur_pct:.1f}%"></div></div>
 <div class="sr-legend"><span><b style="background:var(--panel);border:1px solid var(--line)"></b>pending</span><span><b style="background:var(--blue)"></b>in progress / done</span><span><b style="background:var(--crit)"></b>! has failures</span></div>
 <div class="sr-cols">
  <div><div class="sr-h">Labels so far</div>{_mix_block("Toxicity", self.mix["harm_mention"])}{_mix_block("Irony", self.mix["irony"])}</div>
  <div><div class="sr-h">By game</div>{game_rows}</div>
 </div>
 <div class="sr-h">Latest labeled</div>
 <div class="sr-feed">{feed}</div>
 {skipped}
</div>"""

    # ----- worker side / main side of the loop
    def _work(self, job, resq):
        row = job["row"]
        try:
            if not _review_ok(row):
                res = {"ok": True, "entry": {"status": "skipped_empty"}}
            else:
                res = {"ok": True, "entry": {"status": "ok", **self._label(row)}}
        except Exception as e:
            res = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        res["job"] = job
        resq.put(res)

    def _handle(self, res):
        job = res["job"]
        if res["ok"]:
            entry = {"key": job["key"], "idx": _jsonable(job["idx"]), "game": job["game"],
                     "model": self.model, "ts": round(time.time()), **res["entry"]}
            with open(self.cache_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self.results[job["key"]] = entry
            self._register(job, entry, fresh=True)
        else:
            self.failed[job["key"]] = res["error"]
            self.b_fail[job["pos"] // self.batch_size] += 1
            with open(self.err_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"key": job["key"], "error": res["error"], "ts": round(time.time())}) + "\n")

    # ----- the final panel as a picture (shows up in the notebook output on GitHub too)
    def _final_image(self, status):
        try:
            from matplotlib.figure import Figure
            from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
        except ImportError:
            return None
        import io

        C = dict(surface="#191919", panel="#242424", line="#343434", tx="#efefef", tx2="#9c9c9c", blue="#338ced",
                 orange="#e76624", neutral="#5f5f5f", crit="#dc3c3d", good="#0aac23", warn="#fbb315")
        col = {"yes": C["blue"], "uncertain": C["orange"], "no": C["neutral"]}
        W, M = 1100, 40
        IW = W - 2 * M
        total, done, n_fail = len(self.jobs), self.state["done"], len(self.failed)
        remaining = max(total - done - n_fail, 0)
        elapsed = time.time() - self.t_start
        new = done - getattr(self, "_done_at_start", 0)
        rate = new / elapsed if elapsed > 0 else 0.0
        eta = (remaining / rate) if (remaining and rate > 0) else None
        pct = 100.0 * done / total if total else 100.0

        s, gap = 24, 3
        cols = max((IW + gap) // (s + gap), 1)
        rows = -(-self.n_batches // cols)
        y_tiles = 340
        y_curbar = y_tiles + rows * (s + gap) - gap + 12
        y_leg = y_curbar + 30
        y_cols = y_leg + 44
        y_latest = y_cols + 16 + 150
        n_feed = len(self.recent)
        H = y_latest + 24 + max(n_feed, 1) * 40 + (30 if self.state["skipped"] else 0) + 24

        fig = Figure(figsize=(W / 100, H / 100), dpi=100, facecolor=C["surface"])
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, W)
        ax.set_ylim(H, 0)
        ax.axis("off")

        def box(x, y, w, h, color, r=8):
            p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={min(r, h / 2)}", fc=color, ec="none")
            ax.add_patch(p)
            return p

        def text(x, y, t, size=9, color=C["tx"], weight="normal", ha="left"):
            ax.text(x, y, t, fontsize=size, color=color, fontweight=weight, ha=ha, va="baseline")

        def bar(x, y, w, h, frac):
            base = box(x, y, w, h, C["panel"], r=h)
            if frac > 0:
                fill = Rectangle((x, y), w * min(frac, 1.0), h, fc=C["blue"], ec="none")
                ax.add_patch(fill)
                fill.set_clip_path(base)

        def stack(x, y, w, h, counts):
            base = box(x, y, w, h, C["panel"], r=h)
            tot = sum(counts.values()) or 1
            cx = x
            for k in ("yes", "uncertain", "no"):
                sw = w * counts[k] / tot
                if sw <= 0:
                    continue
                seg = Rectangle((cx, y), sw, h, fc=col[k], ec=C["surface"], lw=1.5)
                ax.add_patch(seg)
                seg.set_clip_path(base)
                cx += sw

        # header
        text(M, 50, "Steam review labeling", 14, weight="bold")
        text(M, 74, f"{self.model} · {self.backend} · {self.workers} workers · batches of {self.batch_size}", 8.5, C["tx2"])
        if status == "PAUSED":
            chip, dot = "PAUSED · re-run the cell to resume", C["warn"]
        elif n_fail:
            chip, dot = f"! DONE · {n_fail} failed", C["crit"]
        else:
            chip, dot = "✓ DONE", C["good"]
        cw = len(chip) * 8.2 + 44
        box(W - M - cw, 30, cw, 32, C["panel"], r=16)
        ax.add_patch(Circle((W - M - cw + 18, 46), 4.5, fc=dot, ec="none"))
        text(W - M - cw + 32, 50, chip, 8, weight="bold")

        # hero + overall bar
        text(M, 148, f"{pct:.1f}%", 34, weight="bold")
        text(M + len(f"{pct:.1f}%") * 30 + 18, 146, f"{done:,} of {total:,} reviews labeled", 10, C["tx2"])
        bar(M, 168, IW, 14, pct / 100)

        # stat tiles
        stats = [("SPEED (AVG)", f"{rate:.1f} rev/s"), ("TIME LEFT", _fmt_eta(eta) if remaining else "—"),
                 ("ELAPSED", _fmt_clock(elapsed)), ("RETRIES (503/429)", f"{self.net['retries']:,}"),
                 ("FAILED", ("! " if n_fail else "") + f"{n_fail:,}")]
        tw = (IW - 4 * 10) / 5
        for i, (k, v) in enumerate(stats):
            x = M + i * (tw + 10)
            box(x, 206, tw, 66, C["panel"], r=12)
            text(x + 14, 228, k, 6.5, C["tx2"])
            text(x + 14, 256, v, 12.5, C["crit"] if (k == "FAILED" and n_fail) else C["tx"], weight="bold")

        # batches
        active = next((b for b in range(self.n_batches) if self.b_done[b] + self.b_fail[b] < self.b_total[b]), None)
        if active is None:
            cur_label, cur_pct = "All batches finished", 100.0
        else:
            cur_pct = 100.0 * self.b_done[active] / self.b_total[active]
            cur_label = f"Batch {active + 1} of {self.n_batches} · {self.b_done[active]}/{self.b_total[active]} · {cur_pct:.0f}%"
        text(M, 316, "Batches", 9, weight="bold")
        text(W - M, 316, cur_label, 8, C["tx2"], ha="right")
        for b in range(self.n_batches):
            x = M + (b % cols) * (s + gap)
            y = y_tiles + (b // cols) * (s + gap)
            d, f, t = self.b_done[b], self.b_fail[b], self.b_total[b]
            if f and d + f == t:
                box(x, y, s, s, C["crit"], r=6)
                text(x + s / 2, y + s / 2 + 4, "!", 9, "#ffffff", weight="bold", ha="center")
            elif d == t:
                box(x, y, s, s, C["blue"], r=6)
            else:
                base = box(x, y, s, s, C["panel"], r=6)
                if d:
                    fill = Rectangle((x, y + s * (1 - d / t)), s, s * d / t, fc=C["blue"], ec="none")
                    ax.add_patch(fill)
                    fill.set_clip_path(base)
        bar(M, y_curbar, IW, 8, cur_pct / 100)
        lx = M
        for label, color, edge in (("pending", C["panel"], C["line"]), ("done / in progress", C["blue"], None), ("! has failures", C["crit"], None)):
            ax.add_patch(Rectangle((lx, y_leg - 9), 10, 10, fc=color, ec=edge or "none", lw=0.8))
            text(lx + 16, y_leg, label, 7.5, C["tx2"])
            lx += 16 + len(label) * 6.2 + 24

        # labels + per game
        text(M, y_cols, "Labels so far", 9, weight="bold")
        for i, (title, counts) in enumerate((("Toxicity", self.mix["harm_mention"]), ("Irony", self.mix["irony"]))):
            y = y_cols + 28 + i * 66
            text(M, y, title, 8.5)
            text(M + 490, y, f"{sum(counts.values()):,} labeled", 8, C["tx2"], ha="right")
            stack(M, y + 10, 490, 12, counts)
            kx = M
            for k in ("yes", "uncertain", "no"):
                ax.add_patch(Circle((kx + 4, y + 36), 3.5, fc=col[k], ec="none"))
                label = f"{k} {counts[k]:,}"
                text(kx + 13, y + 40, label, 7.5, C["tx2"])
                kx += 13 + len(label) * 6.4 + 14
        gx = M + 530
        text(gx, y_cols, "By game", 9, weight="bold")
        for i, g in enumerate(self.games):
            y = y_cols + 28 + i * 40
            text(gx, y, g, 8.5)
            text(gx + 490, y, f"{self.g_done[g]:,} / {self.g_total[g]:,}", 8, C["tx2"], ha="right")
            bar(gx, y + 10, 490, 8, self.g_done[g] / max(self.g_total[g], 1))

        # latest labeled
        text(M, y_latest, "Latest labeled", 9, weight="bold")
        if not self.recent:
            text(M, y_latest + 30, "No new reviews labeled in this run.", 8.5, C["tx2"])
        for i, e in enumerate(self.recent):
            y = y_latest + 14 + i * 40
            box(M, y, IW, 32, C["panel"], r=10)
            text(M + 14, y + 20, _SHORT.get(e["game"], e["game"][:6]), 7, C["tx2"], weight="bold")
            review = " ".join(str(e["_review"]).split())
            text(M + 70, y + 20, review if len(review) <= 105 else review[:105] + "…", 8)
            bx = W - M - 14
            for label, v in (("irony", e.get("irony")), ("toxicity", e.get("harm_mention"))):
                t = f"{label} {v}"
                ax.add_patch(Circle((bx - len(t) * 4.8 - 9, y + 16), 3.5, fc=col.get(v, C["neutral"]), ec="none"))
                text(bx, y + 20, t, 7.5, C["tx2"], ha="right")
                bx -= len(t) * 4.8 + 30
        if self.state["skipped"]:
            text(M, H - 28, f"{self.state['skipped']} review(s) skipped (empty text).", 8, C["tx2"])

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100, facecolor=C["surface"])
        return Image(data=buf.getvalue(), format="png")

    def start(self):
        """Label everything that is not in the cache yet, with the live panel. Interrupt the kernel to pause."""
        self._reset_state()
        pending = [j for j in self.jobs if j["key"] not in self.results]
        resq = queue.Queue()
        self.t_start = time.time()
        self._done_at_start = self.state["done"]
        status = "RUNNING"
        handle = display(HTML(self._render(status)), display_id=True)
        ex = ThreadPoolExecutor(max_workers=self.workers)
        try:
            for j in pending:
                ex.submit(self._work, j, resq)
            got, last = 0, 0.0
            while got < len(pending):
                try:
                    self._handle(resq.get(timeout=0.5))
                    got += 1
                except queue.Empty:
                    pass
                if time.time() - last > 0.4:
                    handle.update(HTML(self._render("RUNNING")))
                    last = time.time()
            status = "DONE"
        except KeyboardInterrupt:
            status = "PAUSED"
        finally:
            ex.shutdown(wait=False, cancel_futures=True)
            final = self._final_image(status)     # a PNG survives in the saved notebook (the HTML panel's CSS doesn't)
            handle.update(final if final is not None else HTML(self._render(status)))

        print(f"{status}: {self.state['done']:,}/{len(self.jobs):,} labeled · {len(self.failed)} failed · "
              f"this run took {_fmt_clock(time.time() - self.t_start)}")
        if self.failed:
            print("First errors:")
            for k, v in list(self.failed.items())[:3]:
                print("  ", k, "->", v[:200])
            print("Re-run this cell to retry only the failed ones (finished reviews are skipped).")
        elif status == "PAUSED":
            print("Re-run this cell to continue where it stopped (finished reviews are skipped).")

    # ----- results table
    def export(self):
        """Write data/gemini_labels_<model>.csv (everything labeled so far) and show per-game summaries."""
        meta = pd.DataFrame([
            {"key": j["key"], "recommendation": self.make_payload(j["row"])["recommendation"], "review": j["row"]["review"]}
            for j in self.jobs if j["key"] in self.results
        ])
        labels = pd.DataFrame([self.results[j["key"]] for j in self.jobs if j["key"] in self.results])
        out = labels.merge(meta, on="key")
        cols = ["key", "idx", "game", "recommendation", "review", "status",
                "harm_mention", "harm_reason", "irony", "irony_reason",
                "gender_age", "gender_age_reason", "model"]
        out = out[[c for c in cols if c in out.columns]]
        out.to_csv(self.labels_path, index=False)
        print(f"Saved {len(out):,} rows -> {self.labels_path}  ({len(self.jobs) - len(out):,} of {len(self.jobs):,} reviews not labeled yet)")

        ok = out[out["status"] == "ok"]
        print("\nToxicity by game")
        display(pd.crosstab(ok["game"], ok["harm_mention"], margins=True))
        print("Irony by game")
        display(pd.crosstab(ok["game"], ok["irony"], margins=True))
        print("Gender / age by game")
        display(pd.crosstab(ok["game"], ok["gender_age"], margins=True))
        return out
