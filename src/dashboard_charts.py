"""Plotly presentation of saved statistics; contains no model-fitting code."""

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path
from textwrap import wrap

from src.dashboard_data import LABELS, METRICS, association_line

TOKENS = json.loads((Path(__file__).resolve().parents[1] / "assets/design_tokens.json").read_text())
TEAL, BLUE, MUTED = TOKENS["accent"], TOKENS["secondary"], TOKENS["muted"]
PALETTE = [TEAL, BLUE, "#7895A3", "#B1C4CC"]
CHART_LABELS = {**LABELS, "low_education_share_25_64_pct": "Primary education (25–64)",
    "less_good_or_poor_self_rated_health_pct": "Less-good/poor health",
    "physical_inactivity_pct": "Insufficient activity", "poor_mental_health_pct": "Poor mental health",
    "education_unknown_share_25_64_pct": "Unknown education (25–64)",
    "life_expectancy_total": "Life expectancy", "life_expectancy_male": "Male life expectancy",
    "life_expectancy_female": "Female life expectancy", "life_expectancy_sex_gap": "Female–male gap"}


def polish(fig, height=420, x=None, y=None):
    if isinstance(x,str) and len(x)>28:
        x="<br>".join(wrap(x,28,break_long_words=False))
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=12, r=28, t=28, b=28),
        font=dict(family=TOKENS["font"], size=13, color=TOKENS["text"]),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        colorway=PALETTE, legend_title_text="", legend=dict(orientation="h", y=1.14, x=0,font=dict(size=12)),
        hoverlabel=dict(bgcolor="white", bordercolor=TOKENS["border"], font=dict(family=TOKENS["font"],size=13,color=TOKENS["text"])),
        hovermode="closest")
    fig.update_xaxes(title=x,gridcolor=TOKENS["grid"],gridwidth=1,zeroline=False,showline=False,automargin=True,
                     tickfont=dict(size=12,color=TOKENS["muted"]),title_font=dict(size=12,color=TOKENS["muted"]))
    fig.update_yaxes(title=y,gridcolor=TOKENS["grid"],gridwidth=1,zeroline=False,showline=False,automargin=True,
                     tickfont=dict(size=12,color=TOKENS["muted"]),title_font=dict(size=12,color=TOKENS["muted"]))
    return fig


def value_column(fig, labels, values, decimals=3):
    """Align signed values in a separate gutter so mobile labels never collide."""
    for label,value in zip(labels,values,strict=True):
        fig.add_annotation(x=1.03,xref="paper",y=label,yref="y",text=f"{value:+.{decimals}f}",
            showarrow=False,xanchor="left",font=dict(size=12,color=TOKENS["text"]))
    fig.update_layout(margin=dict(r=68))
    return fig


def correlation_bars(table, limit=6):
    d = table.head(limit).sort_values("correlation", key=abs, ascending=False)
    fig = go.Figure(go.Bar(x=d.correlation, y=d.other_variable.map(CHART_LABELS), orientation="h",
        marker=dict(color=[TEAL if v > 0 else BLUE for v in d.correlation], opacity=[1 if i < 2 else .64 for i in range(len(d))]),
        customdata=np.column_stack([d.N, d.p_value, d.q_value_BH_all_pairs]),
        hovertemplate="%{y}<br>Correlation: %{x:.3f}<br>N=%{customdata[0]}<br>p=%{customdata[1]:.3g}<br>BH q=%{customdata[2]:.3g}<extra></extra>"))
    fig.update_xaxes(range=[-1, 1], dtick=.5)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.add_vline(x=0, line_color=MUTED, line_width=1)
    polish(fig, max(340, len(d)*34), "Correlation with total life expectancy", None)
    return value_column(fig,d.other_variable.map(CHART_LABELS),d.correlation)


def ranked(data, variable, selection):
    d = data.dropna(subset=[variable]).sort_values(variable)
    if selection == "Lowest 20":
        d = d.head(20)
    elif selection == "Highest 20":
        d = d.tail(20)
    fig = go.Figure(go.Scatter(x=d[variable], y=d.municipality, mode="markers", marker=dict(color=TEAL, size=9),
        hovertemplate=f"<b>%{{y}}</b><br>{LABELS[variable]}: %{{x:,.1f}} {METRICS[variable][1]}<extra></extra>"))
    all_values = data[variable].dropna()
    padding = max((all_values.max() - all_values.min()) * .08, .1)
    fig.update_xaxes(range=[all_values.min()-padding, all_values.max()+padding])
    return polish(fig, max(440, min(1600, len(d)*21)), f"{LABELS[variable]} ({METRICS[variable][1]})", None)


def distribution(data, variable):
    fig = px.histogram(data.dropna(subset=[variable]), x=variable, nbins=18, color_discrete_sequence=[TEAL], labels={variable: LABELS[variable]})
    fig.update_traces(marker_line_color="white", marker_line_width=1)
    return polish(fig, 380, f"{LABELS[variable]} ({METRICS[variable][1]})", "Municipalities")


def heatmap(matrix):
    labels = [CHART_LABELS.get(c, c) for c in matrix.columns]
    numbers = list(range(1, len(labels)+1))
    full = [[[labels[j], labels[i]] for j in range(len(labels))] for i in range(len(labels))]
    fig = go.Figure(go.Heatmap(z=matrix.to_numpy(), x=numbers, y=[f"{i+1}. {label}" for i,label in enumerate(labels)], customdata=full,
        colorscale=[[0, BLUE], [.5, "#F4F7F8"], [1, TEAL]], zmin=-1, zmax=1,
        colorbar=dict(title="Pearson r", orientation="h", len=.6, thickness=10, y=-.16),
        hovertemplate="%{customdata[0]}<br>%{customdata[1]}<br>Pearson r=%{z:.3f}<extra></extra>"))
    fig.update_xaxes(tickangle=0, dtick=2)
    fig.update_yaxes(autorange="reversed")
    return polish(fig, 620)


def association_scatter(bundle, variable):
    d = bundle["master"].dropna(subset=[variable, "life_expectancy_total"])
    fig = go.Figure(go.Scatter(x=d[variable], y=d.life_expectancy_total, mode="markers", customdata=d.municipality,
        marker=dict(color=TEAL,size=9,opacity=.78,line=dict(color="white",width=.8)), showlegend=False,
        hovertemplate=f"<b>%{{customdata}}</b><br>{LABELS[variable]}: %{{x:,.1f}} {METRICS.get(variable, ('', '', ''))[1]}<br>Life expectancy: %{{y:.1f}} years<extra></extra>"))
    x, y = association_line(bundle, variable)
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color=BLUE, width=1.5), name="Descriptive linear guide", hoverinfo="skip", showlegend=False))
    return polish(fig, 440, LABELS[variable], "Life expectancy (years)")


def coefficients(table, mode):
    d = table.loc[table.model.eq("M4") & table.term.ne("const")].iloc[::-1]
    standardized = mode == "Standardized beta"
    estimate, low, high = ("standardized_beta", "standardized_ci_low", "standardized_ci_high") if standardized else ("coefficient", "ci_low", "ci_high")
    fig = go.Figure(go.Scatter(x=d[estimate], y=d.term.map(CHART_LABELS), mode="markers",
        marker=dict(color=[TEAL if v > 0 else BLUE for v in d[estimate]], size=9, line=dict(color="white",width=1)),
        text=[f"{v:+.2f}" for v in d[estimate]], textposition="top center",
        error_x=dict(type="data", array=d[high]-d[estimate], arrayminus=d[estimate]-d[low], color="#9EB0BC", thickness=1.4,width=3),
        customdata=np.column_stack([d.robust_p_value, d.q_value_family_BH, d[low], d[high]]),
        hovertemplate="%{y}<br>Estimate=%{x:.3f}<br>95% CI [%{customdata[2]:.3f}, %{customdata[3]:.3f}]<br>HC3 p=%{customdata[0]:.3g}<br>Primary-family q=%{customdata[1]:.3g}<extra></extra>"))
    fig.add_vline(x=0, line_color=MUTED, line_width=1)
    fig.update_yaxes(showgrid=False)
    return polish(fig, 480, "Standardized beta · 95% HC3 CI" if standardized else "Years per unit · 95% HC3 CI", None)


def prediction_scatter(predictions, highlight=None):
    d = predictions.dropna(subset=["observed", "predicted"])
    hover = "<b>%{customdata[0]}</b><br>Model-predicted life expectancy: %{x:.2f} years<br>Observed life expectancy: %{y:.1f} years<br>Residual: %{customdata[1]:+.2f} years<extra></extra>"
    fig = go.Figure(go.Scatter(x=d.predicted, y=d.observed, mode="markers", customdata=np.column_stack([d.municipality,d.residual]),
        marker=dict(color=TEAL,size=9,opacity=.75,line=dict(color="white",width=.8)),hovertemplate=hover,showlegend=False))
    bounds = [min(d.observed.min(), d.predicted.min())-.2, max(d.observed.max(), d.predicted.max())+.2]
    fig.add_trace(go.Scatter(x=bounds, y=bounds, mode="lines", line=dict(color="#9EB0BC", width=1,dash="dash"), name="Observed = predicted", hoverinfo="skip",showlegend=False))
    fig.update_xaxes(range=bounds)
    fig.update_yaxes(range=bounds)
    if highlight:
        row = d.loc[d.municipality.eq(highlight)]
        if not row.empty:
            fig.add_trace(go.Scatter(x=row.predicted, y=row.observed, text=row.municipality, mode="markers+text", textposition="top center",
                customdata=np.column_stack([row.municipality,row.residual]),marker=dict(color=BLUE, symbol="diamond",size=14,line=dict(color="white",width=1.5)), hovertemplate=hover,showlegend=False))
    return polish(fig, 420, "Model 3 fitted life expectancy (years)", "Observed life expectancy (years)")


def residual_ranking(predictions):
    d = predictions.dropna(subset=["residual"])
    d = d.loc[d.residual.abs().sort_values(ascending=False).head(16).index].sort_values("residual")
    fig = go.Figure(go.Bar(x=d.residual, y=d.municipality, orientation="h",
        marker_color=[TOKENS["residual_positive"] if v > 0 else TOKENS["residual_negative"] for v in d.residual],
        hovertemplate="<b>%{y}</b><br>Observed − predicted: %{x:+.2f} years<extra></extra>"))
    fig.add_vline(x=0, line_color=MUTED,line_width=1)
    fig.update_yaxes(showgrid=False)
    polish(fig, 500, "Observed − predicted (years) · 16 largest absolute residuals", None)
    return value_column(fig,d.municipality,d.residual,decimals=2)


def explorer_profile(bundle, row):
    scaling = bundle["scaling"].set_index("variable")
    features = list(scaling.index)
    z = (row[features].astype(float) - scaling["mean"]) / scaling.SD_ddof0
    fig = go.Figure(go.Scatter(x=z, y=[CHART_LABELS[c] for c in features], mode="markers",
        marker=dict(color=TEAL, size=13,line=dict(color="white",width=1.5)),
        hovertemplate=f"<b>{row.name}</b><br>%{{y}}<br>%{{x:+.2f}} SD from municipality mean<extra></extra>"))
    fig.add_vline(x=0, line_color="#AABAC5", line_width=1,line_dash="dash")
    fig.update_yaxes(showgrid=False)
    return polish(fig, 330, "Standard deviations from the 98-municipality mean", None)


def pca_scatter(membership, highlighted):
    d = membership.copy()
    hover = "<b>%{customdata[0]}</b><br>Profile %{customdata[1]}<br>PC1: %{x:.2f}<br>PC2: %{y:.2f}<br>Municipality silhouette: %{customdata[2]:.3f}<extra></extra>"
    fig = go.Figure()
    for i,(profile,group) in enumerate(d.groupby("cluster")):
        fig.add_trace(go.Scatter(x=group.PC1,y=group.PC2,mode="markers",name=f"Profile {profile}",
            customdata=np.column_stack([group.municipality,group.cluster,group.silhouette]),
            marker=dict(color=PALETTE[i],symbol=["circle","diamond"][i%2],size=8,opacity=.8),hovertemplate=hover))
    if highlighted:
        selected = d.loc[d.municipality.eq(highlighted)]
        fig.add_trace(go.Scatter(x=selected.PC1, y=selected.PC2, mode="markers+text", text=selected.municipality,
            textposition="top center",customdata=np.column_stack([selected.municipality,selected.cluster,selected.silhouette]),
            hovertemplate=hover,marker=dict(size=19,symbol="square-open",color=TOKENS["text"],line=dict(width=2)), showlegend=False))
    return polish(fig, 450)


def model_comparison(fits):
    fig = go.Figure(go.Bar(x=fits.model,y=fits.adjusted_R_squared,
        marker_color=["#BCCBD1","#A9BBC3",BLUE,TEAL],text=[f"{v:.3f}" for v in fits.adjusted_R_squared],textposition="outside",cliponaxis=False,
        customdata=np.column_stack([fits.N,fits.R_squared]),
        hovertemplate="<b>%{x}</b><br>Adjusted R²: %{y:.3f}<br>R²: %{customdata[1]:.3f}<br>Complete cases: %{customdata[0]}<extra></extra>"))
    fig.update_yaxes(range=[0,.88])
    fig.update_layout(bargap=.48)
    return polish(fig,320,"Model specification","Adjusted R²")


def scree(variance):
    values=variance.explained_variance_ratio
    fig=go.Figure(go.Bar(x=variance.component,y=values,text=[f"{100*v:.1f}%" for v in values],textposition="outside",
        marker_color=[BLUE,TEAL,*["#BCCBD1"]*(len(values)-2)],
        hovertemplate="<b>%{x}</b><br>Explained variance: %{y:.1%}<extra></extra>"))
    fig.update_yaxes(tickformat=".0%",range=[0,float(values.max())*1.2])
    return polish(fig,300,"Principal component","Explained variance")


def loading_chart(loadings, component):
    fig=go.Figure(go.Bar(x=loadings[component],y=loadings.variable.map(CHART_LABELS),orientation="h",
        marker_color=[TEAL if v>0 else BLUE for v in loadings[component]],
        hovertemplate=f"%{{y}}<br>{component} loading: %{{x:+.3f}}<extra></extra>"))
    fig.update_xaxes(range=[-1.15,1.15])
    fig.update_yaxes(showgrid=False,autorange="reversed")
    fig.add_vline(x=0,line_color=MUTED,line_width=1)
    polish(fig,350,f"{component} loading · correlation with indicator",None)
    return value_column(fig,loadings.variable.map(CHART_LABELS),loadings[component],decimals=2)


def cluster_comparison(profiles, features):
    fig=go.Figure()
    for i,(cluster,row) in enumerate(profiles.iterrows()):
        fig.add_trace(go.Scatter(x=row[features],y=[CHART_LABELS[c] for c in features],mode="markers",name=f"Profile {cluster}",
            marker=dict(color=PALETTE[i],size=11,symbol=["circle","diamond"][i%2]),
            hovertemplate=f"<b>Profile {cluster}</b><br>%{{y}}<br>Mean: %{{x:+.2f}} SD from municipality mean<extra></extra>"))
    fig.add_vline(x=0,line_color="#AABAC5",line_dash="dash",line_width=1)
    fig.update_yaxes(showgrid=False)
    return polish(fig,360,"Mean standard deviations from municipality mean",None)
