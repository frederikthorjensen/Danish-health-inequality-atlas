"""Presentation-only author profile for the public dashboard."""

from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
PROFILE_IMAGE = ROOT / "assets/frederik_jensen_profile.png"
LINKEDIN_URL = "https://www.linkedin.com/in/frederik-thor-jensen-887839111/"


PROJECTS = [
    {
        "key": "health_inequality_narratives",
        "number": "01",
        "period": "January–June 2025",
        "type": "Master’s thesis",
        "title": "Narratives of Health Inequality",
        "subtitle": "A discourse analysis of problem representations in Danish news media",
        "summary": (
            "An examination of how social and geographical health inequalities are framed, "
            "explained and made meaningful in Danish news coverage."
        ),
        "detail": (
            "The thesis used systematic collection and delimitation of empirical material, "
            "qualitative coding, discourse analysis and critical synthesis. It examined which "
            "explanations for health inequality become visible in news coverage and how different "
            "representations may shape perceptions of people with lower socioeconomic status.\n\n"
            "The work developed experience in structuring substantial bodies of information, "
            "identifying patterns and central problems, and turning complex material into a coherent, "
            "usable analysis."
        ),
        "skills": "Discourse analysis · Qualitative coding · Health inequality",
    },
    {
        "key": "youth_mental_health",
        "number": "02",
        "period": "February–April 2024",
        "type": "Health-science project",
        "title": "Municipal Governance and Strategy for Youth Mental Health",
        "subtitle": "A qualitative study of community, continuity and municipal health promotion",
        "summary": (
            "A study of how the well-being and sense of community developed through Næstved Youth "
            "School’s club services might be sustained when young people leave the programme."
        ),
        "detail": (
            "The project examined mental well-being among children and young people through the case "
            "of Næstved Youth School and the municipality’s work with health-promoting communities. "
            "Semi-structured interviews with a manager and an employee supported analysis across "
            "practice, leadership and organisational perspectives.\n\n"
            "The work developed experience in qualitative data collection, interviewing, coding and "
            "analysis, as well as the investigation and evaluation of health-promoting initiatives in "
            "a municipal context."
        ),
        "skills": "Interviews · Programme evaluation · Municipal health",
    },
    {
        "key": "muscle_dysmorphia",
        "number": "03",
        "period": "September 2023–January 2024",
        "type": "Health-science project",
        "title": "Factors Associated with Muscle Dysmorphia among Young Men",
        "subtitle": "A critical social analysis of body ideals, social media and performance culture",
        "summary": (
            "A qualitative exploration of the individual and societal conditions associated with "
            "muscle dysmorphia—also described as megarexia—among young men."
        ),
        "detail": (
            "The project combined semi-structured interviews and document analysis to examine social "
            "media, body ideals, social pressure and performance culture. It also considered why men "
            "experiencing these concerns may form an overlooked group and which barriers can make it "
            "more difficult to seek help.\n\n"
            "The work developed experience in qualitative data collection, interviewing and the "
            "analysis of complex health issues, connecting individual experiences with broader social "
            "and structural conditions."
        ),
        "skills": "Qualitative research · Document analysis · Critical health studies",
    },
]


def _header(eyebrow: str, title: str, description: str) -> None:
    with st.container(key="page_header", gap="xsmall"):
        st.caption(eyebrow.upper())
        st.title(title)
        st.markdown(description)


def _portrait() -> None:
    with st.container(key="author_portrait", gap="small"):
        if PROFILE_IMAGE.exists():
            # Pass bytes to Streamlit so the portrait is bundled into the media
            # response independently of the process working directory.
            st.image(PROFILE_IMAGE.read_bytes(), alt="Portrait of Frederik Jensen", width="stretch")
        else:
            with st.container(key="author_monogram"):
                st.markdown("FJ")
        st.caption("FREDERIK JENSEN")
        st.markdown(
            "**Master of Science (MSc) in Critical Health Studies**  \n"
            "**Professional Bachelor’s Degree in Physiotherapy**"
        )


def _project_card(project: dict[str, str]) -> None:
    with st.container(border=True, key=f"author_project_{project['key']}", gap="small"):
        with st.container(horizontal=True, key=f"research_meta_{project['key']}", gap="small"):
            st.caption(project["number"])
            st.caption(project["period"].upper())
            st.caption(project["type"].upper())
        st.subheader(project["title"])
        st.caption(project["subtitle"])
        st.markdown(project["summary"])
        st.caption(project["skills"])
        with st.expander(
            "Read the project description",
            key=f"author_project_detail_{project['key']}",
            icon=":material/read_more:",
        ):
            st.markdown(project["detail"])


def author() -> None:
    """Render a professional profile using user-verified qualifications and projects."""
    with st.container(key="author_hero", gap="large"):
        portrait, profile = st.columns([0.72, 1.55], gap="large", vertical_alignment="center")
        with portrait:
            _portrait()
        with profile:
            _header(
                "Author & project lead",
                "Frederik Jensen",
                "Public-health analysis grounded in clinical practice, critical health studies and transparent research methods.",
            )
            st.markdown(
                "Frederik Jensen is a physiotherapist and holds a **Master of Science (MSc) in Critical Health Studies** from Roskilde University. "
                "His work combines qualitative health research, applied statistics, public-data analysis and clear communication of complex evidence."
            )
            st.markdown(
                "Clinical experience from private physiotherapy practice and an acute and semi-intensive gastro-surgical hospital setting informs a practical perspective on rehabilitation, interdisciplinary care and the realities represented by health data."
            )
            with st.container(horizontal=True, gap="small", key="author_status"):
                st.badge("Public health", color="gray")
                st.badge("Critical health studies", color="gray")
                st.badge("Applied analytics", color="gray")
            st.link_button("Connect on LinkedIn", LINKEDIN_URL, icon=":material/open_in_new:", width="content")

    with st.container(key="author_qualifications", gap="medium"):
        st.caption("FORMAL QUALIFICATIONS")
        st.header("Clinical and academic foundation")
        with st.grid(2, min_column_width=300, gap="medium") as grid:
            qualifications = [
                (
                    "clinical",
                    "01",
                    "Professional Bachelor’s Degree in Physiotherapy",
                    "Clinical foundation",
                    "Completed in 2023 · Human health, function, rehabilitation and evidence-informed practice.",
                ),
                (
                    "academic",
                    "02",
                    "Master of Science (MSc) in Critical Health Studies",
                    "Academic degree",
                    "Roskilde University · completed in 2025 · Critical, qualitative and interdisciplinary health research.",
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

    with st.container(key="author_projects", gap="medium"):
        st.caption("SELECTED RESEARCH PROJECTS")
        st.header("Research across inequality, mental health and society")
        st.markdown(
            "Three academic projects demonstrate qualitative research, critical analysis and the ability to translate complex health questions into structured evidence."
        )
        for project in PROJECTS:
            _project_card(project)
        st.link_button("View the full LinkedIn profile", LINKEDIN_URL, icon=":material/open_in_new:", width="content")

    with st.container(key="author_capabilities", gap="medium"):
        st.caption("PORTFOLIO CAPABILITIES")
        st.header("A combined research and analytical toolkit")
        with st.grid(2, min_column_width=300, gap="medium") as grid:
            capabilities = [
                ("qualitative", ":material/format_quote:", "Qualitative research", "Interview design, empirical delimitation, coding, document analysis and critical synthesis."),
                ("public_health", ":material/public:", "Public-health analysis", "Health inequality, mental well-being, health promotion and municipality-level population health."),
                ("statistics", ":material/query_stats:", "Applied analytics", "Descriptive analysis, robust regression, multiple testing, diagnostics, PCA and clustering."),
                ("communication", ":material/insert_chart:", "Evidence communication", "Professional reports, interactive visualisation and careful communication of uncertainty and limitations."),
            ]
            for key, icon, title, description in capabilities:
                with grid.cell():
                    with st.container(border=True, height="stretch", key=f"author_capability_{key}", gap="xsmall"):
                        st.badge(title, icon=icon, color="gray")
                        st.markdown(description)

    with st.container(key="author_toolkit", gap="medium"):
        toolkit, contribution = st.columns(2, gap="large", vertical_alignment="top")
        with toolkit:
            st.caption("RESEARCH TOOLKIT")
            st.subheader("Methods and software")
            st.markdown("Qualitative interviews · coding · document and discourse analysis · SPSS · Jamovi · Excel · SurveyXact · Python · Streamlit")
        with contribution:
            st.caption("ATLAS CONTRIBUTION")
            st.subheader("End-to-end authorship")
            st.markdown("Data acquisition and validation · statistical analysis · interpretation · bilingual report production · dashboard design · reproducibility documentation")

    with st.container(key="author_perspective", gap="small"):
        st.caption("PROFESSIONAL PERSPECTIVE")
        st.subheader("Evidence should be useful without being overstated")
        st.markdown(
            "The work is grounded in transparent methods, reproducible evidence and cautious interpretation. "
            "Population patterns are treated as descriptive and hypothesis-generating—not as causal effects, individual risk estimates or performance rankings."
        )
        st.caption("Independent portfolio project · No institutional or employer affiliation is claimed")
