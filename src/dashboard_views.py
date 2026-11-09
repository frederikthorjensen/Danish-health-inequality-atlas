"""Native Streamlit pages composing verified artifacts and Plotly presentation."""

import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import dashboard_charts as charts
from src.dashboard_layout import reading_guide, section_heading
from src.dashboard_data import ROOT, FEATURES, LABELS, METRICS, MODEL_LABELS, benchmark, characteristics, descriptive_rank, digest, format_value, load_dashboard, rank_label


def bundle():
    try:
        return load_dashboard()
    except (OSError, ValueError, KeyError) as exc:
        st.error("The validated data snapshot is unavailable or inconsistent. Rebuild the saved project outputs before using this dashboard.")
        with st.expander("Validation details"):
            st.code(str(exc), language=None)
        st.stop()


def chart(fig, key, alt):
    with st.container(border=True,key=f"figure_{key}"):
        st.plotly_chart(fig, width="stretch", theme=None, key=key, alt=alt,
            config={"displaylogo": False, "responsive": True, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})


def header(eyebrow, title, description):
    st.caption(eyebrow.upper())
    st.title(title)
    st.markdown(description)


def note():
    st.caption("Official Danish public data · Socioeconomic: 2024 · Health profile: 2025 · Life expectancy: 2021–2025 · Municipality-level associations, not causal effects.")


def overview():
    """Project Home: orientation first, with a small saved-results preview."""
    b = bundle()
    master = b["master"]
    m3 = b["fits"].set_index("model").loc["M3"]
    strongest = characteristics(b).iloc[0]
    with st.container(key="home_hero", gap="small"):
        header("Independent public-health analysis · Frederik Jensen", "Danish Health & Life Expectancy",
            "Geographical inequalities across Danish municipalities.")
        st.markdown("This independent project brings together official Danish municipality-level socioeconomic, health-profile and life-expectancy data. It explores how social conditions and health behaviours are associated with geographical differences in population health, with an emphasis on transparent methods, reproducibility and clear public communication.")
        with st.container(horizontal=True, gap="small", key="home_actions"):
            if st.button("Explore the dashboard", type="primary", key="home_explore", width=230):
                st.switch_page("app_pages/inequalities.py")
            if st.button("Read the analytical report", key="home_report", width=250):
                st.switch_page("app_pages/report.py")
    with st.container(key="home_purpose", gap="small"):
        st.header("Purpose")
        st.markdown("National averages can hide differences between local populations. Comparing municipalities helps reveal broad patterns in health and living conditions, and identify questions for closer local investigation.")
        st.markdown("The atlas combines statistical analysis with accessible communication. Its findings are descriptive and exploratory: they show associations between places, not causal effects on individuals.")
    with st.container(key="home_sources", gap="medium"):
        st.header("What the project combines")
        with st.grid(3, min_column_width=260, gap="medium") as grid:
            for key, title, source, period, text in [
                ("social", "Socioeconomic conditions", "Statistics Denmark", "2024", "Disposable income, educational attainment and age structure."),
                ("health", "Health & behaviour", "Danish National Health Profile", "2025", "Smoking, obesity, physical activity, alcohol, self-rated health and mental health."),
                ("life", "Life expectancy", "Statistics Denmark · HISBK", "2021–2025", "Published municipal life-expectancy estimates, including male and female estimates."),
            ]:
                with grid.cell():
                    with st.container(border=True, height="stretch", key=f"home_source_{key}", gap="small"):
                        st.caption(period)
                        st.subheader(title)
                        st.markdown(text)
                        st.caption(source)
    with st.container(key="home_exploration", gap="medium"):
        st.header("What you can explore")
        with st.grid(3, min_column_width=260, gap="medium") as grid:
            for i, (title, description, path) in enumerate([
                ("Municipal variation", "Compare life expectancy and health indicators across municipalities.", "inequalities"),
                ("Associations", "See how social and behavioural indicators relate to life expectancy.", "explanation"),
                ("Multivariable models", "Explore how associations change when several indicators are considered together.", "explanation"),
                ("Expected vs observed", "Compare observed life expectancy with predictions from the included indicators.", "expected"),
                ("Health profiles", "Explore shared patterns using PCA and descriptive clustering.", "profiles"),
                ("Reports & methods", "Read the English or Danish report, with methodology and limitations.", "report"),
            ]):
                with grid.cell():
                    with st.container(border=True, height="stretch", key=f"home_destination_{i}", gap="small"):
                        st.page_link(f"app_pages/{path}.py", label=title)
                        st.markdown(description)
    with st.container(key="home_findings", gap="medium"):
        st.header("Selected headline findings")
        with st.grid(4, min_column_width=220, gap="medium") as grid:
            for key, label, value, detail, help_text in [
                ("association", "Strongest simple association", f"r = {strongest.correlation:.3f}", "Low educational attainment", "Strongest absolute saved Pearson correlation among included municipality characteristics; N=94."),
                ("increment", "Health behaviours", f"ΔR² = {b['increment']['delta_R_squared']:.3f}", "Beyond the socioeconomic model", "Saved increase in R² from M1 to M3 on the same complete cases; statistical information, not a causal contribution."),
                ("model", "Combined model", f"R² = {m3.R_squared:.3f}", "Between-municipality variation", "Model 3 in-sample fit. R² is not a causal fraction of life expectancy."),
                ("coverage", "Municipality coverage", str(len(master)), f"{int(master.life_expectancy_total.count())} with published life expectancy", "All municipalities remain in the atlas. Four withheld life-expectancy estimates are not imputed."),
            ]:
                with grid.cell():
                    with st.container(border=True, height="stretch", key=f"home_finding_{key}", gap="xsmall"):
                        st.metric(label, value, help=help_text)
                        st.caption(detail)
        st.caption("These are municipality-level statistical associations and should not be interpreted as causal effects. All results, including nonsignificant estimates, are available in the analytical sections.")
    with st.container(key="home_author", gap="small"):
        st.header("About the author")
        st.subheader("Frederik Jensen")
        st.markdown("Professional Bachelor of Physiotherapy  \nMaster of Science (MSc) in Health in Critical Health Studies (cand.san.)")
        st.markdown("With a background in physiotherapy and critical health studies, Frederik Jensen developed this independent portfolio project to bring together public-health data, statistical analysis and clear communication of complex findings.")
    with st.container(key="home_principles", gap="small"):
        st.subheader("Project principles")
        with st.container(horizontal=True, gap="small"):
            for principle in ["Official public data", "Reproducible analysis", "Transparent methods", "No imputation of withheld life-expectancy estimates", "Association ≠ causation"]:
                st.badge(principle, color="gray")
    with st.container(key="home_final", gap="medium"):
        st.header("Explore the analysis")
        with st.grid(4, min_column_width=200, gap="small"):
            for key, label, path in [
                ("dashboard", "Open dashboard", "inequalities"),
                ("english", "Read English report", "report_en"),
                ("danish", "Læs dansk rapport", "report_da"),
                ("methods", "Methods & limitations", "methods"),
            ]:
                if st.button(label, key=f"home_final_{key}", width="stretch"):
                    st.switch_page(f"app_pages/{path}.py")


def key_findings():
    """An executive brief with topic navigation; all values are saved results."""
    b = bundle()
    c = characteristics(b).set_index("other_variable")
    model = b["fits"].set_index("model").loc["M3"]
    increment = b["increment"]["delta_R_squared"]
    with st.container(key="findings_hero",gap="small"):
        header("Executive brief", "Key findings", "Understand the main results, what they mean and where interpretation needs care.")
        st.caption("98 municipalities · 94 with published life expectancy · Official public data")
    with st.container(key="findings_summary",gap="xsmall"):
        st.caption("THE OVERALL PICTURE")
        st.markdown("**Social conditions and health behaviours are closely associated with differences in municipal life expectancy.**")
        st.markdown("The atlas describes patterns between places. It does not identify causal effects or explain individual health outcomes.")
    findings = [
        ("Social patterns", "Education and smoking",
         f"Education r = {c.loc['low_education_share_25_64_pct','correlation']:.3f} · smoking r = {c.loc['daily_smoking_pct','correlation']:.3f}",
         "Higher primary-education shares and more daily smoking accompany lower life expectancy. These are the strongest negative simple associations among the included characteristics.",
         "These patterns do not establish an individual-level or causal effect."),
        ("Social patterns", "Higher disposable income",
         f"r = {c.loc['disposable_income_mean_dkk','correlation']:+.3f}",
         "Municipalities with higher average disposable income generally have longer life expectancy.",
         "Income overlaps with education and other social conditions. This is not the isolated effect of income."),
        ("Model insights", "Health behaviours add information",
         f"Increase in R² = {increment:.3f}",
         "Smoking, obesity, physical activity and alcohol indicators improve model fit beyond income and education alone.",
         "The improvement concerns the indicators together; it does not show an independent causal effect for each behaviour."),
        ("Model insights", "About 75% of observed variation",
         f"R² = {model.R_squared:.3f} · adjusted R² = {model.adjusted_R_squared:.3f}",
         "The combined model statistically accounts for around three quarters of the observed differences in life expectancy between municipalities in this sample.",
         "R² measures model fit. It is not the proportion of life expectancy caused by the included indicators."),
        ("Model insights", "Adjusted estimates need context",
         "Overlapping predictors can change an estimate’s direction",
         "When related indicators are considered together, individual coefficients can weaken or reverse. Simple associations and adjusted estimates answer different questions.",
         "The positive adjusted obesity coefficient must not be interpreted as protective. Its simple association with life expectancy is negative."),
        ("Health profiles", "Profiles are not health rankings",
         "Different patterns across six health indicators",
         "The smaller profile has lower smoking, obesity, inactivity and poorer-health indicators, but higher alcohol exposure. Neither profile is universally healthier.",
         "These are exploratory profiles, not natural or causal groups. PC1 is not a single health-risk score."),
    ]
    with st.container(key="findings_navigation",gap="small"):
        topic = st.segmented_control("Read by topic", ["All findings", "Social patterns", "Model insights", "Health profiles"],
            default="All findings", key="findings_topic", help="Read the complete brief or focus on one topic. All results remain available in the analytical pages.")
        selected = [(i, f) for i, f in enumerate(findings) if topic in (None,"All findings") or f[0]==topic]
        st.caption(f"{len(selected)} of 6 findings · Select a topic above to focus your reading")
    with st.expander("What do r and R² mean?"):
        st.markdown("**r** describes how strongly two measures move together. A negative value means municipalities with more of one measure generally have less of the other. **R²** describes how much observed variation the model statistically accounts for; adjusted R² also accounts for the number of predictors. Neither measure establishes causation.")
    with st.container(key="findings_cards"):
        with st.grid(2,min_column_width=340,gap="medium") as grid:
            for i,(group,title,evidence,meaning,caution) in selected:
                with grid.cell():
                    with st.container(border=True,height="stretch",key=f"brief_card_{i}",gap="small"):
                        st.caption(f"0{i+1} / {group.upper()}")
                        st.subheader(title)
                        with st.container(key=f"brief_evidence_{i}"):
                            st.markdown(evidence)
                        st.markdown(meaning)
                        with st.container(key=f"brief_caution_{i}",gap="xsmall"):
                            st.caption("INTERPRETATION")
                            st.markdown(caution)
    with st.container(key="findings_next",gap="small"):
        st.subheader("Go deeper")
        st.markdown("See the underlying charts, read the complete report or review the methodological limitations.")
        with st.container(horizontal=True,gap="small"):
            st.page_link("app_pages/explanation.py", label="Explore the evidence",width=210)
            st.page_link("app_pages/report.py", label="Read the report",width=190)
            st.page_link("app_pages/methods.py", label="Methods & limitations",width=230)
        st.caption("All primary life-expectancy models use 94 complete cases. Four withheld estimates are not imputed. Full results include nonsignificant estimates.")


def inequalities():
    b = bundle()
    header("Geographical variation", "Health inequalities", "Compare the spread of published indicators across municipalities. Use the same measure in a ranked view and a distribution.")
    reading_guide("Choose an indicator, then switch between the municipality comparison and its distribution. Each municipality has equal weight; missing estimates remain missing.")
    options = ["life_expectancy_total", *FEATURES, "disposable_income_mean_dkk", "low_education_share_25_64_pct"]
    variable = st.selectbox("Choose an indicator", options, format_func=lambda c: LABELS[c], key="inequality_variable")
    valid = b["master"][variable].dropna()
    with st.grid(3, min_column_width=190):
        st.metric("Published municipalities", len(valid), border=True)
        st.metric("Municipality median", format_value(valid.median(), variable), border=True)
        st.metric("Reference period", METRICS[variable][2], border=True)
    if variable == "life_expectancy_total":
        st.info("Life expectancy is withheld for Ærø, Fanø, Samsø and Læsø because the estimates are too uncertain. They are retained in the dataset with missing values.")
    view = st.segmented_control("View", ["Municipality comparison", "Distribution"], default="Municipality comparison", key="inequality_view")
    if view != "Distribution":
        ranking = st.segmented_control("Ranked view", ["Lowest 20", "Highest 20", "All published"], default="Lowest 20", key="inequality_range")
        with st.container():
            st.subheader(f"{LABELS[variable]} by municipality")
            chart(charts.ranked(b["master"], variable, ranking), "inequality_ranked", "Municipality values ordered by the selected published indicator")
    else:
        with st.container():
            st.subheader("The distribution across municipalities")
            chart(charts.distribution(b["master"], variable), "inequality_distribution", "Distribution of the selected municipality indicator")
            st.caption("Each municipality has equal weight. The municipality median is not a population-weighted national estimate.")
    note()


def explanation():
    b = bundle()
    header("Associations & adjustment", "What explains life expectancy?", "Explore simple relationships, then see how estimates change when municipality characteristics are considered together.")
    reading_guide("Start with simple associations to see how indicators move together. Switch to adjusted models to see how estimates change when related indicators are considered simultaneously. These are statistical associations, not causal effects.")
    with st.expander("How to read correlations and adjusted models"):
        st.markdown("**Correlation:** a value close to −1 indicates a strong negative relationship: municipalities with higher values of the indicator generally have lower life expectancy. Spearman compares ranks rather than a straight-line relationship. **FDR correction** limits false discoveries when many tests are considered; it does not make an individual result certain.")
        st.markdown("**R²** describes how much observed variation between municipalities the included variables statistically account for. It does not measure causality. **Adjusted R²** accounts for the number of predictors when comparing model complexity.")
        st.markdown("**Confidence intervals** describe coefficient values reasonably compatible with the data and model assumptions. **Standardized beta** puts slopes on a common scale. **VIF** indicates how strongly a predictor overlaps with the others; overlap can make individual adjusted estimates unstable.")
    view = st.segmented_control("Explore", ["Simple associations", "Adjusted models"], default="Simple associations", key="explanation_view")
    if view != "Adjusted models":
        section_heading("01", "Relationships between indicators", "Compare the strength and direction of the saved correlations, then inspect individual municipalities.")
        method = st.segmented_control("Correlation method", ["Pearson", "Spearman"], default="Pearson", key="correlation_method")
        d = characteristics(b, method)
        chart(charts.correlation_bars(d, limit=len(d)), "association_bars", f"All saved {method} correlations between municipality characteristics and total life expectancy")
        st.caption("Hover for N, p and BH-adjusted q. Q-values use all 136 unique variable pairs separately for each correlation method.")
        with st.expander("Explore the full correlation matrix"):
            chart(charts.heatmap(b["matrix"]), "correlation_heatmap", "Saved Pearson correlation matrix for all 17 continuous analytic variables")
            st.caption("Pearson r · pairwise N=94–98. Columns use the row numbers; hover for full indicator names. The three age shares are compositional; life-expectancy outcomes are related.")
        st.subheader("Look at the municipalities behind an association")
        variable = st.selectbox("Municipality characteristic", d.other_variable.tolist(), format_func=lambda c: LABELS.get(c, c), key="scatter_variable")
        row = characteristics(b).set_index("other_variable").loc[variable]
        st.caption(f"Pearson r = {row.correlation:+.3f} · N = {int(row.N)} · global BH q = {row.q_value_BH_all_pairs:.3g}")
        chart(charts.association_scatter(b, variable), "association_scatter", "Municipality scatterplot with a descriptive line reconstructed from the saved Pearson correlation")
        st.caption("The line visualizes the saved Pearson result using the plotted sample’s means and standard deviations. No new inferential model or confidence band is fitted.")
    else:
        section_heading("02", "Considering indicators together", "Compare model fit and conditional estimates. The full set of specified predictors is retained.")
        st.subheader("From simple associations to adjusted models")
        fits = b["fits"].copy()
        fits["Specification"] = fits.model.map(MODEL_LABELS)
        chart(charts.model_comparison(fits), "model_comparison", "Saved adjusted R squared for Models 1 through 4; combined and expanded models are highlighted without ranking them as best")
        st.markdown("**M1:** income + education · **M2:** four health behaviours · **M3:** M1 + M2 · **M4:** M3 + self-rated and mental health. All use the same 94 complete cases.")
        increment = b["increment"]
        st.markdown(f"Adding health behaviours to the socioeconomic model increased R² by **{increment['delta_R_squared']:.3f}**, with joint HC3 robust **p = {increment['p_value']:.5f}**.")
        st.subheader("The fully adjusted model")
        mode = st.segmented_control("Coefficient scale", ["Standardized beta", "Original units"], default="Standardized beta", key="coefficient_scale")
        chart(charts.coefficients(b["coefficients"], mode), "model4_coefficients", "All eight Model 4 coefficients with saved 95 percent HC3 confidence intervals")
        st.caption("Original units: years per DKK 10,000 income or per percentage point for education/health. Hover for robust p-values and q-values across all 20 primary coefficient tests.")
        with st.container(key="obesity_caution"):
            st.markdown("**Interpretation caution.** The positive adjusted obesity coefficient should not be interpreted as protective. Its simple correlation is negative; collinearity and statistical suppression can reverse a conditional coefficient.")
        st.markdown("Income, education, obesity and poor mental health pass the primary-family FDR correction. Smoking is borderline nominally and does not pass that correction. All predictors remain in the specified model.")
        with st.expander("All coefficients, including nonsignificant results"):
            table = b["coefficients"].copy()
            table["Predictor"] = table.term.map(lambda c: LABELS.get(c, "Intercept" if c == "const" else c))
            st.dataframe(table[["model", "Predictor", "coefficient", "standardized_beta", "ci_low", "ci_high", "robust_p_value", "q_value_family_BH"]], hide_index=True, alt="All primary model coefficients and inference")
    note()


def explorer():
    b = bundle()
    header("A closer look", "Municipality explorer", "Put one municipality’s published indicators in context, with transparent benchmarks and reference periods.")
    reading_guide("Choose a municipality. Life expectancy is shown first; use the topic control for health indicators, social conditions or the model comparison. Differences describe values, not a performance grade.")
    names = sorted(b["master"].municipality.tolist())
    name = st.selectbox("Municipality", names, index=names.index("København"), key="municipality")
    row = b["master"].set_index("municipality").loc[name]
    if st.button("Compare with other municipalities",key="open_municipality_comparison"):
        other="Aarhus" if name!="Aarhus" else "København"
        st.session_state["comparison_municipalities"]=[name,other]
        st.switch_page("app_pages/comparison.py")
    with st.container(key="selected_municipality",gap="xsmall"):
        st.header(name)
        st.caption(f"Municipality {row.municipality_code} · {row.population:,.0f} residents (2024)")
    if pd.isna(row.life_expectancy_total):
        st.info("Life expectancy is not published for this municipality because of source uncertainty. No estimate, prediction or residual has been imputed. Health and socioeconomic indicators remain available.")
    section_heading("01", "Life expectancy", "Published estimates for 2021–2025. Total, male and female life expectancy use Denmark as the reference; the sex gap uses the municipality median.")
    with st.grid(4, min_column_width=200, gap="medium") as grid:
        for variable in list(METRICS)[:4]:
            reference, reference_label = benchmark(b, variable)
            unit = METRICS[variable][1]
            delta = None if pd.isna(row[variable]) else f"{row[variable]-reference:+,.0f} DKK" if unit == "DKK" else f"{row[variable]-reference:+.1f} {'pp' if unit == '%' else 'years'}"
            with grid.cell():
                with st.container(border=True, height="stretch",key=f"municipality_metric_{variable}",gap="xsmall"):
                    st.metric("Female–male gap" if variable == "life_expectancy_sex_gap" else LABELS[variable], format_value(row[variable], variable), delta=delta, delta_color="off", delta_arrow="off",
                        help=f"{reference_label}: {format_value(reference, variable)}. Delta is selected minus benchmark.")
                    short_reference="Denmark" if reference_label.startswith("Denmark") else "Municipality median"
                    st.caption(f"{short_reference}: **{format_value(reference,variable)}** · {METRICS[variable][2]}")
                    st.caption(rank_label(descriptive_rank(b["master"],variable,row[variable])))
    detail = st.segmented_control("Explore this municipality", ["Health & behaviour", "Social conditions", "Model comparison"], default="Health & behaviour", key="municipality_detail_view")
    if detail != "Model comparison":
        variables = list(METRICS)[4:6] if detail == "Social conditions" else FEATURES
        section_heading("02", "Social conditions" if detail == "Social conditions" else "Health & behaviour", "Compare each published value with the unweighted municipality median.")
        with st.grid(3, min_column_width=230, gap="medium") as grid:
            for variable in variables:
                reference, reference_label = benchmark(b, variable)
                unit = METRICS[variable][1]
                delta = None if pd.isna(row[variable]) else f"{row[variable]-reference:+,.0f} DKK" if unit == "DKK" else f"{row[variable]-reference:+.1f} {'pp' if unit == '%' else 'years'}"
                with grid.cell():
                    with st.container(border=True, height="stretch",key=f"municipality_detail_{variable}",gap="xsmall"):
                        st.metric("Female–male gap" if variable == "life_expectancy_sex_gap" else LABELS[variable], format_value(row[variable], variable), delta=delta, delta_color="off", delta_arrow="off",
                            help=f"{reference_label}: {format_value(reference, variable)}. Delta is selected minus benchmark.")
                        short_reference="Denmark" if reference_label.startswith("Denmark") else "Municipality median"
                        st.caption(f"{short_reference}: **{format_value(reference,variable)}** · {METRICS[variable][2]}")
                        st.caption(rank_label(descriptive_rank(b["master"],variable,row[variable])))
    st.caption("Ranks are descriptive numerical positions, not health or performance grades. They use displayed precision and shared ranks for ties. Total, male and female life expectancy use national references; the sex gap and other indicators use unweighted municipality medians, not national prevalence. Differences in shares are percentage points (pp).")
    if detail not in ("Social conditions", "Model comparison"):
        with st.container():
            st.subheader("A profile, not a score")
            chart(charts.explorer_profile(b, row), "municipality_profile", "Six health indicators relative to the saved municipality means and standard deviations")
            st.caption("Uses saved scaling parameters. Each indicator retains its original direction; alcohol does not share the direction of PC1. No combined risk rating is assigned.")
    if detail == "Model comparison":
        section_heading("02", "Observed and model-predicted", "This uses the saved combined Model 3; it is not an evaluation of municipal policy.")
        prediction = b["predictions"].set_index("municipality").loc[name]
        if pd.notna(prediction.residual):
            with st.container():
                st.subheader("Observed versus predicted")
                st.markdown(f"Observed **{prediction.observed:.1f} years** · Model 3 fitted **{prediction.predicted:.2f} years** · residual **{prediction.residual:+.2f} years**.")
                st.caption("An in-sample comparison with the included indicators, not a measure of policy performance.")
                st.page_link("app_pages/expected.py", label="See the full expected-versus-observed analysis", icon=":material/arrow_forward:")
        if pd.isna(prediction.residual):
            st.info("No model prediction or residual is available because this municipality’s life expectancy is withheld.")
    note()


def expected():
    b = bundle()
    header("Beyond the fitted pattern", "Expected vs observed life expectancy", "Which municipalities have higher/lower life expectancy than predicted by the included municipality indicators?")
    reading_guide("Use the comparison chart to inspect individual municipalities, or switch to residuals to see observed-minus-predicted differences. The model-performance view explains how training fit differs from internal validation.")
    with st.container(key="residual_definition"):
        st.markdown("**Residual = observed life expectancy − model-predicted life expectancy.**")
    st.markdown("Positive values mean higher life expectancy than predicted; negative values mean lower. Predictions come from the saved combined Model 3.")
    quality = b["prediction_quality"]
    with st.grid(3, min_column_width=190):
        st.metric("Complete-case municipalities", quality["N"], border=True)
        st.metric("In-sample R²", f"{quality['in_sample_R_squared']:.3f}", border=True)
        st.metric("Leave-one-out R²", f"{quality['leave_one_out_R_squared']:.3f}", border=True)
    view = st.segmented_control("Explore", ["Observed vs predicted", "Municipality residuals", "Model performance"], default="Observed vs predicted", key="expected_view")
    if view in (None,"Observed vs predicted"):
        section_heading("01", "Observed and predicted values", "Points on the diagonal match the model prediction; points above it have higher observed life expectancy.")
        highlight = st.selectbox("Highlight a municipality", ["None", *sorted(b["master"].municipality.tolist())], key="prediction_highlight")
        chart(charts.prediction_scatter(b["predictions"], None if highlight == "None" else highlight), "prediction_scatter", "Saved observed and fitted life expectancy with equality line and optional municipality highlight")
        if highlight != "None" and b["predictions"].set_index("municipality").loc[highlight, "analysis_status"].startswith("withheld"):
            st.info("This municipality’s life expectancy is withheld. It has no fitted prediction or residual in this analysis.")
    elif view == "Municipality residuals":
        section_heading("02", "Differences from the fitted pattern", "Positive and negative residuals describe differences from the included indicators, not best/worst municipalities.")
        with st.grid(2, min_column_width=300, gap="medium") as grid:
            available = b["predictions"].dropna(subset=["residual"])
            for title, selected in [("Higher than predicted", available.nlargest(5, "residual")), ("Lower than predicted", available.nsmallest(5, "residual"))]:
                with grid.cell():
                    with st.container(border=True, height="stretch"):
                        st.subheader(title)
                        for item in selected.itertuples():
                            st.markdown(f"**{item.municipality}** · {item.residual:+.2f} years")
        st.caption("Five largest positive and negative saved residuals. These exploratory ranks are not best/worst labels and do not establish statistically unusual performance.")
        chart(charts.residual_ranking(b["predictions"]), "residual_ranking", "Largest absolute saved municipality residuals, observed minus predicted")
        fig = px.histogram(available, x="residual", nbins=16, color_discrete_sequence=[charts.TEAL],labels={"residual":"Residual (years)"})
        fig.add_vline(x=0, line_color=charts.BLUE, line_dash="dash")
        chart(charts.polish(fig, 300, "Observed − predicted (years)", "Municipalities"), "residual_distribution", "Distribution of all 94 saved Model 3 residuals")
    else:
        section_heading("03", "How well does the model predict?", "In-sample R² describes fit to the observations used to estimate the model. Leave-one-out R² predicts each municipality without using it in the fit.")
        st.markdown(f"**In-sample R²: {quality['in_sample_R_squared']:.3f}** · **Leave-one-out R²: {quality['leave_one_out_R_squared']:.3f}**")
        st.markdown("The lower leave-one-out value reflects a more demanding internal check. It does not establish performance in a future period or a geographically independent population. R² is not a causal fraction explained.")
    st.info("These are in-sample residuals. Leave-one-out validation reduces optimism but does not establish future or geographical transportability. Omitted factors, source uncertainty and chance can contribute to the residuals. Four withheld municipalities are not imputed.")
    note()


def health_profiles():
    b = bundle()
    header("Exploratory patterns", "Health profiles", "Explore how six health indicators vary together, without forcing them into a single measure of health or a natural classification.")
    reading_guide("PCA summarizes patterns shared by the six indicators; each point is a municipality. Start with the descriptive profiles, then open PCA explained or Choosing the profiles for detail. Alcohol behaves differently from the other indicators, so no overall health ranking is assigned.")
    variance = b["variance"].set_index("component")
    chosen = b["cluster_solution"]["chosen_k"]
    silhouette = b["cluster_validation"].set_index("k").loc[chosen, "silhouette"]
    with st.grid(4, min_column_width=170):
        st.metric("PC1 explained variance", f"{100*variance.loc['PC1','explained_variance_ratio']:.1f}%", border=True)
        st.metric("PC2 explained variance", f"{100*variance.loc['PC2','explained_variance_ratio']:.1f}%", border=True)
        st.metric("Selected profiles", chosen, border=True)
        st.metric("Mean silhouette", f"{silhouette:.3f}", border=True)
    st.info("PC1 is a mixed contrast, not a single health-risk score. Alcohol loads in the opposite direction to the other indicators. No variable was reversed to force agreement.")
    view = st.segmented_control("Explore", ["Municipality profiles", "PCA explained", "Choosing the profiles"], default="Municipality profiles", key="profiles_view")
    if view == "PCA explained":
        section_heading("02", "What the components represent", "Explained variance describes the six health indicators, not variation in life expectancy. Loadings show the direction and strength of each indicator’s relationship with a component.")
        chart(charts.scree(b["variance"]), "pca_scree", "Saved explained variance for all six principal components")
        pc = st.segmented_control("Component loadings", ["PC1", "PC2"], default="PC1", key="loading_component")
        loadings = b["loadings"].copy()
        chart(charts.loading_chart(loadings,pc), "pca_loadings", "Saved component loadings with indicators in their original health-exposure direction")
    elif view == "Choosing the profiles":
        section_heading("03", "Why two profiles?", "The choice follows the saved silhouette comparison. It does not establish natural groups.")
        st.markdown("The analysis evaluated k=2–6, retaining candidate solutions with at least five municipalities per group. Two profiles had the highest average silhouette. The inertia curve is a complementary diagnostic, not evidence of a unique natural partition.")
        fig = px.line(b["cluster_validation"].dropna(subset=["silhouette"]), x="k", y="silhouette", markers=True, color_discrete_sequence=[charts.TEAL],labels={"k":"Number of profiles","silhouette":"Mean silhouette"})
        chart(charts.polish(fig, 280, "Number of profiles", "Mean silhouette"), "cluster_selection", "Saved silhouette scores for every evaluated cluster count")
    else:
        section_heading("01", "Compare the descriptive profiles", "Locate a municipality in the projection, then compare the indicators below. Shapes and colours distinguish profiles.")
        st.subheader("Two descriptive municipality profiles")
        with st.grid(2, min_column_width=240):
            for item in b["sizes"].itertuples():
                st.metric(f"Profile {item.cluster}", f"{item.N} municipalities", border=True)
        st.markdown("**Profile 1** has lower smoking, obesity, inactivity and poorer-health indicators, but higher alcohol exposure. **Profile 2** shows the opposite relative pattern. Profiles describe differences across indicators, not an overall quality ranking.")
        highlight = st.selectbox("Locate a municipality in the PCA projection", ["None", *sorted(b["memberships"].municipality.tolist())], key="profile_highlight")
        fig = charts.pca_scatter(b["memberships"], None if highlight == "None" else highlight)
        fig.update_xaxes(title=f"PC1 · {100*variance.loc['PC1','explained_variance_ratio']:.1f}%")
        fig.update_yaxes(title=f"PC2 · {100*variance.loc['PC2','explained_variance_ratio']:.1f}%")
        chart(fig, "cluster_pca", "Municipalities in the saved PCA projection, coloured by their saved two-profile membership")
        st.caption("All 98 municipalities. Clustering uses all six standardized health indicators, not only these two plotted components.")
        profiles = b["profiles"].set_index("cluster")
        chart(charts.cluster_comparison(profiles,FEATURES), "cluster_profiles", "Saved standardized mean health indicators for each profile; symbols and colours distinguish profiles")
        st.caption("Alcohol differs from the other indicators. Profiles should not be read as an overall health ranking: these are descriptive profiles, not natural or causal groups.")
    note()


def methods():
    b = bundle()
    header("How to read the evidence", "Methods & limitations", "A transparent overview of the sources, analytical choices and limits behind the atlas.")
    with st.container(key="method_summary"):
        with st.grid(4,min_column_width=200):
            st.metric("Complete cases",94,border=True)
            st.metric("Robust standard errors","HC3",border=True)
            st.metric("Multiple-testing correction","FDR",border=True)
            st.metric("Missing-data policy","No imputation",border=True)
    reading_guide("Read the limitations before interpreting a result. The other views explain the official sources and statistical methods; full methods are available to download.")
    view = st.segmented_control("Read", ["Limitations", "Data sources", "Statistical methods"], default="Limitations", key="methods_view")
    if view == "Data sources":
        st.subheader("Three source windows, one municipality atlas")
        with st.grid(3, min_column_width=230) as grid:
            for title, description, url in [
                ("Statistics Denmark", "2024 income, education, population and age structure from the public StatBank API.", "https://www.dst.dk/en/Statistik/hjaelp-til-statistikbanken/api"),
                ("National Health Profile", "2025 municipality prevalence exports from the official public guest viewer.", "https://www.danskernessundhed.dk/"),
                ("Official life expectancy", "HISBK period estimates for 2021–2025, both sexes, males and females.", "https://www.statbank.dk/HISBK"),
            ]:
                with grid.cell():
                    with st.container(border=True, height="stretch"):
                        st.subheader(title)
                        st.markdown(description)
                        st.link_button("Official source", url, icon=":material/open_in_new:")
    elif view == "Statistical methods":
        st.subheader("Primary and exploratory analyses")
        st.markdown("The four total-life-expectancy OLS specifications are fixed primary analyses, each with **94 complete cases** and HC3 robust standard errors. Correlations, PCA, k-means, residual rankings and sex-specific analyses are secondary or exploratory. There is no p-value-driven variable deletion and no imputation.")
        for title, content in [
            ("Correlations & multiple testing", "Pearson captures linear association; Spearman captures rank association. Both use pairwise complete cases, N=94–98. BH FDR q-values are saved for all 136 pairs per method; a separate 16-test life-expectancy family is also available. All results are retained."),
            ("OLS, HC3, standardized beta & VIF", "OLS fits the specified municipality associations. HC3 estimates heteroskedasticity-robust covariance with t-based 95% intervals. Standardized beta rescales slopes by SD(X)/SD(Y). VIF describes collinearity. Primary q-values cover 20 non-intercept coefficient tests; no predictor is automatically removed."),
            ("PCA & k-means", "Six health indicators are standardized using saved means and population SDs. Higher raw values retain their adverse-exposure direction. PCA is exploratory; its loadings do not support a single health-risk label. K-means compares k=2–6, with fixed seed 42 and 50 initializations. All 98 municipalities enter these feature-only analyses."),
            ("Cook’s distance & sensitivity analyses", "Cook’s D>4/N flags influence; leverage and studentized residuals are also saved. Full-sample models retain flagged places. Separate exploratory sensitivity fits exclude Cook-flagged observations, without selecting a preferred cleaned result."),
            ("Prediction & leave-one-out validation", "The saved six-predictor Model 3 generates in-sample fitted values and observed-minus-predicted residuals for 94 municipalities. Exact OLS leave-one-out predictions assess internal predictive optimism. They do not establish external or future performance."),
        ]:
            with st.expander(title):
                st.markdown(content)
        with st.expander("Saved diagnostic and sensitivity results"):
            diagnostics = b["diagnostics"].loc[b["diagnostics"].model.eq("M4")].iloc[0]
            max_vif = b["vif"].loc[b["vif"].model.eq("M4"), "VIF"].max()
            st.markdown(f"Expanded-model maximum VIF: **{max_vif:.2f}**. Cook-flagged municipalities: **{int(diagnostics.high_Cook_N)}**. These observations remain in the primary model.")
            st.markdown("Smoking’s nominal p-value changes from about 0.049 to 0.061 under the Model 4 influence exclusion. It does not pass primary-family FDR correction in the full model. No predictor direction changed in the saved influence sensitivities.")
    else:
        st.subheader("Limitations that matter")
        st.markdown("""
    - **Ecological design:** municipality averages do not describe individual risks. Association is not causation.
    - **Timing:** socioeconomic measures refer to 2024, survey measures to 2025, and life expectancy to 2021–2025. Reverse causation and unmeasured confounding remain possible.
    - **Four withheld municipalities:** Ærø, Fanø, Samsø and Læsø are not imputed. Their health profiles are available, but life-expectancy analyses exclude them.
    - **Collinearity:** strongly related predictors can produce unstable or reversed conditional coefficients. A positive adjusted obesity coefficient is not evidence of protection.
    - **Source uncertainty:** self-report, nonresponse, rounding and uncertain mortality estimates are not eliminated by complete aggregate coverage or HC3.
    - **Spatial dependence:** geographical autocorrelation is not modelled. HC3 does not correct it; conventional inference may be optimistic.
    - **Scope:** equal municipality weighting and the prespecified covariates do not resolve population composition, omitted context or within-municipality inequality.
    """)
    st.download_button("Download full analysis methods", (ROOT / "report/analysis_methods.md").read_text(), file_name="atlas-analysis-methods.md", mime="text/markdown", icon=":material/download:")
    note()


def data_page():
    b = bundle()
    header("Open data, clear provenance", "Data", "Inspect the data dictionary, review official sources and download the exact processed data behind the atlas.")
    with st.grid(3, min_column_width=190):
        st.metric("Municipality records", len(b["master"]), border=True)
        st.metric("Published life expectancy", int(b["master"].life_expectancy_total.count()), border=True)
        st.metric("Validated analysis snapshot", "Verified", help="The master and displayed analysis artifacts match their recorded SHA-256 checksums.", border=True)
    reading_guide("Browse municipality values, check indicator definitions or open the source and analysis downloads. Downloaded data retain the validated values, including missing estimates.")
    rows = []
    inventory = b["inventory"].set_index("variable")
    for key, (label, unit, period) in METRICS.items():
        item = inventory.loc[key]
        rows.append({"Indicator": label, "Unit": unit, "Reference period": period, "Published N": int(item.N_observed), "Missing": int(item.missing), "Source": item.source})
    with st.container(horizontal=True):
        st.download_button("Download municipality dataset", (ROOT / "data/processed/municipality_master.csv").read_bytes(), file_name="danish-health-atlas-municipalities.csv", mime="text/csv", icon=":material/download:", key="download_master")
        st.download_button("Download data dictionary", pd.DataFrame(rows).to_csv(index=False), file_name="atlas-data-dictionary.csv", mime="text/csv", icon=":material/download:", key="download_dictionary")
    view = st.segmented_control("Browse", ["Municipality data", "Data dictionary", "Sources & downloads"], default="Municipality data", key="data_view")
    if view == "Data dictionary":
        st.subheader("Data dictionary")
        st.dataframe(pd.DataFrame(rows), hide_index=True,height=420,row_height=36,
            column_config={"Indicator":st.column_config.TextColumn(width=280,pinned=True),"Reference period":st.column_config.TextColumn(width=180),
                "Source":st.column_config.TextColumn(width=250),"Published N":st.column_config.NumberColumn(format="%d",width=110),
                "Missing":st.column_config.NumberColumn(format="%d",width=90)},
            alt="Public-facing indicator dictionary with units, reference periods, sample sizes and official sources")
        st.caption("Low education refers to primary education among ages 25–64, with unknown attainment retained in the denominator. Self-rated health combines ‘mindre godt’ and ‘dårligt’. Poor mental health uses the portal’s low SF-12 score definition.")
    elif view == "Sources & downloads":
        st.subheader("Official sources")
        for label, url in [("Statistics Denmark · socioeconomic data", "https://www.statbank.dk/"), ("Statistics Denmark · HISBK life expectancy", "https://www.statbank.dk/HISBK"), ("Danish National Health Profile · 2025", "https://www.danskernessundhed.dk/"), ("Danish Health Authority · National Health Profile", "https://www.sst.dk/sundhedsprofilen")]:
            st.link_button(label, url, icon=":material/open_in_new:")
        st.caption("Source: Statistics Denmark and Den Nationale Sundhedsprofil, Sundhedsstyrelsen / Statens Institut for Folkesundhed, SDU. Attribute the original publishers when reusing the data.")
        st.subheader("Download the saved analysis")
        downloads = {"Descriptive statistics": "descriptive_statistics.csv", "All correlations and FDR results": "correlations_full.csv", "Primary regression coefficients": "regression_coefficients.csv", "Model fit comparison": "regression_model_fit.csv", "Municipality predictions and residuals": "municipality_predictions_residuals.csv", "Profile membership": "cluster_membership.csv", "Secondary sex-specific coefficients": "secondary_regression_coefficients.csv"}
        choice = st.selectbox("Analysis table", list(downloads), key="download_table")
        filename = downloads[choice]
        path = ROOT / "outputs/tables" / filename
        expected_hash = next(a["sha256"] for a in b["manifest"]["artifacts"] if a["file"] == f"outputs/tables/{filename}")
        if digest(path) != expected_hash:
            st.error("This saved table no longer matches the validated snapshot.")
        else:
            st.download_button("Download selected table", path.read_bytes(), file_name="atlas-" + filename.replace("_", "-"), mime="text/csv", icon=":material/download:", key="download_analysis")
        with st.expander("Provenance and reproducibility"):
            st.markdown("Every displayed result is read from the validated analysis snapshot. Raw responses, original Excel exports, source definitions, API requests, periods and checksums are retained in the acquisition provenance. The dashboard does not refit statistical models.")
            st.code(b["manifest"]["input_sha256"], language=None)
            st.caption("SHA-256 of the exact processed municipality dataset")
            st.download_button("Download source provenance", json.dumps(b["provenance"], ensure_ascii=False, indent=2), file_name="atlas-source-provenance.json", mime="application/json", key="download_provenance")
            st.download_button("Download analysis audit manifest", json.dumps(b["manifest"], ensure_ascii=False, indent=2), file_name="atlas-analysis-audit.json", mime="application/json", key="download_manifest")
    else:
        st.subheader("Processed municipality data")
        preview = b["master"][["municipality", *list(METRICS)[:12]]].rename(columns={"municipality": "Municipality", **LABELS})
        columns={"Municipality":st.column_config.TextColumn(width=170,pinned=True)}
        for variable in list(METRICS)[:12]:
            label,unit,period=METRICS[variable]
            fmt="%,d DKK" if unit=="DKK" else "%.1f%%" if unit=="%" else "%.1f"
            columns[label]=st.column_config.NumberColumn(label,width=200,format=fmt,help=f"{unit} · {period}. Missing estimates are not imputed.")
        st.dataframe(preview, hide_index=True, height=390,row_height=36,column_config=columns,
            alt="Processed data preview for all 98 municipalities; withheld life expectancy remains missing")
        st.caption("Life expectancy is shown in years; shares in percent. The municipality column stays visible while the table scrolls horizontally.")
    with st.container(key="reproducibility_note"):
        st.caption("Raw data are preserved. Processed datasets are reproducible, provenance is stored, and the analyses shown here are precomputed and validated. Downloads retain the original validated values.")
    note()
