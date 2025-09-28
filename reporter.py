#!/usr/bin/env python3
import json, time
from pathlib import Path

def generate_report(run_dir, raw_results, analyzed):
    rep = {'run_dir': run_dir, 'generated_at': time.time(), 'cases': []}
    for r in raw_results:
        cid = r['id']
        case_entry = {'id': cid, 'verdict': r.get('verdict', 'UNKNOWN'), 'errors': r.get('errors', []), 'artifacts': []}
        art_dir = Path(run_dir) / 'artifacts' / cid
        if art_dir.exists():
            for f in art_dir.iterdir():
                case_entry['artifacts'].append(str(f.relative_to(run_dir)))
        rep['cases'].append(case_entry)
    rep['analyzed'] = analyzed
    return rep

if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument('--run_dir', required=True)
    parser.add_argument('--raw', required=True)
    parser.add_argument('--analyzed', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    raw = json.load(open(args.raw))
    analyzed = json.load(open(args.analyzed))
    report = generate_report(args.run_dir, raw.get('results', []), analyzed)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(report, open(args.out, 'w'), indent=2)
    print(f"[reporter] wrote {args.out}")
