"""Read-only presentation data, verified against the validated analysis artifacts."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
TABLES = {
    "correlations": "correlations_total_life_expectancy.csv",
    "matrix": "correlation_matrix_pearson.csv",
    "coefficients": "regression_coefficients.csv",
    "fits": "regression_model_fit.csv",
    "inventory": "analytic_variable_inventory.csv",
    "predictions": "municipality_predictions_residuals.csv",
    "variance": "pca_explained_variance.csv",
    "loadings": "pca_loadings.csv",
    "memberships": "cluster_membership.csv",
    "profiles": "cluster_profiles_standardized.csv",
    "sizes": "cluster_sizes.csv",
    "cluster_validation": "cluster_validation.csv",
    "scaling": "health_feature_scaling.csv",
    "diagnostics": "model_diagnostics.csv",
    "sensitivity": "sensitivity_analysis.csv",
    "vif": "vif.csv",
}
JSONS = {"increment": "incremental_explanatory_value.json", "prediction_quality": "prediction_quality.json", "cluster_solution": "cluster_solution.json"}
METRICS = {
    "life_expectancy_total": ("Life expectancy", "years", "2021–2025"),
    "life_expectancy_male": ("Male life expectancy", "years", "2021–2025"),
    "life_expectancy_female": ("Female life expectancy", "years", "2021–2025"),
    "life_expectancy_sex_gap": ("Female–male life-expectancy gap", "years", "2021–2025"),
    "disposable_income_mean_dkk": ("Disposable income", "DKK", "2024"),
    "low_education_share_25_64_pct": ("Primary education, ages 25–64", "%", "30 September 2024"),
    "daily_smoking_pct": ("Daily smoking", "%", "2025"),
    "obesity_pct": ("Obesity · BMI ≥30", "%", "2025"),
    "physical_inactivity_pct": ("Insufficient physical activity", "%", "2025"),
    "risky_alcohol_pct": ("Alcohol above 10 drinks/week", "%", "2025"),
    "less_good_or_poor_self_rated_health_pct": ("Less-good/poor self-rated health", "%", "2025"),
    "poor_mental_health_pct": ("Poor SF-12 mental health", "%", "2025"),
    "population": ("Population", "people", "1 January 2024"),
    "age_0_17_share_pct": ("Population aged 0–17", "%", "1 January 2024"),
    "age_18_64_share_pct": ("Population aged 18–64", "%", "1 January 2024"),
    "age_65_plus_share_pct": ("Population aged 65+", "%", "1 January 2024"),
    "education_unknown_share_25_64_pct": ("Unknown education, ages 25–64", "%", "30 September 2024"),
}
FEATURES = ["daily_smoking_pct", "obesity_pct", "physical_inactivity_pct", "risky_alcohol_pct", "less_good_or_poor_self_rated_health_pct", "poor_mental_health_pct"]
LABELS = {c: value[0] for c, value in METRICS.items()}
LABELS["income_per_10000_dkk"] = "Income · per DKK 10,000"
MODEL_LABELS = {"M1": "Socioeconomic", "M2": "Health behaviours", "M3": "Combined", "M4": "Expanded health"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_dashboard():
    paths = [ROOT / "data/processed/municipality_master.csv", ROOT / "data/processed/municipality_master_provenance.json",
        ROOT / "outputs/tables/analysis_manifest.json", ROOT / "outputs/tables/life_expectancy_quality.json", ROOT / "report/source_inventory.csv"]
    paths += [ROOT / "outputs/tables" / name for name in [*TABLES.values(), *JSONS.values()]]
    signature = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in paths)
    return _load(signature)


@st.cache_data(ttl=3600, max_entries=2, show_spinner=False)
def _load(signature):
    manifest = json.loads((ROOT / "outputs/tables/analysis_manifest.json").read_text())
    master = ROOT / "data/processed/municipality_master.csv"
    provenance = json.loads(master.with_name("municipality_master_provenance.json").read_text())
    if manifest["status"] != "complete" or digest(master) != manifest["input_sha256"] or digest(master) != provenance["master_sha256"]:
        raise ValueError("The data and validated analysis snapshot do not match.")
    expected = {a["file"]: a["sha256"] for a in manifest["artifacts"]}
    bundle = {"manifest": manifest, "provenance": provenance}
    bundle["master"] = pd.read_csv(master, dtype={"municipality_code": str})
    for key, name in {**TABLES, **JSONS}.items():
        relative = f"outputs/tables/{name}"
        path = ROOT / relative
        if digest(path) != expected[relative]:
            raise ValueError(f"A validated result has changed: {key}.")
        bundle[key] = json.loads(path.read_text()) if key in JSONS else pd.read_csv(path, dtype={"municipality_code": str})
    bundle["matrix"] = bundle["matrix"].set_index(bundle["matrix"].columns[0])
    bundle["life_quality"] = json.loads((ROOT / "outputs/tables/life_expectancy_quality.json").read_text())
    if bundle["life_quality"]["raw_manifest_sha256"] != provenance["raw_manifest_sha256"]:
        raise ValueError("Life-expectancy quality report does not match data provenance.")
    bundle["sources"] = pd.read_csv(ROOT / "report/source_inventory.csv")
    return bundle


def characteristics(bundle, method="Pearson"):
    d = bundle["correlations"]
    return d.loc[d.method.eq(method) & ~d.algebraically_related_outcome].copy().sort_values("correlation", key=abs, ascending=False)


def format_value(value, variable):
    if pd.isna(value):
        return "Not published"
    unit = METRICS[variable][1]
    if unit == "DKK":
        return f"{value:,.0f} DKK"
    if unit == "people":
        return f"{value:,.0f}"
    return f"{value:.1f}{'%' if unit == '%' else ' years'}"


def benchmark(bundle, variable):
    national = bundle["life_quality"]["national_values_years"]
    if variable in national:
        return national[variable], "Denmark · published national value"
    return float(bundle["master"][variable].median()), "Municipality median · unweighted"


def descriptive_rank(master, variable, value):
    """Descending shared rank at displayed precision; never a quality rating."""
    if pd.isna(value):
        return None
    decimals = 0 if METRICS[variable][1] in ("DKK", "people") else 1
    observed = master[variable].dropna().round(decimals)
    displayed = round(float(value), decimals)
    return {"rank": 1 + int(observed.gt(displayed).sum()), "N": len(observed),
            "tied": int(observed.eq(displayed).sum()) > 1}


def rank_label(rank):
    if rank is None:
        return "No rank · value not published"
    number = rank["rank"]
    suffix = "th" if 10 <= number % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{'Tied ' if rank['tied'] else ''}{number}{suffix} highest of {rank['N']} published"


def association_line(bundle, variable):
    """Display the existing Pearson result as a least-squares guide; no model fit."""
    sample = bundle["master"][[variable, "life_expectancy_total"]].dropna()
    r = float(characteristics(bundle).set_index("other_variable").loc[variable, "correlation"])
    x = np.array([sample[variable].min(), sample[variable].max()])
    slope = r * sample.life_expectancy_total.std(ddof=1) / sample[variable].std(ddof=1)
    return x, sample.life_expectancy_total.mean() + slope * (x - sample[variable].mean())
