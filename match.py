"""
match.py
Scores fetched jobs against your profile and keeps a persistent, running
list of active matches (matches_store.json) — so jobs don't disappear just
because you already saw them. Each job stays on your dashboard until it's
older than `keep_days` (set in config.yaml), giving you a real window to apply.
"""

import json
import os
import re
from datetime import datetime, timezone, timedelta

STORE_FILE = "matches_store.json"


def load_store():
    if os.path.exists(STORE_FILE):
        with open(STORE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_store(store):
    with open(STORE_FILE, "w") as f:
        json.dump(store, f, indent=2)


def _normalize(text):
    return re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())


def score_job(job, target_titles, skills):
    """Returns a 0-100 relevance score."""
    title_text = _normalize(job.get("title", ""))
    desc_text = _normalize(job.get("description", ""))
    combined = title_text + " " + desc_text

    score = 0
    matched_skills = []

    # Title match — heaviest weight
    for t in target_titles:
        t_norm = _normalize(t)
        if t_norm and t_norm in title_text:
            score += 50
            break
        words = [w for w in t_norm.split() if len(w) > 2]
        if words and all(w in title_text for w in words):
            score += 35
            break

    # Skill overlap
    for skill in skills:
        s_norm = _normalize(skill)
        if s_norm and s_norm in combined:
            matched_skills.append(skill)
    score += min(50, len(matched_skills) * 6)

    return min(100, score), matched_skills


def filter_and_rank(jobs, config):
    target_titles = config.get("target_titles", [])
    skills = config.get("skills", [])
    min_score = config.get("min_match_score", 15)
    keep_days = config.get("keep_days", 14)

    store = load_store()
    today = datetime.now(timezone.utc).date()

    for job in jobs:
        score, matched_skills = score_job(job, target_titles, skills)
        if score < min_score:
            continue

        job_id = job["id"]
        if job_id in store:
            store[job_id]["match_score"] = score
            store[job_id]["matched_skills"] = matched_skills
            store[job_id]["title"] = job.get("title", store[job_id].get("title"))
            store[job_id]["url"] = job.get("url", store[job_id].get("url"))
        else:
            entry = dict(job)
            entry["match_score"] = score
            entry["matched_skills"] = matched_skills
            entry["first_seen"] = today.isoformat()
            store[job_id] = entry

    cutoff = today - timedelta(days=keep_days)
    pruned_store = {}
    for job_id, entry in store.items():
        try:
            first_seen = datetime.fromisoformat(entry["first_seen"]).date()
        except Exception:
            first_seen = today
        if first_seen >= cutoff:
            pruned_store[job_id] = entry

    save_store(pruned_store)

    active = list(pruned_store.values())
    active.sort(key=lambda j: j["match_score"], reverse=True)
    return active


if __name__ == "__main__":
    import yaml
    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)
    with open("raw_jobs.json") as f:
        raw_jobs = json.load(f)

    matches = filter_and_rank(raw_jobs, cfg)
    with open("matched_jobs.json", "w") as f:
        json.dump(matches, f, indent=2)
    print(f"{len(matches)} active matching job(s) currently on your dashboard.")
