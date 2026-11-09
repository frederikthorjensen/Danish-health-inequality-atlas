"""Native, separate-language readers for the prebuilt analytical publications."""
from pathlib import Path
import json
import re

import streamlit as st

from src.reporting import ROOT, REPORT, PDF_NAMES, sha

TITLES = {'en': 'Danish Health & Life Expectancy', 'da': 'Sundhed og middellevetid i Danmark'}
SUBTITLES = {
    'en': 'Geographical differences in health, socioeconomic conditions and life expectancy across Danish municipalities',
    'da': 'Geografiske forskelle i sundhed, socioøkonomiske forhold og middellevetid på tværs af danske kommuner',
}


def publication(lang):
    """Read-only delivery: PDFs and Markdown must match the publication record."""
    if lang not in PDF_NAMES:
        raise ValueError('Unknown report language')
    manifest = json.loads((REPORT/'publication_manifest.json').read_text())
    record = next(r for r in manifest['reports'] if r['language']==lang)
    source = REPORT/f'final_report_{lang}.md'
    pdf = ROOT/PDF_NAMES[lang]
    if sha(source)!=record['markdown_sha256'] or sha(pdf)!=record['sha256']:
        raise ValueError('Report files do not match the checked publication build.')
    if sha(ROOT/'outputs/tables/analysis_manifest.json')!=manifest['analysis_manifest_sha256']:
        raise ValueError('Report and analysis snapshots differ.')
    sections = [s.strip() for s in source.read_text().split('<!-- page -->') if s.strip()]
    return record, pdf.read_bytes(), sections, manifest['figure_sources']


def download(lang, key):
    record,pdf,_,_=publication(lang)
    st.download_button('Download PDF' if lang=='en' else 'Download PDF',pdf,
        file_name=PDF_NAMES[lang],mime='application/pdf',key=key,width='stretch')
    st.caption(f"{record['pages']} pages · PDF · English" if lang=='en' else f"{record['pages']} sider · PDF · Dansk")


def report_home():
    st.caption('ANALYTICAL REPORT')
    st.title('Danish Health & Life Expectancy')
    st.markdown('A complete analytical report is available in English and Danish. Both versions contain the same validated analyses, figures and methodological discussion.')
    with st.grid(2,min_column_width=330,gap='medium') as grid:
        for lang,heading,button in [('en','English Report','View English Report'),('da','Dansk rapport','Åbn dansk rapport')]:
            with grid.cell():
                with st.container(border=True,height='stretch',key=f'report_card_{lang}'):
                    st.caption('ENGLISH' if lang=='en' else 'DANSK')
                    st.subheader(heading)
                    st.markdown(f'**{TITLES[lang]}**')
                    st.markdown(SUBTITLES[lang])
                    st.caption('Language: English' if lang=='en' else 'Sprog: Dansk')
                    st.space('stretch')
                    st.page_link(f'app_pages/report_{lang}.py',label=button,width='stretch')
                    download(lang,f'report_download_{lang}')
    st.caption('Frederik Jensen · Independent public-health data analysis and portfolio project · Version 1.0 · 6 November 2026')
    with st.expander('About these publications'):
        st.markdown('The reports distinguish descriptive patterns, adjusted associations and exploratory profiles. They include nonsignificant results and methodological cautions. The publications use the preserved analysis snapshot; no models are fitted when you open a report.')
        st.page_link('app_pages/methods.py',label='Methods & limitations')


def section_title(section, index, lang):
    if index==0:return 'Title page' if lang=='en' else 'Titelblad'
    heading=re.search(r'^## (.+)$',section,re.M)
    return heading[1] if heading else str(index+1)


def navigate_section(key, step, count):
    st.session_state[key]=max(0,min(count-1,st.session_state.get(key,0)+step))


def report_reader(lang):
    record,_,sections,figures=publication(lang)
    english=lang=='en'
    st.caption('ENGLISH REPORT' if english else 'DANSK RAPPORT')
    st.title(TITLES[lang])
    with st.container(horizontal=True):
        st.page_link('app_pages/report.py',label='Report home' if english else 'Rapportoversigt')
        st.page_link('app_pages/overview.py',label='Dashboard')
        st.page_link('app_pages/methods.py',label='Methods' if english else 'Metoder')
    with st.container(horizontal=True,vertical_alignment='bottom'):
        with st.container(width=250):download(lang,f'reader_download_{lang}')
        st.caption('Frederik Jensen · Version 1.0 · 6 November 2026' if english else 'Frederik Jensen · Version 1.0 · 6. november 2026')
    key=f'report_section_{lang}'
    index=st.selectbox('Report section' if english else 'Rapportafsnit',range(len(sections)),
        format_func=lambda n: section_title(sections[n],n,lang),key=key)
    with st.container(key='report_reader',width=850):
        for part in re.split(r'(!\[[^\]]*\]\([^)]+\))',sections[index]):
            match=re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)',part)
            if match:
                path=(REPORT/match[2]).resolve()
                if not path.is_relative_to(ROOT) or sha(path)!=figures[match[2]]:
                    raise ValueError('Report figure differs from the publication record.')
                st.image(str(path),alt=match[1],width='stretch')
            elif part.strip():
                # The app already supplies the document title; avoid duplicate title anchors.
                text=part.strip()
                if index==0:
                    text=re.sub(r'^# .+$','',text,flags=re.M)
                    text=re.sub(r'^### (.+)$',r'## \1',text,flags=re.M)
                st.markdown(text)
    with st.container(horizontal=True):
        st.button('Previous section' if english else 'Forrige afsnit',key=f'report_previous_{lang}',disabled=index==0,
                  on_click=navigate_section,args=(key,-1,len(sections)))
        st.caption(f'{index+1} / {len(sections)}')
        st.button('Next section' if english else 'Næste afsnit',key=f'report_next_{lang}',disabled=index==len(sections)-1,
                  on_click=navigate_section,args=(key,1,len(sections)))
