# SignalGraph External Credentials Usage Guide

This guide explains how the backend should use the environment variables in `.env`. It intentionally does not include any secret values.

## 1. Important Safety Notes

- Keep `.env` local and do not commit it.
- `.gitignore` already excludes `.env` and `.env.*`.
- Keep `SIGNALGRAPH_MOCK_MODE=true` until the backend has a stable mock flow.
- Flip `SIGNALGRAPH_MOCK_MODE=false` only when testing live Bright Data, AI/ML API, Cognee, or optional integrations.
- If any credential is rotated, update `.env` locally and restart the backend.

## 2. Current Credential Status

Configured in `.env`:

- Bright Data REST API bearer key.
- Bright Data Browser API WebSocket endpoint.
- Bright Data Selenium endpoint.
- Bright Data SERP zone name.
- Bright Data Web Unlocker zone name.
- AI/ML API key.
- Triggerware API key.
- Speechmatics API key.
- Default SQLite database URL.
- Default CORS origin for local frontend.

Still needed:

- `BRIGHT_DATA_MCP_URL` if the team chooses to use Bright Data MCP.
- Cognee credentials or local Cognee setup.
- AI/ML API model IDs for extraction, briefing, and draft generation.

## 3. Bright Data Usage

Bright Data has three live paths available to us.

Important distinction:

- SERP API and Web Unlocker API use the shared Bright Data REST bearer key.
- Browser API uses the WebSocket or Selenium endpoint with credentials embedded in the URL.
- Do not try to use the Browser API endpoint as the bearer token for SERP/Unlocker calls.

### 3.1 SERP API

Use this for source discovery.

Environment variables:

- `BRIGHT_DATA_API_KEY`
- `BRIGHT_DATA_API_ENDPOINT`
- `BRIGHT_DATA_SERP_ZONE`

Backend behavior:

1. Build a Google search URL for the account query.
2. Send a `POST` request to `BRIGHT_DATA_API_ENDPOINT`.
3. Use bearer authorization from `BRIGHT_DATA_API_KEY`.
4. Set `zone` to `BRIGHT_DATA_SERP_ZONE`.
5. Set `format` to `raw`.
6. Parse the returned HTML/search content into candidate source URLs.

Example use cases:

- Account careers search.
- Engineering blog search.
- Competitor mention search.
- Public company update search.

Python structure:

```python
import os
import requests


def bright_data_serp_search(query: str) -> str:
    api_key = os.environ["BRIGHT_DATA_API_KEY"]
    endpoint = os.environ.get("BRIGHT_DATA_API_ENDPOINT", "https://api.brightdata.com/request")
    zone = os.environ["BRIGHT_DATA_SERP_ZONE"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "zone": zone,
        "url": f"https://www.google.com/search?q={query}",
        "format": "raw",
    }

    response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    return response.text
```

### 3.2 Web Unlocker API

Use this for fetching public pages that block normal requests.

Environment variables:

- `BRIGHT_DATA_API_KEY`
- `BRIGHT_DATA_API_ENDPOINT`
- `BRIGHT_DATA_UNLOCKER_ZONE`

Backend behavior:

1. Select a discovered source URL.
2. Send a `POST` request to `BRIGHT_DATA_API_ENDPOINT`.
3. Use bearer authorization from `BRIGHT_DATA_API_KEY`.
4. Set `zone` to `BRIGHT_DATA_UNLOCKER_ZONE`.
5. Set `url` to the target source URL.
6. Set `format` to `raw`.
7. Store the returned page content as an `evidence_document`.

Use Web Unlocker before Browser API unless the target page needs JavaScript rendering.

Python structure:

```python
import os
import requests


def bright_data_unlock_url(url: str) -> str:
    api_key = os.environ["BRIGHT_DATA_API_KEY"]
    endpoint = os.environ.get("BRIGHT_DATA_API_ENDPOINT", "https://api.brightdata.com/request")
    zone = os.environ["BRIGHT_DATA_UNLOCKER_ZONE"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "zone": zone,
        "url": url,
        "format": "raw",
    }

    response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    return response.text
```

### 3.3 Browser API

Use this only for JavaScript-heavy pages or pages that need browser execution.

Environment variables:

- `BRIGHT_DATA_BROWSER_WS`
- `BRIGHT_DATA_BROWSER_SELENIUM_URL`

Recommended backend usage:

- Use `BRIGHT_DATA_BROWSER_WS` for Playwright or Puppeteer.
- Use `BRIGHT_DATA_BROWSER_SELENIUM_URL` only if the backend team chooses Selenium.

MVP recommendation:

- Prefer Playwright with the WebSocket endpoint.
- Capture rendered HTML or text content.
- Store the fetch method as `browser_api`.
- Limit usage because browser sessions are heavier than SERP or Unlocker calls.

Playwright structure:

```python
import os
from playwright.sync_api import sync_playwright


def bright_data_browser_fetch(url: str) -> str:
    browser_ws = os.environ["BRIGHT_DATA_BROWSER_WS"]

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(browser_ws)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=90_000)
        content = page.content()
        browser.close()
        return content
```

Selenium structure:

```python
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def bright_data_selenium_fetch(url: str) -> str:
    selenium_url = os.environ["BRIGHT_DATA_BROWSER_SELENIUM_URL"]

    options = Options()
    options.add_argument("--headless=new")

    driver = webdriver.Remote(
        command_executor=selenium_url,
        options=options,
    )
    try:
        driver.get(url)
        return driver.page_source
    finally:
        driver.quit()
```

### 3.4 MCP Server

Use this if the backend team wires Bright Data MCP.

Environment variable:

- `BRIGHT_DATA_MCP_URL`

If MCP is not ready, do not block. The backend can call SERP and Unlocker directly using the REST endpoint.

## 4. AI/ML API Usage

Use AI/ML API as the model gateway for three model tasks:

1. Signal extraction.
2. Account brief generation.
3. Outreach draft generation.

Environment variables:

- `AIML_API_KEY`
- `AIML_API_BASE_URL`
- `AIML_EXTRACTION_MODEL`
- `AIML_BRIEFING_MODEL`
- `AIML_DRAFT_MODEL`

Backend behavior:

- Use the API key for authorization.
- Use the base URL as an OpenAI-compatible API endpoint.
- Use the extraction model for strict JSON extraction.
- Use the briefing model for stronger reasoning and summary generation.
- Use the draft model for short outreach drafts.

The model ID variables are intentionally separate so the team can route expensive and cheap tasks differently.

## 5. Cognee Usage

Cognee is the graph memory layer.

Environment variables:

- `COGNEE_API_KEY`
- `COGNEE_API_URL`
- `COGNEE_DATASET_PREFIX`

Backend behavior:

- Keep Cognee behind a wrapper service.
- Use `COGNEE_DATASET_PREFIX` when naming datasets.
- Store seed records, evidence summaries, signals, and account relationships.
- If Cognee is unavailable, the scan should still complete with a graph warning.

The backend should not require Cognee for mock mode.

## 6. Triggerware Usage

Triggerware is optional for the MVP.

Environment variable:

- `TRIGGERWARE_API_KEY`

Possible future usage:

- Schedule daily scans.
- Trigger notifications when an account crosses the sales-ready threshold.
- Trigger approval workflow events.

For the hackathon demo, do not block the main pipeline on Triggerware.

## 7. Speechmatics Usage

Speechmatics is optional for the MVP.

Environment variable:

- `SPEECHMATICS_API_KEY`

Possible future usage:

- Transcribe sales rep voice notes.
- Add call notes into Cognee memory.
- Improve future account briefs and outreach drafts with approved call context.

For the main demo, treat this as a bonus integration only.

## 8. Database And CORS

Environment variables:

- `DATABASE_URL`
- `CORS_ALLOWED_ORIGINS`

MVP defaults:

- Use SQLite locally.
- Use `http://localhost:3000` for the frontend origin.

If the team moves to Supabase/Postgres, update `DATABASE_URL` only. The app should continue using SQLAlchemy.

## 9. Recommended Live Integration Order

1. Build and verify full mock mode.
2. Add AI/ML API extraction against mock scraped content.
3. Add Bright Data SERP source discovery.
4. Add Bright Data Web Unlocker scraping.
5. Add Bright Data Browser API only for JS-heavy fallback.
6. Add Cognee graph memory.
7. Add Triggerware or Speechmatics only if the main demo is already stable.

## 10. Backend Team Checklist

- [ ] Confirm the backend loads `.env`.
- [ ] Keep mock mode functional without any live external services.
- [ ] Add Bright Data REST client using `BRIGHT_DATA_API_ENDPOINT`.
- [ ] Add SERP discovery using `BRIGHT_DATA_SERP_ZONE`.
- [ ] Add Unlocker fetching using `BRIGHT_DATA_UNLOCKER_ZONE`.
- [ ] Add Playwright Browser API fallback using `BRIGHT_DATA_BROWSER_WS`.
- [ ] Add AI/ML API client using OpenAI-compatible configuration.
- [ ] Pick and fill model IDs for extraction, briefing, and drafts.
- [ ] Add Cognee wrapper with graceful fallback.
- [ ] Confirm no secret values are logged in app logs or frontend responses.
