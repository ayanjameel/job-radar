"""
match.py
Scores each fetched job against your profile (target titles + skills),
filters out jobs already seen before, and ranks the rest.
"""

import json
import os
import re

SEEN_FILE = "seen_jobs.json"


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen_ids):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(list(seen_ids)), f, indent=2)


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
        # partial word overlap fallback
        words = [w for w in t_norm.split() if len(w) > 2]
        if words and all(w in title_text for w in words):
            score += 35
            break

    # Skill overlap — up to 50 points, ~5 points per matched skill (capped)
    for skill in skills:
        s_norm = _normalize(skill)
        if s_norm and s_norm in combined:
            matched_skills.append(skill)
    score += min(50, len(matched_skills) * 6)

    return min(100, score), matched_skills


def filter_and_rank(jobs, config):
    target_titles = config.get("target_titles", [])
    skills = config.get("skills", [])
    min_score = config.get("min_match_score", 25)

    seen = load_seen()
    results = []

    for job in jobs:
        if job["id"] in seen:
            continue
        score, matched_skills = score_job(job, target_titles, skills)
        if score < min_score:
            continue
        job["match_score"] = score
        job["matched_skills"] = matched_skills
        results.append(job)

    results.sort(key=lambda j: j["match_score"], reverse=True)

    # Mark all fetched jobs (matched or not) as seen so we don't re-show them tomorrow
    for job in jobs:
        seen.add(job["id"])
    save_seen(seen)

    return results


if __name__ == "__main__":
    import yaml
    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)
    with open("raw_jobs.json") as f:
        raw_jobs = json.load(f)

    matches = filter_and_rank(raw_jobs, cfg)
    with open("matched_jobs.json", "w") as f:
        json.dump(matches, f, indent=2)
    print(f"{len(matches)} new matching jobs found (out of {len(raw_jobs)} fetched).")
