"""Publication-ready, noninteractive statistical figures for the atlas."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

LABELS = {
    "life_expectancy_total": "Life expectancy: both sexes",
    "life_expectancy_male": "Life expectancy: male",
    "life_expectancy_female": "Life expectancy: female",
    "life_expectancy_sex_gap": "Life expectancy: female−male",
    "disposable_income_mean_dkk": "Disposable income",
    "income_per_10000_dkk": "Income (per DKK 10,000)",
    "low_education_share_25_64_pct": "Primary education, ages 25–64",
    "education_unknown_share_25_64_pct": "Unknown education, ages 25–64",
    "population": "Population size",
    "age_0_17_share_pct": "Age 0–17 share",
    "age_18_64_share_pct": "Age 18–64 share",
    "age_65_plus_share_pct": "Age 65+ share",
    "daily_smoking_pct": "Daily smoking",
    "obesity_pct": "Obesity (BMI ≥30)",
    "physical_inactivity_pct": "Insufficient physical activity",
    "risky_alcohol_pct": "Alcohol >10 drinks/week",
    "less_good_or_poor_self_rated_health_pct": "Less good/poor self-rated health",
    "poor_mental_health_pct": "Poor SF-12 mental health",
}


def save_figure(fig, directory: Path, name: str) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for suffix in ("png", "pdf"):
        path = directory / f"{name}.{suffix}"
        options = {"metadata": {"CreationDate": None, "ModDate": None}} if suffix == "pdf" else {}
        fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white", **options)
        paths.append(path)
    plt.close(fig)
    return paths


def style() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold",
        "axes.labelcolor": "#263648", "axes.titlecolor": "#16324f", "pdf.fonttype": 42})


def correlation_heatmap(matrix, directory):
    fig, ax = plt.subplots(figsize=(14, 12))
    image = ax.imshow(matrix, vmin=-1, vmax=1, cmap="RdBu_r")
    labels = [LABELS.get(c, c) for c in matrix.columns]
    ax.set_xticks(range(len(labels)), labels, rotation=60, ha="right", fontsize=8)
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    for i in range(len(labels)):
        for j in range(len(labels)):
            value = matrix.iloc[i, j]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=6,
                    color="white" if abs(value) > .65 else "#263648")
    fig.colorbar(image, ax=ax, shrink=.72, label="Pearson r")
    ax.set_title("Exploratory municipality correlations\nPairwise complete cases: N=94–98; all pairs reported", pad=18)
    return save_figure(fig, directory, "correlation_heatmap")


def coefficient_plot(coefficients, directory):
    d = coefficients.loc[coefficients.term.ne("const")].iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 5))
    y = np.arange(len(d))
    ax.errorbar(d.standardized_beta, y,
        xerr=[d.standardized_beta - d.standardized_ci_low, d.standardized_ci_high - d.standardized_beta],
        fmt="o", color="#176b87", ecolor="#607d8b", capsize=3)
    ax.axvline(0, color="#a64040", ls="--", lw=1)
    ax.set_yticks(y, [LABELS.get(c, c) for c in d.term])
    ax.set_xlabel("Standardized beta (95% HC3 t-based CI)")
    ax.set_title("Model 4: expanded health model (N=94)")
    ax.grid(axis="x", alpha=.18)
    return save_figure(fig, directory, "model4_coefficients")


def diagnostic_plot(fitted, residual, influence, model_name, directory):
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    axes[0, 0].hist(residual, bins="auto", color="#4c8496", edgecolor="white")
    axes[0, 0].set(xlabel="Residual (years)", ylabel="Municipalities", title="Residual distribution")
    stats.probplot(residual, dist="norm", plot=axes[0, 1])
    axes[0, 1].set_title("Normal Q–Q plot")
    axes[1, 0].scatter(fitted, residual, color="#176b87", s=22, alpha=.8)
    axes[1, 0].axhline(0, ls="--", color="#a64040")
    axes[1, 0].set(xlabel="Fitted life expectancy (years)", ylabel="Residual (years)", title="Residual vs fitted")
    scatter = axes[1, 1].scatter(influence.leverage, influence.studentized_external,
        s=25 + 550 * influence.cooks_distance, c=influence.cooks_distance, cmap="viridis", alpha=.8)
    axes[1, 1].axhline(0, color="grey", lw=.7)
    for _, row in influence.loc[influence.high_cook].iterrows():
        axes[1, 1].annotate(row.municipality, (row.leverage, row.studentized_external), fontsize=6)
    axes[1, 1].set(xlabel="Leverage", ylabel="Externally studentized residual", title="Influence: size/colour show Cook’s D")
    fig.colorbar(scatter, ax=axes[1, 1], label="Cook’s D")
    fig.suptitle(f"{model_name}: diagnostic checks; flagged observations retained in primary model", y=1.01)
    fig.tight_layout()
    return save_figure(fig, directory, f"diagnostics_{model_name.lower()}")


def cooks_plot(influence, model_name, directory):
    d = influence.sort_values("cooks_distance", ascending=False)
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.bar(np.arange(len(d)), d.cooks_distance, color=np.where(d.high_cook, "#a64040", "#4c8496"))
    ax.axhline(4 / len(d), ls="--", color="#263648", label="Screen: 4/N")
    flagged = np.where(d.high_cook)[0]
    ax.set_xticks(flagged, d.loc[d.high_cook, "municipality"], rotation=60, ha="right", fontsize=8)
    ax.set(ylabel="Cook’s distance", xlabel="Municipalities ordered by Cook’s distance", title=f"{model_name}: influence screen (not an exclusion rule for the primary analysis)")
    ax.legend(frameon=False)
    return save_figure(fig, directory, f"cooks_distance_{model_name.lower()}")


def scree_plot(explained, directory):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(np.arange(1, len(explained) + 1), 100 * explained, color="#4c8496", label="Component")
    ax.plot(np.arange(1, len(explained) + 1), 100 * np.cumsum(explained), "o-", color="#a64040", label="Cumulative")
    ax.set(xlabel="Principal component", ylabel="Explained variance (%)", title="Exploratory PCA of six health indicators (N=98)")
    ax.legend(frameon=False)
    return save_figure(fig, directory, "pca_scree")


def cluster_validation(metrics, chosen, directory):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(metrics.k, metrics.inertia, "o-", color="#176b87")
    valid = metrics.loc[metrics.k.gt(1)]
    axes[1].plot(valid.k, valid.silhouette, "o-", color="#176b87")
    for ax, ylabel in zip(axes, ["Inertia", "Mean silhouette"]):
        ax.axvline(chosen, ls="--", color="#a64040", label=f"Selected k={chosen}")
        ax.set(xlabel="Number of profiles (k)", ylabel=ylabel)
        ax.legend(frameon=False)
    fig.suptitle("Exploratory k-means: elbow and silhouette diagnostics (N=98)")
    fig.tight_layout()
    return save_figure(fig, directory, "cluster_validation")


def cluster_profiles(profiles, membership, explained, directory):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for cluster, row in profiles.iterrows():
        axes[0].plot(np.arange(len(row)), row.values, "o-", label=f"Profile {cluster}")
    axes[0].set_xticks(range(len(profiles.columns)), [LABELS.get(c, c) for c in profiles.columns], rotation=55, ha="right", fontsize=8)
    axes[0].axhline(0, lw=.8, color="grey")
    axes[0].set(ylabel="Mean standardized indicator", title="Profiles in original indicator directions")
    for cluster, d in membership.groupby("cluster"):
        axes[1].scatter(d.PC1, d.PC2, s=30, alpha=.8, label=f"Profile {cluster} (N={len(d)})")
    axes[1].set(xlabel=f"PC1 ({100*explained[0]:.1f}%)", ylabel=f"PC2 ({100*explained[1]:.1f}%)", title="PCA projection; clustering uses all six indicators")
    axes[1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    return save_figure(fig, directory, "cluster_profiles_pca")


def prediction_plots(predictions, directory):
    d = predictions.dropna(subset=["observed", "predicted"]).copy()
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(d.predicted, d.observed, color="#176b87", alpha=.8)
    bounds = [min(d.predicted.min(), d.observed.min()) - .2, max(d.predicted.max(), d.observed.max()) + .2]
    ax.plot(bounds, bounds, ls="--", color="#a64040")
    ax.set(xlabel="Model 3 fitted life expectancy (years)", ylabel="Observed life expectancy (years)", title="Observed vs fitted: in-sample, N=94")
    paths = save_figure(fig, directory, "observed_vs_predicted")
    extremes = d.sort_values("residual").iloc[list(range(5)) + list(range(len(d)-5, len(d)))].sort_values("residual")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(extremes.municipality, extremes.residual, color=np.where(extremes.residual.gt(0), "#176b87", "#a64040"))
    ax.axvline(0, color="grey", lw=.8)
    ax.set(xlabel="Observed − Model 3 fitted life expectancy (years)", title="Five largest positive and negative residuals\nConditional on included indicators; in-sample, exploratory")
    paths += save_figure(fig, directory, "prediction_residual_ranking")
    return paths
