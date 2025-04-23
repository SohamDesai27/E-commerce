"""
career_links_and_tech_jobs.py
─────────────────────────────
• Click “Fetch career-page links”  → Google search → returns one career URL per company.
• Pick companies and keywords      → JobSpy scrape  → lists U.S. tech jobs for them.
"""

import re, time, csv
import pandas as pd
import streamlit as st
from googlesearch import search          # pip install googlesearch-python
from jobspy import scrape_jobs           # pip install jobspy

st.set_page_config(page_title="Career & U.S. Tech-Job Finder", layout="wide")
st.title("🔗🎯 Company Career Pages + Tech Jobs (USA)")

# ─────────────────────────────────────────
# Full company list (edit if you like)
# ─────────────────────────────────────────
COMPANIES = [
    "Apple", "Microsoft", "NVIDIA", "Amazon", "Alphabet (Google)", "Saudi Aramco",
    "Meta Platforms (Facebook)", "Berkshire Hathaway", "Broadcom", "TSMC", "Tesla",
    "Walmart", "Eli Lilly", "JPMorgan Chase", "Visa", "Tencent", "Mastercard",
    "Exxon Mobil", "Netflix", "Costco", "UnitedHealth", "Procter & Gamble", "Oracle",
    "Johnson & Johnson", "Home Depot", "SAP", "ICBC", "Coca-Cola", "AbbVie",
    "Bank of America", "T-Mobile US", "LVMH", "Alibaba", "Hermès", "Novo Nordisk",
    "Nestlé", "Kweichow Moutai", "Philip Morris International", "ASML", "Samsung",
    "Agricultural Bank of China", "Roche", "Salesforce", "Chevron",
    "International Holding Company", "Toyota", "Palantir", "IBM", "L'Oréal",
    "China Mobile", "McDonald's", "Cisco", "Wells Fargo", "Abbott Laboratories",
    "China Construction Bank", "Novartis", "Linde", "AstraZeneca", "Bank of China",
    "General Electric", "Reliance Industries", "Merck", "Prosus", "HSBC", "PepsiCo",
    "Shell", "PetroChina", "AT&T", "American Express", "Morgan Stanley",
    "HDFC Bank", "Accenture", "Fomento Económico Mexicano", "Intuitive Surgical",
    "Deutsche Telekom", "Verizon", "Siemens", "Commonwealth Bank",
    "Thermo Fisher Scientific", "Inditex", "ServiceNow", "Intuit", "Goldman Sachs",
    "Royal Bank of Canada", "Blackstone Group", "RTX", "Walt Disney", "Xiaomi",
    "Qualcomm", "Uber", "Unilever", "Booking Holdings (Booking.com)", "Allianz SE",
    "Progressive", "BYD", "Adobe", "Amgen", "Sony", "AMD", "Boston Scientific"
]

# ─────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────
def looks_like_career_url(url: str) -> bool:
    """True if URL contains common career / jobs substrings."""
    return bool(re.search(r"(careers?|jobs?|work[-_]?with[-_]?us|join[-_]?us|employment)", url, re.I))

@st.cache_data(ttl=86_400, show_spinner=False)
def fetch_career_links(companies: list[str]) -> pd.DataFrame:
    """Return DataFrame with career pages (Google top result heuristic)."""
    rows = []
    for co in companies:
        query = f"{co} careers"
        link = next(
            (u for u in search(query, num_results=10) if looks_like_career_url(u)),
            "NOT FOUND"
        )
        rows.append({"company": co, "career_page": link})
        time.sleep(1)                   # courteous delay to Google
    return pd.DataFrame(rows)

def scrape_one_company(company: str,
                       keywords: str,
                       results: int = 300) -> pd.DataFrame:
    """Scrape public boards then filter to the exact company name."""
    df = scrape_jobs(
        site_name=["linkedin", "indeed", "google"],
        search_term=keywords,
        location="United States",
        results_wanted=results,
        hours_old=168,                  # last 7 days
        country_indeed="USA",
        linkedin_fetch_description=False,
        verbose=False
    )
    # Keep rows where the company cell equals (or closely matches) our target
    pattern = rf"^{re.escape(company)}$"
    return df[df["company"].str.contains(pattern, case=False, na=False)]

@st.cache_data(ttl=3_600, show_spinner=False)
def fetch_tech_jobs(companies: list[str], keywords: str) -> pd.DataFrame:
    frames = [scrape_one_company(c, keywords) for c in companies]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

# ─────────────────────────────────────────
# UI – Step 1: Career-page links
# ─────────────────────────────────────────
if "career_df" not in st.session_state:
    st.session_state.career_df = None

if st.button("🔍 Fetch career-page links (once/day)"):
    with st.spinner("Searching Google for career pages…"):
        st.session_state.career_df = fetch_career_links(COMPANIES)
    st.success("Career pages retrieved!")

career_df = st.session_state.career_df
if career_df is not None:
    st.subheader("Career-page links")
    st.dataframe(career_df, use_container_width=True)
    st.download_button(
        "⬇️ Download career links CSV",
        career_df.to_csv(index=False),
        file_name="career_pages.csv",
        mime="text/csv"
    )

# ─────────────────────────────────────────
# UI – Step 2: Tech-job scraping
# ─────────────────────────────────────────
st.divider()
st.header("🎯 Tech jobs in the United States")

default_kw = "software OR engineer OR developer OR 'data analyst' OR 'machine learning'"
keywords = st.text_input("Search keywords", value=default_kw)

preferred_defaults = ["Apple", "Microsoft", "Amazon"]
valid_defaults = [c for c in preferred_defaults if c in COMPANIES]

chosen = st.multiselect(
    "Companies to query",
    options=COMPANIES,
    default=valid_defaults
)

if st.button("🚀 Get Tech Jobs"):
    if not chosen:
        st.warning("Please select at least one company.")
    else:
        with st.spinner("Scraping LinkedIn / Indeed / Google Jobs…"):
            jobs_df = fetch_tech_jobs(chosen, keywords)

        if jobs_df.empty:
            st.error("No jobs found with those filters.")
        else:
            st.success(f"Found {len(jobs_df)} postings across "
                       f"{jobs_df['company'].nunique()} companies.")
            cols = ["title", "company", "location", "date_posted", "job_url"]
            st.dataframe(jobs_df[cols], use_container_width=True)

            st.download_button(
                "⬇️ Download jobs CSV",
                jobs_df.to_csv(index=False, quoting=csv.QUOTE_NONNUMERIC,
                               escapechar="\\"),
                file_name="tech_jobs_USA.csv",
                mime="text/csv"
            )
else:
    st.info("Choose companies and click the button to list their U.S. tech openings.")
