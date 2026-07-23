"""
run_all.py
Runs the full daily pipeline: fetch -> match -> generate dashboard.
This is the single script GitHub Actions (or you, locally) needs to run.
"""

import json
import yaml

from fetch_jobs import fetch_all_jobs
from match import filter_and_rank
from generate_dashboard import generate


def main():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    print("=== Step 1/3: Fetching jobs ===")
    jobs = fetch_all_jobs(config)
    with open("raw_jobs.json", "w") as f:
        json.dump(jobs, f, indent=2)

    print("\n=== Step 2/3: Matching against your profile ===")
    matches = filter_and_rank(jobs, config)
    with open("matched_jobs.json", "w") as f:
        json.dump(matches, f, indent=2)
    print(f"{len(matches)} new matching job(s) found.")

    print("\n=== Step 3/3: Building dashboard ===")
    generate(matches)

    print("\nDone. Open docs/index.html (or your GitHub Pages link) to see results.")


if __name__ == "__main__":
    main()
