<!-- page -->
PUBLIC HEALTH · MUNICIPALITY ANALYSIS

# Danish Health & Life Expectancy

### Geographical differences in health, socioeconomic conditions and life expectancy across Danish municipalities

**Frederik Jensen**  
BSc in Physiotherapy  
cand.san. — Interdisciplinary Health Studies

Independent public-health data analysis and portfolio project

6 November 2026 · Version 1.0 · English

This report brings official Danish municipality data together to describe patterns in population health, examine their statistical associations and identify questions for further investigation.

**Source windows**  
Socioeconomic conditions: 2024  
National Health Profile: 2025  
Period life expectancy at birth: 2021–2025

**Scope**  
98 municipalities in the atlas · 94 complete cases in life-expectancy models · No imputation

<!-- page -->
## Executive summary

Health planning requires an understanding of how population health differs between places and how those differences relate to social conditions. This analysis combines official Statistics Denmark records with public municipality estimates from the Danish National Health Profile. It describes 98 municipalities; life-expectancy analyses use 94 because four estimates are withheld.

Low educational attainment and daily smoking have the strongest negative simple associations with life expectancy: Pearson r = {{r_education}} and {{r_smoking}}, respectively. Higher disposable income is positively associated (r = {{r_income}}). These patterns concern municipalities and cannot be transferred directly to individuals.

> **Key findings**
>
> - Education and smoking show particularly strong simple relationships with municipal life expectancy.
> - Health behaviours add statistical information beyond income and education: ΔR² = {{delta_r2}}, joint HC3 p = {{block_p}}.
> - The combined model accounts for approximately 75% of observed between-municipality variation (R² = {{M3_r2}}). This is model fit, not a causal percentage.
> - Overlapping predictors complicate adjusted coefficients. The positive conditional obesity coefficient is not evidence of a protective effect.
> - PCA and clustering describe mixed profiles, including an alcohol contrast; they do not create an overall health ranking.

Model 3 leave-one-out R² is {{loo_r2}}, below its in-sample fit. Residuals may guide further investigation of omitted context, but do not measure municipal performance. Timing differences, self-report, collinearity, missing island estimates and unmodelled spatial dependence limit interpretation. The project is a descriptive and hypothesis-generating overview, not an evaluation of policy effects.

### Reading guide

**Context and design:** 1 Background · 2 Aim · 3 Data · 4 Methods  
**Results:** 5 Variation · 6 Correlations · 7 Models · 8 Adjustment · 9 Residuals · 10 Profiles · 11 Sex-specific analyses · 12 Sensitivity  
**Interpretation:** 13 Discussion · 14 Limitations · 15 Conclusion  
**Documentation:** Reproducibility · References

Numerical tables use a decimal point in both language editions to make the reported results directly comparable. Figures are identical in both editions; their axes use English labels.

<!-- page -->
## 1. Background

National health averages can conceal important differences between local populations. Municipalities provide a useful scale for describing the geographical distribution of health, social conditions and potential prevention needs. Danish public data make it possible to examine these patterns with transparent definitions and identifiable sources.

Education and income describe different aspects of socioeconomic conditions. Smoking, physical activity, alcohol exposure and obesity describe aspects of health behaviour or related health status. They are interrelated rather than competing, self-contained explanations. A municipality’s observed pattern may reflect population composition, living conditions and accumulated exposures as well as current behaviour.

Life expectancy at birth is a broad population-health summary. Here it is a **period measure** based on mortality during 2021–2025, not a forecast of how long children born in 2025 will actually live. It cannot identify which diseases, services or policies account for a difference.

The official National Health Profile is intended to inform health planning [5–6]. Combining its aggregate estimates with socioeconomic data can help formulate questions for local investigation. It cannot establish whether changing one indicator would produce a particular change in life expectancy.

## 2. Aim and research questions

**Primary question:** Which health-behaviour and socioeconomic municipality characteristics are associated with geographical differences in life expectancy across Danish municipalities?

The secondary questions are:

1. Which indicators show the strongest simple associations with life expectancy?
2. Do health behaviours add explanatory information beyond socioeconomic characteristics?
3. Can municipalities be described using distinct multivariate health profiles?
4. Which municipalities have higher or lower observed life expectancy than predicted from the included indicators?
5. Do patterns differ between male and female life expectancy?

The four primary model specifications were fixed in the project code before fitting. This independent portfolio project was not externally preregistered. Correlations, profiles, residual rankings, influence exclusions and sex-specific models are exploratory or secondary.

<!-- page -->
## 3. Data sources and dataset construction

Table 1 documents the sources and reference periods. Public StatBank API responses and formatted Excel exports from the official health-profile guest viewer were preserved. Municipality codes and standardized names link the sources; the master contains one row for each municipality.

**Table 1. Official sources and analytical indicators**

| Data source | Indicator | Reference period | Geography | Notes |
| --- | --- | --- | --- | --- |
| Statistics Denmark, INDKP106 [1] | Mean personal disposable income | 2024 | Municipality | DKK; persons aged over 14; both sexes |
| Statistics Denmark, HFUDD11 [2] | Primary and unknown education | 30 Sep 2024 | Municipality | Shares among ages 25–64; unknown education remains in denominator |
| Statistics Denmark, FOLK1A [3] | Population; age shares | 1 Jan 2024 | Municipality | Age groups 0–17, 18–64, 65+ |
| National Health Profile [5–6] | Smoking; BMI ≥30; insufficient activity; alcohol >10 drinks/week | 2025 | Municipality | Published survey prevalence; indicator-specific valid responses |
| National Health Profile [5–6] | Self-rated health; SF-12 mental health | 2025 | Municipality | See definitions below |
| Statistics Denmark, HISBK [4] | Total, male and female life expectancy; sex gap | 2021–2025 | Municipality | Period estimates; four municipalities withheld |

*Source: preserved acquisition metadata, source inventory and analytical variable inventory. Table 1 is a source description, not a new data extraction.*

**Coverage.** The atlas contains {{municipalities}} municipalities. Ærø, Fanø, Samsø and Læsø have life expectancy withheld because Statistics Denmark considers the estimates too uncertain. The {{N}} remaining municipalities enter all primary and sex-specific models. All 98 enter health-profile PCA and clustering. No missing or withheld values are imputed; no predictions are assigned to withheld outcomes.

**Definitions matter.** Low education means highest completed education is primary education, ages 25–64. Obesity means BMI ≥30 based on self-reported height and weight. Insufficient activity follows the portal’s saved WHO weekly definition and eligibility, including its questionnaire-comparability warning. Alcohol means more than 10 Danish standard drinks in a typical week, not binge drinking or dependence.

Less-good/poor self-rated health combines the two responses *mindre godt* and *dårligt*, derived as the verified complement of excellent/very good/good health. Poor mental health is the portal’s low SF-12 mental-component score (≤35.76), not the complement of high well-being.

**Alignment and quality.** Duplicate keys, municipality names, coverage, missingness and numeric ranges were checked. Raw-file checksums and variable provenance are stored. Source windows overlap but differ: the 2025 survey is not a baseline exposure preceding the entire mortality period. This limits temporal and causal interpretation.

<!-- page -->
## 4. Analytical methods

### Describing and comparing municipalities

Saved descriptive summaries include observed and missing counts, means, sample standard deviations, medians, quartiles and ranges. Municipalities receive equal weight. Their average is therefore not a population-weighted national estimate.

Pearson r ranges from −1 to +1 and describes linear association: a value near −1 means higher values of one indicator generally accompany lower values of the other. Spearman ρ compares ranks and complements Pearson when ordering is more informative than a straight-line relationship.

The analysis evaluates all 136 unique pairs of 17 continuous variables. Benjamini–Hochberg (BH) false discovery rate (FDR) correction is applied separately to the Pearson and Spearman families. It limits the expected proportion of false discoveries among rejected hypotheses under the procedure’s assumptions; it does not make each finding certain. The full results retain weak and nonsignificant associations.

### Adjusted relationships and uncertainty

Ordinary least squares (OLS) models estimate conditional relationships, holding the other included indicators statistically constant. Each includes an intercept. Income is scaled per DKK 10,000; education and health slopes are per percentage point. HC3 robust standard errors make inference less sensitive to unequal residual variance, using t-based 95% confidence intervals [7]. They do not address spatial dependence or measurement error.

A confidence interval describes coefficient values reasonably compatible with the data and model assumptions. Standardized beta rescales a slope by SD(X)/SD(Y), allowing comparisons across units. Variance inflation factors (VIFs) indicate statistical overlap among predictors; high overlap can destabilize individual coefficients. No predictor is removed based on its p-value, sign or VIF.

R² is the proportion of observed outcome variation statistically accounted for by the included variables in this sample. **It is not a causal fraction of life expectancy.** Adjusted R² accounts for the number of predictors. BH correction covers the 20 non-intercept tests across Models 1–4; a separate family covers 18 secondary sex-specific tests. The single prespecified HC3 behaviour-block test is reported without further multiplicity correction [8].

### Profiles, residuals and robustness

PCA summarizes the six standardized health indicators as combinations that vary together. K-means explores k=2–6 in all six dimensions; the selected solution maximizes mean silhouette subject to at least five municipalities per group [9]. Groups are descriptive profiles, not natural or causal categories.

Model 3 residuals equal observed minus fitted life expectancy. Leave-one-out validation omits each municipality from fitting before predicting it, providing an internal check on optimism. Cook’s distance screens influence at D>4/N. Separate sensitivity fits exclude each model’s flagged cases; primary models retain all complete observations. These checks explore dependence on observations, not an automatic data-cleaning rule.

<!-- page -->
## 5. Geographical variation in health

Published municipal life expectancy ranges from **{{min_le}} to {{max_le}} years**. Figure 1 shows the distribution and selected municipalities at either end of the numerical ordering. These are descriptions of the published estimates, not quality ratings or tests of pairwise differences.

![Figure 1. Municipal variation in life expectancy](figures/variation.png)

**Figure 1. Published municipal life expectancy, 2021–2025.** Distribution and five municipalities at each end of the observed ordering; 94 published estimates. The national reference is the direct HISBK value, not a municipality average. Source: HISBK and the validated master dataset.

Table 2 places this variation alongside selected social and health indicators. Smoking and obesity vary appreciably between municipalities, as do income and education. The observed ranges indicate heterogeneity relevant to health planning, but survey estimates have sampling and nonresponse uncertainty that is not shown here.

**Table 2. Selected descriptive statistics across municipalities**

{{descriptive_table}}

*Source: saved descriptive statistics. Means and medians give each municipality equal weight. N=98 except life expectancy (N=94, four withheld). Monetary values are rounded to whole DKK, other measures to one decimal; percentage indicators are shares, not counts.*

<!-- page -->
## 6. Simple associations with life expectancy

Low education (r = {{r_education}}) and smoking (r = {{r_smoking}}) have the strongest negative simple associations: higher shares generally accompany lower life expectancy. Income is positively associated (r = {{r_income}}). Figure 2 includes all characteristics, regardless of significance.

![Figure 2. Correlation ranking](figures/correlations.png)

**Figure 2. Pearson correlations with total life expectancy.** Algebraically related life-expectancy outcomes are excluded from this characteristics display. Positive and negative directions are shown explicitly. Source: saved correlation results, N=94 for each displayed pair.

Self-rated health, activity and obesity also show strong negative associations. All six headline findings pass global BH correction. Table 3 includes both methods and nonsignificant results for population and ages 18–64. Alcohol’s positive municipality association does not demonstrate a health benefit; population composition and social patterns may contribute.

**Table 3. All characteristic–life-expectancy correlations**

{{correlation_table}}

*Source: saved correlations. BH q uses all 136 pairs separately by method; the table shows Pearson q. Spearman q and unrounded p-values are retained in the full saved outputs. All displayed pairs use N=94. Statistical association remains ecological.*

<!-- page -->
## 6. Simple associations with life expectancy — continued

![Figure 3. Education and smoking scatterplots](figures/associations.png)

**Figure 3. Municipality patterns behind two strong simple associations.** Each point is one municipality with published life expectancy. Lines are descriptive guides reconstructed from the saved Pearson correlations and the plotted sample’s means and standard deviations; no new inferential model is fitted. Source: validated master and saved correlations, N=94.

Figure 3 makes the practical interpretation clearer than the coefficient alone: higher primary-education shares and daily smoking prevalences tend to accompany lower life expectancy. The points do not all fall on a line. A strong relationship still permits substantial local variation and does not identify the reasons for any particular municipality’s position.

Spearman correlations in Table 3 are also negative for these indicators. For education, the rank association is weaker than the linear association, illustrating that the two summaries need not have the same magnitude. Neither establishes an effect on individuals.

**From simple to adjusted association.** A simple correlation considers one indicator at a time. Education, income, smoking and other health measures overlap. A multivariable coefficient instead describes a contrast among municipalities that are statistically alike on the other included predictors. Those are different questions; a strong simple association need not remain equally strong after adjustment.

## 7. Multivariable models

The four fixed specifications are:

- **M1 — socioeconomic:** income and primary education.
- **M2 — health behaviours:** smoking, obesity, insufficient activity and alcohol.
- **M3 — combined:** M1 plus the four M2 indicators.
- **M4 — expanded health:** M3 plus self-rated and mental health.

All use the same 94 complete cases. M1 and M2 are alternative specifications; M1→M3 and M3→M4 add predictor blocks. Table 4 and Figure 4 compare their fit on the next page.

<!-- page -->
## 7. Multivariable models — continued

**Table 4. Fit of the four primary life-expectancy models**

{{model_table}}

*Source: saved OLS model-fit table. Equal municipality weights; an intercept is included in every model but excluded from the predictor count. HC3 is used for coefficient inference, not to redefine R².*

![Figure 4. Model fit comparison](figures/models.png)

**Figure 4. R² and adjusted R² for the fixed primary models.** Text labels distinguish the two fit measures; the emphasis on combined specifications does not designate a universally preferred model. Source: saved model-fit results.

Adding behaviours to M1 increases R² by **{{delta_r2}}**. The joint HC3 block-test p-value is **{{block_p}}**. The combined model therefore contains additional statistical information beyond income and education in this sample. The test concerns the block jointly, not proof that each behaviour has an independent effect.

M3 accounts for approximately 75% of observed between-municipality variation (R² = {{M3_r2}}; adjusted R² = {{M3_adj}}). M4 has R² = {{M4_r2}} and adjusted R² = {{M4_adj}}. Higher fit with more health indicators does not establish their causal contribution or future predictive accuracy. These measures describe this dataset and these specifications.

The added self-rated and mental-health indicators partly describe concurrent health status. Their inclusion changes the question: M4 is an expanded conditional association model, whereas the saved residual/prediction analysis deliberately uses M3. Keeping that distinction avoids presenting a more highly adjusted model as the only interpretation of the data.

<!-- page -->
## 8. Fully adjusted results and collinearity

Table 5 reports every non-intercept M4 coefficient, including nonsignificant estimates. Income, education, obesity and mental health pass the declared correction across the 20 primary coefficient tests. Smoking is borderline at the nominal level and does not pass that correction (p=0.0494; q=0.0760).

**Table 5. Model 4 conditional associations with life expectancy**

{{coefficient_table}}

*Source: saved regression coefficients. b is years per DKK 10,000 for income and per percentage point for other indicators. β is standardized beta. Intervals use HC3 covariance and residual-df t references; q covers all 20 primary non-intercept tests. All estimates use N=94.*

![Figure 5. Fully adjusted standardized coefficients](../outputs/figures/model4_coefficients.png)

**Figure 5. Model 4 standardized coefficients and 95% HC3 intervals.** Reproduced unchanged from the validated analysis figure. A point’s direction is conditional on the other predictors; the interval depicts uncertainty, not causal certainty. Source: saved Model 4 output.

**Why the obesity sign needs caution.** Obesity has a negative simple association but a positive adjusted coefficient. Once predictors sharing much of the same variation are held constant, the remaining contrast can reverse direction: a suppression/collinearity pattern. Maximum M4 VIF is {{vif}}. This is **not evidence that obesity is protective**, and the coefficient should not be translated into an intervention recommendation. Inactivity, alcohol and self-rated health also have uncertain conditional estimates; their nonsignificance does not establish absence of a public-health relationship.

<!-- page -->
## 9. Expected versus observed life expectancy

**Residual = observed life expectancy − model-predicted life expectancy.** Positive values mean higher life expectancy than predicted by the included municipality indicators; negative values mean lower. Figure 6 compares observations with M3 fitted values; Figure 7 shows the largest positive and negative saved residuals.

![Figure 6. Observed versus predicted life expectancy](../outputs/figures/observed_vs_predicted.png)

**Figure 6. Observed and M3-predicted life expectancy.** The equality line represents an exact match. Predictions are in-sample fitted values for 94 municipalities; four withheld outcomes receive no predictions. Source: unchanged validated prediction figure.

![Figure 7. Municipality residuals](../outputs/figures/prediction_residual_ranking.png)

**Figure 7. Selected positive and negative M3 residuals.** Values are observed minus fitted life expectancy in years. This is an exploratory residual ordering, not a ranking of municipal performance or proof of statistically unusual outcomes. Source: unchanged validated residual figure.

<!-- page -->
## 9. Expected versus observed life expectancy — continued

Table 6 gives the exact examples represented in Figure 7, rounded to two decimals. A numerical position in this list does not establish that a residual is significantly different from zero or that municipalities differ significantly from one another.

**Table 6. Five largest positive and five largest negative saved residuals**

{{residual_table}}

*Source: saved Model 3 predictions and residuals, not a new ranking model. Observed life expectancy is published to one decimal; predictions and residuals are calculated at saved precision before rounding. All differences are in years.*

Odder and København illustrate higher and lower life expectancy than predicted by the included municipality indicators, respectively. Neither example identifies the cause of that difference. Omitted context, source uncertainty, aggregation, measurement error and chance can all contribute.

**Internal validation.** In-sample R² is {{M3_r2}}; leave-one-out R² is **{{loo_r2}}**. The latter predicts each municipality using coefficients estimated without that municipality. Its lower value is consistent with some optimism in training fit. It is an internal check, not external validation in a new wave or population. Neighbouring municipalities may share contextual features, so leaving out one place does not remove all related information.

**Use in practice.** Residual patterns can identify questions for deeper local review: are relevant health conditions, population movements or social contexts missing from the model? They do not quantify a municipality’s efficiency, policy effectiveness or avoidable mortality. No local explanation is assigned here.

<!-- page -->
## 10. PCA and municipal health profiles

PCA summarizes patterns shared by six standardized health indicators, using all 98 municipalities. PC1 accounts for **{{pc1}}%** and PC2 for **{{pc2}}%** of their variance. Figure 8 shows how much each component contributes; Figure 9 shows what the first two components represent.

![Figure 8. PCA scree plot](../outputs/figures/pca_scree.png)

**Figure 8. Variance accounted for by the six principal components.** Reproduced unchanged from saved PCA output; percentages concern the health-feature matrix, not life-expectancy variation. Source: validated PCA, N=98.

![Figure 9. PCA loadings](figures/loadings.png)

**Figure 9. Indicator correlations with PC1 and PC2.** Signed loadings are saved feature–component correlations, not eigenvector weights. Source: saved PCA loadings. The same figure is used in both language editions.

PC1 loads positively on self-rated health (+0.912), obesity (+0.908), inactivity (+0.887), smoking (+0.855) and mental health (+0.443), but negatively on alcohol (−0.501). It is therefore a **mixed contrast dimension, not a simple health-risk score**. Alcohol was not reversed to force alignment; its direction does not imply a protective exposure. Component signs are a display convention rather than substantive evidence.

<!-- page -->
## 10. PCA and municipal health profiles — continued

The selected k-means solution has **two profiles**, containing **34 and 64 municipalities**, with mean silhouette **{{silhouette}}**. It has the highest mean silhouette among the eligible k=2–6 solutions. This measures separation relative to within-profile similarity; it does not establish two natural types of municipality.

![Figure 10. Municipality projection and descriptive profiles](figures/profiles.png)

**Figure 10. Saved municipality profiles in PCA space and across the six indicators.** Shapes as well as colours distinguish profiles. The projection shows PC1 and PC2, but clustering used all six standardized features. Profile means are deviations from the 98-municipality mean in standard-deviation units. Source: saved scores, memberships and standardized profiles.

Figure 10 shows why an overall quality label would be misleading. The smaller profile has lower smoking, obesity, inactivity and poorer-health indicators, but higher alcohol exposure. The larger profile has the opposite relative pattern. These are **exploratory municipality profiles, not natural or causal groups**; neither is universally healthier on every included indicator.

Profiles can help organize comparisons across several dimensions rather than reducing a municipality to one score. They should be checked against local knowledge and source uncertainty before operational use. The grouping depends on the selected indicators, standardization, algorithm and chosen number of groups. Optimization-seed checks assess computational stability, not stability under a new sample or health-profile wave.

<!-- page -->
## 11. Sex-specific secondary analyses

Table 7 summarizes the same six-predictor M3 specification for male and female life expectancy and the female-minus-male gap.

**Table 7. Secondary model fit**

{{secondary_table}}

*Source: saved secondary model-fit results. Each model uses N=94 and HC3 inference. Sex-specific coefficient tests form a separate 18-test BH family.*

After correction, male associations remain for income, education, smoking and conditional obesity; female associations remain for income and smoking. The other secondary coefficients do not pass the declared correction. No sex-gap predictor passes. A significant result in one sex and a nonsignificant result in the other is not itself a tested sex difference. The positive conditional obesity coefficient retains the same interpretive caution as M4.


## 12. Model diagnostics and sensitivity

Maximum M4 VIF is **{{vif}}**, indicating substantial overlap for at least one predictor. Seven municipalities exceed the M4 Cook’s-distance screening threshold; six exceed it in M3. The primary models retain all 94 complete observations. A screen flags potential influence, not an invalid observation or a reason to delete a municipality automatically.

Separate exploratory sensitivity fits exclude each model’s own flagged observations. Table 8 highlights the nominal p-value threshold changes; all sensitivity coefficients remain available in the saved outputs. The exclusions are outcome-informed and do not define a preferred cleaned analysis.

**Table 8. Examples of sensitivity to influential-case exclusion**

{{sensitivity_table}}

*Source: saved sensitivity comparison. M3 excludes six and M4 seven Cook-flagged municipalities. These are nominal HC3 p-values, not newly multiplicity-adjusted claims; primary results are unchanged.*

Smoking in M4 moves from p=0.049 to p=0.061 under this exclusion, while M3 alcohol moves from p=0.216 to p=0.025. These changes illustrate the fragility of treating 0.05 as a sharp boundary. They reinforce cautious interpretation of conditional estimates rather than selecting whichever specification produces the more appealing result.

Residual-versus-fitted, Q–Q and Cook’s-distance figures are retained in the analysis archive. Heteroskedasticity and normality diagnostics are descriptive checks, not certificates that assumptions hold. HC3 remains in use regardless of those diagnostic p-values. It does not resolve spatial dependence, correlated source errors or confounding.

<!-- page -->
## 13. Discussion

The results are most informative as a connected pattern. Strong education and smoking correlations coexist with a positive income association and shared variation across health indicators. These measures describe different, overlapping features of municipal populations. The added fit of the behaviour block shows that income and education alone do not exhaust the information in the available indicators.

This does not partition population health into separate social and behavioural causes. Socioeconomic conditions may relate to opportunities, exposures, resources and population composition, while the cross-sectional indicators summarize accumulated patterns. The analysis cannot determine these pathways or the effect of changing any one of them.

### Interpreting the patterns

**Simple association and conditional contrast serve different purposes.** Low education and smoking identify strong geographical patterns. Individual M4 slopes are harder to interpret because related predictors are held constant simultaneously. A weakened or reversed slope does not cancel the descriptive relationship. The obesity sign reversal is a concrete example: the conditional contrast is not a recommendation to increase obesity, nor evidence that the negative simple association was spurious.

**Fit is not an explanation of mechanism.** M3’s approximately 75% in-sample R² indicates substantial statistical alignment with observed differences. It does not show that these indicators cause that fraction of life expectancy, and M4’s higher fit does not identify a superior intervention strategy. Internal validation gives a more demanding assessment than training fit, but still falls short of prediction in future periods or geographically independent populations.

**Profiles preserve complexity.** PCA and clustering emphasize that the indicators do not all align on one favourable–unfavourable dimension. The alcohol contrast is important rather than inconvenient: it prevents the profiles from being interpreted as a single health hierarchy. Profiles are useful for asking where a similar mix of exposures occurs, not for classifying residents or assigning municipalities an overall score.

**Residuals point to questions, not answers.** Healthcare accessibility, occupational composition, housing, environmental exposure, morbidity, migration, local healthcare organization and urbanicity are plausible contextual domains for further investigation. None was established as the explanation for a named municipality’s residual. Spatial dependence could also contribute to shared patterns and overly optimistic uncertainty estimates.

**Policy relevance requires another step.** The atlas can support needs assessment, comparison and discussion of where more detailed evidence is needed. Local interpretation should combine these aggregate patterns with within-municipality inequalities, population composition, survey uncertainty, service knowledge and more specific outcomes. Evaluation of policy effects would require a different design with defensible temporal and causal identification.

The strength of this project is the transparent connection between official sources, preserved definitions, saved results and cautious interpretation. Its contribution is a reproducible overview of geographical patterning and a set of better questions for subsequent public-health analysis.

<!-- page -->
## 14. Limitations

**Ecological design and ecological fallacy.** A relationship between municipality averages cannot automatically be applied to individuals. Associations do not establish causation, and municipality averages can hide substantial within-municipality inequality.

**Timing and confounding.** Socioeconomic data are primarily from 2024, health estimates from 2025 and mortality from 2021–2025. Temporal order is not established. Unmeasured conditions, reverse causation and residual demographic confounding remain possible; age shares and population size are described but not additional covariates in the fixed primary models.

**Self-report and uncertainty.** Health-profile estimates use self-reported information, indicator-specific denominators and rounded prevalences. Sampling and nonresponse uncertainty, mortality-estimate uncertainty and measurement error are not incorporated into the regression. HC3 does not correct these limitations.

**Withheld estimates and no imputation.** Ærø, Fanø, Samsø and Læsø are absent from life-expectancy analyses because their estimates are withheld. No values are filled in. The complete-case findings therefore do not describe life expectancy in those small island municipalities.

**Collinearity and influence.** Overlapping predictors complicate conditional slopes, and influential-case exclusions change some nominal inferences. Primary models retain all complete cases; exploratory sensitivity results do not establish a preferred replacement model.

**Spatial dependence and exploratory design.** Neighbouring municipalities may share exposures and errors. Formal spatial models were not estimated; HC3 and BH do not remove that concern. Profiles, residual ordering and secondary analyses remain hypothesis-generating.

## 15. Conclusion

Socioeconomic conditions and health behaviours show pronounced geographical associations with municipal life expectancy. Education and smoking have particularly strong simple relationships, and health behaviours add statistical information beyond income and education. Overlap among indicators complicates individual adjusted coefficients. The atlas is best understood as a descriptive and hypothesis-generating overview of municipality-level health inequality, rather than causal evidence or a municipal performance assessment.

### Reproducibility

Raw source files are preserved; processed data, provenance, programmatic statistical outputs and validation tests are included in the project. Report fields are linked to checksum-verified saved outputs, and existing analysis figures are reproduced unchanged. Additional publication figures only display saved values or validated observations. No withheld life-expectancy values are imputed. The build instructions document the software needed to reproduce these publications; continued availability of external services is not guaranteed.

<!-- page -->
## References and source notes

Source records were acquired or checked on **6 November 2026**. Table titles below retain their official Danish names so the exact source can be identified. The analysis uses the preserved snapshot, not any subsequent revision of a live table.

1. **Statistics Denmark. INDKP106 — Disponibel indkomst efter område, enhed, køn, alder, indkomstinterval og tid.** 2024, mean disposable income in DKK, both sexes. [Official table](https://www.statbank.dk/INDKP106).
2. **Statistics Denmark. HFUDD11 — Befolkningens højeste fuldførte uddannelse (15–69 år) efter bopælsområde, herkomst, højeste fuldførte uddannelse, alder, køn og tid.** Selected ages 25–64, 2024. [Official table](https://www.statbank.dk/HFUDD11).
3. **Statistics Denmark. FOLK1A — Befolkningen den 1. i kvartalet efter område, køn, alder, civilstand og tid.** 2024K1. [Official table](https://www.statbank.dk/FOLK1A).
4. **Statistics Denmark. HISBK — Middellevetid for 0-årige efter område, køn og tid.** Municipalities and Denmark, period 2021:2025; total, male and female. [Official table](https://www.statbank.dk/HISBK).
5. **Sundhedsstyrelsen; Statens Institut for Folkesundhed, SDU; the five Danish regions. Danskernes Sundhed / Den Nationale Sundhedsprofil, 2025.** Public municipality exports: *Andel der ryger dagligt; Svær overvægt; Opfylder ikke WHOs anbefalinger for fysisk aktivitet; Drikker mere end 10 genstande om ugen; Andel med godt selvvurderet helbred; Dårligt mentalt helbred.* [Official portal](https://www.danskernessundhed.dk/). Exact guest-viewer report URLs, selection settings, definitions, workbooks and checksums are recorded in the project source inventory and acquisition manifest.
6. **Sundhedsstyrelsen. Danskernes sundhed — Den Nationale Sundhedsprofil.** Official source overview and link to the 2025 report. [Source overview](https://www.sst.dk/sundhedsprofilen). Used for source context, not as a substitute for the municipality exports.
7. **statsmodels. OLSResults.get_robustcov_results.** Official documentation for robust covariance, including HC3. [Documentation](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html).
8. **statsmodels. stats.multitest.multipletests.** Official documentation for multiple-testing procedures, including Benjamini–Hochberg FDR. [Documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html).
9. **scikit-learn. Clustering; PCA.** Official documentation for k-means, silhouette interpretation and principal component analysis. [Clustering](https://scikit-learn.org/stable/modules/clustering.html) · [PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html).

### Publication record

Author: Frederik Jensen. Independent portfolio analysis; no institutional or employer affiliation is claimed. Analytical values come from the validated project snapshot. Report version 1.0; English and Danish editions have equivalent analytical content, section order, tables and figures.

Full unrounded coefficient, correlation, diagnostic and sensitivity tables remain in the project. The report’s selective descriptive display is not a significance filter; all included M4 slopes and all characteristic correlations are shown, and the saved outputs retain every primary and secondary estimate.
