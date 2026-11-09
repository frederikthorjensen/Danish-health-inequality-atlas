"""Reproducible municipality analysis: python -m src.analysis.

Primary models are fixed before estimation. No imputation or p-value-driven
selection. Exploratory correlations, profiles and residual screens are labelled.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib import metadata as package_metadata
import itertools
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, mean_absolute_error, r2_score, silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from src.data_collection import ROOT
from src import visualization as viz

SEED = 42
SOCIO = ["income_per_10000_dkk", "low_education_share_25_64_pct"]
BEHAVIOURS = ["daily_smoking_pct", "obesity_pct", "physical_inactivity_pct", "risky_alcohol_pct"]
EXPANDED = ["less_good_or_poor_self_rated_health_pct", "poor_mental_health_pct"]
HEALTH_FEATURES = BEHAVIOURS + EXPANDED
FEATURE_DIRECTIONS = {c: 1 for c in HEALTH_FEATURES}
MODELS = {"M1": SOCIO, "M2": BEHAVIOURS, "M3": SOCIO + BEHAVIOURS, "M4": SOCIO + HEALTH_FEATURES}
OUTCOMES = ["life_expectancy_total", "life_expectancy_male", "life_expectancy_female", "life_expectancy_sex_gap"]
CORRELATION_VARIABLES = OUTCOMES + ["disposable_income_mean_dkk", "low_education_share_25_64_pct",
    "education_unknown_share_25_64_pct", "population", "age_0_17_share_pct", "age_18_64_share_pct", "age_65_plus_share_pct"] + HEALTH_FEATURES


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_data(path: Path) -> pd.DataFrame:
    provenance = json.loads(path.with_name(path.stem + "_provenance.json").read_text())
    if sha256(path) != provenance["master_sha256"]:
        raise ValueError("Master checksum does not match acquisition provenance")
    data = pd.read_csv(path, dtype={"municipality_code": str})
    if len(data) != 98 or data.municipality_code.duplicated().any() or data.municipality.duplicated().any():
        raise ValueError("Expected 98 unique municipalities")
    if data[["municipality_code", "municipality"]].isna().any().any():
        raise ValueError("Missing municipality identifiers")
    required = set(CORRELATION_VARIABLES) - {"income_per_10000_dkk"}
    if not required <= set(data):
        raise ValueError(f"Missing required variables: {required - set(data)}")
    unavailable = set(data.loc[data.life_expectancy_total.isna(), "municipality_code"])
    if unavailable != {"492", "563", "741", "825"}:
        raise ValueError("Source-withheld municipality set changed; review the analytic sample contract")
    for c in required:
        observed = data[c].dropna()
        if not np.isfinite(observed).all():
            raise ValueError(f"Nonfinite data: {c}")
    data["income_per_10000_dkk"] = data.disposable_income_mean_dkk / 10_000
    return data


def complete_cases(data: pd.DataFrame, outcome: str, predictors: list[str]) -> pd.DataFrame:
    return data.dropna(subset=[outcome, *predictors]).copy()


def standardized_beta(coefficient: float, x: pd.Series, y: pd.Series) -> float:
    return float(coefficient * x.std(ddof=1) / y.std(ddof=1))


def fit_model(data: pd.DataFrame, outcome: str, predictors: list[str], name: str):
    sample = complete_cases(data, outcome, predictors)
    x = sm.add_constant(sample[predictors].astype(float), has_constant="add")
    y = sample[outcome].astype(float)
    if np.linalg.matrix_rank(x.to_numpy()) != x.shape[1] or len(sample) <= x.shape[1] + 2:
        raise ValueError(f"Insufficient sample or rank-deficient model: {name}")
    result = sm.OLS(y, x, missing="raise").fit(cov_type="HC3", use_t=True)
    confidence = result.conf_int(alpha=.05)
    coefficients = []
    for term in result.params.index:
        scale = sample[term].std(ddof=1) / y.std(ddof=1) if term != "const" else np.nan
        coefficients.append({"model": name, "outcome": outcome, "N": len(sample), "term": term,
            "coefficient": float(result.params[term]), "robust_se_HC3": float(result.bse[term]),
            "standardized_beta": float(result.params[term] * scale),
            "robust_p_value": float(result.pvalues[term]), "ci_low": float(confidence.loc[term, 0]),
            "ci_high": float(confidence.loc[term, 1]),
            "standardized_ci_low": float(confidence.loc[term, 0] * scale),
            "standardized_ci_high": float(confidence.loc[term, 1] * scale),
            "inference": "HC3, Student t, residual degrees of freedom"})
    z = (sample[predictors] - sample[predictors].mean()) / sample[predictors].std(ddof=1)
    zdesign = sm.add_constant(z, has_constant="add")
    fit = {"model": name, "outcome": outcome, "N": len(sample), "predictors": len(predictors),
        "R_squared": float(result.rsquared), "adjusted_R_squared": float(result.rsquared_adj),
        "AIC": float(result.aic), "BIC": float(result.bic), "residual_df": float(result.df_resid),
        "residual_SD_years": float(np.sqrt(result.mse_resid)),
        "condition_number_standardized_design": float(np.linalg.cond(zdesign)),
        "sample_codes": ";".join(sample.municipality_code)}
    vif = [{"model": name, "outcome": outcome, "term": c, "VIF": float(variance_inflation_factor(zdesign.to_numpy(), i + 1))}
           for i, c in enumerate(predictors)]
    return result, sample, pd.DataFrame(coefficients), fit, pd.DataFrame(vif)


def fdr_coefficients(table: pd.DataFrame, family: str) -> pd.DataFrame:
    table = table.copy()
    table["q_value_family_BH"] = np.nan
    test = table.term.ne("const")
    table.loc[test, "q_value_family_BH"] = multipletests(table.loc[test, "robust_p_value"], method="fdr_bh")[1]
    table["FDR_family"] = family
    return table


def correlations(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for a, b in itertools.combinations(CORRELATION_VARIABLES, 2):
        d = data[[a, b]].dropna()
        for method, function in (("Pearson", stats.pearsonr), ("Spearman", stats.spearmanr)):
            statistic, p_value = function(d[a], d[b])
            rows.append({"variable_1": a, "variable_2": b, "method": method, "N": len(d),
                         "correlation": float(statistic), "p_value": float(p_value)})
    table = pd.DataFrame(rows)
    table["q_value_BH_all_pairs"] = np.nan
    table["q_value_BH_total_life_expectancy_family"] = np.nan
    for method in table.method.unique():
        all_pairs = table.method.eq(method)
        table.loc[all_pairs, "q_value_BH_all_pairs"] = multipletests(table.loc[all_pairs, "p_value"], method="fdr_bh")[1]
        outcome_pairs = all_pairs & (table.variable_1.eq(OUTCOMES[0]) | table.variable_2.eq(OUTCOMES[0]))
        table.loc[outcome_pairs, "q_value_BH_total_life_expectancy_family"] = multipletests(table.loc[outcome_pairs, "p_value"], method="fdr_bh")[1]
    table["analysis_role"] = "exploratory; pairwise complete cases"
    return table


def prepare_health_features(data: pd.DataFrame):
    sample = data.dropna(subset=HEALTH_FEATURES).copy()
    directed = sample[HEALTH_FEATURES].multiply(pd.Series(FEATURE_DIRECTIONS))
    scaler = StandardScaler()
    scaled = scaler.fit_transform(directed)
    return sample, scaled, scaler


def profile_analysis(data: pd.DataFrame) -> dict:
    sample, scaled, scaler = prepare_health_features(data)
    pca = PCA(svd_solver="full")
    scores = pca.fit_transform(scaled)
    # PCA signs are arbitrary: orient PC1 to positive sum, others by largest weight.
    for i in range(len(HEALTH_FEATURES)):
        sign = np.sign(pca.components_[i].sum()) if i == 0 else np.sign(pca.components_[i, np.argmax(np.abs(pca.components_[i]))])
        if sign < 0:
            scores[:, i] *= -1
            pca.components_[i] *= -1
    loading = np.corrcoef(scaled.T, scores.T)[:len(HEALTH_FEATURES), len(HEALTH_FEATURES):]
    coherent = bool((loading[:, 0] >= .2).all())
    metrics, solutions = [], {}
    with threadpool_limits(limits=1):
        for k in range(1, 7):
            model = KMeans(n_clusters=k, random_state=SEED, n_init=50, algorithm="lloyd").fit(scaled)
            sizes = np.bincount(model.labels_)
            metrics.append({"k": k, "inertia": float(model.inertia_),
                "silhouette": float(silhouette_score(scaled, model.labels_)) if k > 1 else np.nan,
                "minimum_cluster_size": int(sizes.min()), "eligible_minimum_size_5": bool(sizes.min() >= 5)})
            solutions[k] = model
        validation = pd.DataFrame(metrics)
        eligible = validation.loc[validation.k.between(2, 6) & validation.eligible_minimum_size_5]
        if eligible.empty:
            raise ValueError("No eligible cluster solution; review profiles rather than force a selection")
        chosen = int(eligible.sort_values(["silhouette", "k"], ascending=[False, True]).iloc[0].k)
        model = solutions[chosen]
        # Profile numbering is a stable display convention, not a quality ranking.
        ordered = np.argsort(model.cluster_centers_ @ pca.components_[0])
        labels = np.array([{int(old): i + 1 for i, old in enumerate(ordered)}[int(c)] for c in model.labels_])
        stability = []
        for seed in range(10):
            other = KMeans(n_clusters=chosen, random_state=seed, n_init=50, algorithm="lloyd").fit_predict(scaled)
            stability.append({"seed": seed, "k": chosen, "adjusted_Rand_index_vs_seed42": float(adjusted_rand_score(labels, other))})
    membership = sample[["municipality_code", "municipality"]].reset_index(drop=True)
    membership["cluster"] = labels
    membership["silhouette"] = silhouette_samples(scaled, labels)
    for i in range(len(HEALTH_FEATURES)):
        membership[f"PC{i+1}"] = scores[:, i]
    ztable = pd.DataFrame(scaled, columns=HEALTH_FEATURES)
    ztable["cluster"] = labels
    raw = sample[HEALTH_FEATURES].reset_index(drop=True).copy()
    raw["cluster"] = labels
    return {"sample": sample, "scaled": scaled, "scaler": scaler, "pca": pca,
        "loadings": loading, "scores": scores, "coherent_PC1": coherent,
        "validation": validation, "chosen_k": chosen, "membership": membership,
        "standardized_profiles": ztable.groupby("cluster")[HEALTH_FEATURES].mean(),
        "raw_profiles": raw.groupby("cluster")[HEALTH_FEATURES].mean(),
        "stability": pd.DataFrame(stability)}


def influence_table(result, sample, name):
    influence = result.get_influence()
    table = sample[["municipality_code", "municipality"]].copy()
    table["model"] = name
    table["fitted"] = result.fittedvalues
    table["residual"] = result.resid
    table["studentized_internal"] = influence.resid_studentized_internal
    table["studentized_external"] = influence.resid_studentized_external
    table["leverage"] = influence.hat_matrix_diag
    table["cooks_distance"] = influence.cooks_distance[0]
    table["high_cook"] = table.cooks_distance.gt(4 / len(sample))
    table["high_leverage"] = table.leverage.gt(2 * len(result.params) / len(sample))
    table["large_studentized_residual"] = table.studentized_external.abs().gt(2)
    return table


def residual_table(data, result, sample):
    influence = result.get_influence()
    table = sample[["municipality_code", "municipality"]].copy()
    table["observed"] = sample.life_expectancy_total
    table["predicted"] = result.predict(sm.add_constant(sample[MODELS["M3"]], has_constant="add"))
    table["residual"] = table.observed - table.predicted
    table["standardized_residual"] = influence.resid_studentized_internal
    table["externally_studentized_residual"] = influence.resid_studentized_external
    table["loo_residual"] = table.residual / (1 - influence.hat_matrix_diag)
    table["loo_predicted"] = table.observed - table.loo_residual
    table["residual_rank_descending"] = table.residual.rank(ascending=False, method="min").astype(int)
    table["residual_screen"] = np.select([table.externally_studentized_residual.ge(2), table.externally_studentized_residual.le(-2)],
        ["higher than fitted; |studentized residual| >=2", "lower than fitted; |studentized residual| >=2"], default="not flagged by descriptive 2-SD screen")
    merged = data[["municipality_code", "municipality"]].merge(table, on=["municipality_code", "municipality"], how="left", validate="one_to_one")
    merged["analysis_status"] = np.where(merged.observed.notna(), "complete case; Model 3 in-sample fit", "withheld life expectancy; no prediction/imputation")
    return merged.sort_values("residual", ascending=False, na_position="last")


class Artifacts:
    def __init__(self, root):
        self.root, self.files = root, []
        self.tables, self.figures = root / "outputs/tables", root / "outputs/figures"
        self.tables.mkdir(parents=True, exist_ok=True)
        self.figures.mkdir(parents=True, exist_ok=True)

    def csv(self, table, name, index=False):
        path = self.tables / name
        table.to_csv(path, index=index, float_format="%.12g")
        self.files.append(path)

    def json(self, value, name):
        path = self.tables / name
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        self.files.append(path)

    def text(self, text, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self.files.append(path)


def inventory_and_descriptives(data):
    measures = [c for c in data.select_dtypes(include="number") if not c.endswith("_year")]
    inventory = []
    for c in data:
        if c.startswith("life_expectancy"):
            source, period = "Statistics Denmark HISBK", "2021:2025"
        elif any(c.startswith(feature.removesuffix("_pct")) for feature in [*HEALTH_FEATURES, "good_self_rated_health_pct"]):
            source, period = "National Health Profile", "2025"
        elif "income" in c:
            source, period = "Statistics Denmark INDKP106", "2024"
        elif "education" in c:
            source, period = "Statistics Denmark HFUDD11", "2024-09-30"
        else:
            source, period = "Statistics Denmark FOLK1A / municipality identifiers", "2024-01-01"
        role = "measurement" if c in measures else "identifier" if c in ("municipality", "municipality_code") else "status" if c.endswith("_status") else "reference period/date"
        note = ""
        if c == "good_self_rated_health_pct":
            note = "Excluded from correlations/PCA/models: exact complement of less-good/poor measure"
        elif c not in CORRELATION_VARIABLES and c in measures:
            note = "Descriptive only; redundant component/denominator count or rescaled income"
        if c == "income_per_10000_dkk":
            note = "Derived disposable_income_mean_dkk / 10000 for interpretable regression coefficients"
        inventory.append({"variable": c, "label": viz.LABELS.get(c, c), "role": role,
            "dtype": str(data[c].dtype), "source": source, "reference_period": period,
            "unit": "percent" if c.endswith("_pct") else "years" if c in OUTCOMES else "DKK 10000" if c == "income_per_10000_dkk" else "DKK" if c == "disposable_income_mean_dkk" else "persons" if c in measures else "metadata",
            "N_observed": int(data[c].notna().sum()), "missing": int(data[c].isna().sum()),
            "correlation_analysis": c in CORRELATION_VARIABLES,
            "primary_models": ";".join(m for m, variables in MODELS.items() if c in variables),
            "PCA_clustering": c in HEALTH_FEATURES, "higher_is_worse_for_profiles": FEATURE_DIRECTIONS.get(c), "note": note})
    descriptions = []
    for c in measures:
        s = data[c]
        q25, q75 = s.quantile([.25, .75])
        descriptions.append({"variable": c, "N": int(s.count()), "missing": int(s.isna().sum()),
            "mean": s.mean(), "SD": s.std(ddof=1), "median": s.median(), "Q1": q25, "Q3": q75,
            "IQR": q75 - q25, "min": s.min(), "max": s.max()})
    return pd.DataFrame(inventory), pd.DataFrame(descriptions)


def markdown_table(frame: pd.DataFrame) -> str:
    def render(value):
        if pd.isna(value):
            return "—"
        if isinstance(value, (float, np.floating)):
            return f"{value:.4g}"
        return str(value).replace("|", "/").replace("\n", " ")
    return ("| " + " | ".join(map(str, frame.columns)) + " |\n| " + " | ".join("---" for _ in frame.columns) + " |\n"
        + "\n".join("| " + " | ".join(render(v) for v in row) + " |" for row in frame.itertuples(index=False, name=None)) + "\n")


def results_report(artifacts, coefficients, fit_table, total_corr, incremental, diagnostic_rows,
                   sensitivities, profiles, predictions, secondary, secondary_fit, prediction_quality, vif_table):
    lines = ["# Analysis results\n", "Generated by `python -m src.analysis` from the checksum-verified official municipality master. All source data and the dashboard remain unchanged. No imputation. These are municipality-level associations, not causal effects.\n",
        "## Samples and reporting\n", "All four primary models and each sex-specific model use **94 complete cases**. PCA/clustering use **98 municipalities**. Ærø, Fanø, Samsø and Læsø have withheld life expectancy and are never assigned outcome values or predictions. Correlations use pairwise complete cases (N=94–98). Full outputs include nonsignificant results.\n",
        "## Exploratory correlations with total life expectancy\n", "Other life-expectancy outcomes are excluded from this characteristics summary because they are algebraically related; they remain in the full correlation table. Q-values below use the global 136-pair family separately for Pearson and Spearman.\n"]
    corr = total_corr.loc[~total_corr.algebraically_related_outcome]
    summary = corr.pivot(index="other_variable", columns="method", values=["correlation", "p_value", "q_value_BH_all_pairs"])
    summary.columns = [f"{method} {statistic}" for statistic, method in summary.columns]
    summary = summary.sort_values("Pearson correlation", key=abs, ascending=False).reset_index()
    lines += [markdown_table(summary), "## Primary regressions\n", "HC3 SEs, t-based 95% intervals, equal municipality weights. Income coefficients are per DKK 10,000; health and education coefficients per percentage point. All models include an intercept; full intercept/SE/VIF information is saved in CSV/text.\n",
        markdown_table(fit_table[["model", "N", "R_squared", "adjusted_R_squared", "AIC", "BIC"]])]
    for model in MODELS:
        c = coefficients.loc[coefficients.model.eq(model) & coefficients.term.ne("const"), ["term", "coefficient", "standardized_beta", "ci_low", "ci_high", "robust_p_value", "q_value_family_BH"]]
        lines += [f"### {model}\n", markdown_table(c)]
    lines += [f"Adding the four behaviour variables to M1 increases R² by **{incremental['delta_R_squared']:.4f}** and adjusted R² by **{incremental['delta_adjusted_R_squared']:.4f}**. The prespecified HC3 joint block test is F({incremental['df_num']:.0f}, {incremental['df_denom']:.0f})={incremental['HC3_joint_Wald_F']:.3f}, p={incremental['p_value']:.4g}. This is in-sample incremental association, not a causal fraction explained.\n"]
    final = coefficients.loc[coefficients.model.eq("M4") & coefficients.term.ne("const")]
    nominal = final.loc[final.robust_p_value.lt(.05), "term"].tolist()
    adjusted = final.loc[final.q_value_family_BH.lt(.05), "term"].tolist()
    smoking = final.loc[final.term.eq("daily_smoking_pct")].iloc[0]
    vif_final = vif_table.loc[vif_table.model.eq("M4")].sort_values("VIF", ascending=False)
    lines += [f"M4 nominal p<0.05 predictors: {', '.join(nominal)}. After BH over all 20 primary non-intercept tests: {', '.join(adjusted)}. Smoking has nominal p={smoking.robust_p_value:.4g} and primary-family q={smoking.q_value_family_BH:.4g}.\n",
        "Obesity is negatively correlated with life expectancy marginally but has a positive conditional slope in M3/M4. Strongly related predictors and specification sensitivity mean this must not be interpreted as a protective effect.\n",
        "## Diagnostics and influence sensitivity\n", markdown_table(pd.DataFrame(diagnostic_rows).drop(columns="analysis_role")),
        "Koenker–Breusch–Pagan and Shapiro p-values are diagnostic summaries, not proof of valid assumptions. HC3 does not address spatial dependence or source measurement error. M4 VIFs:\n", markdown_table(vif_final[["term", "VIF"]])]
    for model in ("M3", "M4"):
        d = sensitivities.loc[sensitivities.model.eq(model)]
        lines += [f"### {model}: Cook >4/N exclusion sensitivity only\n",
            f"Excluded only in sensitivity: {d.excluded_municipalities.iloc[0]}. Sensitivity N={int(d.N_sensitivity.iloc[0])}; primary N=94 is unchanged.\n",
            markdown_table(d.loc[d.term.ne("const"), ["term", "coefficient_full", "coefficient_sensitivity", "robust_p_value_full", "robust_p_value_sensitivity", "sign_changed", "p_0_05_status_changed"]])]
    changed = sensitivities.loc[sensitivities.term.ne("const") & sensitivities.p_0_05_status_changed]
    sign_changes = int(sensitivities.loc[sensitivities.term.ne("const"), "sign_changed"].sum())
    change_text = "; ".join(f"{r.model} {r.term}: p {r.robust_p_value_full:.4g} → {r.robust_p_value_sensitivity:.4g}" for r in changed.itertuples()) or "none"
    lines += [f"Predictor sign changes across influence sensitivities: **{sign_changes}**. Nominal p=0.05 threshold changes: {change_text}. These outcome-informed sensitivities are exploratory and do not replace the full-sample models.\n",
        "## PCA and profiles\n", f"PC1 explains **{100*profiles['pca'].explained_variance_ratio_[0]:.2f}%**, PC2 **{100*profiles['pca'].explained_variance_ratio_[1]:.2f}%**. The first two together explain **{100*profiles['pca'].explained_variance_ratio_[:2].sum():.2f}%**. Loadings below are feature–component correlations, not eigenvector weights.\n",
        markdown_table(pd.DataFrame({"variable": HEALTH_FEATURES, "PC1_loading": profiles["loadings"][:, 0], "PC2_loading": profiles["loadings"][:, 1]})),
        ("All six loadings meet the declared common-axis criterion.\n" if profiles["coherent_PC1"] else "The loadings do not meet the declared common-axis criterion. PC1 is a **contrast**, not a coherent unidimensional health-risk index. No alcohol values were reversed to force agreement.\n"),
        markdown_table(profiles["validation"]),
        f"Selected **k={profiles['chosen_k']}** by highest mean silhouette among k=2–6 with all groups >=5. The inertia curve provides a complementary elbow diagnostic, not a unique natural boundary. Sizes:\n",
        markdown_table(profiles["membership"].groupby("cluster").size().rename("N").reset_index()),
        "Standardized profiles (positive means above the 98-municipality mean):\n",
        markdown_table(profiles["standardized_profiles"].reset_index()),
        f"These are exploratory labels, not natural/causal groups or quality rankings. Across ten optimization-seed checks, adjusted Rand indices range from {profiles['stability'].adjusted_Rand_index_vs_seed42.min():.3f} to {profiles['stability'].adjusted_Rand_index_vs_seed42.max():.3f}; this does not assess sampling stability.\n",
        "## Observed versus fitted life expectancy\n", "Model 3 is the fixed prediction specification. Ranking uses **in-sample** observed-minus-fitted residuals. A rank alone is not a significant or substantial deviation. No predictions are assigned to withheld outcomes.\n"]
    available = predictions.dropna(subset=["observed", "predicted"])
    for title, selected in (("Largest positive residuals", available.nlargest(5, "residual")), ("Largest negative residuals", available.nsmallest(5, "residual"))):
        lines += [f"### {title}\n", markdown_table(selected[["municipality", "observed", "predicted", "residual", "externally_studentized_residual"]])]
    substantial = available.loc[available.externally_studentized_residual.abs().ge(2), ["municipality", "residual", "externally_studentized_residual"]]
    lines += ["The descriptive |externally studentized residual|>=2 screen flags the following; it is not a multiplicity-adjusted outlier test:\n", markdown_table(substantial),
        f"In-sample R²={prediction_quality['in_sample_R_squared']:.3f}, MAE={prediction_quality['in_sample_MAE_years']:.3f} years. Exact leave-one-out R²={prediction_quality['leave_one_out_R_squared']:.3f}, MAE={prediction_quality['leave_one_out_MAE_years']:.3f} years. Neither establishes future/spatial transportability.\n",
        "## Secondary sex-specific regressions\n", "All use the six-predictor M3 specification, N=94, HC3. Q-values use the separate family of 18 non-intercept tests. A sex-specific p-value difference is not itself evidence of a sex difference.\n",
        markdown_table(pd.DataFrame(secondary_fit)[["outcome", "N", "R_squared", "adjusted_R_squared"]]),
        markdown_table(secondary.loc[secondary.term.ne("const"), ["outcome", "term", "coefficient", "ci_low", "ci_high", "robust_p_value", "q_value_family_BH"]])]
    for outcome in OUTCOMES[1:]:
        d = secondary.loc[secondary.outcome.eq(outcome) & secondary.term.ne("const")]
        passing = d.loc[d.q_value_family_BH.lt(.05)]
        nominal_only = d.loc[d.robust_p_value.lt(.05) & d.q_value_family_BH.ge(.05)]
        names = ", ".join(f"{r.term} ({'+' if r.coefficient > 0 else '−'})" for r in passing.itertuples()) or "none"
        nominal_names = ", ".join(nominal_only.term) or "none"
        lines.append(f"{outcome}: q<0.05 predictors: {names}. Additional nominal-only p<0.05 predictors: {nominal_names}.\n")
    lines += ["## Limits and complete outputs\n", "These are ecological associations with differently dated sources, unweighted municipality fits, collinearity, unmodelled spatial dependence and uncertainty in the source aggregates. The four withheld municipalities are excluded only from life-expectancy analyses. See [analysis_methods.md](analysis_methods.md) for the full strategy and [analysis_artifacts.md](analysis_artifacts.md) for every generated file. Full tables preserve nonsignificant results.\n"]
    artifacts.text("\n".join(lines), artifacts.root / "report/analysis_results.md")


def run(input_path: Path = ROOT / "data/processed/municipality_master.csv", output_root: Path = ROOT):
    data = load_data(input_path)
    artifacts = Artifacts(output_root)
    viz.style()
    inventory, descriptions = inventory_and_descriptives(data)
    artifacts.csv(inventory, "analytic_variable_inventory.csv")
    artifacts.csv(descriptions, "descriptive_statistics.csv")
    ledger = data[["municipality_code", "municipality"]].copy()
    for name, predictors in MODELS.items():
        ledger[f"included_{name}"] = data[[OUTCOMES[0], *predictors]].notna().all(axis=1)
    ledger["included_PCA_clustering"] = data[HEALTH_FEATURES].notna().all(axis=1)
    ledger["life_expectancy_status"] = np.where(data[OUTCOMES[0]].isna(), "withheld by HISBK; never imputed", "observed")
    artifacts.csv(ledger, "analysis_sample_membership.csv")
    corr = correlations(data)
    artifacts.csv(corr, "correlations_full.csv")
    total_corr = corr.loc[corr.variable_1.eq(OUTCOMES[0]) | corr.variable_2.eq(OUTCOMES[0])].copy()
    total_corr["other_variable"] = np.where(total_corr.variable_1.eq(OUTCOMES[0]), total_corr.variable_2, total_corr.variable_1)
    total_corr["algebraically_related_outcome"] = total_corr.other_variable.isin(OUTCOMES)
    artifacts.csv(total_corr, "correlations_total_life_expectancy.csv")
    pearson = data[CORRELATION_VARIABLES].corr(method="pearson")
    artifacts.csv(pearson, "correlation_matrix_pearson.csv", index=True)
    artifacts.csv(data[CORRELATION_VARIABLES].corr(method="spearman"), "correlation_matrix_spearman.csv", index=True)
    artifacts.csv(data[CORRELATION_VARIABLES].notna().astype(int).T @ data[CORRELATION_VARIABLES].notna().astype(int), "correlation_pairwise_N.csv", index=True)
    artifacts.files += viz.correlation_heatmap(pearson, artifacts.figures)
    print("Audit, descriptives and all correlation pairs saved.", flush=True)
    fits, samples, coefficients, fit_rows, vifs, summaries = {}, {}, [], [], [], []
    for name, predictors in MODELS.items():
        result, sample, coefficient, fit, vif = fit_model(data, OUTCOMES[0], predictors, name)
        if len(sample) != 94:
            raise ValueError(f"Unexpected primary sample size for {name}: {len(sample)}")
        fits[name], samples[name] = result, sample
        coefficients.append(coefficient); fit_rows.append(fit); vifs.append(vif)
        summaries.append(f"PRIMARY {name}\n{result.summary()}\n")
    coefficients = fdr_coefficients(pd.concat(coefficients, ignore_index=True), "20 non-intercept tests across prespecified Models 1–4")
    fit_table = pd.DataFrame(fit_rows)
    artifacts.csv(coefficients, "regression_coefficients.csv")
    artifacts.csv(fit_table, "regression_model_fit.csv")
    artifacts.csv(pd.concat(vifs, ignore_index=True), "vif.csv")
    artifacts.files += viz.coefficient_plot(coefficients.loc[coefficients.model.eq("M4")], artifacts.figures)
    joint = fits["M3"].wald_test(", ".join(f"{c} = 0" for c in BEHAVIOURS), use_f=True, scalar=True)
    incremental = {"comparison": "M1 to M3 on the same 94 complete cases", "added_predictors": BEHAVIOURS,
        "delta_R_squared": float(fits["M3"].rsquared - fits["M1"].rsquared),
        "delta_adjusted_R_squared": float(fits["M3"].rsquared_adj - fits["M1"].rsquared_adj),
        "HC3_joint_Wald_F": float(joint.statistic), "df_num": float(joint.df_num), "df_denom": float(joint.df_denom),
        "p_value": float(joint.pvalue), "family": "single prespecified block test; unadjusted", "interpretation": "In-sample incremental association, not causality or external predictive validation"}
    artifacts.json(incremental, "incremental_explanatory_value.json")
    diagnostic_rows, influences, sensitivities, sensitivity_fits = [], [], [], []
    for name in ("M3", "M4"):
        result, sample = fits[name], samples[name]
        influence = influence_table(result, sample, name)
        influences.append(influence)
        lm, lm_p, f_stat, f_p = het_breuschpagan(result.resid, result.model.exog, robust=True)
        shapiro = stats.shapiro(result.resid)
        diagnostic_rows.append({"model": name, "N": len(sample), "Koenker_BP_LM": float(lm),
            "Koenker_BP_p": float(lm_p), "BP_F": float(f_stat), "BP_F_p": float(f_p),
            "Shapiro_W": float(shapiro.statistic), "Shapiro_p": float(shapiro.pvalue),
            "Cook_threshold": 4 / len(sample), "high_Cook_N": int(influence.high_cook.sum()),
            "leverage_threshold": 2 * len(result.params) / len(sample), "high_leverage_N": int(influence.high_leverage.sum()),
            "large_studentized_residual_N": int(influence.large_studentized_residual.sum()),
            "max_Cook": float(influence.cooks_distance.max()), "max_leverage": float(influence.leverage.max()),
            "analysis_role": "exploratory model diagnostics; no automatic removal"})
        artifacts.files += viz.diagnostic_plot(result.fittedvalues, result.resid, influence, name, artifacts.figures)
        artifacts.files += viz.cooks_plot(influence, name, artifacts.figures)
        reduced = sample.loc[~influence.high_cook]
        sensitivity, _, reduced_coefficients, reduced_fit, _ = fit_model(reduced, OUTCOMES[0], MODELS[name], f"{name}_exclude_Cook_gt_4_over_N")
        original = coefficients.loc[coefficients.model.eq(name)].drop(columns=["model", "outcome", "FDR_family", "q_value_family_BH"])
        reduced_coefficients = reduced_coefficients.drop(columns=["model", "outcome"])
        comparison = original.merge(reduced_coefficients, on="term", suffixes=("_full", "_sensitivity"), validate="one_to_one")
        comparison["model"] = name
        comparison["coefficient_change"] = comparison.coefficient_sensitivity - comparison.coefficient_full
        comparison["sign_changed"] = np.sign(comparison.coefficient_full).ne(np.sign(comparison.coefficient_sensitivity))
        comparison["p_0_05_status_changed"] = comparison.robust_p_value_full.lt(.05).ne(comparison.robust_p_value_sensitivity.lt(.05))
        comparison["excluded_municipalities"] = ";".join(influence.loc[influence.high_cook, "municipality"])
        sensitivities.append(comparison); sensitivity_fits.append(reduced_fit)
        summaries.append(f"EXPLORATORY INFLUENCE SENSITIVITY {name}\n{sensitivity.summary()}\n")
    artifacts.csv(pd.DataFrame(diagnostic_rows), "model_diagnostics.csv")
    artifacts.csv(pd.concat(influences, ignore_index=True), "influential_observations.csv")
    sensitivity_table = pd.concat(sensitivities, ignore_index=True)
    artifacts.csv(sensitivity_table, "sensitivity_analysis.csv")
    artifacts.csv(pd.DataFrame(sensitivity_fits), "sensitivity_model_fit.csv")
    print("Primary HC3 models, influence diagnostics and sensitivity analyses saved.", flush=True)
    profiles = profile_analysis(data)
    pc_names = [f"PC{i+1}" for i in range(len(HEALTH_FEATURES))]
    pca = profiles["pca"]
    explained = pd.DataFrame({"component": pc_names, "eigenvalue": pca.explained_variance_,
        "explained_variance_ratio": pca.explained_variance_ratio_, "cumulative_variance_ratio": np.cumsum(pca.explained_variance_ratio_)})
    artifacts.csv(explained, "pca_explained_variance.csv")
    artifacts.csv(pd.DataFrame(profiles["loadings"], index=pd.Index(HEALTH_FEATURES, name="variable"), columns=pc_names), "pca_loadings.csv", index=True)
    artifacts.csv(pd.DataFrame(pca.components_.T, index=pd.Index(HEALTH_FEATURES, name="variable"), columns=pc_names), "pca_component_weights.csv", index=True)
    artifacts.csv(pd.DataFrame({"variable": HEALTH_FEATURES, "mean": profiles["scaler"].mean_,
        "SD_ddof0": profiles["scaler"].scale_, "direction_multiplier": [FEATURE_DIRECTIONS[c] for c in HEALTH_FEATURES]}), "health_feature_scaling.csv")
    artifacts.csv(profiles["membership"][["municipality_code", "municipality", *pc_names]], "municipality_pca_scores.csv")
    artifacts.csv(profiles["validation"], "cluster_validation.csv")
    artifacts.csv(profiles["membership"], "cluster_membership.csv")
    artifacts.csv(profiles["standardized_profiles"], "cluster_profiles_standardized.csv", index=True)
    artifacts.csv(profiles["raw_profiles"], "cluster_profiles_raw_percent.csv", index=True)
    artifacts.csv(profiles["membership"].groupby("cluster").size().rename("N").to_frame(), "cluster_sizes.csv", index=True)
    artifacts.csv(profiles["stability"], "cluster_seed_stability.csv")
    solution = {"N": len(profiles["sample"]), "chosen_k": profiles["chosen_k"], "seed": SEED, "n_init": 50,
        "rule": "Highest mean silhouette among k=2..6 with every cluster >=5; prefer lower k for exact ties. Inertia/elbow reported alongside, no claimed unique natural partition.",
        "PC1_coherent_all_loadings_at_least_0_2": profiles["coherent_PC1"],
        "PC1_label": "Common adverse-health axis" if profiles["coherent_PC1"] else "PC1 contrast; not a unidimensional health-risk index",
        "orientation": "All six inputs higher=more adverse exposure/poorer health; no data-driven reversals. PC1 sign set by positive sum of weights, not to force coherence.",
        "interpretation": "Exploratory profiles, not natural/causal groups. Numbering by centroid PC1 is a display convention, not a best/worst ranking."}
    artifacts.json(solution, "cluster_solution.json")
    artifacts.files += viz.scree_plot(pca.explained_variance_ratio_, artifacts.figures)
    artifacts.files += viz.cluster_validation(profiles["validation"], profiles["chosen_k"], artifacts.figures)
    artifacts.files += viz.cluster_profiles(profiles["standardized_profiles"], profiles["membership"], pca.explained_variance_ratio_, artifacts.figures)
    predictions = residual_table(data, fits["M3"], samples["M3"])
    artifacts.csv(predictions, "municipality_predictions_residuals.csv")
    observed = predictions.dropna(subset=["observed", "predicted"])
    prediction_quality = {"model": "M3: income, primary education, smoking, obesity, inactivity, alcohol", "N": len(observed),
        "in_sample_R_squared": float(r2_score(observed.observed, observed.predicted)),
        "in_sample_MAE_years": float(mean_absolute_error(observed.observed, observed.predicted)),
        "leave_one_out_R_squared": float(r2_score(observed.observed, observed.loo_predicted)),
        "leave_one_out_MAE_years": float(mean_absolute_error(observed.observed, observed.loo_predicted)),
        "method": "Exact OLS leave-one-out PRESS residual e/(1-h); no training prediction for withheld outcomes",
        "residual_screen": "|externally studentized residual| >=2, descriptive only; not a simultaneous significance test"}
    artifacts.json(prediction_quality, "prediction_quality.json")
    artifacts.files += viz.prediction_plots(predictions, artifacts.figures)
    secondary_coefficients, secondary_fit, secondary_vif = [], [], []
    for outcome in OUTCOMES[1:]:
        result, _, coefficient, fit, vif = fit_model(data, outcome, MODELS["M3"], f"secondary_{outcome}")
        secondary_coefficients.append(coefficient); secondary_fit.append(fit); secondary_vif.append(vif)
        summaries.append(f"SECONDARY/EXPLORATORY {outcome}\n{result.summary()}\n")
    secondary = fdr_coefficients(pd.concat(secondary_coefficients, ignore_index=True), "18 non-intercept tests across male, female and sex-gap Model 3 analyses")
    artifacts.csv(secondary, "secondary_regression_coefficients.csv")
    artifacts.csv(pd.DataFrame(secondary_fit), "secondary_regression_model_fit.csv")
    artifacts.csv(pd.concat(secondary_vif, ignore_index=True), "secondary_vif.csv")
    artifacts.text("\n\n".join(summaries), artifacts.tables / "regression_summaries.txt")
    versions = {name: package_metadata.version(name) for name in ["pandas", "numpy", "scipy", "statsmodels", "scikit-learn", "matplotlib", "threadpoolctl"]}
    artifacts.text("\n".join(f"{d.metadata['Name']}=={d.version}" for d in sorted(package_metadata.distributions(), key=lambda x: x.metadata['Name'].casefold())) + "\n", artifacts.tables / "analysis_environment.txt")
    summary = {"input_sha256": sha256(input_path), "primary_N": {m: len(s) for m, s in samples.items()},
        "profile_N": len(profiles["sample"]), "primary_fit": fit_table.drop(columns="sample_codes").to_dict("records"),
        "incremental_value": incremental, "cluster_solution": solution, "prediction_quality": prediction_quality,
        "secondary_fit": [{k: v for k, v in row.items() if k != "sample_codes"} for row in secondary_fit],
        "PC1_variance_ratio": float(pca.explained_variance_ratio_[0]),
        "PC2_variance_ratio": float(pca.explained_variance_ratio_[1])}
    artifacts.json(summary, "analysis_summary.json")
    configuration = {"primary_outcome": OUTCOMES[0], "primary_models": MODELS, "secondary_outcomes": OUTCOMES[1:],
        "correlation_variables": CORRELATION_VARIABLES, "health_profile_features": FEATURE_DIRECTIONS,
        "missing_data": "complete cases only; no imputation", "robust_covariance": "HC3", "use_t": True,
        "correlation_FDR": "Separate BH families: all 136 unique pairs per method, plus 16 total-life-expectancy pairs per method",
        "primary_FDR": "20 non-intercept coefficients across Models 1–4", "secondary_FDR": "18 non-intercept coefficients across 3 secondary models",
        "sensitivity_exclusion": "Cook distance >4/N, separately for M3 and M4; exploratory only",
        "cluster_selection": solution["rule"], "seed": SEED}
    artifacts.json(configuration, "analysis_configuration.json")
    results_report(artifacts, coefficients, fit_table, total_corr, incremental, diagnostic_rows,
                   sensitivity_table, profiles, predictions, secondary, secondary_fit, prediction_quality, pd.concat(vifs, ignore_index=True))
    catalog = ["# Analysis file inventory\n", "Generated by `python -m src.analysis`. Numeric results are reproduced from the official master; figures are saved as PNG (300 dpi) and vector PDF.\n",
        "## Implementation and documentation\n", "Modified: `src/analysis.py`, `src/visualization.py`, `README.md`. Created: `tests/test_analysis.py`, `report/analysis_methods.md`, `report/analysis_results.md`, `report/analysis_artifacts.md`.\n",
        "## Generated analysis artifacts\n"]
    for path in sorted(artifacts.files):
        relative = str(path.relative_to(output_root))
        catalog.append(f"- [{relative}](../{relative})")
    catalog.append("- [outputs/tables/analysis_manifest.json](../outputs/tables/analysis_manifest.json)")
    artifacts.text("\n".join(catalog) + "\n", output_root / "report/analysis_artifacts.md")
    manifest = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "status": "complete",
        "input_file": str(input_path), "input_sha256": sha256(input_path),
        "input_provenance_sha256": sha256(input_path.with_name(input_path.stem + "_provenance.json")),
        "python": platform.python_version(), "package_versions": versions,
        "source_hashes": {str(p.relative_to(ROOT)): sha256(p) for p in [ROOT / "src/analysis.py", ROOT / "src/visualization.py", ROOT / "tests/test_analysis.py", ROOT / "report/analysis_methods.md", ROOT / "README.md"]},
        "artifacts": [{"file": str(p.relative_to(output_root)), "sha256": sha256(p)} for p in artifacts.files]}
    artifacts.json(manifest, "analysis_manifest.json")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/processed/municipality_master.csv")
    args = parser.parse_args()
    run(args.input)
