# 💼 Smart Job Application Tracker

A clean Streamlit dashboard to manage a job search, backed by SQLite.
Built with **Python · SQLite · Pandas · Streamlit · Altair**.

<!-- Add screenshots: docs/dashboard.png, docs/applications.png, docs/resume-match.png -->

## Features
- **Dashboard:** KPI cards (Total, Applied, Interviews, Offers, Rejected), status donut chart,
  weekly/monthly applications chart, most-applied companies and roles
- **Follow-up Due:** overdue and next-7-day follow-ups, plus upcoming interviews
- **Add Job:** company, role, location, salary, job URL, status, applied / interview / follow-up dates, notes
- **Applications:** search (company, role, location), status filter, sorting, edit, delete (with confirmation)
- **Export:** download the current (filtered) view as CSV or Excel
- **Resume Match:** Match Percentage, Matched Skills and Missing Skills
- **Sample data:** one-click demo data from the sidebar (empty tracker only)

Status pipeline: Saved → Applied → Assessment → Interview → Offer / Rejected

## ⚠️ About Resume Match
The analyzer is **keyword-based**. It finds known skills (a built-in list plus a few aliases such as
`js` → `javascript`) in the job description and compares them with the skills you type. It does not use
ML/NLP and can't judge context, experience level or unlisted skills. Extend `SKILL_BANK` in `analyzer.py`
to cover more skills.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Data is stored in `jobs.db` (created automatically, git-ignored).

## Project structure
| File | Purpose |
|---|---|
| `app.py` | Streamlit UI (dashboard, forms, charts, export) |
| `db.py` | SQLite CRUD, search/filter/sort queries, demo data |
| `analyzer.py` | Keyword-based resume matcher |
| `requirements.txt` | Dependencies |

## Future improvements
Email reminders, PDF resume upload, richer skill matching, unit tests.
