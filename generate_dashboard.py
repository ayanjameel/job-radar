"""
generate_dashboard.py
Builds docs/index.html — a static dashboard page listing all currently
matched jobs, ranked by relevance. This file is what GitHub Pages serves.
"""

import json
import os
from datetime import datetime, timezone

OUTPUT_PATH = os.path.join("docs", "index.html")


def build_card(job):
    skills_html = "".join(
        f'<span class="pill">{s}</span>' for s in job.get("matched_skills", [])[:8]
    )
    score = job.get("match_score", 0)
    posted = job.get("posted_date") or "—"
    return f"""
    <article class="card">
      <div class="card-top">
        <div>
          <h2 class="title">{job.get('title', 'Untitled role')}</h2>
          <p class="company">{job.get('company', 'Unknown company')} &middot; {job.get('location', '')}</p>
        </div>
        <div class="score" title="Match score">{score}</div>
      </div>
      <div class="meta">
        <span class="source-tag">{job.get('source', '')}</span>
        <span class="posted">Posted: {posted}</span>
      </div>
      <div class="pills">{skills_html}</div>
      <a class="apply-btn" href="{job.get('url', '#')}" target="_blank" rel="noopener">Apply →</a>
    </article>
    """


def generate(matched_jobs):
    os.makedirs("docs", exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    cards_html = "".join(build_card(j) for j in matched_jobs) if matched_jobs else (
        '<p class="empty">No new matching jobs today. Check back tomorrow — '
        "the list refreshes daily.</p>"
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Job Radar — Daily Matches</title>
<style>
  :root {{
    --bg: #0f1417;
    --panel: #161d22;
    --border: #26313a;
    --ink: #e9edf0;
    --muted: #8fa1ac;
    --accent: #4fd1c5;
    --accent-soft: rgba(79,209,197,0.12);
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: 'Segoe UI', 'Inter', system-ui, sans-serif;
    padding: 40px 20px 80px;
  }}
  .wrap {{ max-width: 760px; margin: 0 auto; }}
  header {{ margin-bottom: 32px; }}
  .eyebrow {{
    color: var(--accent);
    font-size: 13px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 600;
  }}
  h1 {{
    font-size: 32px;
    margin: 6px 0 4px;
    letter-spacing: -0.01em;
  }}
  .sub {{ color: var(--muted); font-size: 14px; }}
  .card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 16px;
  }}
  .card-top {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
  }}
  .title {{ font-size: 18px; margin: 0 0 4px; }}
  .company {{ color: var(--muted); font-size: 14px; margin: 0; }}
  .score {{
    background: var(--accent-soft);
    color: var(--accent);
    font-weight: 700;
    font-size: 14px;
    border-radius: 8px;
    padding: 6px 10px;
    min-width: 34px;
    text-align: center;
  }}
  .meta {{
    display: flex;
    gap: 14px;
    margin-top: 10px;
    font-size: 12px;
    color: var(--muted);
  }}
  .source-tag {{
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 2px 10px;
  }}
  .pills {{ margin-top: 12px; display: flex; flex-wrap: wrap; gap: 6px; }}
  .pill {{
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--border);
    color: var(--muted);
    font-size: 11px;
    border-radius: 999px;
    padding: 3px 9px;
  }}
  .apply-btn {{
    display: inline-block;
    margin-top: 16px;
    background: var(--accent);
    color: #06201d;
    font-weight: 700;
    font-size: 13px;
    text-decoration: none;
    padding: 9px 16px;
    border-radius: 8px;
  }}
  .apply-btn:hover {{ opacity: 0.88; }}
  .empty {{ color: var(--muted); text-align: center; margin-top: 60px; }}
  footer {{
    text-align: center;
    color: var(--muted);
    font-size: 12px;
    margin-top: 40px;
  }}
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="eyebrow">Job Radar</div>
      <h1>Today's matches</h1>
      <p class="sub">Last refreshed: {generated_at} &middot; {len(matched_jobs)} new match(es)</p>
    </header>
    {cards_html}
    <footer>Refreshes automatically once a day via GitHub Actions.</footer>
  </div>
</body>
</html>
"""
    with open(OUTPUT_PATH, "w") as f:
        f.write(html)
    print(f"Dashboard written to {OUTPUT_PATH}")


if __name__ == "__main__":
    path = "matched_jobs.json"
    jobs = []
    if os.path.exists(path):
        with open(path) as f:
            jobs = json.load(f)
    generate(jobs)
