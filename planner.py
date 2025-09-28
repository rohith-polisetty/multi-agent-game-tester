#!/usr/bin/env python3
import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from playwright.sync_api import sync_playwright
import requests

DEFAULT_MODEL = "google/flan-t5-base"

def fetch_rendered_dom(url: str, timeout: int = 30) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_navigation_timeout(timeout * 1000)
        print(f"[planner] navigating to {url} ...")
        page.goto(url, wait_until="networkidle")
        time.sleep(1.0)
        html = page.content()
        try:
            os.makedirs("artifacts/planner", exist_ok=True)
            page.screenshot(path="artifacts/planner/preview.png", full_page=True)
        except Exception:
            pass
        browser.close()
    return html

def build_prompt_from_dom(dom_html: str, num_cases: int = 20) -> str:
    body = (dom_html[:8000]) if len(dom_html) > 8000 else dom_html
    prompt = f"""You are a test-case generator for a web number/math puzzle game. Given the rendered HTML body below, generate exactly {num_cases} candidate test cases in JSON array form.

Each element must be an object with fields:
- id (t001...)
- title
- description
- priority (low|medium|high)
- tags (array of short tags)
- steps (array of step objects with action, selector, value optional)

Allowed step actions: navigate, click, type, assert_text, assert_contains, wait

HTML body:
{body}

Return ONLY valid JSON array and nothing else.
"""
    return prompt


from huggingface_hub import InferenceClient

from transformers import pipeline

def call_local_llm(prompt: str, model_name="google/flan-t5-base"):
    generator = pipeline("text2text-generation", model=model_name)
    output = generator(prompt, max_length=512, do_sample=True)
    return output[0]["generated_text"]



# def call_hf_inference_api(prompt: str, model_name: str = DEFAULT_MODEL, hf_token: Optional[str] = None) -> str:
#     from huggingface_hub import InferenceApi
#     if hf_token is None:
#         hf_token = os.getenv("HF_API_TOKEN")
#     if not hf_token:
#         raise RuntimeError("HF_API_TOKEN not set for hf_api backend")
#     infer = InferenceApi(repo_id=model_name, token=hf_token)
#     print("[planner] calling HF Inference API (may be slow)")
#     resp = infer(prompt)
#     # response can be str or dict/list
#     if isinstance(resp, str):
#         return resp
#     if isinstance(resp, dict) and "generated_text" in resp:
#         return resp["generated_text"]
#     if isinstance(resp, list):
#         texts = [item.get("generated_text") or item.get("text") for item in resp]
#         return "\n".join([t for t in texts if t])
    # return str(resp)

def save_plan(cases, out_path):
    from pathlib import Path
    import json

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2)
    print(f"✅ Generated {len(cases)} cases and saved to {out_path}")


def try_parse_json_array(raw_text: str):
    start = raw_text.find("[")
    end = raw_text.rfind("]")
    if start == -1 or end == -1:
        return None
    candidate = raw_text[start:end+1]
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        cleaned = re.sub(r",\s*\]", "]", candidate)
        cleaned = re.sub(r"//.*?\n", "\n", cleaned)
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            return None
    return None

def fallback_generate_simple_cases(dom_html: str, n: int = 20):
    candidates = []

    # Detect input fields and buttons
    input_ids = re.findall(r"<input[^>]+id=\"([^\"]+)\"", dom_html)
    btn_ids = re.findall(r"<button[^>]+id=\"([^\"]+)\"", dom_html)

    # Detect first language button by text (simplest fallback)
    lang_buttons = re.findall(r"<button[^>]*>(English|हिन्दी|ಕನ್ನಡ|தமிழ்|తెలుగు)</button>", dom_html)
    lang_selector = None
    if lang_buttons:
        # Use the first button text for selection
        lang_selector = f"button:has-text('{lang_buttons[0]}')"

    input_selector = f"#{input_ids[0]}" if input_ids else None
    btn_selector = f"#{btn_ids[0]}" if btn_ids else None

    for i in range(1, n + 1):
        tid = f"t{str(i).zfill(3)}"
        steps = [{"action": "navigate", "selector": "https://play.ezygamers.com/"}]

        # Step 1: select language
        if lang_selector:
            steps.append({"action": "click", "selector": lang_selector})
            steps.append({"action": "wait", "value": 1})

        # Step 2: type input and click submit if available
        if input_selector:
            steps.append({"action": "type", "selector": input_selector, "value": str(i)})
        if btn_selector:
            steps.append({"action": "click", "selector": btn_selector})

        # Step 3: assert result
        steps.append({"action": "assert_contains", "selector": "body", "value": str(i)})

        case = {
            "id": tid,
            "title": f"Auto-generated case {i}",
            "description": "Deterministic fallback test with language selection",
            "priority": "low",
            "tags": ["fallback", "language"],
            "steps": steps
        }
        candidates.append(case)

    return candidates


# def generate_test_cases(dom_html: str, num_cases: int = 20, backend: str = "hf_api"):
#     prompt = build_prompt_from_dom(dom_html, num_cases)
#     raw = None
#     if backend == "hf_api":
#         raw = call_hf_inference_api(prompt)
#     else:
#         raise RuntimeError("This planner.py in this repo uses hf_api by default for speed. Use hf_api.")
#     parsed = try_parse_json_array(raw)
#     if parsed and len(parsed) >= num_cases:
#         return parsed[:num_cases]
#     if parsed and len(parsed) > 0:
#         if len(parsed) < num_cases:
#             parsed += fallback_generate_simple_cases(dom_html, num_cases - len(parsed))
#         return parsed[:num_cases]
#     return fallback_generate_simple_cases(dom_html, num_cases)

# def save_plan(cases, out_path):
#     Path(out_path).parent.mkdir(parents=True, exist_ok=True)
#     with open(out_path, 'w', encoding='utf-8') as f:
#         json.dump({"generated_at": time.time(), "cases": cases}, f, indent=2, ensure_ascii=False)
#     print(f"[planner] saved {len(cases)} cases to {out_path}")

def generate_test_cases(dom_html: str, num_cases: int = 20, backend: str = "transformers"):
    prompt = build_prompt_from_dom(dom_html, num_cases)
    if backend == "transformers":
        raw = call_local_llm(prompt)
    elif backend == "hf_api":
        pass
        # raw = call_hf_inference_api(prompt)
    else:
        raise RuntimeError("Unsupported backend")

    parsed = try_parse_json_array(raw)
    if parsed and len(parsed) >= num_cases:
        return parsed[:num_cases]
    return fallback_generate_simple_cases(dom_html, num_cases)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--num', type=int, default=20)
    # parser.add_argument('--backend', choices=['hf_api'], default='hf_api')
    parser.add_argument('--backend', choices=['hf_api', 'transformers'], default='transformers')

    args = parser.parse_args()
    dom = fetch_rendered_dom(args.url)
    MAX_DOM_CHARS = 3000
    dom_snippet = dom[:MAX_DOM_CHARS]
    cases = generate_test_cases(dom_snippet, num_cases=args.num, backend=args.backend)
    save_plan(cases, args.out)

if __name__ == '__main__':
    main()
