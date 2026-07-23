# Job Radar — Your Personal Daily Job Tracker

Automatically finds fresh job listings matching your profile every day and
shows them on a simple webpage — no manual searching needed.

You don't need to write any code. Just follow the steps below once, and it
runs itself daily.

---

## What this does

1. Every day, a robot (GitHub Actions) wakes up and searches job boards +
   company career pages for roles matching your target titles.
2. It scores each listing against your skills/resume profile.
3. It builds a simple dashboard webpage listing the best matches, with
   direct "Apply" links.
4. You just open the link each morning and click through to apply.

---

## One-time setup (about 15–20 minutes)

### Step 1 — Create a free GitHub account (skip if you have one)
Go to [github.com](https://github.com) and sign up.

### Step 2 — Create a new repository
1. Click the **+** icon (top right) → **New repository**
2. Name it something like `job-radar`
3. Set it to **Public** (required for free GitHub Pages)
4. Click **Create repository**

### Step 3 — Upload these project files
1. On your new repo's page, click **Add file → Upload files**
2. Drag in every file/folder from this project (keep the folder structure —
   especially `.github/workflows/daily-job-search.yml`)
3. Click **Commit changes**

> Tip: if you're comfortable with GitHub Desktop or `git`, cloning and
> pushing works too — but drag-and-drop upload is fine.

### Step 4 — Get a free Adzuna API key (2 minutes)
Adzuna is one of the job sources. It's free but needs a key:
1. Go to [developer.adzuna.com](https://developer.adzuna.com/)
2. Sign up → you'll get an **App ID** and **App Key** instantly
3. Keep this tab open, you'll need both values in the next step

*(Arbeitnow and RemoteOK need no signup — they're already wired in.)*

### Step 5 — Add your API key as a GitHub Secret
Secrets keep your keys private (never put them directly in code).
1. In your repo: **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Add:
   - Name: `ADZUNA_APP_ID` → Value: (your App ID)
   - Name: `ADZUNA_APP_KEY` → Value: (your App Key)

### Step 6 — Turn on GitHub Pages (this makes your dashboard viewable)
1. In your repo: **Settings → Pages**
2. Under "Build and deployment" → Source: **Deploy from a branch**
3. Branch: `main`, folder: `/docs` → **Save**
4. GitHub will give you a URL like:
   `https://yourusername.github.io/job-radar/`
   This is your daily dashboard link — bookmark it!

### Step 7 — Run it for the first time
1. Go to the **Actions** tab in your repo
2. Click **Daily Job Search** (left sidebar) → **Run workflow** → **Run workflow**
3. Wait ~1 minute, then refresh — you should see a green checkmark
4. Open your GitHub Pages URL from Step 6 — your dashboard should now show
   matched jobs!

After this, it runs **automatically every day at 3:00 AM UTC** (~8:30 AM
IST) with zero effort from you.

---

## Customizing your search

Open `config.yaml` in your repo (click it → pencil/edit icon) any time to:
- Add/remove **target job titles**
- Add/remove **skills** used for matching
- Add **specific companies** to track (see below)
- Adjust **minimum match score** (lower = more results, higher = stricter)

Commit the change, and it takes effect on the next daily run (or trigger it
manually via Actions → Run workflow).

### Finding a company's Greenhouse/Lever slug
If you want to track a specific company:
1. Search `site:boards.greenhouse.io [company name]` or
   `site:jobs.lever.co [company name]` on Google
2. The slug is the part of the URL right after `greenhouse.io/` or `lever.co/`
   - e.g. `boards.greenhouse.io/stripe` → slug is `stripe`
   - e.g. `jobs.lever.co/netflix` → slug is `netflix`
3. Add it to `config.yaml` under `target_companies`

---

## Project files

| File | What it does |
|---|---|
| `config.yaml` | Your profile — edit this to change what jobs you're targeting |
| `fetch_jobs.py` | Pulls listings from Adzuna, Arbeitnow, RemoteOK, Greenhouse, Lever |
| `match.py` | Scores listings against your profile, filters out ones you've seen |
| `generate_dashboard.py` | Builds the `docs/index.html` dashboard page |
| `run_all.py` | Runs the full pipeline (fetch → match → dashboard) in one go |
| `seen_jobs.json` | Tracks which job IDs you've already been shown (auto-managed) |
| `.github/workflows/daily-job-search.yml` | The daily automation schedule |

---

## Running it locally instead (optional)

If you'd rather run it on your own computer instead of GitHub Actions:

```bash
pip install -r requirements.txt
export ADZUNA_APP_ID=your_id_here
export ADZUNA_APP_KEY=your_key_here
python run_all.py
```

Then open `docs/index.html` in your browser.

---

## Troubleshooting

- **No jobs showing up?** Try lowering `min_match_score` in `config.yaml`
  (e.g. from 25 to 15), or double check your Adzuna keys are set correctly.
- **Action shows a red X (failed)?** Click into it in the Actions tab —
  the log will show which step failed and why (usually a missing secret).
- **Want faster refresh?** Edit the `cron` line in the workflow file —
  cron format is `minute hour day month weekday` (all in UTC).
