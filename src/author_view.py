"""Presentation-only author profile for the public dashboard."""

import streamlit as st


def _header(eyebrow: str, title: str, description: str) -> None:
    with st.container(key="page_header", gap="xsmall"):
        st.caption(eyebrow.upper())
        st.title(title)
        st.markdown(description)


def author() -> None:
    """Render the professional profile using documented qualifications only."""
    with st.container(key="author_hero", gap="medium"):
        profile, identity = st.columns([1.65, .85], gap="large", vertical_alignment="center")
        with profile:
            _header(
                "Author & project lead",
                "Frederik Jensen",
                "Clinical experience, interdisciplinary health-science training and applied public-health analysis.",
            )
            st.markdown(
                "Frederik Jensen is a physiotherapist (Professional Bachelor, 2023) and holds a cand.san./MSc-level degree in Interdisciplinary Health Studies from Roskilde University (2025). "
                "His background combines quantitative and qualitative health research, including survey data, interviews, statistical analysis, evidence appraisal and health-science methodology. "
                "He has worked with SPSS, Jamovi, Excel and SurveyXact, applying descriptive statistics, t-tests, ANOVA and chi-square analysis to health-related data.\n\n"
                "Experience from private physiotherapy practice and an acute/semi-intensive gastro-surgical hospital setting provides a practical perspective on rehabilitation, interdisciplinary care and the realities behind health data. "
                "He created Danish Health & Life Expectancy as an independent applied portfolio project, using Python and Streamlit to integrate official municipal data and communicate reproducible analyses. "
                "His professional interests include public health, health inequality, evaluation, evidence, health administration and clear communication of complex findings."
            )
            with st.container(horizontal=True, gap="small", key="author_status"):
                st.badge("Independent project", color="gray")
                st.badge("Official public data", color="gray")
                st.badge("Reproducible analysis", color="gray")
        with identity:
            with st.container(key="author_identity", gap="small"):
                with st.container(key="author_monogram"):
                    st.markdown("FJ")
                st.caption("PROJECT AUTHOR")
                st.header("Frederik Jensen")
                st.caption("HEALTH · ANALYSIS · COMMUNICATION")

    with st.container(key="author_qualifications", gap="medium"):
        st.caption("FORMAL QUALIFICATIONS")
        st.header("Clinical and academic foundation")
        st.markdown("The formal qualifications listed below are the credentials documented for this project.")
        with st.grid(2, min_column_width=300, gap="medium") as grid:
            qualifications = [
                (
                    "clinical",
                    "01",
                    "Professional Bachelor’s degree in Physiotherapy",
                    "Clinical foundation",
                    "Completed in 2023 · Clinical training in human health, function, rehabilitation and evidence-informed practice.",
                ),
                (
                    "academic",
                    "02",
                    "cand.san. / MSc-level degree in Interdisciplinary Health Studies",
                    "Academic degree",
                    "Roskilde University · completed in 2025 · Quantitative and qualitative health research and methodology.",
                ),
            ]
            for key, number, title, label, description in qualifications:
                with grid.cell():
                    with st.container(border=True, height="stretch", key=f"author_qualification_{key}", gap="small"):
                        with st.container(horizontal=True, horizontal_alignment="distribute"):
                            st.caption(label.upper())
                            st.caption(number)
                        st.subheader(title)
                        st.markdown(description)

    with st.container(key="author_capabilities", gap="medium"):
        st.caption("PORTFOLIO CAPABILITIES")
        st.header("Capabilities demonstrated in this project")
        st.markdown("These are demonstrated areas of project work, presented separately from formal academic credentials.")
        with st.grid(2, min_column_width=300, gap="medium") as grid:
            capabilities = [
                ("public_health", ":material/public:", "Public-health analysis", "Municipality-level health inequality, life expectancy, socioeconomic conditions and health behaviours."),
                ("statistics", ":material/query_stats:", "Applied statistics", "Descriptive analysis, correlations, multiple-testing correction, robust regression, diagnostics, PCA and clustering."),
                ("data", ":material/database:", "Public-data engineering", "Reproducible acquisition, validation and integration of official Statistics Denmark and National Health Profile data."),
                ("communication", ":material/insert_chart:", "Analytical communication", "Clear reports, interactive visualisation and careful communication of uncertainty, limitations and non-causal findings."),
            ]
            for key, icon, title, description in capabilities:
                with grid.cell():
                    with st.container(border=True, height="stretch", key=f"author_capability_{key}", gap="xsmall"):
                        st.badge(title, icon=icon, color="gray")
                        st.markdown(description)

    with st.container(key="author_toolkit", gap="medium"):
        toolkit, contribution = st.columns(2, gap="large", vertical_alignment="top")
        with toolkit:
            st.caption("TECHNICAL TOOLKIT")
            st.subheader("Tools used in the project")
            st.markdown("SPSS · Jamovi · Excel · SurveyXact · applied Python and Streamlit workflow")
            st.caption("Python and Streamlit are presented as part of this applied portfolio workflow, not as separate certifications.")
        with contribution:
            st.caption("PROJECT CONTRIBUTION")
            st.subheader("End-to-end authorship")
            st.markdown("Data acquisition and quality assurance · statistical analysis · interpretation · report production · dashboard design · reproducibility documentation")

    with st.container(key="author_perspective", gap="small"):
        st.caption("PROFESSIONAL PERSPECTIVE")
        st.subheader("Evidence should be useful without being overstated")
        st.markdown(
            "The project is designed around transparent methods, reproducible evidence and cautious interpretation. "
            "Municipality patterns are treated as descriptive and hypothesis-generating—not as causal effects, individual risk estimates or rankings of municipal performance."
        )
        st.caption("Independent portfolio project · No institutional or employer affiliation is claimed")
