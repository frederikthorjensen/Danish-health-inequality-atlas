# Dashboard presentation and verification

The dashboard is a read-only presentation of the validated master and saved statistical outputs. Start it from the project root:

```bash
source .venv/bin/activate
streamlit run app.py
```

Tested with the project's installed Streamlit 1.67.0 and Plotly 7.1.0. No new runtime dependencies, statistical models, source datasets or imputed values were added for the dashboard.

## Navigation and design

Eight native Streamlit pages provide Overview, Health inequalities, What explains life expectancy?, Municipality explorer, Expected vs observed, Health profiles, Methods & limitations, and Data. Expected vs observed has its own prominent navigation item and an overview preview. Responsive native grids, bordered cards, a local SVG wordmark and a restrained blue/teal theme create a consistent product. Fonts use the local sans-serif stack; no external font service is required. Plotly provides interactive charts with accessible descriptions and hover details. The appearance is configured in `.streamlit/config.toml`, without private CSS selectors or custom JavaScript.

Ranked dot plots and distributions display exact published values. No municipality boundary data were already available in the validated project; no unverified map geometry was introduced. A standardized dot profile replaces a radar score: the six axes retain their original directions, and mixed PCA loadings are not disguised as a single health-risk index. All statistical ranks and profile memberships come from existing outputs; ranked raw indicator values use ordinary sorting only.

## Separation from statistical analysis

- `app.py` registers native pages; `app_pages/` contains direct page scripts.
- `src/dashboard_data.py` caches read-only artifacts, checks the master against acquisition/analysis hashes, verifies displayed statistical tables, and provides labels/units/reference periods.
- `src/dashboard_charts.py` builds Plotly figures. It does not import or call the analysis pipeline or any regression/PCA/clustering estimator.
- `src/dashboard_views.py` composes page layouts, controls, benchmarks, interpretation and downloads.

The fitted line on an exploratory scatterplot is a display transform of the saved Pearson r and the exact plotted sample's means/SDs: slope = r × SD(Y)/SD(X). No new inferential model or confidence interval is estimated. Histograms, medians and sorting are descriptive presentation transforms. Coefficient intervals, model fits, prediction residuals, PCA scores/loadings, silhouette values and group assignments are read from validated outputs.

The original analysis source files, README, source data and outputs remain unchanged, preserving the analysis manifest's existing hashes. Full analytical details are in [analysis_methods.md](analysis_methods.md); the dashboard does not replace that record.

## Benchmarks and missingness

The explorer compares total, male and female life expectancy against directly published national HISBK values. Other indicators use the unweighted municipality median, explicitly distinguished from national prevalence. Health-share differences are percentage points; higher/lower benchmark differences are shown neutrally rather than as a performance grade. The dot profile uses previously saved feature scaling parameters.

Ærø, Fanø, Samsø and Læsø display “Not published” for life-expectancy fields. They retain their observed socioeconomic/health data and profile membership, but have no predicted life expectancy or residual. The residual page displays in-sample Model 3 results and the existing leave-one-out metric, explains the residual definition and avoids best/worst labels.

## Verification

`tests/test_dashboard.py` smoke-tests every page, checks the five overview KPIs against validated results, exercises correlation/coefficient/profile controls and data downloads, verifies withheld municipalities, and checks that displaying the app does not mutate saved analysis artifacts. The numerical scatter-line transform is checked against the saved correlation. Existing statistical tests remain unchanged.

During development, a separate localhost-only Streamlit instance with the agent API was used to exercise all sections and controls. Headless browser checks cover desktop and mobile layout and browser errors. The agent API is enabled only by a test-server command-line flag, not in the app's deployed configuration. Source provenance downloads intentionally retain the original technical audit metadata; normal page labels and download names use readable indicator names.

Run all tests with `python -m unittest discover -s tests -v`. The production dashboard requires the existing local validated output files to be distributed with it; ignored data files are not automatically included in a Git-only deployment. It stops clearly if required artifacts are absent or fail integrity checks.
