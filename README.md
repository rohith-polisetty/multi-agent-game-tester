# POC Multi-Agent Game Tester (End-to-End Minimal)

This repository is a minimal, runnable end-to-end POC that:
- Generates candidate test cases from a Planner (LLM-backed or fallback)
- Ranks candidates and selects top K
- Executes selected tests (Executor agents using Playwright)
- Analyzes results with repeats and cross-agent checks
- Produces a JSON report with artifacts

## Quickstart (Windows / PowerShell example)
1. Create and activate virtualenv
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. Install requirements
   ```powershell
   pip install -r requirements.txt
   python -m playwright install
   ```
3. (Optional) Set HF token for hf_api backend:
   ```powershell
   setx HF_API_TOKEN "hf_xxx..."
   ```
4. Generate plan (planner uses hf_api by default here)
   ```powershell
   python planner.py --url "https://play.ezygamers.com/" --out examples/plan.json --num 20 --backend hf_api
   ```
5. Run end-to-end orchestrator (rank -> execute -> analyze -> report)
   ```powershell
   python orchestrator.py --plan examples/plan.json --out runs/run_001
   ```
6. Open report: `runs/run_001/report.json` and artifacts in `runs/run_001/artifacts/...`

## Notes
- Playwright will download browsers on first run (`python -m playwright install`).
- HF Inference API free tier may be rate-limited; use `--backend transformers` to run locally (downloads model weights).
- This is a minimal POC; adjust selectors and LLM prompts for better quality.
