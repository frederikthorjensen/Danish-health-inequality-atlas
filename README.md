# Danish Health & Life Expectancy

*Geographical inequalities across Danish municipalities*

An independent public-health analytics portfolio combining official municipality-level socioeconomic, health-profile and life-expectancy data. The project includes a Streamlit dashboard and equivalent English and Danish analytical reports.

**Public dashboard:** _Not deployed yet. Replace this line with the public `https://…streamlit.app` URL after deployment._

## Research question

Which socioeconomic conditions and health-behaviour indicators are associated with geographical differences in life expectancy across Danish municipalities?

The atlas describes ecological associations, not individual-level or causal effects.

## Data sources

| Source | Data | Period |
| --- | --- | --- |
| Statistics Denmark [INDKP106](https://www.statbank.dk/INDKP106) | Mean personal disposable income | 2024 |
| Statistics Denmark [HFUDD11](https://www.statbank.dk/HFUDD11), [FOLK1A](https://www.statbank.dk/FOLK1A) | Education, population and age structure | 2024 |
| [Danish National Health Profile](https://www.danskernessundhed.dk/) | Smoking, obesity, physical activity, alcohol, self-rated and SF-12 mental health | 2025 |
| Statistics Denmark [HISBK](https://www.statbank.dk/HISBK) | Period life expectancy at birth, total/male/female | 2021–2025 |

The master contains **98 municipalities**. Life expectancy is published for **94**; Ærø, Fanø, Samsø and Læsø are withheld for source uncertainty. No withheld values are imputed. Definitions, selections and attribution are recorded in the [source inventory](report/source_inventory.csv). Original publishers’ data terms apply separately from the project’s code.

## Methods and main findings

Methods include descriptive statistics, Pearson and Spearman correlations, Benjamini–Hochberg FDR correction, fixed OLS models with HC3 robust standard errors, standardized coefficients, VIF, PCA, k-means, Cook’s distance, influence sensitivities and leave-one-out validation.

- Low education (**r = −0.814**) and daily smoking (**r = −0.810**) show the strongest negative simple associations with life expectancy; income is positively associated (**r = +0.709**).
- Adding health behaviours to the socioeconomic model increases R² by **0.062**. The combined model has **R² = 0.751**, adjusted R² **0.733** and leave-one-out R² **0.706**.
- Predictors overlap substantially. The positive adjusted obesity coefficient is **not evidence of protection**.
- PCA and clustering describe mixed municipality profiles. PC1 is not a single health-risk score, and profiles are not natural or causal groups.

These are saved, validated results, including nonsignificant estimates—not analyses recomputed by the dashboard. See the [English report](Danish_Health_Life_Expectancy_Report_EN.pdf), [Danish report](Sundhed_og_Middellevetid_i_Danmark_Rapport_DA.pdf) and [full methods](report/analysis_methods.md).

## Dashboard features

- Executive findings with plain-language interpretation.
- Indicator distributions and municipality comparisons.
- Correlations, adjusted models and saved coefficient intervals.
- A municipality explorer and direct comparison of 2–4 municipalities across up to six factors.
- Observed/predicted life expectancy, residuals and exploratory health profiles.
- Separate English/Danish report readers, PDF downloads, data dictionary and CSV downloads.

## Methodological limitations

The analysis is ecological and observational. Municipality averages hide within-municipality inequality and cannot establish individual effects or causation. Source periods differ, survey measures are self-reported, four small municipalities lack published life expectancy, and collinearity, influential observations and unmeasured confounding complicate interpretation. Spatial dependence is not modelled; HC3 does not correct it. Residuals are not municipal performance rankings, and R² is not a causal percentage explained.

## Run locally

Use **Python 3.14**, the tested analysis/runtime series. The dashboard needs no credentials, browser automation or network acquisition at runtime.

```sh
python3.14 -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Run from the repository root. The committed release must contain the processed snapshot, saved outputs, assets and reports; installing packages alone does not supply those files.

For checks:

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m scripts.check_deployment
```

The GitHub Actions workflow also runs whole-project type checks. Acquisition integration tests require locally preserved raw snapshots and explicitly skip when these are absent from a public release; numerical, dashboard, report and comparison tests still run.

## Repository structure

```text
app.py                       Streamlit entry point and navigation
app_pages/                   Thin page scripts
src/                         Acquisition, analysis and separate presentation modules
assets/                      Wordmark, design tokens and dashboard styling
.streamlit/config.toml       Public application theme; no secrets
requirements*.txt            Runtime, development and optional build dependencies
data/raw/                    Original local acquisition archive; excluded from public release
data/processed/              Validated municipality datasets and provenance
outputs/tables/              Saved statistical results, quality reports and manifest
outputs/figures/             Validated analysis figures
report/                      Bilingual reports, sources, methods and publication assets
scripts/                     Report build, public export and deployment validation
tests/                       Numerical, data-quality, UI and publication checks
.github/workflows/ci.yml      Public-repository CI
```

## Reproducibility and public release

Raw API responses and original health-profile exports are preserved locally. Processed data and saved outputs are generated programmatically; provenance and integrity checksums link the stages. No missing life-expectancy estimates are filled in. Optional acquisition and PDF-build tools are separated into `requirements-health.txt` and `requirements-report.txt`; see [report build instructions](report/BUILD.md).

The original analysis manifest includes a historical README checksum and workstation paths. Its exact README is preserved at `report/analysis_snapshot/README.md`; the project README can now evolve without rewriting statistical results. Runtime path resolution uses the current repository, never the original workstation.

**Publish the prepared release, not the unfiltered working folder:**

```sh
python -m scripts.prepare_public_repository --output public_release
cd public_release
python -m scripts.check_deployment
```

The exporter copies the code, required data, validated outputs and reports. It excludes raw acquisitions, virtual environments, local agent/editor files and secrets. It redacts workstation paths in **metadata copies only** and reconnects dependent checksum records. Observation/statistical CSVs, figures and PDFs are verified byte-for-byte unchanged. `public_export_manifest.json` records this process; original files remain untouched.

See the [deployment readiness record](report/deployment_readiness.md) for verification results and remaining manual steps.

Review the release folder, create your GitHub repository and push **its contents**. For Streamlit Community Cloud select the repository/branch, **`app.py`**, and **Python 3.14** in Advanced settings. No secrets or system packages are required for the read-only app. `.python-version` documents the local target; choose the Cloud Python version explicitly. See [Streamlit deployment documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

After deployment, smoke-test all pages and downloads, then replace the public-dashboard placeholder above. Exact dependency pins and tests improve repeatability; external services and future hosting environments are not guaranteed to remain unchanged.

## Author

**Frederik Jensen**  
Professional Bachelor of Physiotherapy  
Master of Science (MSc) in Critical Health Studies

Independent portfolio project focused on public-health data, statistical analysis, reproducibility and clear communication. No institutional or employer affiliation is claimed.

## License

No `LICENSE` file exists and no open-source license has been selected. This is a public portfolio presentation; do not assume the code has been licensed for unrestricted reuse. Select a license explicitly if desired. The official source data remain subject to their publishers’ terms and attribution requirements.
