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
# Wrap, rather than shorten, the published indicator names.
CHART_LABELS = {key: "<br>".join(wrap(label, 21, break_long_words=False, break_on_hyphens=False))
                for key, label in LABELS.items()}


def zero_reference(fig):
    fig.add_vline(x=0, line_color=MUTED, line_width=1)
    return fig


def signed_range(values, padding=.22):
    extent = max(float(np.nanmax(np.abs(np.asarray(values, dtype=float)))), .1)
    return [-extent * (1 + padding), extent * (1 + padding)]


def direct_labels(fig, values, decimals=2, signed=True, bounded=False):
    """Values sit beside their marks; axis padding reserves room for the text."""
    threshold = .55 if bounded else max(abs(float(v)) for v in values) * .65
    fig.update_traces(text=[f"{v:+.{decimals}f}" if signed else f"{v:,.{decimals}f}" for v in values],
                      textposition=["inside" if abs(v) >= threshold else "outside" for v in values],
                      insidetextanchor="end", insidetextfont=dict(color="white"),
                      cliponaxis=False, textfont=dict(size=12),
                      selector=dict(type="bar"))
    return fig


def polish(fig, height=420, x=None, y=None):
    if isinstance(x,str) and len(x)>40:
        x="<br>".join(wrap(x,40,break_long_words=False))
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=12, r=30, t=22, b=30),
        font=dict(family=TOKENS["font"], size=13.5, color=TOKENS["text"]),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        colorway=PALETTE, legend_title_text="", legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, font=dict(size=12)),
        hoverlabel=dict(bgcolor="white", bordercolor=TOKENS["border"], font=dict(family=TOKENS["font"],size=13,color=TOKENS["text"])),
        hovermode="closest", bargap=.3)
    axis_style = dict(gridcolor=TOKENS["grid"],gridwidth=1,zeroline=False,showline=True,
                      linecolor=TOKENS["border"],linewidth=1,ticks="outside",ticklen=4,tickcolor=TOKENS["border"],
                      automargin=True,tickfont=dict(size=12,color=TOKENS["muted"]),
                      title_font=dict(size=12,color=TOKENS["muted"]),title_standoff=10)
    fig.update_xaxes(title=x, **axis_style)
    fig.update_yaxes(title=y, **axis_style)
    fig.update_yaxes(showgrid=False)
    # Reserve actual label room: Plotly's auto margin underestimates some font glyphs.
    categorical = any(trace.y is not None and len(trace.y) and
                      isinstance(next((v for v in trace.y if v is not None), None), str)
                      for trace in fig.data)
    if categorical:
        fig.update_layout(margin=dict(l=155))
    return fig


def correlation_bars(table, limit=6):
    d = table.sort_values("correlation", key=abs, ascending=False).head(limit)
    fig = go.Figure(go.Bar(x=d.correlation, y=d.other_variable.map(CHART_LABELS), orientation="h",
        marker_color=[TEAL if v >= 0 else BLUE for v in d.correlation],
        customdata=np.column_stack([d.N, d.p_value, d.q_value_BH_all_pairs]),
        hovertemplate="%{y}<br>Correlation: %{x:+.3f}<br>N=%{customdata[0]}<br>p=%{customdata[1]:.3g}<br>BH q=%{customdata[2]:.3g}<extra></extra>"))
    polish(fig, max(360, len(d)*56+80), "Correlation with life expectancy", None)
    fig.update_xaxes(range=[-1.15, 1.15], tickvals=[-1, -.5, 0, .5, 1])
    fig.update_yaxes(autorange="reversed")
    zero_reference(fig)
    return direct_labels(fig, d.correlation, decimals=3, bounded=True)


def ranked(data, variable, selection):
    # Stable ordering keeps source tie order; values and shared-rank logic are untouched.
    d = data.dropna(subset=[variable]).sort_values(variable, kind="stable")
    if selection == "Lowest 20":
        d = d.head(20)
    elif selection == "Highest 20":
        d = d.tail(20)
    values = data[variable].dropna()
    median = float(values.median())
    decimals = 0 if METRICS[variable][1] in ("DKK", "people") else 1
    # A lollipop uses a declared local axis origin, not a misleading truncated bar.
    low = min(float(d[variable].min()), median)
    high = max(float(d[variable].max()), median)
    span = max(high-low, abs(high)*.015, .1)
    origin = low-span*.07
    fig = go.Figure()
    stems_x, stems_y = [], []
    for name, value in zip(d.municipality, d[variable], strict=True):
        stems_x.extend([origin, value, None]); stems_y.extend([name, name, None])
    # Keep observations as the first trace for transparent numerical inspection.
    fig.add_trace(go.Scatter(x=d[variable], y=d.municipality, mode="markers+text",
        text=[f"{v:,.{decimals}f}" for v in d[variable]], textposition="middle right", cliponaxis=False,
        marker=dict(color=BLUE, size=8), textfont=dict(size=12), showlegend=False,
        hovertemplate=f"<b>%{{y}}</b><br>{LABELS[variable]}: %{{x:,.{decimals}f}} {METRICS[variable][1]}<extra></extra>"))
    fig.add_trace(go.Scatter(x=stems_x, y=stems_y, mode="lines", line=dict(color="#B1C4CC", width=2),
                            hoverinfo="skip", showlegend=False))
    polish(fig, max(560, len(d)*26+100), f"{LABELS[variable]} ({METRICS[variable][1]})", None)
    fig.update_xaxes(range=[origin, high+span*.25], tickformat=",.0f" if decimals==0 else ".1f", nticks=5)
    fig.update_yaxes(categoryorder="array", categoryarray=d.municipality.tolist(), tickmode="array", tickvals=d.municipality)
    fig.add_vline(x=median, line_color=TEAL, line_width=1.3, line_dash="dot")
    fig.update_layout(title=dict(text=f"Municipality median: {median:,.{decimals}f} {METRICS[variable][1]}",
                                font=dict(size=12, color=TEAL), x=0), margin=dict(t=48))
    return fig


def distribution(data, variable):
    fig = px.histogram(data.dropna(subset=[variable]), x=variable, nbins=18, color_discrete_sequence=[TEAL], labels={variable: LABELS[variable]})
    median=float(data[variable].dropna().median())
    fig.update_traces(marker_color="#8BBCC4",marker_line_color="white", marker_line_width=1,
                      hovertemplate=f"{LABELS[variable]}: %{{x}} {METRICS[variable][1]}<br>Municipalities: %{{y}}<extra></extra>")
    fig.add_vline(x=median,line_color=BLUE,line_width=1.5,line_dash="dot",
                  annotation_text="Median",annotation_position="top right",annotation_font=dict(size=11,color=BLUE))
    return polish(fig, 380, f"{LABELS[variable]} ({METRICS[variable][1]})", "Municipalities")


def heatmap(matrix):
    labels = [CHART_LABELS.get(c, c) for c in matrix.columns]
    # Full wrapped row names and numbered columns also fit a phone-width chart.
    full = [[[labels[j], labels[i]] for j in range(len(labels))] for i in range(len(labels))]
    values=matrix.to_numpy()
    fig = go.Figure(go.Heatmap(z=values, x=list(range(1, len(labels)+1)), y=[f"{i+1}. {label}" for i,label in enumerate(labels)], customdata=full,
        colorscale=[[0, BLUE], [.5, "#F4F7F8"], [1, TEAL]], zmin=-1, zmax=1,
        colorbar=dict(title="Pearson r", orientation="h", len=.65, thickness=10, y=-.12),
        hovertemplate="%{customdata[0]}<br>%{customdata[1]}<br>Pearson r=%{z:.3f}<extra></extra>"))
    fig.update_xaxes(tickangle=0, dtick=2, tick0=1, showgrid=False, ticks="")
    fig.update_yaxes(autorange="reversed",showgrid=False,ticks="",tickfont=dict(size=11))
    return polish(fig, 1080).update_layout(margin=dict(l=175))


def association_scatter(bundle, variable):
    d = bundle["master"].dropna(subset=[variable, "life_expectancy_total"])
    fig = go.Figure(go.Scatter(x=d[variable], y=d.life_expectancy_total, mode="markers", customdata=d.municipality,
        marker=dict(color=TEAL,size=9,opacity=.78,line=dict(color="white",width=.8)), showlegend=False,
        hovertemplate=f"<b>%{{customdata}}</b><br>{LABELS[variable]}: %{{x:,.1f}} {METRICS.get(variable, ('', '', ''))[1]}<br>Life expectancy: %{{y:.1f}} years<extra></extra>"))
    x, y = association_line(bundle, variable)
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color=BLUE, width=2), name="Descriptive linear guide", hoverinfo="skip", showlegend=False))
    return polish(fig, 390, f"{LABELS[variable]} ({METRICS[variable][1]})", "Life expectancy (years)")


def coefficients(table, mode):
    d = table.loc[table.model.eq("M4") & table.term.ne("const")].iloc[::-1]
    standardized = mode == "Standardized beta"
    estimate, low, high = ("standardized_beta", "standardized_ci_low", "standardized_ci_high") if standardized else ("coefficient", "ci_low", "ci_high")
    fig = go.Figure(go.Scatter(x=d[estimate], y=d.term.map(CHART_LABELS), mode="markers",
        marker=dict(color=[TEAL if v > 0 else BLUE for v in d[estimate]], size=11, line=dict(color="white",width=1.2)),
        text=[f"{v:+.2f}" for v in d[estimate]], textposition="top center",
        error_x=dict(type="data", array=d[high]-d[estimate], arrayminus=d[estimate]-d[low], color="#859DAA", thickness=2,width=4),
        customdata=np.column_stack([d.robust_p_value, d.q_value_family_BH, d[low], d[high]]),
        hovertemplate="%{y}<br>Estimate=%{x:.3f}<br>95% CI [%{customdata[2]:.3f}, %{customdata[3]:.3f}]<br>HC3 p=%{customdata[0]:.3g}<br>Primary-family q=%{customdata[1]:.3g}<extra></extra>"))
    fig.add_vline(x=0, line_color=MUTED, line_width=1)
    fig.update_yaxes(showgrid=False)
    return polish(fig, 560, "Standardized beta · 95% HC3 CI" if standardized else "Years per unit · 95% HC3 CI", None)


def prediction_scatter(predictions, highlight=None):
    d = predictions.dropna(subset=["observed", "predicted"])
    hover = "<b>%{customdata[0]}</b><br>Model-predicted life expectancy: %{x:.2f} years<br>Observed life expectancy: %{y:.1f} years<br>Residual: %{customdata[1]:+.2f} years<extra></extra>"
    fig = go.Figure(go.Scatter(x=d.predicted, y=d.observed, mode="markers", customdata=np.column_stack([d.municipality,d.residual]),
        marker=dict(color=[TEAL if v>=0 else BLUE for v in d.residual],
                    symbol=["circle" if v>=0 else "diamond" for v in d.residual],
                    size=9,opacity=.85,line=dict(color="white",width=.8)),hovertemplate=hover,showlegend=False))
    bounds = [min(d.observed.min(), d.predicted.min())-.2, max(d.observed.max(), d.predicted.max())+.2]
    fig.add_trace(go.Scatter(x=bounds, y=bounds, mode="lines", line=dict(color="#9EB0BC", width=1,dash="dash"), name="Observed = predicted", hoverinfo="skip",showlegend=False))
    fig.update_xaxes(range=bounds)
    fig.update_yaxes(range=bounds, scaleanchor="x", scaleratio=1, constrain="domain")
    if highlight:
        row = d.loc[d.municipality.eq(highlight)]
        if not row.empty:
            fig.add_trace(go.Scatter(x=row.predicted, y=row.observed, text=row.municipality, mode="markers+text", textposition="top center",
                customdata=np.column_stack([row.municipality,row.residual]),marker=dict(color=BLUE, symbol="diamond",size=14,line=dict(color="white",width=1.5)), hovertemplate=hover,showlegend=False))
    return polish(fig, 410, "Fitted life expectancy (years)", "Observed life expectancy (years)")


def residual_ranking(predictions):
    d = predictions.dropna(subset=["residual"])
    d = d.loc[d.residual.abs().sort_values(ascending=False, kind="stable").head(16).index]
    fig = go.Figure(go.Bar(x=d.residual, y=d.municipality, orientation="h",
        marker_color=[TEAL if v >= 0 else BLUE for v in d.residual],
        hovertemplate="<b>%{y}</b><br>Observed − fitted: %{x:+.2f} years<extra></extra>"))
    polish(fig, 560, "Observed − fitted life expectancy (years)", None)
    fig.update_xaxes(range=signed_range(d.residual))
    fig.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=d.municipality.tolist())
    zero_reference(fig)
    return direct_labels(fig, d.residual)


def explorer_profile(bundle, row):
    scaling = bundle["scaling"].set_index("variable")
    features = list(scaling.index)
    z = (row[features].astype(float) - scaling["mean"]) / scaling.SD_ddof0
    fig = go.Figure(go.Bar(x=z, y=[CHART_LABELS[c] for c in features], orientation="h",
        marker_color=[TEAL if v >= 0 else BLUE for v in z],
        hovertemplate=f"<b>{row.name}</b><br>%{{y}}<br>%{{x:+.3f}} SD from municipality mean<extra></extra>"))
    polish(fig, 440, "Below mean ← SD → Above mean", None)
    fig.update_layout(title=dict(text=str(row.name), font=dict(size=13), x=0), margin=dict(t=40))
    fig.update_xaxes(range=signed_range(z))
    fig.update_yaxes(autorange="reversed")
    zero_reference(fig)
    return direct_labels(fig, z)


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
    fig.add_hline(y=0,line_color=TOKENS["grid"],line_dash="dot",line_width=1)
    fig.add_vline(x=0,line_color=TOKENS["grid"],line_dash="dot",line_width=1)
    return polish(fig, 410, "PC1 score", "PC2 score")


def model_comparison(fits):
    fig = go.Figure(go.Bar(x=fits.model,y=fits.adjusted_R_squared,
        marker_color=["#BCCBD1","#A9BBC3",BLUE,TEAL],text=[f"{v:.3f}" for v in fits.adjusted_R_squared],textposition="outside",cliponaxis=False,
        customdata=np.column_stack([fits.N,fits.R_squared,fits.get("Specification",fits.model)]),
        hovertemplate="<b>%{x} · %{customdata[2]}</b><br>Adjusted R²: %{y:.3f}<br>R²: %{customdata[1]:.3f}<br>Complete cases: %{customdata[0]}<extra></extra>"))
    fig.update_yaxes(range=[0,.88])
    ticktext=["<b>M1</b><br>Socioeconomic","<b>M2</b><br>Health behaviours","<b>M3</b><br>Combined","<b>M4</b><br>Expanded"]
    fig.update_xaxes(tickmode="array",tickvals=fits.model,ticktext=ticktext)
    fig.update_layout(bargap=.42)
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
    polish(fig,440,f"{component} loading",None)
    fig.update_xaxes(range=[-1.22,1.22],tickvals=[-1,-.5,0,.5,1])
    fig.update_yaxes(autorange="reversed")
    zero_reference(fig)
    return direct_labels(fig,loadings[component],bounded=True)


def cluster_comparison(profiles, features):
    fig=go.Figure()
    for i,(cluster,row) in enumerate(profiles.iterrows()):
        fig.add_trace(go.Bar(x=row[features],y=[CHART_LABELS[c] for c in features],orientation="h",name=f"Profile {cluster}",
            marker=dict(color=PALETTE[i], pattern=dict(shape=["", "/"][i%2])),
            offsetgroup=str(cluster),
            hovertemplate=f"<b>Profile {cluster}</b><br>%{{y}}<br>Mean: %{{x:+.3f}} SD from municipality mean<extra></extra>"))
    polish(fig,520,"Mean difference from 98-municipality mean (SD)",None)
    fig.update_layout(barmode="group",bargap=.25,bargroupgap=.12, margin=dict(t=50))
    fig.update_xaxes(range=signed_range(profiles[features].to_numpy().ravel()))
    fig.update_yaxes(autorange="reversed")
    zero_reference(fig)
    return fig
