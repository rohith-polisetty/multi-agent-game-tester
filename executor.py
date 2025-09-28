#!/usr/bin/env python3
import json, time, random
from pathlib import Path
from playwright.sync_api import sync_playwright

def run_case(case, run_dir):
    """
    Executes a single test case using Playwright.
    Each test case gets a fresh browser page.
    Saves artifacts:
      - step-wise screenshots
      - DOM snapshot
      - console logs
    """

    case_id = case.get('id', f"case_{int(time.time())}")
    case_dir = Path(run_dir) / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "id": case_id,
        "verdict": "fail",
        "artifacts": {}
    }

    url = case.get('url', "https://play.ezygamers.com/")
    steps = case.get('steps', [])

    with sync_playwright() as p:
        try:
            # Launch fresh browser for each test case
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Capture console logs
            console_messages = []
            page.on("console", lambda msg: console_messages.append(msg.text))

            # Navigate to URL
            page.goto(url, wait_until="networkidle")
            time.sleep(1)

            # Auto-select first language (if button exists)
            try:
                page.wait_for_selector("button", timeout=2000)
                buttons = page.query_selector_all("button")
                if buttons:
                    buttons[0].click()
                    page.wait_for_timeout(1000)
            except Exception:
                pass

            # Execute steps
            for i, step in enumerate(steps):
                action = step.get('action')
                selector = step.get('selector')
                value = step.get('value', '')

                try:
                    if selector:
                        if action == 'click':
                            page.click(selector)
                        elif action == 'type':
                            page.fill(selector, value)
                    else:
                        # fallback random click
                        viewport = page.viewport_size or {"width": 800, "height": 600}
                        x = random.randint(50, viewport["width"] - 50)
                        y = random.randint(50, viewport["height"] - 50)
                        page.mouse.click(x, y)

                    page.wait_for_timeout(500)

                    # Save step screenshot
                    step_screenshot = case_dir / f"screenshot_step{i+1}.png"
                    page.screenshot(path=str(step_screenshot), full_page=True)

                except Exception as e:
                    print(f"[executor] step {i+1} failed: {e}")
                    continue

            # Save DOM
            dom_path = case_dir / "dom.html"
            dom_path.write_text(page.content(), encoding='utf-8')
            result['artifacts']['dom'] = str(dom_path)

            # Save console logs
            console_path = case_dir / "console.log"
            console_path.write_text("\n".join(console_messages), encoding='utf-8')
            result['artifacts']['console'] = str(console_path)

            # Final screenshot
            final_screenshot = case_dir / "screenshot_final.png"
            page.screenshot(path=str(final_screenshot), full_page=True)
            result['artifacts']['final_screenshot'] = str(final_screenshot)

            result['verdict'] = "pass"

        except Exception as e:
            result['verdict'] = "error"
            result['error'] = str(e)
        finally:
            browser.close()

    return result
