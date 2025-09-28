#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from ranker import simple_rank
from executor import run_case
from analyzer import analyze_run
from reporter import generate_report


def run_orchestrator(plan_path, out_dir, topk=10, workers=3):
    plan = json.load(open(plan_path))
    cases = plan.get('cases') if isinstance(plan, dict) else plan
    scored = simple_rank(cases)
    selected = [s['case'] for s in scored[:topk]]

    run_dir = Path(out_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    raw_results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(run_case, case, str(run_dir)): case for case in selected}
        for fut in as_completed(futures):
            case = futures[fut]
            try:
                res = fut.result()
                res['case_obj'] = case
                raw_results.append(res)
                print(f"[orchestrator] completed {res.get('id')} -> {res.get('verdict')}")
            except Exception as e:
                print(f"[orchestrator] error running case {case.get('id')}: {e}")

    raw_path = run_dir / 'raw_results.json'
    json.dump({'results': raw_results}, open(raw_path, 'w'), indent=2)
    return run_dir, raw_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--topk', type=int, default=10)
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()

    run_dir, raw = run_orchestrator(args.plan, args.out, topk=args.topk, workers=args.workers)
    analyzed = analyze_run(json.load(open(raw))['results'], str(run_dir), repeats=1)
    analyzed_path = run_dir / 'analyzed.json'
    json.dump({'analyzed': analyzed}, open(analyzed_path, 'w'), indent=2)

    report = generate_report(str(run_dir), json.load(open(raw))['results'], analyzed)
    report_path = run_dir / 'report.json'
    json.dump(report, open(report_path, 'w'), indent=2)

    print(f"[orchestrator] finished run. Report: {report_path}")
