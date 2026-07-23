"""
fetch_jobs.py
Pulls fresh job listings from multiple sources:
  1. Adzuna API        (needs free API key)
  2. Arbeitnow API     (no key needed)
  3. RemoteOK API       (no key needed)
  4. Greenhouse boards  (no key needed, per-company)
  5. Lever boards       (no key needed, per-company)

Returns a single flat list of job dicts with a common shape:
  {
    "id": str,            # unique id (source + original id)
    "title": str,
    "company": str,
    "location": str,
    "url": str,
    "source": str,
    "posted_date": str,   # ISO date if available, else ""
    "description": str,
  }
"""

import os
import requests
import yaml

ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")

HEADERS = {"User-Agent": "personal-job-tracker/1.0"}


def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def fetch_adzuna(query, location, max_results=20):
    """Adzuna free API. Sign up at https://developer.adzuna.com/ for APP_ID + APP_KEY."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("  [Adzuna] Skipped — no API credentials set (ADZUNA_APP_ID / ADZUNA_APP_KEY).")
        return []

    country = "in" if location.lower() == "india" else "gb"
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": max_results,
        "what": query,
        "content-type": "application/json",
    }
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        jobs = []
        for item in data.get("results", []):
            jobs.append({
                "id": f"adzuna-{item.get('id')}",
                "title": item.get("title", ""),
                "company": (item.get("company") or {}).get("display_name", "Unknown"),
                "location": (item.get("location") or {}).get("display_name", ""),
                "url": item.get("redirect_url", ""),
                "source": "Adzuna",
                "posted_date": item.get("created", "")[:10],
                "description": item.get("description", ""),
            })
        return jobs
    except Exception as e:
        print(f"  [Adzuna] Error fetching '{query}': {e}")
        return []


def fetch_arbeitnow(query):
    """Arbeitnow API — free, no key required. Good for remote + tech roles."""
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        jobs = []
        q_lower = query.lower()
        for item in data.get("data", []):
            title = item.get("title", "")
            if q_lower not in title.lower():
                continue
            jobs.append({
                "id": f"arbeitnow-{item.get('slug')}",
                "title": title,
                "company": item.get("company_name", "Unknown"),
                "location": item.get("location", "") or "Remote",
                "url": item.get("url", ""),
                "source": "Arbeitnow",
                "posted_date": "",
                "description": item.get("description", ""),
            })
        return jobs
    except Exception as e:
        print(f"  [Arbeitnow] Error fetching '{query}': {e}")
        return []


def fetch_remoteok(query):
    """RemoteOK API — free, no key required. Remote jobs only."""
    url = "https://remoteok.com/api"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        jobs = []
        q_lower = query.lower()
        for item in data:
            if not isinstance(item, dict) or "position" not in item:
                continue
            title = item.get("position", "")
            if q_lower not in title.lower():
                continue
            jobs.append({
                "id": f"remoteok-{item.get('id')}",
                "title": title,
                "company": item.get("company", "Unknown"),
                "location": "Remote",
                "url": item.get("url", ""),
                "source": "RemoteOK",
                "posted_date": item.get("date", "")[:10] if item.get("date") else "",
                "description": item.get("description", ""),
            })
        return jobs
    except Exception as e:
        print(f"  [RemoteOK] Error fetching '{query}': {e}")
        return []


def fetch_greenhouse(company_slug):
    """Greenhouse job board API for a specific company. No key needed."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        jobs = []
        for item in data.get("jobs", []):
            jobs.append({
                "id": f"greenhouse-{company_slug}-{item.get('id')}",
                "title": item.get("title", ""),
                "company": company_slug,
                "location": (item.get("location") or {}).get("name", ""),
                "url": item.get("absolute_url", ""),
                "source": "Greenhouse",
                "posted_date": (item.get("updated_at") or "")[:10],
                "description": "",
            })
        return jobs
    except Exception as e:
        print(f"  [Greenhouse:{company_slug}] Error: {e}")
        return []


def fetch_lever(company_slug):
    """Lever job board API for a specific company. No key needed."""
    url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        jobs = []
        for item in data:
            jobs.append({
                "id": f"lever-{company_slug}-{item.get('id')}",
                "title": item.get("text", ""),
                "company": company_slug,
                "location": (item.get("categories") or {}).get("location", ""),
                "url": item.get("hostedUrl", ""),
                "source": "Lever",
                "posted_date": "",
                "description": item.get("descriptionPlain", "")[:500],
            })
        return jobs
    except Exception as e:
        print(f"  [Lever:{company_slug}] Error: {e}")
        return []


def fetch_all_jobs(config):
    """Runs every source across every target title / company and merges results."""
    all_jobs = {}
    titles = config.get("target_titles", [])
    locations = config.get("locations", ["India"])

    print(f"Fetching jobs for {len(titles)} title(s)...")
    for title in titles:
        print(f" -> {title}")
        for loc in locations:
            for job in fetch_adzuna(title, loc):
                all_jobs[job["id"]] = job
        for job in fetch_arbeitnow(title):
            all_jobs[job["id"]] = job
        for job in fetch_remoteok(title):
            all_jobs[job["id"]] = job

    companies = config.get("target_companies", {})
    for slug in companies.get("greenhouse", []):
        print(f" -> Greenhouse: {slug}")
        for job in fetch_greenhouse(slug):
            all_jobs[job["id"]] = job
    for slug in companies.get("lever", []):
        print(f" -> Lever: {slug}")
        for job in fetch_lever(slug):
            all_jobs[job["id"]] = job

    print(f"Total unique jobs fetched: {len(all_jobs)}")
    return list(all_jobs.values())


if __name__ == "__main__":
    cfg = load_config()
    jobs = fetch_all_jobs(cfg)
    import json
    with open("raw_jobs.json", "w") as f:
        json.dump(jobs, f, indent=2)
    print("Saved raw_jobs.json")
