"""Direct comparisons of published municipality observations. No inference or imputation."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard_data import METRICS, LABELS, FEATURES, format_value
from src.dashboard_charts import polish, TEAL, BLUE, MUTED
from textwrap import wrap
from src.dashboard_views import bundle, header
from src.dashboard_layout import chart_explanation, reading_guide

PRESETS = {
    'Key indicators': ['life_expectancy_total','disposable_income_mean_dkk','low_education_share_25_64_pct','daily_smoking_pct'],
    'Life expectancy': list(METRICS)[:4],
    'Health & behaviour': FEATURES,
    'Social conditions': ['disposable_income_mean_dkk','low_education_share_25_64_pct','population','age_0_17_share_pct','age_18_64_share_pct','age_65_plus_share_pct'],
}
COLOURS = [TEAL,'#6D6385',MUTED]
SYMBOLS = ['circle','square','triangle-up']


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
    """Two-place dumbbell, or compact named dot rows; no scale mixing or imputation."""
    d=table.loc[table.variable.eq(variable)]
    reference=d.reference_municipality.iloc[0]
    ref=d.reference_value.iloc[0]
    unit=METRICS[variable][1]
    two=len(d)==2
    observed=d.value.dropna()
    fig=go.Figure()
    for i,row in enumerate(d.itertuples()):
        is_reference=row.municipality==reference
        label="<br>".join(wrap(row.municipality,18,break_long_words=False))
        if is_reference:
            label+="<br>(reference)"
        other_index=0 if is_reference else [n for n in d.municipality if n!=reference].index(row.municipality)
        colour=BLUE if is_reference else COLOURS[other_index]
        if pd.notna(row.value):
            value=format_value(row.value,variable)
            fig.add_trace(go.Scatter(x=[row.value],y=[0 if two else label],name=row.municipality,
                mode='markers' if two else 'markers+text',
                text=None if two else [value],textposition='middle right',cliponaxis=False,
                marker=dict(color=colour,symbol='diamond' if is_reference else SYMBOLS[other_index],size=12,line=dict(color='white',width=1)),
                customdata=[[value,reference,difference_text(row.difference,variable),row.period]],
                hovertemplate=f'<b>{row.municipality}</b><br>{LABELS[variable]}: %{{customdata[0]}}<br>Difference from %{{customdata[1]}}: %{{customdata[2]}}<br>Period: %{{customdata[3]}}<extra></extra>'))
            if two:
                fig.add_annotation(x=row.value,y=0,text=f'{label}<br><b>{value}</b>',showarrow=False,
                    yshift=14 if i==0 else -14,yanchor='bottom' if i==0 else 'top',font=dict(size=12,color=colour))
        else:
            fig.add_annotation(x=.5,xref='paper',y=.9-i*1.8 if two else label,
                text=f'{label}: Not published' if two else 'Not published',showarrow=False,font=dict(size=12,color=MUTED))
    if two and len(observed)==2:
        fig.add_trace(go.Scatter(x=observed.tolist(),y=[0,0],mode='lines',line=dict(color='#9EB0BC',width=3),hoverinfo='skip',showlegend=False))
    elif not two and pd.notna(ref):
        fig.add_vline(x=float(ref),line_color=MUTED,line_dash='dot',line_width=1)
    polish(fig,210 if two else len(d)*60+85,unit,None)
    fig.update_layout(showlegend=False,margin=dict(l=8 if two else 155,r=20,t=20,b=35))
    if len(observed):
        span=max(float(observed.max()-observed.min()),abs(float(observed.mean()))*.02,.1)
        fig.update_xaxes(range=[float(observed.min())-span*.65,float(observed.max())+span*.85],nticks=3,
                         tickformat=',.0f' if unit in ('DKK','people') else '.1f')
    else:
        fig.update_xaxes(visible=False)
    if two:
        fig.update_yaxes(visible=False,range=[-1.2,1.2],fixedrange=True)
    else:
        fig.update_yaxes(type='category',autorange='reversed',showgrid=False)
    return fig


def apply_preset():
    choice=st.session_state.get('comparison_preset')
    if choice in PRESETS:
        st.session_state['comparison_factors']=list(PRESETS[choice])


def compare_municipalities():
    b=bundle()
    header('Places side by side','Compare municipalities','Choose the places and factors that interest you. See published values and the differences from a reference municipality.')
    reading_guide('Select two to four municipalities, then choose up to six indicators. A navy diamond identifies your reference municipality; a dotted line marks its value in comparisons of three or four places. Differences are numerical comparisons, not rankings of health or municipal performance.')
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
        with st.grid(2,min_column_width=440,gap='medium') as grid:
            for variable in variables:
                with grid.cell():
                    with st.container(border=True,height='stretch',key=f'comparison_factor_{variable}',gap='small'):
                        st.subheader(LABELS[variable])
                        st.caption(f'{METRICS[variable][2]} · {METRICS[variable][1]}')
                        # Existing figure wrapper would add a second border inside each comparison card.
                        st.plotly_chart(comparison_figure(table,variable),key=f'comparison_plot_{variable}',theme=None,width='stretch',
                            alt=f'Published {LABELS[variable]} for selected municipalities, with {reference} as the reference',config={'displaylogo':False,'responsive':True})
                        published = table.loc[table.variable.eq(variable)].dropna(subset=['value'])
                        if len(selected)==2 and len(published)==2:
                            other=published.loc[published.municipality.ne(reference)].iloc[0]
                            finding=f'{other.municipality}: {difference_text(other.difference,variable)} relative to {reference}.'
                        elif len(published) > 1:
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
                            f'Published {LABELS[variable].lower()} values for the selected municipalities; the navy diamond identifies {reference} as the reference.',
                            finding,
                            'Each municipality is identified by name, colour and shape. Values use the indicator’s original unit, and each chart has its own scale. The connecting line in a two-place comparison shows the numerical gap; a dotted reference line is used for three or four places. Neither defines a target. Higher or lower values are descriptive and are not automatically better or worse.',
                        )
                        if len(selected)>2:
                            for row in table.loc[table.variable.eq(variable) & table.municipality.ne(reference)].itertuples():
                                st.caption(f'{row.municipality}: {difference_text(row.difference,variable)} vs {reference}')
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
