"""SQLite data layer for the Smart Job Application Tracker."""
import sqlite3
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "jobs.db"
STATUSES = ["Saved", "Applied", "Assessment", "Interview", "Offer", "Rejected"]
FIELDS = ["company", "role", "location", "salary", "url", "status",
          "applied_date", "interview_date", "followup_date", "notes"]
SORTS = {
    "Newest first": "id DESC",
    "Oldest first": "id ASC",
    "Applied date": "applied_date DESC",
    "Follow-up date": "followup_date IS NULL, followup_date ASC",
    "Company (A-Z)": "company COLLATE NOCASE ASC",
}


def _conn():
    return sqlite3.connect(DB_PATH)


def _write(sql, params=()):
    with closing(_conn()) as c, c:  # commits on success, always closes
        c.execute(sql, params)


def init_db():
    _write("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT NOT NULL, role TEXT NOT NULL,
        location TEXT, salary TEXT, url TEXT,
        status TEXT DEFAULT 'Saved',
        applied_date TEXT, interview_date TEXT, followup_date TEXT,
        notes TEXT)""")
    _write("CREATE INDEX IF NOT EXISTS idx_status ON applications(status)")


def add_job(d: dict):
    _write(f"INSERT INTO applications ({','.join(FIELDS)}) "
           f"VALUES ({','.join(':' + f for f in FIELDS)})", d)


def update_job(job_id: int, d: dict):
    sets = ",".join(f"{f}=:{f}" for f in FIELDS)
    _write(f"UPDATE applications SET {sets} WHERE id=:id", {**d, "id": job_id})


def delete_job(job_id: int):
    _write("DELETE FROM applications WHERE id=?", (job_id,))


def get_jobs(search="", statuses=None, sort="Newest first") -> pd.DataFrame:
    """Fetch applications with optional text search, status filter and sorting."""
    where, params = [], []
    if search and search.strip():
        like = f"%{search.strip()}%"
        where.append("(company LIKE ? OR role LIKE ? OR location LIKE ?)")
        params += [like] * 3
    if statuses:
        where.append(f"status IN ({','.join('?' * len(statuses))})")
        params += list(statuses)
    sql = "SELECT * FROM applications"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY " + SORTS.get(sort, SORTS["Newest first"])
    with closing(_conn()) as c:
        return pd.read_sql(sql, c, params=params)


def seed_demo() -> int:
    """Insert sample data (only into an empty tracker). Returns rows added."""
    if not get_jobs().empty:
        return 0
    t = date.today()
    day = lambda n: None if n is None else (t + timedelta(days=n)).isoformat()
    rows = [
        ("Zoho", "Python Developer", "Chennai", "₹6 LPA", "Interview", -14, 3, None, "Round 2: DSA + SQL"),
        ("Freshworks", "Data Analyst", "Chennai", "₹7 LPA", "Assessment", -10, None, 2, "Online test link received"),
        ("TCS", "Junior Software Engineer", "Hyderabad", "₹4 LPA", "Applied", -21, None, -3, "Ping recruiter"),
        ("Infosys", "QA Engineer", "Bengaluru", "₹4.5 LPA", "Applied", -9, None, 1, ""),
        ("Wipro", "Data Analyst", "Pune", "₹4.2 LPA", "Rejected", -30, None, None, "Not shortlisted"),
        ("Accenture", "Python Developer", "Hyderabad", "₹5 LPA", "Offer", -40, -20, None, "Offer received"),
        ("Capgemini", "Test Engineer", "Chennai", "₹4 LPA", "Applied", -5, None, 4, ""),
        ("Cognizant", "Data Analyst Trainee", "Remote", "₹4.5 LPA", "Saved", None, None, None, "Apply before Friday"),
        ("Razorpay", "Software Engineer I", "Bengaluru", "₹10 LPA", "Applied", -3, None, 5, "Referral via LinkedIn"),
        ("Zoho", "QA Engineer", "Chennai", "₹5 LPA", "Rejected", -45, None, None, ""),
        ("Amazon", "Data Analyst", "Hyderabad", "₹9 LPA", "Interview", -18, 6, -1, "Phone screen done"),
        ("Tech Mahindra", "Python Developer", "Pune", "₹4 LPA", "Applied", -60, None, -10, ""),
    ]
    for co, ro, lo, sa, st_, ap, iv, fu, no in rows:
        add_job(dict(company=co, role=ro, location=lo, salary=sa, url="", status=st_,
                     applied_date=day(ap), interview_date=day(iv), followup_date=day(fu), notes=no))
    return len(rows)
