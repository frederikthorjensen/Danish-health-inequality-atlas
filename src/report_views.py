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
EDITION = {'en': 'English edition', 'da': 'Dansk udgave'}
VERSION = {'en': 'Version 1.1 · 10 November 2026', 'da': 'Version 1.1 · 10. november 2026'}


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
    st.download_button('Download the English PDF' if lang=='en' else 'Download dansk PDF',pdf,
        file_name=PDF_NAMES[lang],mime='application/pdf',key=key,width='stretch',
        icon=':material/download:',on_click='ignore')
    st.caption(f"{record['pages']} pages · PDF · English" if lang=='en' else f"{record['pages']} sider · PDF · Dansk")


def report_home():
    st.caption('BILINGUAL ANALYTICAL PUBLICATION')
    st.title('Danish Health & Life Expectancy')
    st.markdown('### Read the full analytical report')
    st.markdown('A publication-ready account of the data, methods, results and limitations. Choose a language to read online or download the designed PDF.')
    with st.container(horizontal=True,key='report_facts'):
        st.metric('Report sections','18')
        st.metric('Figures','10')
        st.metric('Analytical tables','8')
    with st.grid(2,min_column_width=330,gap='medium') as grid:
        for lang,heading,button in [('en','English report','Read the English report'),('da','Dansk rapport','Læs den danske rapport')]:
            with grid.cell():
                with st.container(border=True,height='stretch',key=f'report_card_{lang}'):
                    st.caption(EDITION[lang].upper())
                    st.subheader(heading)
                    st.markdown(f'**{TITLES[lang]}**')
                    st.markdown(SUBTITLES[lang])
                    st.caption(f'{VERSION[lang]} · 18 sections · 10 figures')
                    st.space('stretch')
                    st.page_link(f'app_pages/report_{lang}.py',label=button,width='stretch',icon=':material/menu_book:')
                    download(lang,f'report_download_{lang}')
    with st.container(border=True,key='report_integrity',gap='small'):
        st.caption('PUBLICATION STANDARD')
        st.markdown('Both editions contain equivalent analytical content and use the same checksum-verified result snapshot. They distinguish descriptive patterns, adjusted associations and exploratory profiles; retain nonsignificant results; and state the methodological cautions alongside the findings.')
        st.page_link('app_pages/methods.py',label='Review methods & limitations',icon=':material/fact_check:')
    with st.expander('Author qualification wording in this publication'):
        st.markdown('The current qualification is **Master of Science (MSc) in Critical Health Studies, Roskilde University, completed 2025**. Version 1.1 of the archived reports retains an earlier English degree wording. The published PDFs and their analytical content have been preserved.')
        st.page_link('app_pages/author.py', label='Read the current author profile')
    st.caption('Frederik Jensen · Independent public-health data analysis and portfolio project · Version 1.1 · 10 November 2026')


def section_title(section, index, lang):
    if index==0:return 'Title page' if lang=='en' else 'Titelblad'
    heading=re.search(r'^## (.+)$',section,re.M)
    return heading[1] if heading else str(index+1)


def navigate_section(key, step, count):
    st.session_state[key]=max(0,min(count-1,st.session_state.get(key,0)+step))


def report_reader(lang):
    record,_,sections,figures=publication(lang)
    english=lang=='en'
    st.caption(EDITION[lang].upper())
    st.title(TITLES[lang])
    st.markdown(SUBTITLES[lang])
    with st.container(horizontal=True):
        st.page_link('app_pages/report.py',label='Report home' if english else 'Rapportoversigt',icon=':material/library_books:')
        st.page_link('app_pages/overview.py',label='Dashboard',icon=':material/dashboard:')
        st.page_link('app_pages/methods.py',label='Methods' if english else 'Metoder',icon=':material/fact_check:')
    with st.container(horizontal=True,vertical_alignment='bottom'):
        with st.container(width=250):download(lang,f'reader_download_{lang}')
        st.caption(f'Frederik Jensen · {VERSION[lang]} · Validated publication snapshot')
    key=f'report_section_{lang}'
    index=st.selectbox('Go to report section' if english else 'Gå til rapportafsnit',range(len(sections)),
        format_func=lambda n: section_title(sections[n],n,lang),key=key)
    st.progress((index+1)/len(sections),text=(f'Section {index+1} of {len(sections)}' if english else f'Afsnit {index+1} af {len(sections)}'))
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
    previous_title=section_title(sections[index-1],index-1,lang) if index else ''
    next_title=section_title(sections[index+1],index+1,lang) if index+1<len(sections) else ''
    with st.container(horizontal=True,key='report_reader_navigation'):
        st.button((f'Previous: {previous_title}' if english else f'Forrige: {previous_title}') if previous_title else
                  ('Previous section' if english else 'Forrige afsnit'),key=f'report_previous_{lang}',disabled=index==0,
                  on_click=navigate_section,args=(key,-1,len(sections)),icon=':material/arrow_back:',width='stretch')
        st.button((f'Next: {next_title}' if english else f'Næste: {next_title}') if next_title else
                  ('Next section' if english else 'Næste afsnit'),key=f'report_next_{lang}',disabled=index==len(sections)-1,
                  on_click=navigate_section,args=(key,1,len(sections)),icon_position='right',icon=':material/arrow_forward:',width='stretch')
