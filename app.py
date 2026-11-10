"""Read-only Streamlit entry point for the Danish Health & Life Expectancy."""

import streamlit as st
from pathlib import Path
import json
from src.dashboard_layout import reading_navigation

st.set_page_config(page_title="Danish Health & Life Expectancy", page_icon=":material/public:", layout="wide")

st.logo(
    str(Path(__file__).parent / "assets/atlas_wordmark_light.svg"),
    icon_image=str(Path(__file__).parent / "assets/atlas_mark.svg"),
    size="large",
)
assets = Path(__file__).parent / "assets"
tokens = json.loads((assets / "design_tokens.json").read_text())
variables = ";".join(f"--{name.replace('_', '-')}: {value}" for name, value in tokens.items())
st.html("<style>:root{" + variables + "}" + (assets / "dashboard.css").read_text() + "</style>")

pages = [
    st.Page("app_pages/overview.py", title="Home", icon=":material/home:", default=True, help="Project overview, official sources, headline evidence and routes into the analysis."),
    st.Page("app_pages/key_findings.py", title="Key findings", icon=":material/summarize:", url_path="key-findings", help="The main validated findings, with concise explanations and interpretation cautions."),
    st.Page("app_pages/author.py", title="About the author", icon=":material/person:", url_path="author", help="Read about Frederik Jensen's qualifications, professional perspective and contribution to this independent project."),
    st.Page("app_pages/inequalities.py", title="Health inequalities", icon=":material/bar_chart:", url_path="inequalities", help="Rank and compare published health, socioeconomic and life-expectancy indicators across municipalities."),
    st.Page("app_pages/explanation.py", title="What explains life expectancy?", icon=":material/query_stats:", url_path="associations", help="Explore simple correlations, adjusted models and the conditional estimates behind municipality differences."),
    st.Page("app_pages/explorer.py", title="Municipality explorer", icon=":material/location_on:", url_path="municipality", help="Inspect one municipality in detail and compare every published indicator with transparent reference values."),
    st.Page("app_pages/comparison.py", title="Compare municipalities", icon=":material/compare_arrows:", url_path="compare", help="Choose two to four municipalities and compare their published indicators and differences side by side."),
    st.Page("app_pages/expected.py", title="Expected vs observed", icon=":material/scatter_plot:", url_path="expected", help="Compare observed life expectancy with saved model predictions and explore municipality residuals."),
    st.Page("app_pages/profiles.py", title="Health profiles", icon=":material/hub:", url_path="profiles", help="Explore saved PCA results and two descriptive municipality profiles across six health indicators."),
    st.Page("app_pages/report.py", title="Report", icon=":material/menu_book:", url_path="report", help="Read the English or Danish analytical report online and download the designed PDF editions."),
    st.Page("app_pages/methods.py", title="Methods & limitations", icon=":material/fact_check:", url_path="methods", help="Review official sources, statistical methods, analytical choices and the limitations that govern interpretation."),
    st.Page("app_pages/data.py", title="Data", icon=":material/database:", url_path="data", help="Inspect the processed data, dictionary and provenance, and download validated datasets and result tables."),
]
report_readers = [
    st.Page("app_pages/report_en.py", title="English report", icon=":material/article:", url_path="report-en", visibility="hidden"),
    st.Page("app_pages/report_da.py", title="Dansk rapport", icon=":material/article:", url_path="report-da", visibility="hidden"),
]
page = st.navigation([*pages, *report_readers], position="hidden")
with st.sidebar:
    st.caption("MUNICIPALITY HEALTH REPORT")
    with st.container(key="atlas_navigation", gap="xsmall"):
        for i,item in enumerate(pages):
            if i==0:
                st.caption("OVERVIEW")
            if item.url_path=="inequalities":
                st.caption("ANALYSIS")
            if item.url_path=="report":
                st.caption("DOCUMENTATION")
            active=item.url_path==page.url_path or (item.url_path=="report" and page.url_path in {"report-en", "report-da"})
            with st.container(key="nav_active" if active else f"nav_link_{i}"):
                st.page_link(item)
    with st.container(key="sidebar_metadata"):
        st.caption("DATA STATUS")
        st.badge("Validated snapshot", icon=":material/verified:", color="green")
        st.caption("Life expectancy **2021–2025**  \nSocioeconomic data **2024**  \nHealth profile **2025**")
        st.caption("Official Danish public data  \nAssociations, not causal effects")
with st.container(key="atlas_page"):
    if page.url_path:
        with st.container(key="document_breadcrumb",horizontal=True,gap="small"):
            st.page_link(pages[0],label="Home",icon=":material/home:")
            st.caption("/  " + page.title)
    page.run()
    reading_navigation(pages,page)
    with st.container(key="site_footer",gap="xsmall"):
        with st.container(horizontal=True,horizontal_alignment="distribute"):
            st.caption("© 2026 Frederik Jensen")
            st.caption("Danish Health & Life Expectancy")
        st.caption("Independent public-health portfolio · Official Danish public data · Validated analysis snapshot")
