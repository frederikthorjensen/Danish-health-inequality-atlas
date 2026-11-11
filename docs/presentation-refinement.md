# Analytical presentation refinement

Baseline: `4c7a0f502cbf823fc93572ad8c8d643d2ad2e582` on `main`.

This change updates the Streamlit presentation layer. It does not run an acquisition pipeline, refit a model, change a saved result, reverse an indicator, impute an outcome or generate a composite health score.

## Reading the revised figures

| Page / figure | Before | After |
| --- | --- | --- |
| Health inequalities / ranked values | Isolated points on a broad range, separate value gutter | Sorted horizontal lollipops with values beside marks and an explicitly labelled municipality median; local axis range |
| Associations / correlations | Diverging bars with detached value gutter | Symmetric zero-centred bars ordered by absolute saved correlation; end labels, complete wrapped indicator names |
| Associations / scatter | Numeric scatter with descriptive line and unlabelled mean crosshairs | Compact numeric scatter with original units, municipality tooltips and the same saved-result descriptive line; redundant crosshairs removed |
| Adjusted estimates | Coefficient points and saved intervals | Conventional forest plot, full wrapped predictor names, zero line and saved 95% HC3 intervals on both scales |
| Municipality explorer | Isolated standardized points | Diverging horizontal indicator bars using exactly the saved means and population SDs |
| Compare two places | Separate point rows in a large plot | Compact dumbbell with names and original-unit values at endpoints; exact difference below |
| Compare three/four places | Sparse point rows and a value gutter | Compact directly labelled dot rows; navy reference diamond, distinct other marks and explicit reference line |
| Observed versus fitted | Single-colour scatter and decorative annotations | Scatter with colour **and** symbol separating above/below fitted values; equal axis scaling, equality line and exact residual tooltips |
| Municipality residuals | Diverging bars and a separate value gutter | Zero-centred bars in descending absolute-residual order, values at bar ends, original residual years |
| Health profiles | Isolated mean points below the abstract PCA figure | Grouped diverging horizontal profile bars first, with pattern/colour redundancy; saved PCA projection remains secondary |
| PCA loadings | Bars with detached value gutter | Diverging bars with direct labels and complete names |
| Correlation matrix | Long angled column names and dense printed cells | Full numbered row names and matching numbered columns; exact saved correlations in hover |

`Lowest 20`, `Highest 20` and `All published` use the same saved values. Stable ordering retains the source ordering within ties; the separate displayed-precision/shared-rank helper is untouched. Long `All published` views deliberately give each municipality a readable row instead of compressing 94–98 labels into a short card.

Positive/negative directions retain the indicator's original meaning. Alcohol is not reversed. There is no best/worst performance interpretation of residuals or descriptive profiles. The positive conditional obesity coefficient, ecological limitations, multiple-testing family, missing outcomes and leave-one-out validation caveats remain explicit.

## Explanations and layout

Each chart has one compact “What to notice” line. The fuller description, definitions and cautions are in “Read how to interpret this figure”. The page width, navy sidebar, restrained palette, navigation and overall typography are retained. Chart cards and section spacing are tighter; headings and long categorical labels have deliberate room. Home, Key findings and Methods retain their existing structure. English and Danish report routes remain separate.

## Author facts and the published reports

The portrait, research-project titles, dates, descriptions and methods are retained from the baseline repository. These are repository-documented claims, not new independently verified credentials. No employer affiliation, new qualification, project or achievement has been added.

The author page retains:

- Professional Bachelor’s Degree in Physiotherapy, completed 2023.
- Master of Science (MSc) in Critical Health Studies, Roskilde University, completed 2025.

The portrait descriptor becomes “Health analysis · Public health · Physiotherapist” to avoid implying that “Public-health analyst” is an official current employment title.

The archived version 1.1 reports contain an older English degree wording. A note on the report page discloses the correct current title and links to the author page. The existing Markdown, templates, figures, PDFs and publication manifests are intentionally preserved; the PDFs have not been silently relabelled or rebuilt.

## Validation

The validation compares every protected file against its baseline SHA-256: all tracked `data/`, `outputs/`, `report/` files, both PDFs, and the core analysis/data-loading modules (103 files). New presentation tests compare plotted coordinates, coefficients, both HC3 interval scales, correlation inference fields, selected ranks, residuals, standardized indicator means, comparison values and missing/tied cases directly with saved outputs.

The existing whole-project unittest suite, type check and deployment validator are run, together with Chromium page and chart checks. The local runtime is Python 3.12 with Streamlit 1.67.0; repository CI uses the configured Python 3.14. Acquisition suites require the raw snapshots omitted from this release and retain their explicit skip behaviour.

Validation results: 43 tests completed successfully with three raw-acquisition suites skipped; whole-project `ty check` and the deployment validator passed. Chromium checked all 14 routes at 1920, 1366, 768 and 390 pixels (100 route/state/width combinations). Separate categorical-figure checks covered 33 figure/width combinations at 960, 700 and 350 pixels. Browser interactions verified three/four-place selection, reference changes, a withheld municipality, portrait alt text and keyboard operation of the interpretation expander. Both downloaded PDFs and the municipality CSV matched repository bytes exactly. All 103 protected files remained unchanged.
