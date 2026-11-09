# National Health Profile access investigation

Checked 6 November 2026. **Updated: automated acquisition succeeded for all six target reports, wave 2025, through the official public guest viewer and its documented formatted Excel export.** Each workbook contains 98 municipality rows. This document records access and definitions, with no substantive findings.

## Successful follow-up investigation

The earlier browsing-tool redirects below were incomplete evidence of access. A normal cookie-preserving HTTP session followed the site's advertised guest redirects and reached the SAS Visual Analytics Viewer 7.5. Its public configuration enabled export. A headless Chromium browser then rendered the reports, selected the `Kommune` tab and **2025** radio control, left region and municipality filters unselected (all municipalities), and used the report object's `Export data...` command. No credentials were provided and no access control was bypassed.

The observed public report-link parameters are `reportName`, `reportPath=/Produktion/Danskernes_Sundhed/`, and `reportViewOnly=true`. The page advertises service registries at `/SASVisualAnalyticsViewer/rest` and `/SASWIPClientAccess/rest/services`. The normal viewer makes requests to `/SASVisualAnalyticsTransport/onebi/services/getReport`, `generateReport`, `getReportFile`, and `getData`, plus `/SASVisualAnalyticsTransport/sasui/data/executors`. These are session-dependent viewer services, not a documented stable open-data API. We used the supported UI export instead of guessing their request payloads. Exported workbooks are available through the viewer; no standalone stable bulk-download URL was identified.

The export dialog offered rows `1-98`, all three columns (municipality, prevalence, and a published adjusted OR), formatted data, and Excel/TSV/CSV formats. The automated workflow explicitly selected all 98 rows, retained formatted data, and downloaded XLSX. The importer reads the prevalence column by its exact title and uses the Excel percentage format to multiply fractional numeric values by 100. The adjusted OR remains in raw; it is not used as a prevalence or analysed.

The completed snapshot is `data/raw/health_profile_2025_20261106T120114Z_5041ba1d/`. It holds six original XLSX files, six official definition HTML fragments (including category emphasis), and a manifest with selections, URLs, timestamps, and SHA-256 checksums. The manifest's network log stores paths/status codes only and omits session cookies and CAS tickets. Processing leaves all raw files unchanged.

### Acquired definitions

| Export | Adopted measure |
| --- | --- |
| `daily_smoking_2025.xlsx` | Daily smoking, distinct from occasional smoking |
| `obesity_2025.xlsx` | Severe overweight: BMI >=30 from self-reported height and weight |
| `physical_inactivity_2025.xlsx` | Failing the portal's WHO minimum weekly activity criterion; not sedentary leisure activity |
| `risky_alcohol_2025.xlsx` | More than 10 Danish standard drinks in a typical week |
| `good_self_rated_health_2025.xlsx` | Excellent, very good, or good health; retained as the directly published measure |
| `poor_mental_health_2025.xlsx` | Low SF-12 mental component score, <=35.76 in the portal definition; distinct from low well-being |

The self-rated definition provides five response categories and marks excellent/very good/good as the selected outcome. The importer verifies those categories and emphasis before deriving `less_good_or_poor_self_rated_health_pct = 100 - good_self_rated_health_pct`. This is **mindre godt OR dårligt**, not `dårligt` alone. The complement retains source rounding and propagates missingness. It does not invent an observation or substitute for a suppressed value.

Survey eligibility is generally 16+; each prevalence uses the portal's indicator-specific valid-response population. No additional age/sex filter was selected. The saved physical-activity definition describes adult WHO thresholds (18+) and warns against comparing 2017 with 2021 after questionnaire changes. This pipeline preserves the portal's total without reconstructing its eligibility; these nuances must be reviewed before interpretation. The portal's physical-activity definition should not be silently updated to current recommendations.

All six source columns match 98 municipalities with no unexpected names, duplicate municipalities, missing municipality rows, blank prevalence cells, suppression markers, or range failures. Missingness checks concern published municipality aggregates; they do not establish absence of survey item nonresponse. No imputation, correlations, regression, or new hypothesis tests were performed. The existing 2024 socioeconomic master is preserved; a separate combined master retains 2025 health years and embeds original socioeconomic provenance.

No manual action is required for this completed acquisition. The exact supported export selections and a fallback checklist are recorded in [health_profile_exports.md](health_profile_exports.md). Use `src.health_profile_collection` to acquire a new snapshot and `src.health_profile_import` to replay the completed snapshot offline.

## Why the earlier access result changed

The initial browsing-tool fetch stopped on SAS login/guest pages. Following the normal guest flow in a cookie-preserving browser resolved this, so the earlier programmatic-access conclusion is superseded. The guest viewer and official export are now verified end to end. No inference about a private API or user credentials was needed.
