"""Direct comparisons of published municipality observations. No inference or imputation."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard_data import METRICS, LABELS, FEATURES, format_difference, format_value, semantic_badge_colour, semantic_state
from src.dashboard_charts import polish, TEAL, BLUE, MUTED, NEUTRAL_LINE, REFERENCE_LINE, MARKER_SIZE
from src.dashboard_views import bundle, header
from src.dashboard_layout import reading_guide

PRESETS = {
    'Key indicators': ['life_expectancy_total','disposable_income_mean_dkk','low_education_share_25_64_pct','daily_smoking_pct'],
    'Life expectancy': list(METRICS)[:4],
    'Health & behaviour': FEATURES,
    'Social conditions': ['disposable_income_mean_dkk','low_education_share_25_64_pct','population','age_0_17_share_pct','age_18_64_share_pct','age_65_plus_share_pct'],
}
COLOURS = [TEAL,BLUE,'#6D6385',MUTED]


def comparison_table(master, names, variables, reference):
    """Preserve every selected observation; subtract only when both are published."""
    if len(set(names))!=len(names) or len(set(variables))!=len(variables):
        raise ValueError('Duplicate comparison selections')
    indexed=master.set_index('municipality')
    if reference not in names or any(n not in indexed.index for n in names):
        raise ValueError('Select known municipalities and a reference from that selection')
    if any(v not in METRICS for v in variables):
        raise ValueError('Unknown indicator')
    rows=[]
    for variable in variables:
        ref=indexed.loc[reference,variable]
        for name in names:
            value=indexed.loc[name,variable]
            difference=value-ref if pd.notna(value) and pd.notna(ref) else np.nan
            label,unit,period=METRICS[variable]
            rows.append({'municipality':name,'indicator':label,'variable':variable,'value':value,
                'unit':unit,'period':period,'reference_municipality':reference,'reference_value':ref,
                'difference':difference,'difference_unit':'pp' if unit=='%' else unit,
                'status':'Published' if pd.notna(value) else 'Not published'})
    return pd.DataFrame(rows)


def difference_text(value, variable):
    return format_difference(value,variable)


def comparison_figure(table, variable):
    """Vertical comparison: category positions on x and published values on y."""
    d=table.loc[table.variable.eq(variable)]
    reference=d.reference_municipality.iloc[0]
    ref=d.reference_value.iloc[0]
    fig=go.Figure()
    unit=METRICS[variable][1]
    published=d.dropna(subset=['value'])
    if len(d)==2 and len(published)==2:
        fig.add_trace(go.Scatter(x=published.municipality,y=published.value,mode='lines',
            line=dict(color=NEUTRAL_LINE,width=2),hoverinfo='skip',showlegend=False))
    for i,row in enumerate(d.itertuples()):
        if pd.notna(row.value):
            is_reference=row.municipality==reference
            fig.add_trace(go.Scatter(x=[row.municipality],y=[row.value],mode='markers+text',showlegend=False,
                marker=dict(color=TEAL if is_reference else COLOURS[(i+1)%4],
                            symbol='diamond' if is_reference else 'circle',size=MARKER_SIZE+2 if is_reference else MARKER_SIZE,
                            line=dict(color='white',width=1.5)),
                text=[format_value(row.value,variable)],textposition='top center',
                cliponaxis=False,
                customdata=[[format_value(row.value,variable),reference,difference_text(row.difference,variable),row.period]],
                hovertemplate=f'<b>{row.municipality}</b><br>{LABELS[variable]}: %{{customdata[0]}}<br>Difference from %{{customdata[1]}}: %{{customdata[2]}}<br>Period: %{{customdata[3]}}<extra></extra>'))
        else:
            fig.add_annotation(x=row.municipality,xref='x',y=.5,yref='paper',text='Not published',showarrow=False,
                               font=dict(size=12,color=MUTED))
    observed=d.value.dropna()
    if len(observed):
        span=max(float(observed.max()-observed.min()),abs(float(observed.mean()))*.035,.1)
        lower=float(observed.min())-span*.30
        upper=float(observed.max())+span*.38
        if variable!='life_expectancy_sex_gap': lower=max(0,lower)
        fig.update_yaxes(range=[lower,upper])
    else:
        fig.update_yaxes(visible=False)
    polish(fig,300,None,f'{LABELS[variable]} ({unit})')
    fig.update_layout(showlegend=False,margin=dict(l=72,r=28,t=42,b=68))
    fig.update_xaxes(type='category',categoryorder='array',categoryarray=d.municipality.tolist(),showgrid=False,
                     tickfont=dict(size=12,color=MUTED),tickangle=0)
    fig.update_yaxes(nticks=4,tickformat=',.0f' if unit in ('DKK','people') else '.1f',gridcolor='rgba(167,184,193,.22)')
    if pd.notna(ref):
        fig.add_annotation(x=reference,xref='x',y=1.02,yref='paper',text='Reference',showarrow=False,
                           yanchor='bottom',font=dict(size=10,color=REFERENCE_LINE))
    return fig


def apply_preset():
    choice=st.session_state.get('comparison_preset')
    if choice in PRESETS:
        st.session_state['comparison_factors']=list(PRESETS[choice])


def compare_municipalities():
    b=bundle()
    header('Places side by side','Compare municipalities','Choose the places and factors that interest you. See published values and the differences from a reference municipality.')
    reading_guide('Select two to four municipalities, then choose up to six indicators. The dotted line marks your reference municipality. Differences are numerical comparisons, not rankings of health or municipal performance.')
    names=sorted(b['master'].municipality.tolist())
    with st.container(border=True,key='comparison_controls',gap='medium'):
        if 'comparison_municipalities' not in st.session_state:
            st.session_state['comparison_municipalities']=['København','Aarhus']
        selected=st.multiselect('Municipalities',names,max_selections=4,key='comparison_municipalities',
            help='Search by name. Select two to four places; remove a name using its × control.')
        st.segmented_control('Start with an indicator group',list(PRESETS),default='Key indicators',key='comparison_preset',on_change=apply_preset)
        if 'comparison_factors' not in st.session_state:
            st.session_state['comparison_factors']=list(PRESETS['Key indicators'])
        variables=st.multiselect('Indicators to compare',list(METRICS),format_func=lambda v:LABELS[v],max_selections=6,key='comparison_factors',
            help='A group provides a starting selection. Add or remove individual indicators to customize your comparison.')
    if len(selected)<2:
        st.info('Select at least two municipalities to start comparing. You can include up to four.')
        return
    if not variables:
        st.info('Choose at least one indicator, or select an indicator group above.')
        return
    if st.session_state.get('comparison_reference') not in selected:
        st.session_state['comparison_reference']=selected[0]
    with st.container(horizontal=True,gap='medium',vertical_alignment='bottom'):
        with st.container(width=300):
            reference=st.selectbox('Reference municipality',selected,key='comparison_reference',help='Differences are each selected municipality minus this reference. Changing it does not change the published values.')
        view=st.segmented_control('Display',['Charts','Table'],default='Charts',key='comparison_display')
    table=comparison_table(b['master'],selected,variables,reference)
    st.caption(f'{len(selected)} municipalities · {len(variables)} indicators · Differences relative to {reference}')
    missing=table.loc[table.value.isna(),['municipality','indicator']]
    if not missing.empty:
        st.info('Some selected estimates are not published: '+ '; '.join(f'{r.municipality} — {r.indicator}' for r in missing.itertuples())+'. These remain missing; no values or differences are imputed.')
    if view!='Table':
        with st.grid(2,min_column_width=420,gap='medium') as grid:
            for variable in variables:
                with grid.cell():
                    with st.container(border=True,height='stretch',key=f'comparison_factor_{variable}',gap='small'):
                        st.subheader(LABELS[variable])
                        st.caption(f'{METRICS[variable][2]} · {METRICS[variable][1]}')
                        # Existing figure wrapper would add a second border inside each comparison card.
                        st.plotly_chart(comparison_figure(table,variable),key=f'comparison_plot_{variable}',theme=None,width='stretch',
                            alt=f'Published {LABELS[variable]} for selected municipalities, with {reference} as the reference',config={'displaylogo':False,'responsive':True})
                        for row in table.loc[table.variable.eq(variable) & table.municipality.ne(reference)].itertuples():
                            with st.container(horizontal=True,gap='small',vertical_alignment='center',key=f'comparison_delta_{variable}_{row.municipality}'):
                                st.markdown(f'**{row.municipality}**')
                                st.badge(f'{difference_text(row.difference,variable)} vs {reference}',
                                    color=semantic_badge_colour(variable,row.difference),
                                    help=f'{semantic_state(variable,row.difference).capitalize()} benchmark difference. The signed value is {row.municipality} minus {reference}.')
                        if table.loc[table.variable.eq(variable),'reference_value'].isna().all():
                            st.caption('Reference estimate not published. The other published values are shown, but differences cannot be calculated.')
        with st.expander('How to interpret these comparisons',key='comparison_interpretation',icon=':material/read_more:'):
            st.markdown(
                'Each indicator uses its own original-unit scale, so distances should only be compared within a chart. '
                'For percentage indicators, differences are **percentage points**, not relative percentages. '
                f'The dotted line consistently marks **{reference}**, the selected reference municipality. '
                'Higher or lower values do not automatically mean better or worse outcomes; all comparisons are descriptive and no overall score is calculated.'
            )
    else:
        # Format strings only for presentation; the download below preserves numeric precision.
        rows=[]
        for variable in variables:
            d=table.loc[table.variable.eq(variable)].set_index('municipality')
            row={'Indicator':LABELS[variable],'Period':METRICS[variable][2]}
            for name in selected:
                row[name]=format_value(d.loc[name,'value'],variable)
                if name!=reference:row[f'{name} − {reference}']=difference_text(d.loc[name,'difference'],variable)
            rows.append(row)
        st.dataframe(pd.DataFrame(rows),hide_index=True,column_config={'Indicator':st.column_config.TextColumn(width=260,pinned=True),'Period':st.column_config.TextColumn(width=150)},
            alt='Exact published values and numerical differences for the selected municipalities and indicators')
        st.caption('The indicator column remains visible when scrolling. A difference is unavailable if either source value is missing.')
    with st.container(key='comparison_notes',gap='small'):
        st.download_button('Download this comparison',table.to_csv(index=False),file_name='atlas-municipality-comparison.csv',mime='text/csv',key='comparison_download')
        st.page_link('app_pages/explorer.py',label='Open the single-municipality explorer')
