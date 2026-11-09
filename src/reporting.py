"""Publication formatting of validated saved results. No model fitting or inference."""
from pathlib import Path
import hashlib
import json
import re

import pandas as pd
from src.project_paths import artifact_path, snapshot_source

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'report'
PDF_NAMES = {'en': 'Danish_Health_Life_Expectancy_Report_EN.pdf',
             'da': 'Sundhed_og_Middellevetid_i_Danmark_Rapport_DA.pdf'}
LABELS = {
 'life_expectancy_total': ('Life expectancy (years)', 'Middellevetid (år)'),
 'life_expectancy_male': ('Male life expectancy', 'Middellevetid, mænd'),
 'life_expectancy_female': ('Female life expectancy', 'Middellevetid, kvinder'),
 'life_expectancy_sex_gap': ('Female–male gap (years)', 'Forskel, kvinder–mænd (år)'),
 'disposable_income_mean_dkk': ('Disposable income (DKK)', 'Disponibel indkomst (kr.)'),
 'income_per_10000_dkk': ('Income / DKK 10,000', 'Indkomst / 10.000 kr.'),
 'low_education_share_25_64_pct': ('Primary education, 25–64 (%)', 'Grundskole, 25–64 år (%)'),
 'education_unknown_share_25_64_pct': ('Unknown education, 25–64 (%)', 'Uoplyst uddannelse, 25–64 år (%)'),
 'population': ('Population (persons)', 'Befolkning (personer)'),
 'age_0_17_share_pct': ('Aged 0–17 (%)', '0–17-årige (%)'),
 'age_18_64_share_pct': ('Aged 18–64 (%)', '18–64-årige (%)'),
 'age_65_plus_share_pct': ('Aged 65+ (%)', '65+-årige (%)'),
 'daily_smoking_pct': ('Daily smoking (%)', 'Daglig rygning (%)'),
 'obesity_pct': ('Obesity, BMI ≥30 (%)', 'Svær overvægt, BMI ≥30 (%)'),
 'physical_inactivity_pct': ('Insufficient activity (%)', 'Utilstrækkelig fysisk aktivitet (%)'),
 'risky_alcohol_pct': ('Alcohol >10 drinks/week (%)', 'Alkohol >10 genstande/uge (%)'),
 'less_good_or_poor_self_rated_health_pct': ('Less-good/poor self-rated health (%)', 'Mindre godt/dårligt selvvurderet helbred (%)'),
 'poor_mental_health_pct': ('Poor SF-12 mental health (%)', 'Dårlig mental sundhed, SF-12 (%)'),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_results():
    manifest = json.loads((ROOT/'outputs/tables/analysis_manifest.json').read_text())
    for item in manifest['artifacts']:
        if sha(ROOT/item['file']) != item['sha256']:
            raise ValueError(f"Validated artifact changed: {item['file']}")
    if sha(artifact_path(manifest['input_file'])) != manifest['input_sha256']:
        raise ValueError('Input dataset does not match validated analysis.')
    for file, expected in manifest['source_hashes'].items():
        snapshot_source(file,expected,sha)
    tables = {p.stem: pd.read_csv(p) for p in (ROOT/'outputs/tables').glob('*.csv')}
    tables['master'] = pd.read_csv(artifact_path(manifest['input_file']))
    return manifest, tables


def number(value, digits=3, signed=False):
    if pd.isna(value):
        return '—'
    return f'{value:+.{digits}f}' if signed else f'{value:.{digits}f}'


def probability(value):
    return f'{value:.2e}' if value < .0001 else f'{value:.4f}'


def md_table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |',
                      *['| '+' | '.join(map(str,row))+' |' for row in rows]])


def report_context(lang, tables):
    """Identical numbers, parallel localized labels; no new statistical estimates."""
    i = 0 if lang == 'en' else 1
    label = lambda v: LABELS[v][i]
    d = tables['descriptive_statistics'].set_index('variable')
    c = tables['correlations_total_life_expectancy']
    pearson = c[c.method.eq('Pearson') & ~c.algebraically_related_outcome].sort_values('correlation',key=abs,ascending=False)
    spearman = c[c.method.eq('Spearman')].set_index('other_variable')
    fit = tables['regression_model_fit'].set_index('model')
    coef = tables['regression_coefficients']
    m4 = coef[coef.model.eq('M4') & coef.term.ne('const')]
    summary = json.loads((ROOT/'outputs/tables/analysis_summary.json').read_text())
    vif = tables['vif']; maximum = vif.loc[vif.model.eq('M4'),'VIF'].max()
    cv = tables['cluster_validation'].set_index('k')
    residual = tables['municipality_predictions_residuals'].dropna(subset=['residual'])
    H = lambda en,da: en if lang=='en' else da
    context = {'N': str(len(residual)), 'municipalities':str(len(tables['master'])),
      'r_education':number(pearson.set_index('other_variable').loc['low_education_share_25_64_pct','correlation']),
      'r_smoking':number(pearson.set_index('other_variable').loc['daily_smoking_pct','correlation']),
      'r_income':number(pearson.set_index('other_variable').loc['disposable_income_mean_dkk','correlation'],signed=True),
      'vif':number(maximum,2), 'pc1':number(summary['PC1_variance_ratio']*100,1),
      'pc2':number(summary['PC2_variance_ratio']*100,1), 'silhouette':number(cv.loc[2,'silhouette']),
      'delta_r2':number(summary['incremental_value']['delta_R_squared']),
      'block_p':number(summary['incremental_value']['p_value'],5),
      'loo_r2':number(summary['prediction_quality']['leave_one_out_R_squared']),
      'min_le':number(d.loc['life_expectancy_total','min'],1),'max_le':number(d.loc['life_expectancy_total','max'],1)}
    for model in fit.index:
        context[f'{model}_r2']=number(fit.loc[model,'R_squared'])
        context[f'{model}_adj']=number(fit.loc[model,'adjusted_R_squared'])
    for r in tables['secondary_regression_model_fit'].itertuples():
        context[r.outcome+'_adj']=number(r.adjusted_R_squared)
    # All eligible characteristics, not a significance-filtered selection.
    context['correlation_table']=md_table([H('Indicator','Indikator'),'Pearson r','Spearman ρ',H('Pearson BH q','Pearson BH-q')],
      [[label(r.other_variable),number(r.correlation,signed=True),number(spearman.loc[r.other_variable,'correlation'],signed=True),probability(r.q_value_BH_all_pairs)] for r in pearson.itertuples()])
    desc_vars=['life_expectancy_total','disposable_income_mean_dkk','low_education_share_25_64_pct',
               'daily_smoking_pct','obesity_pct','physical_inactivity_pct','risky_alcohol_pct',
               'less_good_or_poor_self_rated_health_pct','poor_mental_health_pct','population','age_65_plus_share_pct']
    context['descriptive_table']=md_table([H('Indicator','Indikator'),'N',H('Mean','Gns.'),H('Median','Median'),H('Min–max','Min.–maks.')],
      [[label(v),int(d.loc[v,'N']),number(d.loc[v,'mean'],0 if v in ('disposable_income_mean_dkk','population') else 1),
        number(d.loc[v,'median'],0 if v in ('disposable_income_mean_dkk','population') else 1),
        number(d.loc[v,'min'],0 if v in ('disposable_income_mean_dkk','population') else 1)+'–'+number(d.loc[v,'max'],0 if v in ('disposable_income_mean_dkk','population') else 1)] for v in desc_vars])
    models = [('Socioeconomic','Socioøkonomi'),('Health behaviours','Sundhedsadfærd'),('Combined','Kombineret'),('Expanded health','Udvidet helbred')]
    context['model_table']=md_table([H('Model','Model'),H('Specification','Specifikation'),'N',H('Predictors','Prædiktorer'),'R²',H('Adjusted R²','Justeret R²')],
      [[m,models[j][i],int(fit.loc[m,'N']),int(fit.loc[m,'predictors']),number(fit.loc[m,'R_squared']),number(fit.loc[m,'adjusted_R_squared'])] for j,m in enumerate(fit.index)])
    context['coefficient_table']=md_table([H('Predictor','Prædiktor'),'b',H('95% HC3 CI','95% HC3-KI'),'β','p','BH q'],
      [[label(r.term),number(r.coefficient,4,signed=True),f'{number(r.ci_low,4)}; {number(r.ci_high,4)}',number(r.standardized_beta,3,signed=True),probability(r.robust_p_value),probability(r.q_value_family_BH)] for r in m4.itertuples()])
    rows=[]
    for r in pd.concat([residual.nlargest(5,'residual'),residual.nsmallest(5,'residual')]).itertuples():
        rows.append([r.municipality,number(r.observed,1),number(r.predicted,2),number(r.residual,2,signed=True)])
    context['residual_table']=md_table([H('Municipality','Kommune'),H('Observed','Observeret'),H('Predicted','Modelberegnet'),H('Residual (years)','Residual (år)')],rows)
    context['loading_table']=md_table([H('Indicator','Indikator'),'PC1','PC2'],
      [[label(r.variable),number(r.PC1,3,signed=True),number(r.PC2,3,signed=True)] for r in tables['pca_loadings'].itertuples()])
    secondary=tables['secondary_regression_model_fit']
    context['secondary_table']=md_table([H('Outcome','Udfald'),'N','R²',H('Adjusted R²','Justeret R²')],
      [[label(r.outcome),int(r.N),number(r.R_squared),number(r.adjusted_R_squared)] for r in secondary.itertuples()])
    sens=tables['sensitivity_analysis']
    context['sensitivity_table']=md_table([H('Model / predictor','Model / prædiktor'),H('Primary p','Primær p'),H('Sensitivity p','Følsomheds-p'),H('Sensitivity N','Følsomheds-N')],
      [[r.model+' / '+label(r.term),number(r.robust_p_value_full),number(r.robust_p_value_sensitivity),int(r.N_sensitivity)] for r in sens.loc[(sens.model.eq('M4') & sens.term.eq('daily_smoking_pct')) | (sens.model.eq('M3') & sens.term.eq('risky_alcohol_pct'))].itertuples()])
    return context


def build_markdown():
    manifest,tables=load_results()
    contexts={lang:report_context(lang,tables) for lang in ('en','da')}
    for lang,context in contexts.items():
        template=(REPORT/'templates'/f'report_{lang}.md').read_text()
        rendered=re.sub(r'\{\{(\w+)\}\}',lambda m:context[m[1]],template)
        if '{{' in rendered:raise ValueError('Unresolved report field')
        (REPORT/f'final_report_{lang}.md').write_text(rendered)
    return manifest,contexts
