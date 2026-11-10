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
from pypdf import PdfReader, PdfWriter

from src.reporting import ROOT, REPORT, PDF_NAMES, LABELS, build_markdown, load_results, sha

INK, NAVY, TEAL, MUTED, PALE, WARM = '#102A3A', '#244A64', '#0E7180', '#607684', '#E8F0F2', '#A85F3D'
REPORT_META = {
    'en': {
        'title': 'Danish Health & Life Expectancy',
        'strapline': 'Municipality health report',
        'report': 'Analytical report',
        'subject': 'Geographical inequalities in health and life expectancy across Danish municipalities',
        'keywords': 'Denmark, municipalities, public health, life expectancy, health inequality',
    },
    'da': {
        'title': 'Sundhed og middellevetid i Danmark',
        'strapline': 'Kommunal sundhedsrapport',
        'report': 'Analyserapport',
        'subject': 'Geografiske forskelle i sundhed og middellevetid på tværs af danske kommuner',
        'keywords': 'Danmark, kommuner, folkesundhed, middellevetid, sundhedsulighed',
    },
}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'text.color':INK,
 'axes.labelcolor':INK,'axes.edgecolor':'#D7E1E6','xtick.color':MUTED,'ytick.color':MUTED,
 'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.spines.bottom':False,
 'axes.titleweight':700,'axes.titlesize':10,'axes.titlepad':10,
 'savefig.facecolor':'white','figure.facecolor':'white'})


def finish(fig, name):
    fig.savefig(REPORT/'figures'/f'{name}.png',dpi=240,bbox_inches='tight',pad_inches=.16)
    plt.close(fig)


def axes_style(ax, axis='x'):
    ax.set_axisbelow(True)
    ax.grid(axis=axis,color='#E8EEF1',linewidth=.7)
    ax.tick_params(length=0,pad=6)


def publication_figures(t):
    """Reformat observations and saved summaries; never estimate a new model."""
    m=t['master']; le=m.dropna(subset=['life_expectancy_total']).sort_values('life_expectancy_total')
    national=json.loads((ROOT/'outputs/tables/life_expectancy_quality.json').read_text())['national_values_years']['life_expectancy_total']
    fig,(a,b)=plt.subplots(1,2,figsize=(9.2,3.0),gridspec_kw={'width_ratios':[1.5,1]},layout='constrained')
    extremes=__import__('pandas').concat([le.head(5),le.tail(5)])
    a.scatter(extremes.life_expectancy_total,extremes.municipality,c=[NAVY]*5+[TEAL]*5,s=34,
              edgecolors='white',linewidths=.7,zorder=3)
    a.axvline(national,c=MUTED,ls=(0,(3,3)),lw=1,label=f'Denmark {national:.1f}')
    a.legend(frameon=False,fontsize=8,loc='lower right');a.set_xlabel('Life expectancy (years)');axes_style(a)
    b.hist(le.life_expectancy_total,bins=12,color=NAVY,alpha=.92,edgecolor='white',linewidth=1)
    b.axvline(national,c=TEAL,ls=(0,(3,3)),lw=1.2);b.set_xlabel('Life expectancy (years)');b.set_ylabel('Municipalities');axes_style(b,'y')
    finish(fig,'variation')
    c=t['correlations_total_life_expectancy']; c=c[c.method.eq('Pearson') & ~c.algebraically_related_outcome].sort_values('correlation',key=abs)
    names=[LABELS[v][0].replace(' (%)','').replace(' (persons)','') for v in c.other_variable]
    strength=np.abs(c.correlation)
    colors=[TEAL if v>0 else (INK if s>=.7 else NAVY) for v,s in zip(c.correlation,strength,strict=True)]
    alpha=[1 if s>=.65 else .65 for s in strength]
    fig,a=plt.subplots(figsize=(9.2,3.5),layout='constrained')
    bars=a.barh(names,c.correlation,color=colors,height=.62)
    for bar,value in zip(bars,alpha,strict=True):bar.set_alpha(value)
    a.axvline(0,color=MUTED,lw=1);a.set_xlim(-1,1);a.set_xlabel('Pearson correlation with life expectancy');axes_style(a)
    for j,v in enumerate(c.correlation):
        a.text(.96 if v>=0 else -.96,j,f'{v:+.3f}',va='center',ha='right' if v>=0 else 'left',fontsize=8,color=INK,fontweight=700)
    finish(fig,'correlations')
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.6),layout='constrained')
    for ax,v in zip(axes,['low_education_share_25_64_pct','daily_smoking_pct'],strict=True):
        sample=m[[v,'life_expectancy_total']].dropna();r=c.set_index('other_variable').loc[v,'correlation']
        x=np.array([sample[v].min(),sample[v].max()]);y=sample.life_expectancy_total.mean()+r*sample.life_expectancy_total.std(ddof=1)/sample[v].std(ddof=1)*(x-sample[v].mean())
        ax.scatter(sample[v],sample.life_expectancy_total,s=22,color=TEAL,alpha=.72,
                   edgecolors='white',linewidths=.45,zorder=3);ax.plot(x,y,color=INK,lw=1.4)
        ax.set_xlabel(LABELS[v][0]);ax.set_ylabel('Life expectancy (years)')
        ax.set_title(f'Pearson r = {r:.3f}',loc='left',color=INK);axes_style(ax,'y')
    finish(fig,'associations')
    fits=t['regression_model_fit'];x=np.arange(len(fits));fig,a=plt.subplots(figsize=(9.2,3.2),layout='constrained')
    a.bar(x-.17,fits.R_squared,.34,color='#B9C8CF',label='R²')
    a.bar(x+.17,fits.adjusted_R_squared,.34,color=[NAVY,NAVY,TEAL,TEAL],label='Adjusted R²')
    for j,r in enumerate(fits.itertuples()):
        a.text(j-.17,r.R_squared+.01,f'{r.R_squared:.3f}',ha='center',fontsize=8)
        a.text(j+.17,r.adjusted_R_squared+.01,f'{r.adjusted_R_squared:.3f}',ha='center',fontsize=8)
    a.set_xticks(x,fits.model);a.set_ylim(0,.9);a.legend(frameon=False,ncols=2,loc='upper left')
    a.set_ylabel('Proportion of observed variation');axes_style(a,'y');finish(fig,'models')
    load=t['pca_loadings'];fig,axes=plt.subplots(1,2,figsize=(9.2,3),layout='constrained')
    for a,pc in zip(axes,['PC1','PC2'],strict=True):
        values=load[pc]
        a.barh([LABELS[v][0].replace(' (%)','') for v in load.variable],values,
               color=[TEAL if v>0 else NAVY for v in values],height=.62)
        a.axvline(0,color=MUTED,lw=1);a.set_xlim(-1,1);a.set_xlabel(f'{pc} loading');axes_style(a)
    finish(fig,'loadings')
    membership=t['cluster_membership'];profiles=t['cluster_profiles_standardized'].set_index('cluster');features=list(load.variable)
    fig,(a,b)=plt.subplots(2,1,figsize=(9.2,5.7),layout='constrained')
    for k,color,marker in [(1,TEAL,'o'),(2,NAVY,'D')]:
        g=membership[membership.cluster.eq(k)]
        a.scatter(g.PC1,g.PC2,c=color,marker=marker,s=27,alpha=.82,edgecolors='white',linewidths=.45,
                  label=f'Profile {k} (N={len(g)})')
        b.scatter(profiles.loc[k,features],np.arange(6)+(k-1.5)*.15,color=color,marker=marker,s=38,
                  edgecolors='white',linewidths=.45,label=f'Profile {k}')
    a.set_xlabel('PC1 · 60.4%');a.set_ylabel('PC2 · 17.8%');a.legend(frameon=False,ncols=2,loc='upper left');axes_style(a,'y')
    b.set_yticks(np.arange(6),[LABELS[v][0].replace(' (%)','') for v in features])
    b.axvline(0,color=MUTED,lw=1,ls=(0,(3,3)));b.set_xlabel('Mean standard deviations from the municipality mean');axes_style(b)
    finish(fig,'profiles')


def _plain_heading(body):
    match=re.search(r'<h2>(.*?)</h2>',body,re.S)
    return re.sub(r'<[^>]+>','',match[1]).strip() if match else ''


def _page_group(index, lang):
    if lang=='en':
        if index==0:return 'Cover'
        if index==1:return 'Executive brief'
        if index<=4:return 'Context & design'
        if index<=13:return 'Results'
        if index==14:return 'Robustness & secondary analyses'
        if index==15:return 'Interpretation'
        if index==16:return 'Limitations & conclusion'
        return 'Sources'
    if index==0:return 'Forside'
    if index==1:return 'Resumé'
    if index<=4:return 'Kontekst & design'
    if index<=13:return 'Resultater'
    if index==14:return 'Robusthed & sekundære analyser'
    if index==15:return 'Fortolkning'
    if index==16:return 'Begrænsninger & konklusion'
    return 'Kilder'


def _section_titles(lang):
    source=(REPORT/f'final_report_{lang}.md').read_text()
    pages=[s.strip() for s in source.split('<!-- page -->') if s.strip()]
    titles=[]
    for index,page in enumerate(pages):
        match=re.search(r'^## (.+)$',page,re.M)
        titles.append(match[1] if match else ('Title page' if lang=='en' else 'Titelblad'))
    return titles


def _set_pdf_metadata(path, lang):
    """Add durable metadata and one navigational bookmark per report section."""
    meta=REPORT_META[lang]
    writer=PdfWriter(path,incremental=True)
    writer.add_metadata({
        '/Title':meta['title'], '/Author':'Frederik Jensen', '/Subject':meta['subject'],
        '/Keywords':meta['keywords'], '/Creator':'Danish Health & Life Expectancy report build',
    })
    for index,title in enumerate(_section_titles(lang)):
        writer.add_outline_item(title,index)
    temporary=path.with_suffix('.metadata.pdf')
    with temporary.open('wb') as stream:writer.write(stream)
    temporary.replace(path)


def publication_html(lang):
    source=(REPORT/f'final_report_{lang}.md').read_text()
    pages=[s.strip() for s in source.split('<!-- page -->') if s.strip()]
    sections=[]
    meta=REPORT_META[lang]
    for i,page in enumerate(pages):
        body=markdown.markdown(page,extensions=['tables','sane_lists'])
        body=re.sub(r'<p><strong>((?:Figure|Figur) \d+\.)',r'<p class="figure-caption"><strong>\1',body)
        def inline_image(match):
            path=(REPORT/match[1]).resolve()
            if not path.is_relative_to(ROOT):raise ValueError('Image outside project')
            return 'src="data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'"'
        body=re.sub(r'src="([^"]+\.png)"',inline_image,body)
        heading=_plain_heading(body)
        page_class='cover' if i==0 else ('summary' if i==1 else 'content')
        if i==0:
            body=(f'<div class="cover-brand"><span class="cover-monogram">DH</span>'
                  f'<span>{meta["strapline"]}</span></div>{body}'
                  '<div class="cover-rule" aria-hidden="true"></div>')
        section_name=_page_group(i,lang)
        accessible=heading or meta['title']
        sections.append(
            f'<article class="sheet {page_class} page-{i+1}" aria-label="{accessible}">'
            f'<header><span class="running-title">{meta["title"]}</span>'
            f'<span class="running-section">{section_name}</span></header>'
            f'<main>{body}</main>'
            f'<footer><span>Frederik Jensen · {meta["report"]} · 2026</span>'
            f'<span class="folio">{i+1:02d} / {len(pages):02d}</span></footer></article>')
    css=(REPORT/'publication.css').read_text()
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
            f'<meta name="author" content="Frederik Jensen"><meta name="description" content="{meta["subject"]}">'
            f'<meta name="color-scheme" content="light"><title>{meta["title"]}</title>'
            f'<style>{css}</style></head><body>'+''.join(sections)+'</body></html>')


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
            pdf=ROOT/name
            page.pdf(path=str(pdf),format='A4',print_background=True,prefer_css_page_size=True,tagged=True,outline=False)
            _set_pdf_metadata(pdf,lang)
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
