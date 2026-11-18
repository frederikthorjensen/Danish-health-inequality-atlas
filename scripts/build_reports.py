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
        'title': 'Danish Health Inequality Atlas',
        'strapline': 'Independent public-health analysis',
        'report': 'Analytical report',
        'subject': 'Geographical inequalities in health and life expectancy across Danish municipalities',
        'keywords': 'Denmark, municipalities, public health, life expectancy, health inequality',
    },
    'da': {
        'title': 'Dansk Atlas over Ulighed i Sundhed',
        'strapline': 'Selvstændig folkesundhedsanalyse',
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


def finish(fig, name, lang):
    destination=REPORT/'figures'/lang
    destination.mkdir(parents=True,exist_ok=True)
    fig.savefig(destination/f'{name}.png',dpi=240,bbox_inches='tight',pad_inches=.16)
    plt.close(fig)


def axes_style(ax, axis='x'):
    ax.set_axisbelow(True)
    ax.grid(axis=axis,color='#E8EEF1',linewidth=.7)
    ax.tick_params(length=0,pad=6)


def publication_figures(t):
    """Create localized displays from saved observations and statistics only."""
    m=t['master'];le=m.dropna(subset=['life_expectancy_total']).sort_values('life_expectancy_total')
    national=json.loads((ROOT/'outputs/tables/life_expectancy_quality.json').read_text())['national_values_years']['life_expectancy_total']
    correlations=t['correlations_total_life_expectancy']
    correlations=correlations[correlations.method.eq('Pearson') & ~correlations.algebraically_related_outcome].sort_values('correlation',key=abs)
    load=t['pca_loadings'];features=list(load.variable)

    for lang,index in [('en',0),('da',1)]:
        H=lambda en,da:en if lang=='en' else da
        label=lambda variable:LABELS[variable][index]
        clean=lambda variable:label(variable).replace(' (%)','').replace(' (persons)','').replace(' (personer)','')

        fig,(a,b)=plt.subplots(1,2,figsize=(9.2,3.0),gridspec_kw={'width_ratios':[1.5,1]},layout='constrained')
        extremes=__import__('pandas').concat([le.head(5),le.tail(5)])
        a.scatter(extremes.life_expectancy_total,extremes.municipality,c=[NAVY]*5+[TEAL]*5,s=36,edgecolors='white',linewidths=.7,zorder=3)
        a.axvline(national,c=MUTED,ls=(0,(3,3)),lw=1,label=f'{H("Denmark","Danmark")} {national:.1f}')
        a.legend(frameon=False,fontsize=8.5,loc='lower right');a.set_xlabel(H('Life expectancy (years)','Middellevetid (år)'));axes_style(a)
        b.hist(le.life_expectancy_total,bins=12,color=NAVY,alpha=.92,edgecolor='white',linewidth=1)
        b.axvline(national,c=TEAL,ls=(0,(3,3)),lw=1.2);b.set_xlabel(H('Life expectancy (years)','Middellevetid (år)'));b.set_ylabel(H('Municipalities','Kommuner'));axes_style(b,'y')
        finish(fig,'variation',lang)

        names=[clean(v) for v in correlations.other_variable];strength=np.abs(correlations.correlation)
        colors=[TEAL if v>0 else (INK if s>=.7 else NAVY) for v,s in zip(correlations.correlation,strength,strict=True)]
        fig,a=plt.subplots(figsize=(9.2,3.7),layout='constrained')
        bars=a.barh(names,correlations.correlation,color=colors,height=.62)
        for bar,value in zip(bars,[1 if s>=.65 else .65 for s in strength],strict=True):bar.set_alpha(value)
        a.axvline(0,color=MUTED,lw=1);a.set_xlim(-1,1);a.set_xlabel(H('Pearson correlation with life expectancy','Pearson-korrelation med middellevetid'));axes_style(a)
        for j,v in enumerate(correlations.correlation):
            a.text(.96 if v>=0 else -.96,j,f'{v:+.3f}',va='center',ha='right' if v>=0 else 'left',fontsize=8.5,color=INK,fontweight=700)
        finish(fig,'correlations',lang)

        fig,axes=plt.subplots(1,2,figsize=(9.2,3.6),layout='constrained')
        for ax,v in zip(axes,['low_education_share_25_64_pct','daily_smoking_pct'],strict=True):
            sample=m[[v,'life_expectancy_total']].dropna();r=correlations.set_index('other_variable').loc[v,'correlation']
            x=np.array([sample[v].min(),sample[v].max()]);y=sample.life_expectancy_total.mean()+r*sample.life_expectancy_total.std(ddof=1)/sample[v].std(ddof=1)*(x-sample[v].mean())
            ax.scatter(sample[v],sample.life_expectancy_total,s=23,color=TEAL,alpha=.72,edgecolors='white',linewidths=.45,zorder=3);ax.plot(x,y,color=INK,lw=1.5)
            ax.set_xlabel(label(v));ax.set_ylabel(H('Life expectancy (years)','Middellevetid (år)'))
            ax.set_title(f'Pearson r = {r:.3f}',loc='left',color=INK);axes_style(ax,'y')
        finish(fig,'associations',lang)

        fits=t['regression_model_fit'];x=np.arange(len(fits));fig,a=plt.subplots(figsize=(9.2,3.2),layout='constrained')
        a.bar(x-.17,fits.R_squared,.34,color='#B9C8CF',label='R²')
        a.bar(x+.17,fits.adjusted_R_squared,.34,color=[NAVY,NAVY,TEAL,TEAL],label=H('Adjusted R²','Justeret R²'))
        for j,r in enumerate(fits.itertuples()):
            a.text(j-.17,r.R_squared+.01,f'{r.R_squared:.3f}',ha='center',fontsize=8.5);a.text(j+.17,r.adjusted_R_squared+.01,f'{r.adjusted_R_squared:.3f}',ha='center',fontsize=8.5)
        a.set_xticks(x,fits.model);a.set_ylim(0,.9);a.legend(frameon=False,ncols=2,loc='upper left')
        a.set_ylabel(H('Proportion of observed variation','Andel af observeret variation'));axes_style(a,'y');finish(fig,'models',lang)

        coefficients=t['regression_coefficients'];coefficients=coefficients[coefficients.model.eq('M4') & coefficients.term.ne('const')].iloc[::-1]
        fig,a=plt.subplots(figsize=(9.2,3.7),layout='constrained')
        estimate=coefficients.standardized_beta
        a.errorbar(estimate,[clean(v) for v in coefficients.term],xerr=[estimate-coefficients.standardized_ci_low,coefficients.standardized_ci_high-estimate],
                   fmt='o',color=INK,ecolor='#7895A3',elinewidth=1.7,capsize=3,markersize=5.5,mfc=TEAL,mec='white',mew=.7,zorder=3)
        a.axvline(0,color=MUTED,lw=1);a.set_xlabel(H('Standardized coefficient (β) · 95% HC3 CI','Standardiseret koefficient (β) · 95% HC3-KI'));axes_style(a)
        finish(fig,'coefficients',lang)

        predictions=t['municipality_predictions_residuals'].dropna(subset=['observed','predicted'])
        fig,a=plt.subplots(figsize=(9.2,3.4),layout='constrained')
        a.scatter(predictions.predicted,predictions.observed,s=26,color=TEAL,alpha=.78,edgecolors='white',linewidths=.5,zorder=3)
        limits=(min(predictions.predicted.min(),predictions.observed.min())-.15,max(predictions.predicted.max(),predictions.observed.max())+.15)
        a.plot(limits,limits,color=MUTED,lw=1,ls=(0,(3,3)));a.set_xlim(limits);a.set_ylim(limits)
        a.set_xlabel(H('Model-predicted life expectancy (years)','Modelberegnet middellevetid (år)'));a.set_ylabel(H('Observed life expectancy (years)','Observeret middellevetid (år)'));axes_style(a)
        finish(fig,'predictions',lang)

        selected=predictions.loc[predictions.residual.abs().sort_values(ascending=False).head(10).index].sort_values('residual')
        fig,a=plt.subplots(figsize=(9.2,3.5),layout='constrained')
        bars=a.barh(selected.municipality,selected.residual,color=[TEAL if value>0 else NAVY for value in selected.residual],height=.62)
        a.axvline(0,color=MUTED,lw=1);a.set_xlabel(H('Observed − predicted life expectancy (years)','Observeret − modelberegnet middellevetid (år)'));axes_style(a)
        for bar,value in zip(bars,selected.residual,strict=True):
            a.text(value+(.035 if value>0 else -.035),bar.get_y()+bar.get_height()/2,f'{value:+.2f}',va='center',ha='left' if value>0 else 'right',fontsize=8.3)
        finish(fig,'residuals',lang)

        variance=t['pca_explained_variance'];fig,a=plt.subplots(figsize=(9.2,3.1),layout='constrained')
        bars=a.bar(variance.component,variance.explained_variance_ratio,color=[NAVY,TEAL,*['#B9C8CF']*(len(variance)-2)],width=.62)
        for bar,value in zip(bars,variance.explained_variance_ratio,strict=True):a.text(bar.get_x()+bar.get_width()/2,value+.012,f'{100*value:.1f}%',ha='center',fontsize=8.5)
        a.set_ylim(0,float(variance.explained_variance_ratio.max())*1.18);a.set_xlabel(H('Principal component','Hovedkomponent'));a.set_ylabel(H('Explained variance','Forklaret variation'));axes_style(a,'y')
        finish(fig,'scree',lang)

        fig,axes=plt.subplots(1,2,figsize=(9.2,3.2),layout='constrained')
        for a,pc in zip(axes,['PC1','PC2'],strict=True):
            values=load[pc];a.barh([clean(v) for v in load.variable],values,color=[TEAL if v>0 else NAVY for v in values],height=.62)
            a.axvline(0,color=MUTED,lw=1);a.set_xlim(-1,1);a.set_xlabel(H(f'{pc} loading',f'{pc}-loading'));axes_style(a)
        finish(fig,'loadings',lang)

        membership=t['cluster_membership'];profiles=t['cluster_profiles_standardized'].set_index('cluster')
        fig,(a,b)=plt.subplots(2,1,figsize=(9.2,5.7),layout='constrained')
        for k,color,marker in [(1,TEAL,'o'),(2,NAVY,'D')]:
            g=membership[membership.cluster.eq(k)];profile=H('Profile','Profil')
            a.scatter(g.PC1,g.PC2,c=color,marker=marker,s=28,alpha=.82,edgecolors='white',linewidths=.45,label=f'{profile} {k} (N={len(g)})')
            b.scatter(profiles.loc[k,features],np.arange(6)+(k-1.5)*.15,color=color,marker=marker,s=40,edgecolors='white',linewidths=.45,label=f'{profile} {k}')
        a.set_xlabel('PC1 · 60.4%');a.set_ylabel('PC2 · 17.8%');a.legend(frameon=False,ncols=2,loc='upper left');axes_style(a,'y')
        b.set_yticks(np.arange(6),[clean(v) for v in features]);b.axvline(0,color=MUTED,lw=1,ls=(0,(3,3)))
        b.set_xlabel(H('Mean standard deviations from the municipality mean','Gennemsnitlige standardafvigelser fra kommunegennemsnittet'));axes_style(b)
        finish(fig,'profiles',lang)


def _plain_heading(body):
    match=re.search(r'<h2>(.*?)</h2>',body,re.S)
    return re.sub(r'<[^>]+>','',match[1]).strip() if match else ''


def _page_group(index, lang):
    if lang=='en':
        if index==0:return 'Cover'
        if index==1:return 'Contents'
        if index==2:return 'Executive brief'
        if index<=5:return 'Context & design'
        if index<=15:return 'Results'
        if index==16:return 'Interpretation'
        if index==17:return 'Limitations & conclusion'
        return 'Sources'
    if index==0:return 'Forside'
    if index==1:return 'Indhold'
    if index==2:return 'Resumé'
    if index<=5:return 'Kontekst & design'
    if index<=15:return 'Resultater'
    if index==16:return 'Fortolkning'
    if index==17:return 'Begrænsninger & konklusion'
    return 'Kilder'


TOC = {
    'en': [
        ('Executive summary', 3), ('1. Background', 4), ('2. Aim and research questions', 4),
        ('3. Data sources and dataset construction', 5), ('4. Analytical methods', 6),
        ('5. Geographical variation in health', 7), ('6. Simple associations with life expectancy', 8),
        ('7. Multivariable models', 9), ('8. Fully adjusted results and collinearity', 11),
        ('9. Expected versus observed life expectancy', 12), ('10. PCA and municipal health profiles', 14),
        ('11. Sex-specific analyses', 16), ('12. Diagnostics and sensitivity', 16), ('13. Discussion', 17),
        ('14. Limitations', 18), ('15. Conclusion', 18), ('References', 19),
    ],
    'da': [
        ('Resumé', 3), ('1. Baggrund', 4), ('2. Formål og undersøgelsesspørgsmål', 4),
        ('3. Datakilder og opbygning af datasæt', 5), ('4. Analytiske metoder', 6),
        ('5. Geografisk variation i sundhed', 7), ('6. Simple sammenhænge med middellevetid', 8),
        ('7. Multivariable modeller', 9), ('8. Fuldt justerede resultater og kollinearitet', 11),
        ('9. Modelberegnet og observeret middellevetid', 12), ('10. PCA og kommunale sundhedsprofiler', 14),
        ('11. Kønsspecifikke analyser', 16), ('12. Diagnostik og følsomhed', 16), ('13. Diskussion', 17),
        ('14. Begrænsninger', 18), ('15. Konklusion', 18), ('Referencer', 19),
    ],
}


def _toc_html(lang):
    title='Contents' if lang=='en' else 'Indholdsfortegnelse'
    intro=('Sections are arranged from research design to results, interpretation and documentation.' if lang=='en'
           else 'Afsnittene følger analysen fra design til resultater, fortolkning og dokumentation.')
    rows=''.join(
        f'<a class="toc-entry" href="#page-{page}"><span>{label}</span><i></i><strong>{page:02d}</strong></a>'
        for label,page in TOC[lang]
    )
    return f'<h2>{title}</h2><p class="toc-intro">{intro}</p><nav class="toc-list" aria-label="{title}">{rows}</nav>'


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
        '/Keywords':meta['keywords'], '/Creator':'Danish Health Inequality Atlas publication build',
    })
    for index,title in enumerate(_section_titles(lang)):
        writer.add_outline_item(title=title, page_number=index)
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
        page_class='cover' if i==0 else ('toc' if i==1 else ('summary' if i==2 else 'content'))
        if i==0:
            body=(f'<div class="cover-brand"><span class="cover-monogram">DHI</span>'
                  f'<span>{meta["strapline"]}</span></div>{body}'
                  '<div class="cover-rule" aria-hidden="true"></div>')
        elif i==1:
            body=_toc_html(lang)
        section_name=_page_group(i,lang)
        accessible=heading or meta['title']
        sections.append(
            f'<article id="page-{i+1}" class="sheet {page_class} page-{i+1}" aria-label="{accessible}">'
            f'<header><span class="running-title">{meta["title"]}</span>'
            f'<span class="running-section">{section_name}</span></header>'
            f'<main>{body}</main>'
            f'<footer><span>Frederik Jensen · {meta["report"]} · Version 2.0</span>'
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
        configured=os.environ.get('REPORT_BROWSER_EXECUTABLE')
        system_chrome=Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
        executable=configured or (str(system_chrome) if system_chrome.exists() else None)
        browser=p.chromium.launch(headless=True,executable_path=executable)
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
