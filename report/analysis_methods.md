# Statistical analysis methods

## Research questions and status

The primary question is which municipality health-behaviour and socioeconomic characteristics are associated with differences in period life expectancy at birth. The four primary regression specifications below follow the user's requested strategy and were fixed in code before fitting. This is an observational portfolio analysis, not an externally preregistered confirmatory study. Correlations, model diagnostics, influence exclusions, PCA, clustering, residual profiles, and sex-specific models are explicitly secondary or exploratory. All coefficients, correlations, candidate cluster metrics, and sensitivity results are exported, regardless of p-value.

Run from the repository root with `python -m src.analysis`. The input is `data/processed/municipality_master.csv`; its SHA-256 must match `municipality_master_provenance.json`. `outputs/tables/analysis_manifest.json` records the input and source-code hashes, Python/package versions, and exact names/checksums of every generated analysis table and figure. `analysis_environment.txt` records installed package versions. Acquisition raw files and processed masters are not modified. The dashboard remains unchanged.

## Data, populations and time

There are 98 Danish municipalities. Sources are official Statistics Denmark INDKP106, HFUDD11, FOLK1A and HISBK, and National Health Profile public municipality exports. Socioeconomic measures refer to 2024, health prevalences to 2025, and life expectancy to the five-year period **2021:2025**. Life expectancy is not an annual 2025 value or a birth-cohort forecast. These overlapping but nonidentical reference periods preclude a simple prospective or causal interpretation.

Ærø (492), Fanø (563), Samsø (741), and Læsø (825) have life expectancy withheld in HISBK because estimates are considered too uncertain. **No outcome or predictor is imputed.** Complete-case life-expectancy analyses use **N=94**. All primary and sex-specific models happen to share those same 94 municipalities because every model predictor is observed. Correlations use pairwise complete cases (**94–98**); PCA and clustering use the six health features only, all observed for **N=98**, including the four municipalities with withheld life expectancy. No life-expectancy values or predictions are filled in for the four withheld municipalities.

`analytic_variable_inventory.csv` lists every input field plus the regression income transformation, with source, period, unit, observed/missing N, role and analytic inclusion. `analysis_sample_membership.csv` lists inclusion by municipality. Descriptive statistics report observed N, missing N, mean, sample SD (ddof=1), median, Q1, Q3, IQR, min and max for every numeric measurement. Metadata years/dates, status codes, and identifiers are not treated as continuous measurements. Denominator/component counts and good self-rated health remain in descriptive outputs but are excluded from correlations/models/PCA when redundant.

## Variables

Disposable income is mean personal disposable income; regression slopes use **DKK 10,000 increments** (`income_per_10000_dkk = disposable_income_mean_dkk / 10000`). Low education is the percentage of people aged 25–64 whose highest completed education is primary education; unknown attainment is retained in the source denominator and separately described. Health variables are percentages: daily smoking, BMI >=30, insufficient activity under the portal's stated WHO weekly definition, >10 Danish standard drinks in a typical week, less-good/poor self-rated health, and poor SF-12 mental health. They are not participant-level data or directly comparable denominators.

The self-rated outcome explicitly combines **mindre godt OR dårligt**, derived from the verified complement of excellent/very good/good; it is not `dårligt` alone. Poor mental health uses the portal's low SF-12 mental component threshold (<=35.76), not a complement of high well-being. The portal's physical-activity definition and its questionnaire-break warning are preserved in the acquisition record; it must not be silently replaced by a different current guideline.

Population size, all three age-share variables and unknown-education share enter exploratory correlations and descriptives. They are not added to the requested primary models. The three age shares are compositional (sum to 100%); the income rescaling and good/poor-health complement are not entered as duplicate features. Income and education are not population-weighted municipality predictors. All models give municipalities equal weight and do not estimate a person-weighted association.

## Exploratory correlations and multiplicity

The 17 relevant continuous variables are the four life-expectancy measures, income, primary education, unknown education, population, three age shares and six health measures. All **136 unique pairs** are evaluated using both Pearson r and Spearman rho, with two-sided p-values. The full table includes sample size for each pair, and the matrix/heatmap does not suppress weak associations. Correlations among total, male/female life expectancy and the derived sex gap are algebraically related outcomes and are marked separately when discussing characteristics associated with total life expectancy.

Benjamini–Hochberg (BH) q-values are computed over **all 136 tests separately for Pearson and Spearman**. A second, explicitly labelled family of the **16 correlations involving total life expectancy per method** is also exported. The global all-pairs q-value is the default for reporting. Dependence among variables and multiple complementary families limit a literal confirmatory interpretation of these exploratory q-values. No table is filtered for significance.

## Primary OLS models

Outcome: `life_expectancy_total`, in years. Each model has an intercept and uses complete cases:

| Model | Fixed predictors | N |
| --- | --- | --- |
| M1 — socioeconomic | Income per DKK 10,000; primary-education percentage | 94 |
| M2 — health behaviours | Daily smoking; obesity; insufficient physical activity; >10 drinks/week | 94 |
| M3 — combined | M1 plus the four M2 predictors | 94 |
| M4 — expanded health | M3 plus less-good/poor self-rated health and poor SF-12 mental health | 94 |

M1 and M2 are alternative, nonnested specifications. M1→M3 and M3→M4 are progressive specifications; all use the same sample. No variables are removed on the basis of p-values, VIFs or fitted signs. The fully adjusted model means M4. Both M3 and M4 receive diagnostics to avoid ambiguity about “final combined model.”

OLS uses **HC3 heteroskedasticity-robust covariance**, with two-sided **Student t reference distributions using residual degrees of freedom** and 95% intervals. This finite-df reference is an inference convention, not exact small-sample protection under arbitrary errors. Coefficients are in years per DKK 10,000 or per **percentage point**, not per relative percent change. Standardized beta is `b × SD(X)/SD(Y)` using sample SDs from the exact model sample; standardized CIs scale the robust slope interval by the same positive factor. The intercept has no standardized beta. Independent refits of standardized X and Y are used in tests to verify the calculations.

Every coefficient, HC3 SE, p-value, CI and beta is exported. An extra BH column treats all **20 non-intercept coefficient tests across M1–M4** as one declared family; intercepts are excluded. Nominal p<0.05 and family-adjusted q<0.05 are distinguished, especially for borderline results. Exact p/q values are saved at numerical precision, rather than reporting only threshold crossings.

Model-fit tables report N, R², adjusted R², AIC, BIC, residual SD, residual df and standardized-design condition number. R²/AIC/BIC are ordinary OLS/Gaussian-likelihood fit summaries, not “robust” or externally validated measures. VIF is calculated for each predictor with an intercept; no VIF threshold triggers automatic selection. A separate prespecified HC3 joint Wald F test assesses whether the four behaviours jointly add association beyond M1 in M3, alongside ΔR² and Δadjusted R². It is one block test, reported without an additional multiplicity correction; it does not prove causal explanatory value.

## Diagnostics and influence sensitivities

For M3 and M4, save residual histograms, normal Q–Q plots, residual-vs-fitted plots, Cook's distance charts, leverage, and internally/externally studentized residuals. A Koenker studentized Breusch–Pagan test evaluates heteroskedasticity; Shapiro–Wilk evaluates residual normality as a descriptive diagnostic. Their unadjusted p-values are not validity certificates and are not used for variable selection. HC3 remains in use regardless of the diagnostic p-values.

Screen Cook's distance at **D>4/N**, leverage at **h>2p/N** where p includes the intercept, and absolute externally studentized residual at **>2**. These are heuristic screens, not familywise outlier tests. Primary fits retain every complete-case municipality. As an explicitly exploratory sensitivity, refit M3 and M4 separately after excluding only their own Cook-flagged municipalities; report every original/sensitivity coefficient, CI, p-value, direction change and nominal-threshold change, together with the excluded names and N. SDs for sensitivity betas are recalculated within those samples, so raw slopes are the preferred direct comparison. These exclusions are outcome-informed and do not establish a preferred “cleaned” result.

## PCA and exploratory municipality profiles

Use the six health features only, without life expectancy or socioeconomic variables. Every feature is oriented so a higher raw value represents more adverse exposure or poorer reported health. **Alcohol is not reversed because of its observed correlation.** StandardScaler centers and scales each feature using population SD (ddof=0) over the 98 complete feature rows; scaling parameters and +1 direction multipliers are saved. No demographic weighting is applied.

PCA uses full singular-value decomposition. Save eigenvalues, explained/cumulative variance, component weights (eigenvectors), loadings defined as correlations between standardized features and component scores, and all municipality PC scores. Component signs are arbitrary; orient PC1 to a positive sum of weights and later components by the largest absolute weight. This sign convention does not change explained variance or force all indicators to align. Treat PC1 as a possible common adverse-health axis only if all six feature correlations with PC1 are >=0.2 under this orientation. Otherwise call it a **PC1 contrast**, not a health-risk index. Higher alcohol exposure is not protective merely because it points in an opposite multivariate direction.

Explore k-means for **k=2–6**, plus k=1 for the inertia baseline. Use all six standardized features, `random_state=42`, `n_init=50`, Lloyd's algorithm and one numerical thread. Save every k's inertia, silhouette, and minimum cluster size. The declared selection rule is the highest mean silhouette among k=2–6 with every group >=5 municipalities, preferring lower k for exact ties; show the elbow alongside this rule without claiming a unique elbow. If no candidate qualifies, stop rather than force a solution. Labels “Profile 1”, “Profile 2”, etc. are ordered by centroid PC1 solely for stable display, not as quality rankings. Save standardized/raw cluster profiles, sizes, memberships, municipality silhouettes, and a PC1/PC2 projection. Clustering uses all six dimensions, not just the plot's two PCs. Refit the selected k at seeds 0–9 with 50 initializations and report adjusted Rand indices as optimization-stability checks, not bootstrap population stability.

## Expected vs observed life expectancy

Use the fixed **M3 combined model** for the requested risk-profile residual analysis; M4 is reserved as expanded association adjustment. Predict fitted life expectancy only for the **94 complete cases** and calculate `residual = observed - predicted`. Export all 98 rows, leaving observed/predicted/residual fields null for withheld outcomes with explicit statuses. Rank available municipalities by the in-sample residual; positive means higher life expectancy than fitted by the included indicators, negative means lower. Use externally studentized residual magnitude >=2 as a descriptive “substantial” screen, not a simultaneous significance statement. The top/bottom-five figure is a ranking, not evidence that each selected municipality passes that screen.

Save exact OLS leave-one-out predictions using PRESS residuals `e/(1-h)` and LOO R²/MAE to distinguish fitted from held-out performance. Tests independently refit selected leave-one-out cases. This internal validation does not validate transport to future years, and spatial dependence may make it optimistic. Extreme in-sample residuals can reflect omitted factors, measurement error, source uncertainty or chance; do not call municipalities best/worst or attribute residuals to local policy.

## Secondary sex-specific analyses

Repeat the six-predictor M3 specification for male life expectancy, female life expectancy and female-minus-male life-expectancy gap, with **N=94 each**, HC3, t-based intervals, betas, fit summaries and VIFs. Treat the **18 non-intercept tests across these three models** as a separate exploratory BH family. A coefficient significant in one sex and nonsignificant in the other is not itself a tested sex difference; the gap model directly examines difference associations. No multiplicity-adjusted sex-gap result should be inferred from nominal p-values alone.

## Limitations and interpretation

- Ecological, cross-sectional associations do not describe individual risks or establish causation. Concurrent and differently dated measures permit reverse causation and omitted-variable confounding.
- Municipality averages hide within-municipality inequality. Equal municipality weighting targets between-place associations, not a national individual-level relation.
- Self-reported survey measures have outcome-specific valid-response populations, rounding, sampling/nonresponse uncertainty and potentially correlated errors. No municipality prevalence SEs or life-expectancy SEs are incorporated into these fits; HC3 does not correct measurement error or mortality-estimate uncertainty.
- Age composition and population size are audited but are not additional covariates in the user's fixed primary specifications. Three age shares must not all be added with an intercept because of their exact sum constraint. Residual demographic confounding remains possible.
- Life-expectancy missingness is concentrated in four small islands, so complete-case findings do not cover those municipalities. They are retained in profiles based only on fully observed health features.
- Collinearity can reverse adjusted coefficients and inflate their uncertainty; a positive conditional obesity/alcohol coefficient is not evidence of a protective exposure. Fully adjusted self-rated/mental health coefficients are conditional on strongly related indicators.
- HC3 addresses heteroskedastic covariance under independent observations, **not spatial dependence**. No geographical weights or spatial autocorrelation adjustment are available in this analysis; conventional p-values may therefore be optimistic. BH does not remove this concern.
- PCA/clustering/residual rankings are exploratory and sensitive to features, scaling, group selection, sampling noise and omitted context. Seed stability is not validation of natural or causal groups. In-sample R² is not a causal fraction explained.

Method references: [statsmodels robust covariance](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html), [statsmodels BH multiple-testing correction](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html), and [scikit-learn clustering documentation](https://scikit-learn.org/stable/modules/clustering.html). Source-specific definitions and attribution remain in the acquisition provenance and source inventory.
