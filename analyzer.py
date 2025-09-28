#!/usr/bin/env python3
import json, time
from pathlib import Path
from executor import run_case

def analyze_run(raw_results, run_dir, repeats=1):
    analyzed = []
    for r in raw_results:
        case_id = r['id']
        verdict = r.get('verdict','PASS')
        repeats_info = []
        if verdict == 'FAIL' and repeats > 0:
            for i in range(repeats):
                time.sleep(0.5)
                newr = run_case(r.get('case_obj', r), run_dir)
                repeats_info.append(newr)
            fails = sum(1 for x in repeats_info if x.get('verdict')=='FAIL')
            reproducibility = {'initial_verdict': verdict, 'repeats_failed': fails, 'repeat_runs': repeats}
        else:
            reproducibility = {'initial_verdict': verdict, 'repeats_failed': 0, 'repeat_runs': 0}
        analyzed.append({'id': case_id, 'initial': r, 'repro': reproducibility, 'repeats': repeats_info})
    return analyzed

if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--run_dir', required=True)
    args = parser.parse_args()
    raw = json.load(open(args.raw))
    analyzed = analyze_run(raw.get('results', []), args.run_dir, repeats=1)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump({'analyzed': analyzed}, open(args.out, 'w'), indent=2)
    print(f"[analyzer] wrote {args.out}")
