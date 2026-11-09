"""Build publications from saved outputs only: python -m scripts.build_reports.

Install requirements-report.txt and run `playwright install chromium` once.
No acquisition or statistical analysis entry point is invoked.
"""
import base64
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/tmp/atlas-report-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import markdown
from playwright.sync_api import sync_playwright
from pypdf import PdfReader

from src.reporting import ROOT, REPORT, PDF_NAMES, LABELS, build_markdown, load_results, sha

NAVY, TEAL, MUTED = '#294C68', '#147486', '#526B7B'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'text.color':'#142F43',
 'axes.labelcolor':'#142F43','axes.edgecolor':'#DEE6EB','xtick.color':MUTED,'ytick.color':MUTED,
 'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.spines.bottom':False,
 'savefig.facecolor':'white'})


def finish(fig, name):
    fig.savefig(REPORT/'figures'/f'{name}.png',dpi=200,bbox_inches='tight',pad_inches=.15)
    plt.close(fig)


def axes_style(ax, axis='x'):
    ax.set_axisbelow(True)
    ax.grid(axis=axis,color='#EDF1F4',linewidth=.7)
    ax.tick_params(length=0,pad=6)


def publication_figures(t):
    """Reformat observations and saved summaries; never estimate a new model."""
    m=t['master']; le=m.dropna(subset=['life_expectancy_total']).sort_values('life_expectancy_total')
    national=json.loads((ROOT/'outputs/tables/life_expectancy_quality.json').read_text())['national_values_years']['life_expectancy_total']
    fig,(a,b)=plt.subplots(1,2,figsize=(9.2,3.0),gridspec_kw={'width_ratios':[1.5,1]},layout='constrained')
    extremes=__import__('pandas').concat([le.head(5),le.tail(5)])
    a.scatter(extremes.life_expectancy_total,extremes.municipality,c=TEAL,s=24)
    a.axvline(national,c=MUTED,ls='--',lw=.8,label=f'Denmark {national:.1f}')
    a.legend(frameon=False,fontsize=8,loc='lower right');a.set_xlabel('Life expectancy (years)');axes_style(a)
    b.hist(le.life_expectancy_total,bins=12,color=NAVY,edgecolor='white');b.set_xlabel('Life expectancy (years)');b.set_ylabel('Municipalities');axes_style(b,'y')
    finish(fig,'variation')
    c=t['correlations_total_life_expectancy']; c=c[c.method.eq('Pearson') & ~c.algebraically_related_outcome].sort_values('correlation',key=abs)
    names=[LABELS[v][0].replace(' (%)','').replace(' (persons)','') for v in c.other_variable]
    fig,a=plt.subplots(figsize=(9.2,3.4),layout='constrained');a.barh(names,c.correlation,color=[TEAL if v>0 else NAVY for v in c.correlation],height=.64)
    a.axvline(0,color=MUTED,lw=.8);a.set_xlim(-1,1);a.set_xlabel('Pearson correlation with life expectancy');axes_style(a)
    for j,v in enumerate(c.correlation):a.text(1.01,j,f'{v:+.3f}',va='center',fontsize=8)
    finish(fig,'correlations')
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.6),layout='constrained')
    for ax,v in zip(axes,['low_education_share_25_64_pct','daily_smoking_pct'],strict=True):
        sample=m[[v,'life_expectancy_total']].dropna();r=c.set_index('other_variable').loc[v,'correlation']
        x=np.array([sample[v].min(),sample[v].max()]);y=sample.life_expectancy_total.mean()+r*sample.life_expectancy_total.std(ddof=1)/sample[v].std(ddof=1)*(x-sample[v].mean())
        ax.scatter(sample[v],sample.life_expectancy_total,s=18,color=TEAL,alpha=.8);ax.plot(x,y,color=NAVY,lw=1)
        ax.set_xlabel(LABELS[v][0]);ax.set_ylabel('Life expectancy (years)');ax.set_title(f'Pearson r = {r:.3f}',loc='left',fontsize=10);axes_style(ax,'y')
    finish(fig,'associations')
    fits=t['regression_model_fit'];x=np.arange(len(fits));fig,a=plt.subplots(figsize=(9.2,3.2),layout='constrained')
    a.bar(x-.17,fits.R_squared,.34,color='#A7BBC4',label='R²');a.bar(x+.17,fits.adjusted_R_squared,.34,color=[NAVY,NAVY,TEAL,TEAL],label='Adjusted R²')
    for j,r in enumerate(fits.itertuples()):
        a.text(j-.17,r.R_squared+.01,f'{r.R_squared:.3f}',ha='center',fontsize=8)
        a.text(j+.17,r.adjusted_R_squared+.01,f'{r.adjusted_R_squared:.3f}',ha='center',fontsize=8)
    a.set_xticks(x,fits.model);a.set_ylim(0,.92);a.legend(frameon=False,ncols=2,loc='upper left');a.set_ylabel('Proportion of observed variation');axes_style(a,'y');finish(fig,'models')
    load=t['pca_loadings'];fig,axes=plt.subplots(1,2,figsize=(9.2,3),layout='constrained')
    for a,pc in zip(axes,['PC1','PC2'],strict=True):
        a.barh([LABELS[v][0].replace(' (%)','') for v in load.variable],load[pc],color=[TEAL if v>0 else NAVY for v in load[pc]])
        a.axvline(0,color=MUTED,lw=.8);a.set_xlim(-1,1);a.set_xlabel(f'{pc} loading');axes_style(a)
    finish(fig,'loadings')
    membership=t['cluster_membership'];profiles=t['cluster_profiles_standardized'].set_index('cluster');features=list(load.variable)
    fig,(a,b)=plt.subplots(2,1,figsize=(9.2,5.7),layout='constrained')
    for k,color,marker in [(1,TEAL,'o'),(2,NAVY,'D')]:
        g=membership[membership.cluster.eq(k)]
        a.scatter(g.PC1,g.PC2,c=color,marker=marker,s=22,alpha=.85,label=f'Profile {k} (N={len(g)})')
        b.scatter(profiles.loc[k,features],np.arange(6)+(k-1.5)*.15,color=color,marker=marker,s=32,label=f'Profile {k}')
    a.set_xlabel('PC1 · 60.4%');a.set_ylabel('PC2 · 17.8%');a.legend(frameon=False,ncols=2,loc='upper left');axes_style(a,'y')
    b.set_yticks(np.arange(6),[LABELS[v][0].replace(' (%)','') for v in features]);b.axvline(0,color=MUTED,lw=.8,ls='--');b.set_xlabel('Mean standard deviations from the municipality mean');axes_style(b)
    finish(fig,'profiles')


def publication_html(lang):
    source=(REPORT/f'final_report_{lang}.md').read_text()
    pages=[s.strip() for s in source.split('<!-- page -->') if s.strip()]
    sections=[]
    for i,page in enumerate(pages):
        body=markdown.markdown(page,extensions=['tables','sane_lists'])
        body=re.sub(r'<p><strong>((?:Figure|Figur) \d+\.)',r'<p class="figure-caption"><strong>\1',body)
        def inline_image(match):
            path=(REPORT/match[1]).resolve()
            if not path.is_relative_to(ROOT):raise ValueError('Image outside project')
            return 'src="data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'"'
        body=re.sub(r'src="([^"]+\.png)"',inline_image,body)
        # Content stays selectable; CSS limits figure heights, never text overflow.
        sections.append(f'<article class="sheet {"cover" if i==0 else ""}"><header>DANISH HEALTH &amp; LIFE EXPECTANCY <span>{"ANALYTICAL REPORT" if lang=="en" else "ANALYSERAPPORT"}</span></header><main>{body}</main><footer>Frederik Jensen · 2026 <span>{i+1} / {len(pages)}</span></footer></article>')
    css=(REPORT/'publication.css').read_text()
    return f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>{PDF_NAMES[lang][:-4]}</title><style>{css}</style></head><body>'+''.join(sections)+'</body></html>'


def main():
    manifest,contexts=build_markdown();_,tables=load_results();publication_figures(tables)
    outputs=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        for lang,name in PDF_NAMES.items():
            html=REPORT/f'final_report_{lang}.html';html.write_text(publication_html(lang))
            page=browser.new_page();page.goto(html.as_uri());page.emulate_media(media='print');page.wait_for_function('Array.from(document.images).every(i => i.complete)')
            overflow=page.locator('.sheet').evaluate_all('(items)=>items.map((e,i)=>({page:i+1,overflow:e.scrollHeight>e.clientHeight+2,main:e.querySelector("main").getBoundingClientRect().bottom>e.querySelector("footer").getBoundingClientRect().top-6})).filter(x=>x.overflow||x.main)')
            if overflow:raise ValueError(f'{lang} report page overflow: {overflow}')
            pdf=ROOT/name;page.pdf(path=str(pdf),format='A4',print_background=True,prefer_css_page_size=True)
            count=len(PdfReader(pdf).pages)
            if count!=page.locator('.sheet').count():raise ValueError('Unexpected PDF pagination')
            outputs.append({'language':lang,'file':name,'pages':count,'sha256':sha(pdf),'markdown_sha256':sha(REPORT/f'final_report_{lang}.md')})
            page.close()
        browser.close()
    record={'created_at_utc':datetime.now(timezone.utc).isoformat(),'analysis_manifest_sha256':sha(ROOT/'outputs/tables/analysis_manifest.json'),
      'analysis_input_sha256':manifest['input_sha256'],'reports':outputs,'figure_sources':{},'facts':contexts,
      'build':'python -m scripts.build_reports; publication only; no inference rerun'}
    for lang in PDF_NAMES:
        for image in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',(REPORT/f'final_report_{lang}.md').read_text()):
            record['figure_sources'][image]=sha((REPORT/image).resolve())
    (REPORT/'publication_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(outputs,indent=2))


if __name__=='__main__':main()
