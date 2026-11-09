# Danish Health Inequality Atlas

## Project question

**What explains geographical differences in health and life expectancy across Danish municipalities?**

This Python public-health portfolio project will investigate geographical health inequalities across Danish municipalities using official Danish public data. The eventual analysis will integrate health outcomes with socioeconomic indicators at municipality level.

## Current status

The project has acquired and validated official 2024 socioeconomic data, 2025 National Health Profile data, and HISBK life expectancy for 2021:2025. The final combined master retains all 98 municipalities; life expectancy is available for 94, with four municipalities withheld by Statistics Denmark. The statistical analysis is implemented and validated: four fixed primary HC3 OLS specifications, complete descriptive/correlation outputs, diagnostics and influence sensitivities, exploratory PCA/clustering/residual profiles, and secondary sex-specific models. Results are associations, not causal findings. The Streamlit app remains a placeholder and does not load the acquired files.

## Analytic scope

- Descriptive statistics for health outcomes and socioeconomic indicators.
- Correlations to explore relationships between indicators.
- Regression models with robust standard errors where appropriate.
- Multiple-testing correction for families of statistical tests.
- PCA and/or clustering to explore municipality profiles.
- Municipality comparisons with attention to population size and uncertainty.
- Interactive visualizations and a municipality explorer.
- Explicit discussion of methodological limitations.

Source metadata, exact API requests, retrieval timestamps, and response checksums are retained with each Statistics Denmark extract. Raw source files are preserved separately from processed data.

## Statistical analysis

Run the complete analysis offline after creating the final municipality master:

```bash
source .venv/bin/activate
python -m src.analysis
python -m unittest discover -s tests -v
```

The input master must match its acquisition-provenance checksum. Analysis never changes raw files or masters. All four primary regressions use **N=94 complete cases**, excluding Ærø, Fanø, Samsø and Læsø because their life expectancy is withheld; their outcomes are not imputed. PCA and clustering use **N=98** because all six health indicators are observed. Each male, female and female-minus-male secondary model uses **N=94**. Correlations use pairwise complete cases (**N=94–98**) and report the N for every pair.

The primary outcome is **total period life expectancy at birth**. The fixed OLS specifications are M1 (income and primary education), M2 (smoking, obesity, insufficient activity, >10 drinks/week), M3 (M1+M2), and M4 (M3+less-good/poor self-rated health and poor SF-12 mental health). All include an intercept, use HC3 covariance with t-based 95% intervals, and retain all specified predictors regardless of p-values. Regression income is expressed per DKK 10,000; health and education slopes are per percentage point. Standardized betas use the model sample's SD(X)/SD(Y). Model fit, VIFs and every coefficient/CI/p-value are saved.

Primary coefficient q-values apply BH across the 20 non-intercept tests across M1–M4. Exploratory correlations report all 136 pairs for each of Pearson/Spearman with separate BH families per method, plus a separately labelled 16-pair total-life-expectancy family. A single prespecified HC3 joint behaviour-block test evaluates M1→M3. Secondary outcomes are male life expectancy, female life expectancy, and the female-minus-male gap, each using the M3 predictors, with BH across their 18 non-intercept tests. These analyses are explicitly secondary/exploratory, not evidence that a significant coefficient in one sex differs from a nonsignificant coefficient in the other.

M3/M4 diagnostics include residual distribution, Q–Q and residual-vs-fitted figures, heteroskedasticity tests, leverage and Cook's distance. Primary fits retain all complete cases; Cook's D>4/N exclusions are saved as exploratory sensitivities only. Fixed Model 3 produces observed/fitted/residual rankings and exact leave-one-out predictions for the 94 observed outcomes. Withheld outcomes receive neither predicted life expectancy nor residuals. A large residual means higher/lower life expectancy than fitted by included indicators, not a best/worst municipality designation.

Exploratory PCA and k-means use six standardized health indicators, with higher values consistently meaning more adverse exposure or poorer reported health. Alcohol is not reversed to force a common factor. PCA loadings determine whether PC1 supports a coherent interpretation; the current mixed loading pattern is recorded as a **contrast**, not a single health-risk index. K-means evaluates k=2–6 using inertia and silhouette, with a declared minimum group size of 5 and selection by highest silhouette. Random seed 42 and 50 initializations are recorded; group labels are exploratory profile identifiers.

All statistical tables are under `outputs/tables/`; every figure is exported as a 300-dpi PNG and vector PDF under `outputs/figures/`. The analysis manifest records exact output names/checksums, input/source-code hashes, configuration and environment versions. Every correlation and model coefficient is retained, including nonsignificant results.

- [Analysis methods](report/analysis_methods.md): definitions, fixed specifications, multiplicity families, diagnostics and limitations.
- [Generated results report](report/analysis_results.md): correlations, all four regressions, sensitivities, PCA/profiles, residual extremes and secondary results.
- [Exact analysis file inventory](report/analysis_artifacts.md): every generated table/figure and the implementation files.
- `outputs/tables/analysis_manifest.json`: machine-readable output hashes and environment/source provenance.

Interpretation is limited by ecological aggregation, differently dated sources, outcome-specific survey denominators/rounding/uncertainty, equal municipality weighting, withheld island outcomes, confounding and strong predictor collinearity. Age composition/population are audited but are not extra covariates in the fixed primary models. HC3 does not correct spatial dependence, measurement error or uncertainty in the source aggregates. Positive conditional obesity/alcohol coefficients must not be described as protective effects, and PCA/clusters/residual ranks do not establish natural or causal groups.

## Data sources

### Already acquired: Statistics Denmark / StatBank

All variables use **2024**, the latest common year available in the selected tables when inspected. Income in INDKP106 ends in 2024; choosing 2025 would require mixing years. A common year does not mean identical measurement dates or populations.

| Variable | Official table | Exact selection and definition | Reference period |
| --- | --- | --- | --- |
| Mean disposable income, DKK | [INDKP106](https://www.statbank.dk/INDKP106) | Unit `118` (average income in DKK), both sexes `MOK`, total age `00`, all income intervals `000`; persons over 14 according to the Danish table title. Personal income, not equivalised household income or median income. | Calendar year 2024 |
| Low education share, ages 25–64, % | [HFUDD11](https://www.statbank.dk/HFUDD11) | Sum primary education `H10` across eight five-year age bands 25–29 through 60–64, divided by sum `TOT` for the same ages, multiplied by 100. Both sexes and all ancestry groups. Unknown education `H90` remains in the denominator and is reported separately. | 30 September 2024, as specified by the table footnote |
| Population, persons | [FOLK1A](https://www.statbank.dk/FOLK1A) | Both sexes, all marital statuses, total age `IALT`, period `2024K1`. | 1 January 2024 |
| Age structure, persons and % | [FOLK1A](https://www.statbank.dk/FOLK1A) | Sum single-year ages into 0–17, 18–64, and 65+ (65–125); divide each by total population for percentages. | 1 January 2024 |

The master uses Statistics Denmark's three-digit municipality codes and Danish municipality names from FOLK1A metadata. It includes the **98 municipalities**, excluding Denmark/region/province aggregates and Christiansø (`411`), which is outside the municipal structure. See the official [geographical classification](https://www.dst.dk/da/Statistik/dokumentation/nomenklaturer/nuts). Names from every source are checked against the FOLK1A registry; joins use codes, with no fuzzy matching.

Statistics Denmark documents its [public API and attribution requirements](https://www.dst.dk/en/Statistik/hjaelp-til-statistikbanken/api); the data are provided under terms corresponding to CC BY 4.0. Cite Statistics Denmark and the relevant table. Raw metadata includes table documentation links, update dates, category labels, and footnotes.

Low education is an operational measure of primary education as highest completed attainment among ages 25–64. Unknown attainment is not classified as low education. This population differs from the income and total-population universes, and the education date differs from the population date. These measures require further methodological review before modelling.

### Already acquired: National Health Profile, wave 2025

The [Sundhedsstyrelsen overview](https://www.sst.dk/sundhedsprofilen) links to [Danskernes Sundhed](https://www.danskernessundhed.dk/) for municipality-level results. **Automated acquisition succeeded for 2025 for all six target reports**, with 98 municipality rows and no missing/suppressed prevalence values in each export. The fallback to 2021 was not needed.

The official [guide](https://www.danskernessundhed.dk/Vejledning.html) and [FAQ](https://www.danskernessundhed.dk/FAQ.html) document Excel/CSV/TSV exports. Following the normal guest redirect with a cookie-preserving browser reaches the live SAS viewer. `src/health_profile_collection.py` automates **Kommune → 2025 → all municipalities → Export data → formatted XLSX, rows 1–98**. No credentials or access-control bypass is involved. The viewer's session-based services were observed, but no documented stable open-data API or standalone export URL was identified; acquisition uses the supported UI rather than reconstructing internal API payloads.

| Output variable | Definition | Source wave |
| --- | --- | --- |
| `daily_smoking_pct` | Daily smoking, excluding occasional-only smoking | 2025 |
| `obesity_pct` | BMI >=30 using self-reported height and weight | 2025 |
| `physical_inactivity_pct` | Failing the portal's WHO minimum weekly activity criterion; not sedentary leisure activity | 2025 |
| `risky_alcohol_pct` | More than 10 Danish standard drinks during a typical week | 2025 |
| `good_self_rated_health_pct` | Published excellent/very good/good health share, retained for audit | 2025 |
| `less_good_or_poor_self_rated_health_pct` | Derived as 100 minus the published good-health share after verifying the five-category partition; means **mindre godt OR dårligt**, not dårligt alone | 2025 |
| `poor_mental_health_pct` | Low SF-12 mental component score, <=35.76 in the saved portal definition; distinct from low mental well-being | 2025 |

Raw exports are stored unchanged with official definition HTML, source URLs, selected wave/filters, retrieval timestamps, and SHA-256 checksums. Excel stores prevalences as fractions with percentage cell formatting; the importer validates that formatting before multiplying by 100. It reads the exact prevalence column, retains raw adjusted-OR columns without analysing them, and maps normalized official municipality names to the existing municipality codes without fuzzy matching.

Every health measure has a year and missingness/status column plus variable-level provenance. No missing or suppressed values are imputed. The combined master retains **2024 socioeconomic years and 2025 health years**, so it is not a single-year panel. The population for each outcome is the portal's valid-response municipality total; survey eligibility is generally 16+, with indicator-specific definitions retained verbatim. Physical-activity thresholds and the documented 2017–2021 questionnaire break require care before interpretation. Sampling weights, response bias, uncertainty, and eligibility differences remain methodological considerations; complete aggregate coverage does not imply complete survey response.

See [source inventory](report/source_inventory.csv), [access investigation](report/health_source_investigation.md), and [reproduction/export instructions](report/health_profile_exports.md). No manual action is currently required. Research data access through [NATSUP application](https://www.danskernessundhed.dk/Dataudlevering.html) is distinct from public aggregate exports. A separate low-well-being measure has not been acquired; poor mental health is the selected mental-health outcome. Credit Den Nationale Sundhedsprofil when publishing these data and follow the acknowledgement requirements in the portal guide.

### Already acquired: municipality life expectancy, HISBK

[HISBK — Middellevetid for 0-årige](https://www.statbank.dk/HISBK) provides period life expectancy at birth in years. The latest available period at acquisition was **2021:2025**, selected from live table metadata rather than hard-coded. Both sexes (`TOT`), males (`M`), and females (`K`) are retrieved directly for the existing 98 municipality codes. National area `000` is retrieved separately for quality checks; its values are not municipality averages. Christiansø and national aggregates are not added as municipality rows.

The HISBK footnote states that estimates for **Ærø (492), Fanø (563), Samsø (741), and Læsø (825)** are not shown because the municipalities are too small for sufficiently reliable estimates. All 98 municipality rows match by official code/name, while 94 have all three life-expectancy values. Each sex-specific column has four missing values, and the derived sex gap has four missing values. These are retained as null, without imputation. Raw JSON null/status markers are preserved, and any source suppression zero is treated as missing rather than a genuine zero-year expectancy.

The final master is **`data/processed/municipality_master.csv`**, containing the existing socioeconomic/health columns plus:

- `life_expectancy_total`, `life_expectancy_male`, `life_expectancy_female`: directly published HISBK values in years; total is not averaged from the sexes.
- `life_expectancy_sex_gap`: female minus male, in years; null if either is missing.
- `life_expectancy_period`: exact code `2021:2025`, including rows with withheld estimates.
- Three `life_expectancy_*_status` columns distinguishing available observations from source missingness/suppression.

This is a five-year **period** measure, not an annual 2025 estimate or a forecast for a birth cohort. The master combines 2024 socioeconomic data, 2025 health-profile data, and 2021:2025 life expectancy; this temporal alignment must be considered before analysis. National and municipal minima/maxima appear only in the quality report, without substantive interpretation.

## Run the life-expectancy pipeline

Run after producing the socioeconomic-plus-health master:

```bash
source .venv/bin/activate
python -m src.life_expectancy_collection
```

This makes explicit POST requests to the Statistics Denmark API, with timeouts/retries, and creates a new exclusive `data/raw/hisbk_<UTC timestamp>_<unique suffix>/` snapshot. It contains `HISBK_metadata.json`, `HISBK_data.json`, and `manifest.json` with the exact requests, selected period, URLs, retrieval times, and SHA-256 checksums. Raw data and earlier master snapshots are never overwritten. Replay the completed acquisition offline:

```bash
python -m src.life_expectancy_collection --raw-dir data/raw/hisbk_20261106T121025Z_53322f84
```

The command writes/replaces derived `data/processed/municipality_master.csv`, `data/processed/municipality_master_provenance.json`, and `outputs/tables/life_expectancy_quality.json`. Provenance embeds the original combined-master provenance, records variable-level HISBK definitions/selections, and checksums both input and output masters. Checks cover 98 municipality rows, source-cell completeness, duplicate keys, exact official names, missing values, and broad numeric screens of 50–110 years for nonmissing life expectancy and −20 to +20 years for the sex gap. Source-withheld estimates are reported as `passed_with_source_missingness`; structural errors or invalid nonmissing values prevent publication. National values and municipal extrema are quality checks only.

## Run the health-profile pipeline

Rebuild the acquired snapshot **offline**, using the standard requirements:

```bash
source .venv/bin/activate
python -m src.health_profile_import --raw-dir data/raw/health_profile_2025_20261106T120114Z_5041ba1d
```

To acquire a fresh snapshot, install the optional browser dependencies:

```bash
python -m pip install -r requirements-health.txt
python -m playwright install chromium
python -m src.health_profile_collection --wave 2025
```

Then import the new raw directory printed by that command. An explicit `--wave 2021` is available if a future 2025 acquisition fails; the importer rejects mixed waves. Each acquisition creates a new exclusive directory and retains failed manifests rather than substituting data.

Outputs are:

- `data/processed/municipality_master_2024_health_2025.csv`: combined master, preserving the original socioeconomic master.
- `data/processed/municipality_master_2024_health_2025_provenance.json`: original socioeconomic provenance and variable-level health sources, definitions, transformations, selections, and checksums.
- `data/processed/health_profile_2025_long.csv`: the six directly exported measures in long form with codes, source names, wave, and statuses.
- `outputs/tables/health_profile_quality_2025.json`: municipality coverage, unmatched names, duplicates, source missing/suppression tokens, and numeric range checks per export.

The acquired snapshot contains six XLSX workbooks, six definition HTML files, and `manifest.json`. Import verifies source and definition checksums and the existing socioeconomic master's provenance. Unsupported formats, ambiguous percentage units, duplicate municipalities, unexpected names, and an unverified self-rated-health response partition prevent publication. Recognized missing/suppressed cells and absent municipality rows remain null and are reported explicitly. Keep complete raw snapshots for reproduction; data and outputs remain Git-ignored.

## Run the data pipeline

From the repository root, after installing requirements:

```bash
source .venv/bin/activate
python -m src.data_collection
```

The command requires internet access to `api.statbank.dk`. It uses POST requests, explicit 2024 selections, timeouts, and bounded retries for transient failures. There is no silent fallback to other years or fabricated data.

Each acquisition creates a new directory `data/raw/statbank_<UTC timestamp>_<unique suffix>/` containing:

- `FOLK1A_metadata.json`, `INDKP106_metadata.json`, `HFUDD11_metadata.json`: official category and table metadata.
- `FOLK1A_data.json`, `INDKP106_data.json`, `HFUDD11_data.json`: unchanged JSON-stat response bytes.
- `manifest.json`: exact requests, URLs, retrieval times, HTTP statuses, SHA-256 checksums, and completion status.

Raw files use exclusive creation and are never overwritten by processing. Failed acquisitions retain an explicitly failed manifest. To rebuild the exact extract offline, copy the raw directory path printed by the first run:

```bash
python -m src.data_collection --raw-dir data/raw/statbank_<UTC timestamp>_<unique suffix>
```

Replay verifies all six raw-file checksums. Each successful run writes or replaces these **derived** artifacts:

- `data/processed/municipality_master_2024.csv`: one row per municipality, source-year columns, reference dates, income, population, age counts/shares, education counts/shares.
- `data/processed/municipality_master_2024_provenance.json`: raw snapshot reference, table selections, documentation URLs, source updates, and master checksum.
- `outputs/tables/data_quality_report_2024.json`: municipality counts, missing values for every column, duplicate codes/names, unexpected names and cells by source, numeric ranges, reconciliation checks, and pass/fail status.
- `outputs/tables/numeric_ranges_2024.csv`: observed minima/maxima and validation bounds, for data-quality review only.

Quality gates require 98 unique municipalities, all requested source cells, matching source labels, no missing master values, nonnegative integer counts, positive denominators/income, shares between 0 and 100, and reconciliation of single-year age counts to population totals. A broad ceiling of 10 million is a screening rule for counts and mean income, not a finding or estimated range. Primary plus unknown education must not exceed the education denominator. Failed checks stop publication of a new master; any previous successful master remains linked to its own provenance and must not be confused with the failed run.

Missing JSON-stat cells and status-marked values are preserved as missing; partial sums are not accepted. StatBank metadata declares `suppressedDataValue=0`, so confidential small counts can be indistinguishable from genuine zeros. This source limitation is reported; values are not imputed. Source and processed numeric ranges are validation information, not substantive health findings.

Run the integration checks against an acquired complete snapshot:

```bash
python -m unittest discover -s tests -v
```

Tests use real local extracts and skip if none exist. They check offline reproduction, raw immutability, checksum rejection, missing-cell handling, and unexpected source names. Raw data and derived outputs remain ignored by Git; retain the complete raw snapshot alongside the code for exact reproduction. The source inventory and methodological notes are versioned.

## Methodological considerations

The analysis will need to address missing and suppressed observations, municipality boundaries and codes, differences in reporting periods, age structure and standardisation, measurement differences, confounding, spatial dependence, and model assumptions. Municipality-level associations cannot establish individual-level relationships or causality. Uncertainty, sensitivity analyses, and the limits of comparisons will be reported alongside eventual results.

## Repository structure

```text
danish-health-inequality-atlas/
├── app.py
├── README.md
├── requirements.txt
├── requirements-health.txt
├── .gitignore
├── data/
│   ├── raw/
│   └── processed/
├── src/
│   ├── __init__.py
│   ├── data_collection.py
│   ├── health_profile_collection.py
│   ├── health_profile_import.py
│   ├── life_expectancy_collection.py
│   ├── data_cleaning.py
│   ├── analysis.py
│   └── visualization.py
├── outputs/
│   ├── figures/
│   └── tables/
└── report/
```

Empty directories include `.gitkeep` files so that Git preserves the structure. The local `.venv` directory and generated data and outputs are excluded from version control.

## Local setup

Requires Python 3 and a compatible pip installation.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate` instead. Dependencies are currently unpinned; record tested versions when the analytical workflow is established.

## Module responsibilities

- `src/data_collection.py`: official StatBank acquisition, snapshot verification, master-table assembly, and quality reporting.
- `src/health_profile_collection.py`: official public guest-viewer exports and raw health snapshot metadata.
- `src/health_profile_import.py`: health export validation, missingness, municipality matching, and combined-master publication.
- `src/life_expectancy_collection.py`: latest HISBK acquisition, immutable snapshots, quality checks, and final-master assembly.
- `src/data_cleaning.py`: future additional harmonisation and preparation.
- `src/analysis.py`: reproducible audit, primary regressions, exploratory profiles/diagnostics and secondary analyses.
- `src/visualization.py`: statistical figures in PNG/PDF formats.
- `report/`: acquisition notes, statistical methods, generated results and complete output inventory.
