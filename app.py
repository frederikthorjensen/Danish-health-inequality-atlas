"""Read-only Streamlit entry point for the Danish Health & Life Expectancy."""

import streamlit as st
from pathlib import Path
import json
from src.dashboard_layout import reading_navigation

st.set_page_config(page_title="Danish Health & Life Expectancy", page_icon=":material/public:", layout="wide")

st.logo(str(Path(__file__).parent / "assets/atlas_wordmark.svg"), size="large")
assets = Path(__file__).parent / "assets"
tokens = json.loads((assets / "design_tokens.json").read_text())
variables = ";".join(f"--{name.replace('_', '-')}: {value}" for name, value in tokens.items())
st.html("<style>:root{" + variables + "}" + (assets / "dashboard.css").read_text() + "</style>")

pages = [
    st.Page("app_pages/overview.py", title="Home", default=True, help="Start here: the project purpose, official sources, author and routes into the analysis."),
    st.Page("app_pages/key_findings.py", title="Key findings", url_path="key-findings", help="The main validated findings, with short explanations and interpretation cautions."),
    st.Page("app_pages/inequalities.py", title="Health inequalities", url_path="inequalities"),
    st.Page("app_pages/explanation.py", title="What explains life expectancy?", url_path="associations"),
    st.Page("app_pages/explorer.py", title="Municipality explorer", url_path="municipality"),
    st.Page("app_pages/comparison.py", title="Compare municipalities", url_path="compare", help="Choose two to four municipalities and compare their published indicators and differences side by side."),
    st.Page("app_pages/expected.py", title="Expected vs observed", url_path="expected"),
    st.Page("app_pages/profiles.py", title="Health profiles", url_path="profiles"),
    st.Page("app_pages/report.py", title="Report", url_path="report", help="Choose the English or Danish analytical report and download its PDF."),
    st.Page("app_pages/methods.py", title="Methods & limitations", url_path="methods"),
    st.Page("app_pages/data.py", title="Data", url_path="data"),
]
report_readers = [
    st.Page("app_pages/report_en.py", title="English report", url_path="report-en"),
    st.Page("app_pages/report_da.py", title="Dansk rapport", url_path="report-da"),
]
page = st.navigation([*pages, *report_readers], position="hidden")
with st.sidebar:
    st.caption("START HERE")
    with st.container(key="atlas_navigation", gap="xsmall"):
        for i,item in enumerate(pages):
            if item.url_path=="inequalities":
                st.caption("EXPLORE THE DATA")
            if item.url_path=="report":
                st.caption("REPORTS & REFERENCES")
            active=item.url_path==page.url_path or (item.url_path=="report" and page.url_path in {"report-en", "report-da"})
            with st.container(key="nav_active" if active else f"nav_link_{i}"):
                st.page_link(item)
    with st.container(key="sidebar_metadata"):
        st.caption("OFFICIAL DANISH PUBLIC DATA")
        st.caption("Life expectancy **2021–2025**\n\nSocioeconomic data **2024**\n\nHealth profile **2025**")
        st.caption("Associations, not causal effects.")
with st.container(key="atlas_page"):
    if page.url_path:
        with st.container(key="document_breadcrumb",horizontal=True,gap="small"):
            st.page_link(pages[0],label="Project home")
            st.caption("/ " + page.title)
    page.run()
    reading_navigation(pages,page)
