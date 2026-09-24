import io
from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

import analyzer
import db

st.set_page_config(page_title="Smart Job Tracker", page_icon="💼", layout="wide")
db.init_db()

COLORS = {"Saved": "#94a3b8", "Applied": "#3b82f6", "Assessment": "#f59e0b",
          "Interview": "#8b5cf6", "Offer": "#10b981", "Rejected": "#ef4444"}
DEFAULT_SKILLS = ("Python, SQL, Pandas, Streamlit, Git, Excel, Postman, "
                  "Manual Testing, Test Cases, Regression Testing")

st.markdown("""<style>
.block-container{padding-top:2rem;max-width:1200px}
.kpi{border:1px solid rgba(128,128,128,.25);border-top:4px solid var(--c);
     border-radius:10px;padding:14px 16px;background:rgba(128,128,128,.06)}
.kpi .v{font-size:2rem;font-weight:700;line-height:1.15}
.kpi .l{font-size:.75rem;opacity:.7;text-transform:uppercase;letter-spacing:.06em}
.chip{display:inline-block;padding:3px 12px;margin:3px 2px;border-radius:999px;
      font-size:.85rem;color:#fff}
</style>""", unsafe_allow_html=True)


# ---------- helpers ----------
def to_date(v):
    return date.fromisoformat(v) if isinstance(v, str) and v else None


def iso(d):
    return d.isoformat() if d else None


def kpi(col, label, value, color):
    col.markdown(f'<div class="kpi" style="--c:{color}"><div class="l">{label}</div>'
                 f'<div class="v">{value}</div></div>', unsafe_allow_html=True)


def chips(items, color):
    return "".join(f'<span class="chip" style="background:{color}">{i}</span>' for i in items)


def days_until(series):
    return (pd.to_datetime(series) - pd.Timestamp(date.today())).dt.days


def due_label(n):
    return f"Overdue by {int(-n)}d" if n < 0 else "Today" if n == 0 else f"In {int(n)}d"


def hbar(series, color):
    d = series.head(5).rename_axis("name").reset_index(name="count")
    return alt.Chart(d).mark_bar(color=color, cornerRadiusEnd=4).encode(
        x=alt.X("count:Q", axis=alt.Axis(tickMinStep=1), title=None),
        y=alt.Y("name:N", sort="-x", title=None), tooltip=["name", "count"]).properties(height=200)


def job_form(key, job=None):
    j = job or {}
    a, b = st.columns(2)
    company = a.text_input("Company*", j.get("company") or "", key=f"{key}co")
    role = b.text_input("Role*", j.get("role") or "", key=f"{key}ro")
    location = a.text_input("Location", j.get("location") or "", key=f"{key}lo")
    salary = b.text_input("Salary", j.get("salary") or "", key=f"{key}sa", placeholder="e.g. ₹6 LPA")
    url = st.text_input("Job URL", j.get("url") or "", key=f"{key}ur", placeholder="https://...")
    status = a.selectbox("Status", db.STATUSES,
                         index=db.STATUSES.index(j.get("status") or "Saved"), key=f"{key}st")
    applied = b.date_input("Applied date", to_date(j.get("applied_date")), key=f"{key}ad")
    interview = a.date_input("Interview date", to_date(j.get("interview_date")), key=f"{key}id")
    follow = b.date_input("Follow-up date", to_date(j.get("followup_date")), key=f"{key}fd")
    notes = st.text_area("Notes", j.get("notes") or "", key=f"{key}no")
    return dict(company=company.strip(), role=role.strip(), location=location.strip(),
                salary=salary.strip(), url=url.strip(), status=status, applied_date=iso(applied),
                interview_date=iso(interview), followup_date=iso(follow), notes=notes)


def validate(d):
    if not d["company"] or not d["role"]:
        return "Company and Role are required."
    if d["url"] and not d["url"].startswith(("http://", "https://")):
        return "Job URL must start with http:// or https://"
    if d["applied_date"] and d["followup_date"] and d["followup_date"] < d["applied_date"]:
        return "Follow-up date can't be before the applied date."
    return None


# ---------- header / sidebar ----------
if msg := st.session_state.pop("flash", None):
    st.toast(msg, icon="✅")

with st.sidebar:
    st.header("💼 Job Tracker")
    st.caption("Python · SQLite · Pandas · Streamlit")
    st.write("Track applications from **Saved → Offer**, watch follow-ups, "
             "and check resume-to-JD keyword fit.")
    if st.button("Load sample data"):
        if db.seed_demo():
            st.session_state["flash"] = "Sample data loaded"
            st.rerun()
        st.info("Sample data loads only into an empty tracker.")

st.title("💼 Smart Job Application Tracker")
st.caption("Manage your job search in one place.")
all_jobs = db.get_jobs()
t_dash, t_add, t_list, t_match = st.tabs(
    ["📊 Dashboard", "➕ Add Job", "📋 Applications", "🎯 Resume Match"])

# ---------- Dashboard ----------
with t_dash:
    if all_jobs.empty:
        st.info("No applications yet. Add one in the **Add Job** tab, or load sample data from the sidebar.")
    else:
        cnt = all_jobs["status"].value_counts()
        cols = st.columns(5)
        for col, (lbl, val, clr) in zip(cols, [
                ("Total Applications", len(all_jobs), "#0ea5e9"),
                ("Applied", cnt.get("Applied", 0), COLORS["Applied"]),
                ("Interviews", cnt.get("Interview", 0), COLORS["Interview"]),
                ("Offers", cnt.get("Offer", 0), COLORS["Offer"]),
                ("Rejected", cnt.get("Rejected", 0), COLORS["Rejected"])]):
            kpi(col, lbl, int(val), clr)
        st.write("")

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Application status")
            sd = cnt.rename_axis("status").reset_index(name="count")
            st.altair_chart(alt.Chart(sd).mark_arc(innerRadius=55).encode(
                theta="count:Q", tooltip=["status", "count"],
                color=alt.Color("status:N", legend=alt.Legend(title=None),
                                scale=alt.Scale(domain=list(COLORS), range=list(COLORS.values())))
            ).properties(height=280))
        with c2:
            st.subheader("Applications over time")
            per = st.radio("Group by", ["Weekly", "Monthly"], horizontal=True,
                           label_visibility="collapsed")
            ap = all_jobs.dropna(subset=["applied_date"])
            if ap.empty:
                st.caption("Add applied dates to see the trend.")
            else:
                freq = "W" if per == "Weekly" else "M"
                t = pd.to_datetime(ap["applied_date"]).dt.to_period(freq).value_counts().sort_index()
                fmt = "%d %b" if freq == "W" else "%b %Y"
                td = pd.DataFrame({"period": [p.start_time.strftime(fmt) for p in t.index],
                                   "applications": t.values})
                st.altair_chart(alt.Chart(td).mark_bar(
                    color="#3b82f6", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                    x=alt.X("period:N", sort=None, title=None),
                    y=alt.Y("applications:Q", axis=alt.Axis(tickMinStep=1), title=None),
                    tooltip=["period", "applications"]).properties(height=280))

        # Follow-up due
        st.subheader("⏰ Follow-up due")
        openj = ~all_jobs["status"].isin(["Offer", "Rejected"])
        fu = days_until(all_jobs["followup_date"])
        due = all_jobs[openj & fu.notna() & (fu <= 7)].assign(days=fu).sort_values("days")
        iv = days_until(all_jobs["interview_date"])
        soon = all_jobs[iv.notna() & (iv >= 0)].assign(days=iv).sort_values("days")
        f1, f2 = st.columns([3, 2])
        with f1:
            if due.empty:
                st.success("No follow-ups due in the next 7 days 🎉")
            else:
                n_over = int((due["days"] < 0).sum())
                (st.warning if n_over else st.info)(
                    f"{len(due)} follow-up(s) due within 7 days · {n_over} overdue")
                out = due[["company", "role", "status", "followup_date"]].copy()
                out["due"] = due["days"].map(due_label)
                st.dataframe(out, hide_index=True)
        with f2:
            st.write("**📅 Upcoming interviews**")
            if soon.empty:
                st.caption("None scheduled.")
            else:
                out = soon[["company", "role", "interview_date"]].copy()
                out["in"] = soon["days"].map(due_label)
                st.dataframe(out, hide_index=True)

        c3, c4 = st.columns(2)
        c3.subheader("🏢 Most-applied companies")
        c3.altair_chart(hbar(all_jobs["company"].value_counts(), "#0ea5e9"))
        c4.subheader("🧑‍💻 Most-applied roles")
        c4.altair_chart(hbar(all_jobs["role"].value_counts(), "#8b5cf6"))

# ---------- Add Job ----------
with t_add:
    with st.form("add_form", clear_on_submit=True):
        data = job_form("new")
        if st.form_submit_button("Save application", type="primary"):
            err = validate(data)
            if err:
                st.error(err)
            else:
                db.add_job(data)
                st.session_state["flash"] = f"Saved {data['company']} – {data['role']}"
                st.rerun()

# ---------- Applications ----------
with t_list:
    f1, f2, f3 = st.columns([3, 3, 2])
    q = f1.text_input("🔎 Search", placeholder="Company, role or location")
    sel = f2.multiselect("Status", db.STATUSES)
    sort = f3.selectbox("Sort by", list(db.SORTS))
    view = db.get_jobs(q, sel, sort)
    st.caption(f"Showing {len(view)} of {len(all_jobs)} applications")
    st.dataframe(view, hide_index=True, column_config={
        "url": st.column_config.LinkColumn("Job URL", display_text="Open")})

    buf = io.BytesIO()
    view.to_excel(buf, index=False)
    d1, d2, _ = st.columns([1, 1, 4])
    d1.download_button("📥 Export CSV", view.to_csv(index=False), "applications.csv", "text/csv")
    d2.download_button("📥 Export Excel", buf.getvalue(), "applications.xlsx")

    if not view.empty:
        with st.expander("✏️ Edit / Delete an application"):
            labels = {int(r.id): f"#{r.id} · {r.company} — {r.role} ({r.status})"
                      for r in view.itertuples()}
            jid = st.selectbox("Select application", list(labels), format_func=labels.get)
            job = view[view["id"] == jid].iloc[0].to_dict()
            with st.form(f"edit_{jid}"):
                new = job_form(f"e{jid}", job)
                confirm = st.checkbox("Confirm delete")
                u, d = st.columns(2)
                do_update = u.form_submit_button("Update", type="primary")
                do_delete = d.form_submit_button("🗑️ Delete")
            if do_update:
                err = validate(new)
                if err:
                    st.error(err)
                else:
                    db.update_job(jid, new)
                    st.session_state["flash"] = "Application updated"
                    st.rerun()
            if do_delete:
                if confirm:
                    db.delete_job(jid)
                    st.session_state["flash"] = "Application deleted"
                    st.rerun()
                else:
                    st.error("Tick 'Confirm delete' first.")

# ---------- Resume Match ----------
with t_match:
    st.info("🔍 **Keyword-based analysis.** Compares skill keywords found in the job description "
            "with the skills you list. It doesn't understand context, experience level, or "
            "synonyms beyond a small alias list, so use it as a quick guide, not a verdict.")
    a, b = st.columns(2)
    skills = a.text_area("Your skills (comma-separated)", DEFAULT_SKILLS, height=220)
    jd = b.text_area("Paste job description", height=220)
    if st.button("Analyze match", type="primary"):
        if not jd.strip():
            st.warning("Paste a job description first.")
        else:
            r = analyzer.analyze(skills, jd)
            if r["total"] == 0:
                st.warning("No known skill keywords found in this job description.")
            else:
                m1, m2, m3 = st.columns(3)
                m1.metric("Match Percentage", f"{r['percent']}%")
                m2.metric("Matched Skills", len(r["matched"]))
                m3.metric("Missing Skills", len(r["missing"]))
                st.progress(r["percent"] / 100)
                g, x = st.columns(2)
                g.markdown("**✅ Matched Skills**")
                g.markdown(chips(r["matched"], "#10b981") or "_None_", unsafe_allow_html=True)
                x.markdown("**❌ Missing Skills**")
                x.markdown(chips(r["missing"], "#ef4444") or "_None_", unsafe_allow_html=True)
