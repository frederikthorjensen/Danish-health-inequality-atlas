"""Direct comparisons of published municipality observations. No inference or imputation."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard_data import METRICS, LABELS, FEATURES, format_value
from src.dashboard_charts import polish, TEAL, BLUE, MUTED
from src.dashboard_views import bundle, header
from src.dashboard_layout import chart_explanation, reading_guide

PRESETS = {
    'Key indicators': ['life_expectancy_total','disposable_income_mean_dkk','low_education_share_25_64_pct','daily_smoking_pct'],
    'Life expectancy': list(METRICS)[:4],
    'Health & behaviour': FEATURES,
    'Social conditions': ['disposable_income_mean_dkk','low_education_share_25_64_pct','population','age_0_17_share_pct','age_18_64_share_pct','age_65_plus_share_pct'],
}
COLOURS = [TEAL,BLUE,'#6D6385',MUTED]
SYMBOLS = ['circle','diamond','square','triangle-up']


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
    if pd.isna(value):
        return 'Difference unavailable'
    unit=METRICS[variable][1]
    decimals=0 if unit in ('DKK','people') else 1
    suffix='pp' if unit=='%' else unit
    displayed=round(float(value),decimals)
    if displayed==0:displayed=0.0
    return f'{displayed:+,.{decimals}f} {suffix}'


def comparison_figure(table, variable):
    """Original-unit dot plot; name, shape and colour all identify the municipality."""
    d=table.loc[table.variable.eq(variable)]
    reference=d.reference_municipality.iloc[0]
    ref=d.reference_value.iloc[0]
    fig=go.Figure()
    unit=METRICS[variable][1]
    for i,row in enumerate(d.itertuples()):
        if pd.notna(row.value):
            fig.add_trace(go.Scatter(x=[row.value],y=[row.municipality],name=row.municipality,mode='markers',
                marker=dict(color=COLOURS[i%4],symbol=SYMBOLS[i%4],size=12,line=dict(color='white',width=1)),
                customdata=[[format_value(row.value,variable),reference,difference_text(row.difference,variable),row.period]],
                hovertemplate=f'<b>{row.municipality}</b><br>{LABELS[variable]}: %{{customdata[0]}}<br>Difference from %{{customdata[1]}}: %{{customdata[2]}}<br>Period: %{{customdata[3]}}<extra></extra>'))
        value='Not published' if pd.isna(row.value) else f'{row.value:,.0f}' if unit in ('DKK','people') else f'{row.value:.1f}'
        fig.add_annotation(x=1.03,xref='paper',y=row.municipality,yref='y',text=value,showarrow=False,xanchor='left',font=dict(size=12,color=MUTED))
    if pd.notna(ref):
        fig.add_vline(x=float(ref),line_color=MUTED,line_dash='dot',line_width=1)
    observed=d.value.dropna()
    if len(observed):
        span=max(float(observed.max()-observed.min()),abs(float(observed.mean()))*.02,.1)
        lower=float(observed.min())-span*.22
        if variable!='life_expectancy_sex_gap':lower=max(0,lower)
        fig.update_xaxes(range=[lower,float(observed.max())+span*.22])
    else:
        fig.update_xaxes(visible=False)
    polish(fig,max(240,len(d)*42+100),f'{LABELS[variable]} ({unit})',None)
    fig.update_layout(showlegend=False,margin=dict(r=95))
    fig.update_yaxes(type='category',categoryorder='array',categoryarray=d.municipality.tolist(),autorange='reversed',showgrid=False)
    fig.update_xaxes(nticks=3,tickformat=',.0f' if unit in ('DKK','people') else '.1f')
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
                        published = table.loc[table.variable.eq(variable)].dropna(subset=['value'])
                        if len(published) > 1:
                            high = published.loc[published.value.idxmax()]
                            low = published.loc[published.value.idxmin()]
                            finding = (f'Among the selected municipalities, {high.municipality} has the highest published value '
                                       f'({format_value(high.value, variable)}) and {low.municipality} the lowest '
                                       f'({format_value(low.value, variable)}).')
                        elif len(published) == 1:
                            only = published.iloc[0]
                            finding = f'Only {only.municipality} has a published value in this selection: {format_value(only.value, variable)}.'
                        else:
                            finding = 'No selected municipality has a published value for this indicator.'
                        chart_explanation(
                            f'comparison_{variable}',
                            f'Published {LABELS[variable].lower()} values for the selected municipalities; the dotted line marks {reference}.',
                            finding,
                            'Each municipality is identified by name, colour and shape. Values use the indicator’s original unit, and each chart has its own scale. The dotted reference line supports direct numerical comparison; it does not define a target. Higher or lower values are descriptive and are not automatically better or worse.',
                        )
                        for row in table.loc[table.variable.eq(variable) & table.municipality.ne(reference)].itertuples():
                            st.markdown(f'**{row.municipality}** · {difference_text(row.difference,variable)} vs {reference}')
                        if table.loc[table.variable.eq(variable),'reference_value'].isna().all():
                            st.caption('Reference estimate not published. The other published values are shown, but differences cannot be calculated.')
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
        st.caption('Each chart uses its own original-unit axis; scales differ between indicators. Percentage differences are percentage points (pp), not relative percentages. Higher or lower does not automatically mean better or worse. No overall health score is created.')
        st.download_button('Download this comparison',table.to_csv(index=False),file_name='atlas-municipality-comparison.csv',mime='text/csv',key='comparison_download')
        st.page_link('app_pages/explorer.py',label='Open the single-municipality explorer')
