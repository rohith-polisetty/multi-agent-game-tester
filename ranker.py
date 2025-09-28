#!/usr/bin/env python3
import argparse, json, math
from pathlib import Path

def simple_rank(cases):
    scored = []
    for c in cases:
        steps = len(c.get('steps', []))
        pri = {'low':1,'medium':2,'high':3}.get(c.get('priority','low'),1)
        score = steps * 1.0 + pri * 2.0
        scored.append({'case': c, 'score': score})
    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--topk', type=int, default=10)
    args = parser.parse_args()
    plan = json.load(open(args.plan))
    cases = plan.get('cases') if isinstance(plan, dict) else plan
    scored = simple_rank(cases)
    top = [ {'case': s['case'], 'score': s['score']} for s in scored[:args.topk] ]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump({'top_k': top}, f, indent=2)
    print(f"[ranker] wrote top {len(top)} to {args.out}")

if __name__ == '__main__':
    main()
