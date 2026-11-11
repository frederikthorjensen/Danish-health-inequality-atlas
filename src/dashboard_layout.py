"""Shared report-style presentation and navigation; no analytical calculations."""
import streamlit as st


def reading_guide(text):
    with st.container(key='page_reading_guide',gap='xsmall'):
        st.caption('HOW TO USE THIS PAGE')
        st.markdown(text)


def section_heading(number, title, description=None):
    with st.container(key=f'section_{number}',gap='xsmall'):
        st.caption(f'SECTION {number}')
        st.subheader(title)
        if description:
            st.markdown(description)


def chart_explanation(key, shows, finding, detail):
    """Add a consistent, concise reading guide beneath an analytical figure."""
    with st.container(key=f'chart_story_{key}', gap='xsmall'):
        st.caption('CHART GUIDE')
        st.markdown(f'**What it shows** — {shows}')
        st.markdown(f'**Key finding** — {finding}')
        show_detail = st.toggle(
            'Show detailed explanation',
            key=f'chart_detail_{key}',
            help='Open or close the methodological and interpretive explanation for this chart.',
        )
        if show_detail:
            with st.container(key=f'chart_detail_body_{key}', gap='xsmall'):
                st.markdown(detail)


def reading_navigation(pages, current):
    """Every page has an explicit next step, including when the sidebar is collapsed."""
    index=next((i for i,p in enumerate(pages) if p.url_path==current.url_path),None)
    if index is None:
        return  # Separate-language document readers supply their own navigation.
    with st.container(key='reading_navigation',gap='small'):
        st.caption(f'REPORT NAVIGATION · {index+1:02d} / {len(pages):02d}')
        with st.grid(2,min_column_width=240,gap='medium') as grid:
            if index>0:
                with grid.cell():
                    with st.container(border=True,key='reading_previous',gap='xsmall'):
                        st.caption('PREVIOUS')
                        st.page_link(pages[index-1],width='stretch')
            if index+1<len(pages):
                with grid.cell():
                    with st.container(border=True,key='reading_next',gap='xsmall'):
                        st.caption('NEXT')
                        st.page_link(pages[index+1],width='stretch')
            else:
                with grid.cell():
                    with st.container(border=True,key='reading_next',gap='xsmall'):
                        st.caption('RETURN TO THE SUMMARY')
                        st.page_link(pages[1],width='stretch')
