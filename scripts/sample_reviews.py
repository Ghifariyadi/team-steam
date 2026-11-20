"""Reproduce the GTA sampling rule for an assigned game; use private inputs."""
import argparse
import hashlib
from pathlib import Path
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pool', type=Path, required=True)
    parser.add_argument('--pilot', type=Path, required=True, help='CSV containing the original 90 case_id values')
    parser.add_argument('--appid', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--n', type=int, default=700)
    parser.add_argument('--seed', type=int, default=20261118)
    args = parser.parse_args()
    if args.n < 1:
        parser.error('--n must be positive')
    if args.output.exists():
        parser.error('Output already exists; preserve the original sample.')
    pool = pd.read_csv(args.pool, dtype=str, keep_default_na=False)
    pilot = pd.read_csv(args.pilot, dtype=str, keep_default_na=False)
    rows = pool.loc[(pool.appid == args.appid) & pool.review.str.strip().ne('')].drop_duplicates('recommendationid').copy()
    rows['case_id'] = rows.recommendationid.map(lambda x: 'R' + hashlib.sha256(x.encode()).hexdigest()[:10])
    rows = rows.loc[~rows.case_id.isin(pilot.case_id)].sort_values('case_id')
    sample = rows.sample(n=args.n, random_state=args.seed).reset_index(drop=True)
    sample['recommendation'] = sample.voted_up.str.lower().map({'true':'Recommended','false':'Not recommended','1':'Recommended','0':'Not recommended'})
    if sample.recommendation.isna().any() or not sample.case_id.is_unique:
        raise ValueError('Invalid recommendation or duplicate case IDs.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sample[['case_id','appid','game','review','recommendation','timestamp_created']].to_csv(args.output, index=False)
    print(f'Saved {len(sample)} of {len(rows)} eligible reviews; appid={args.appid}; seed={args.seed}.')

if __name__ == '__main__':
    main()
