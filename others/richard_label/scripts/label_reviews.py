"""Portable, resumable toxicity/irony annotation of a prepared private sample."""
from pathlib import Path
import argparse, csv, hashlib, json, time, os, getpass
from contextlib import contextmanager
from datetime import datetime, timezone
import pandas as pd
from google import genai
from google.genai import types, errors

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'gemini-3.5-flash-lite'
LABELS = ['yes', 'no', 'uncertain']
SCHEMA = {'type': 'object', 'properties': {k: {'type': 'string', **({'enum': LABELS} if k in ['toxicity', 'irony'] else {})} for k in ['toxicity', 'irony', 'toxicity_reason', 'irony_reason']}, 'required': ['toxicity', 'irony', 'toxicity_reason', 'irony_reason']}

def prepare(input_path, output_dir, prompt):
    sample = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    required = {'case_id', 'game', 'review', 'recommendation'}
    if not required.issubset(sample.columns):
        raise ValueError('Input needs case_id, game, review, recommendation columns.')
    if sample.empty or not sample.case_id.is_unique or sample.case_id.str.strip().eq('').any() or sample.review.str.strip().eq('').any():
        raise ValueError('Input must have unique nonblank IDs and nonblank reviews.')
    if not sample.recommendation.isin(['Recommended', 'Not recommended']).all():
        raise ValueError('Recommendation must be Recommended or Not recommended.')
    config = {'model': MODEL, 'temperature': 0, 'system': prompt, 'schema': SCHEMA,
              'sample_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(),
              'sample_size': len(sample)}
    manifest = output_dir / 'manifest.json'
    if manifest.exists():
        if json.loads(manifest.read_text(encoding='utf-8')) != config:
            raise ValueError('Input or configuration changed. Use a new output directory.')
    else:
        if (output_dir / 'results.csv').exists():
            raise ValueError('Existing results have no manifest. Use a new output directory.')
        manifest.write_text(json.dumps(config, indent=2), encoding='utf-8')
    return sample


@contextmanager
def run_lock(directory):
    # Atomic directory creation also works on Windows. Removed on normal exit/Ctrl+C.
    lock = directory / '.running'
    try:
        lock.mkdir()
    except FileExistsError:
        raise SystemExit('Run already active or stale .running lock. See labeling guide.')
    try:
        yield
    finally:
        lock.rmdir()


def api_key():
    # No key is written to disk. Environment variable or hidden terminal entry.
    return os.environ.get('GEMINI_API_KEY') or getpass.getpass('Your Gemini API key (hidden): ').strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true', help='Validate without API calls')
    parser.add_argument('--limit', type=int, help='Maximum NEW labels this run')
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with run_lock(args.output_dir):
        run(args)


def run(args):
    system = (ROOT / 'outputs/gta_v_700/prompt.txt').read_text(encoding='utf-8')
    sample = prepare(args.input, args.output_dir, system)
    output = args.output_dir / 'results.csv'
    existing = pd.read_csv(output, dtype=str, keep_default_na=False) if output.exists() else pd.DataFrame(columns=['case_id'])
    if not existing.case_id.is_unique or not set(existing.case_id).issubset(set(sample.case_id)):
        raise ValueError('Results contain duplicate or unknown IDs.')
    done = set(existing.case_id)
    print(f'Validated {len(sample)} reviews; {len(done)} already saved; model={MODEL}', flush=True)
    if args.check_only or len(done) == len(sample):
        return
    key = api_key()
    if not key:
        raise SystemExit('No API key entered.')
    client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=120000))
    fields = ['case_id','toxicity','irony','toxicity_reason','irony_reason','model','timestamp_utc']
    print(f'Resuming: {len(done)}/{len(sample)} already saved', flush=True)
    new_count = 0
    for row in sample.itertuples(index=False):
        if row.case_id in done: continue
        payload = {'game': row.game, 'review': row.review, 'recommendation': row.recommendation}
        reply = None
        for attempt in range(5):
            try:
                response = client.models.generate_content(model=MODEL, contents=json.dumps(payload, ensure_ascii=False), config=types.GenerateContentConfig(system_instruction=system, response_mime_type='application/json', response_schema=SCHEMA, temperature=0))
                reply = json.loads(response.text)
                assert reply['toxicity'] in LABELS and reply['irony'] in LABELS
                assert all(isinstance(reply[k],str) for k in ['toxicity_reason','irony_reason'])
                break
            except (errors.APIError, ValueError, AssertionError, KeyError, TypeError) as exc:
                code = getattr(exc, 'code', None)
                detail = str(exc).replace(key, '[REDACTED]')
                if code == 429 and ('GenerateRequestsPerDay' in detail or 'requests per day limit exceeded' in detail):
                    print('DAILY QUOTA EXHAUSTED. Saved results retained; resume after quota reset.', flush=True)
                    return
                if isinstance(exc, errors.APIError) and code not in {429,500,502,503,504}:
                    print(f'Stopped: API error code={code}. Check your key/model access. Saved results retained.', flush=True)
                    return
                if attempt == 4:
                    print(f'Stopped at {row.case_id}; saved results retained. Error type={type(exc).__name__}, code={code}', flush=True)
                    return
                delay = 15 * 2**attempt
                print(f'Retrying {row.case_id}: type={type(exc).__name__}, code={code}; wait {delay}s', flush=True)
                time.sleep(delay)
        record = {k:reply[k] for k in fields if k in reply}
        record.update(case_id=row.case_id, model=MODEL, timestamp_utc=datetime.now(timezone.utc).isoformat())
        header = not output.exists()
        with output.open('a', newline='', encoding='utf-8') as f:
            writer=csv.DictWriter(f, fieldnames=fields); writer.writeheader() if header else None; writer.writerow(record)
        done.add(row.case_id)
        print(f'{len(done)}/{len(sample)} saved: {row.case_id} | toxicity={reply["toxicity"]} | irony={reply["irony"]}', flush=True)
        new_count += 1
        if args.limit and new_count >= args.limit:
            print('Run limit reached. Run the same command without --limit to continue.')
            return
        if len(done) < len(sample):
            time.sleep(15)
    print(f'DONE: {len(done)}/{len(sample)}. Results saved to {output}', flush=True)

if __name__ == '__main__': main()
