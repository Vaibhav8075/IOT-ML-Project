# digital_twin_dashboard.py
# Real-time fire detection digital twin dashboard.
# Reads fire_sensor_log.csv (written by smart_fire_logger.py).
# Run:  python digital_twin_dashboard.py
#       then open http://127.0.0.1:8050

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_CSV  = os.path.join(BASE_DIR, "fire_sensor_log.csv")
MAX_ROWS = 120   # keep last 120 readings (~4 min at 2s interval)
EXPECTED_COLUMNS = [
    "Timestamp", "Scenario",
    "Temperature", "Humidity", "Smoke_ADC", "CO_ADC",
    "Flame", "LDR_ADC", "LDR_Flicker", "Motion",
    "ML_Pred", "Final_Label", "Reason"
]

# ── Colour palette ────────────────────────────────────────────────────────────
BG        = "#0F0F0F"
SURFACE   = "#161616"
CARD      = "#1C1C1C"
BORDER    = "#2A2A2A"
TEXT      = "#D4D0C8"
TEXT_DIM  = "#6B6860"
ACCENT    = "#E05C2A"   # burnt orange — fire
SAFE      = "#3DAA6E"   # muted green
WARN      = "#C9952A"   # amber
FIRE_CLR  = "#D94F35"   # red-orange
BLUE      = "#4A90C4"   # CO / secondary trace

FONT = "IBM Plex Mono"

# ── App ───────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__)
app.title = "Fire Detection — Digital Twin"

# Inject Google Font + base resets
app.index_string = '''
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #0F0F0F; color: #D4D0C8; font-family: "IBM Plex Sans", sans-serif; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #161616; }
        ::-webkit-scrollbar-thumb { background: #2A2A2A; border-radius: 3px; }
        .js-plotly-plot .plotly .modebar { display: none !important; }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>
'''

def card(children, extra_style=None):
    style = {
        "background": CARD,
        "border": f"1px solid {BORDER}",
        "borderRadius": "4px",
        "padding": "20px 24px",
    }
    if extra_style:
        style.update(extra_style)
    return html.Div(children, style=style)

def label_cell(title, value_id, unit=""):
    return html.Div([
        html.Div(title, style={
            "fontSize": "10px", "letterSpacing": "0.12em",
            "textTransform": "uppercase", "color": TEXT_DIM,
            "fontFamily": FONT, "marginBottom": "6px"
        }),
        html.Div([
            html.Span("—", id=value_id, style={
                "fontSize": "26px", "fontWeight": "500",
                "fontFamily": FONT, "color": TEXT
            }),
            html.Span(f" {unit}", style={
                "fontSize": "12px", "color": TEXT_DIM,
                "fontFamily": FONT
            })
        ])
    ], style={"flex": "1", "minWidth": "130px"})

app.layout = html.Div(style={"background": BG, "minHeight": "100vh", "padding": "32px 40px"}, children=[

    # ── Header ─────────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Div("FIRE DETECTION", style={
                "fontSize": "11px", "letterSpacing": "0.18em",
                "color": TEXT_DIM, "fontFamily": FONT, "marginBottom": "4px"
            }),
            html.H1("Digital Twin Monitor", style={
                "fontSize": "22px", "fontWeight": "400",
                "color": TEXT, "fontFamily": FONT, "letterSpacing": "-0.01em"
            }),
        ]),
        html.Div([
            html.Div("SYSTEM STATUS", style={
                "fontSize": "10px", "letterSpacing": "0.14em",
                "color": TEXT_DIM, "fontFamily": FONT, "marginBottom": "6px"
            }),
            html.Div("—", id="status-badge", style={
                "fontSize": "13px", "fontWeight": "500",
                "fontFamily": FONT, "letterSpacing": "0.1em",
                "padding": "6px 16px", "borderRadius": "2px",
                "border": f"1px solid {BORDER}", "display": "inline-block"
            })
        ], style={"textAlign": "right"})
    ], style={
        "display": "flex", "justifyContent": "space-between",
        "alignItems": "flex-end", "marginBottom": "28px",
        "paddingBottom": "20px", "borderBottom": f"1px solid {BORDER}"
    }),

    # ── Live readout strip ─────────────────────────────────────────────────────
    card(
        html.Div([
            label_cell("Temperature", "val-temp", "°C"),
            label_cell("Humidity",    "val-hum",  "%"),
            label_cell("Smoke ADC",   "val-smoke", ""),
            label_cell("CO ADC",      "val-co",    ""),
            label_cell("LDR ADC",     "val-ldr",   ""),
            label_cell("LDR Flicker", "val-flicker",""),
            label_cell("Flame",       "val-flame",  ""),
            label_cell("Motion",      "val-motion", ""),
            label_cell("ML Decision", "val-ml",     ""),
        ], style={
            "display": "flex", "flexWrap": "wrap", "gap": "24px",
            "alignItems": "flex-start"
        }),
        extra_style={"marginBottom": "20px"}
    ),

    # ── Gauges row ─────────────────────────────────────────────────────────────
    html.Div([
        html.Div(dcc.Graph(id="gauge-temp",    config={"displayModeBar": False}),
                 style={"flex": "1"}),
        html.Div(dcc.Graph(id="gauge-smoke",   config={"displayModeBar": False}),
                 style={"flex": "1"}),
        html.Div(dcc.Graph(id="gauge-co",      config={"displayModeBar": False}),
                 style={"flex": "1"}),
        html.Div(dcc.Graph(id="gauge-flicker", config={"displayModeBar": False}),
                 style={"flex": "1"}),
    ], style={
        "display": "flex", "gap": "16px", "marginBottom": "20px"
    }),

    # ── Time series row ────────────────────────────────────────────────────────
    html.Div([
        html.Div(
            card(dcc.Graph(id="chart-temp-smoke", config={"displayModeBar": False})),
            style={"flex": "1"}
        ),
        html.Div(
            card(dcc.Graph(id="chart-co-ldr", config={"displayModeBar": False})),
            style={"flex": "1"}
        ),
    ], style={"display": "flex", "gap": "16px", "marginBottom": "20px"}),

    # ── Bottom row: motion bar + label history ─────────────────────────────────
    html.Div([
        html.Div(
            card(dcc.Graph(id="chart-motion", config={"displayModeBar": False})),
            style={"flex": "1"}
        ),
        html.Div(
            card(dcc.Graph(id="chart-label-history", config={"displayModeBar": False})),
            style={"flex": "2"}
        ),
    ], style={"display": "flex", "gap": "16px", "marginBottom": "20px"}),

    # ── Footer ─────────────────────────────────────────────────────────────────
    html.Div([
        html.Span("ESP32 DevKit V1", style={"color": TEXT_DIM, "fontFamily": FONT, "fontSize": "11px"}),
        html.Span(" · ", style={"color": BORDER}),
        html.Span("PIR · LDR · MQ-7 · Flame · DHT22", style={"color": TEXT_DIM, "fontFamily": FONT, "fontSize": "11px"}),
        html.Span(" · ", style={"color": BORDER}),
        html.Span("Random Forest  n=300", style={"color": TEXT_DIM, "fontFamily": FONT, "fontSize": "11px"}),
        html.Span("  ·  updates every 2s", style={"color": TEXT_DIM, "fontFamily": FONT, "fontSize": "11px"}),
    ], style={"paddingTop": "16px", "borderTop": f"1px solid {BORDER}"}),

    dcc.Interval(id="tick", interval=2000, n_intervals=0)
])

# ── Data reader ───────────────────────────────────────────────────────────────
def read_log():
    if not os.path.exists(LOG_CSV):
        return pd.DataFrame()
    read_error = None
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            df = pd.read_csv(LOG_CSV, encoding=encoding, skipinitialspace=True)
            if not df.empty:
                df.columns = [str(c).strip() for c in df.columns]
                if "Temperature" not in df.columns and len(df.columns) == len(EXPECTED_COLUMNS):
                    first_row = list(df.columns)
                    df.columns = EXPECTED_COLUMNS
                    df.loc[-1] = first_row
                    df.index = df.index + 1
                    df = df.sort_index().reset_index(drop=True)
                df = df.tail(MAX_ROWS).reset_index(drop=True)
                if "Temperature" in df.columns:
                    return df
            read_error = f"unexpected columns: {df.columns.tolist()}"
        except Exception as e:
            read_error = e
    print(f"[read_log error] {read_error}")
    return pd.DataFrame()

# ── Plot helpers ──────────────────────────────────────────────────────────────

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family=FONT, color=TEXT_DIM, size=11),
    margin=dict(l=48, r=16, t=36, b=40),
    legend=dict(
        bgcolor="rgba(0,0,0,0)", borderwidth=0,
        font=dict(size=10, color=TEXT_DIM)
    ),
    xaxis=dict(
        gridcolor=BORDER, showgrid=True,
        zeroline=False, tickfont=dict(size=10)
    ),
    yaxis=dict(
        gridcolor=BORDER, showgrid=True,
        zeroline=False, tickfont=dict(size=10)
    ),
    height=220,
)


def layout_with_overrides(**overrides):
    merged = dict(PLOT_LAYOUT)
    merged.update(overrides)
    return merged

def make_gauge(value, title, max_val, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=float(value),
        number={"font": {"family": FONT, "color": TEXT, "size": 22}},
        title={"text": title, "font": {"family": FONT, "color": TEXT_DIM, "size": 11}},
        gauge={
            "axis": {
                "range": [0, max_val],
                "tickfont": {"family": FONT, "color": TEXT_DIM, "size": 9},
                "tickcolor": BORDER,
                "tickwidth": 1,
            },
            "bar": {"color": color, "thickness": 0.55},
            "bgcolor": SURFACE,
            "borderwidth": 1,
            "bordercolor": BORDER,
            "steps": [
                {"range": [0, max_val * 0.5], "color": "#1C1C1C"},
                {"range": [max_val * 0.5, max_val * 0.8], "color": "#222222"},
                {"range": [max_val * 0.8, max_val], "color": "#262626"},
            ]
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT),
        height=170,
        margin=dict(l=24, r=24, t=36, b=8)
    )
    return fig

def empty_fig(title=""):
    fig = go.Figure()
    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text=title, font=dict(size=12, color=TEXT_DIM), x=0, xref="paper"),
        annotations=[dict(
            text="Waiting for data...", showarrow=False,
            font=dict(color=TEXT_DIM, size=12),
            xref="paper", yref="paper", x=0.5, y=0.5
        )]
    )
    return fig

# ── Callback ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("status-badge",        "children"),
    Output("status-badge",        "style"),
    Output("val-temp",            "children"),
    Output("val-hum",             "children"),
    Output("val-smoke",           "children"),
    Output("val-co",              "children"),
    Output("val-ldr",             "children"),
    Output("val-flicker",         "children"),
    Output("val-flame",           "children"),
    Output("val-motion",          "children"),
    Output("val-ml",              "children"),
    Output("gauge-temp",          "figure"),
    Output("gauge-smoke",         "figure"),
    Output("gauge-co",            "figure"),
    Output("gauge-flicker",       "figure"),
    Output("chart-temp-smoke",    "figure"),
    Output("chart-co-ldr",        "figure"),
    Output("chart-motion",        "figure"),
    Output("chart-label-history", "figure"),
    Input("tick", "n_intervals")
)
def refresh(_):
    df = read_log()

    badge_base = {
        "fontSize": "13px", "fontWeight": "500",
        "fontFamily": FONT, "letterSpacing": "0.1em",
        "padding": "6px 16px", "borderRadius": "2px",
        "display": "inline-block"
    }

    if df.empty:
        style = {**badge_base, "border": f"1px solid {BORDER}", "color": TEXT_DIM}
        empty = empty_fig()
        return (
            "WAITING", style,
            "—", "—", "—", "—", "—", "—", "—", "—", "—",
            empty, empty, empty, empty,
            empty, empty, empty, empty
        )

    latest = df.iloc[-1]

    # Status badge colour
    label = str(latest.get("Final_Label", "NORMAL")).upper()
    if label == "FIRE":
        badge_color = FIRE_CLR
    elif label == "WARNING":
        badge_color = WARN
    else:
        badge_color = SAFE

    badge_style = {
        **badge_base,
        "border": f"1px solid {badge_color}",
        "color": badge_color,
        "background": f"{badge_color}18"
    }

    # Gauge accent color
    g_color = badge_color

    def safe(col, fmt=".1f"):
        try:
            v = latest[col]
            return f"{v:{fmt}}" if fmt else str(v)
        except Exception:
            return "—"

    # Time axis
    t_axis = list(range(len(df)))

    # ── Temperature + Smoke chart ─────────────────────────────────────────────
    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(
        x=t_axis, y=df["Temperature"].tolist(),
        name="Temp °C", line=dict(color=ACCENT, width=1.5), mode="lines"
    ))
    if "Smoke_ADC" in df.columns:
        # Normalise smoke to temp scale for overlay
        smoke_norm = (df["Smoke_ADC"] / 4095 * df["Temperature"].max()).tolist()
        fig_ts.add_trace(go.Scatter(
            x=t_axis, y=smoke_norm,
            name="Smoke (scaled)", line=dict(color=TEXT_DIM, width=1, dash="dot"), mode="lines"
        ))
    fig_ts.update_layout(
        **layout_with_overrides(
        title=dict(text="Temperature & Smoke", font=dict(size=12, color=TEXT_DIM), x=0, xref="paper")
        )
    )

    # ── CO + LDR chart ────────────────────────────────────────────────────────
    fig_co = go.Figure()
    if "CO_ADC" in df.columns:
        fig_co.add_trace(go.Scatter(
            x=t_axis, y=df["CO_ADC"].tolist(),
            name="CO ADC", line=dict(color=BLUE, width=1.5), mode="lines"
        ))
    if "LDR_Flicker" in df.columns:
        fig_co.add_trace(go.Scatter(
            x=t_axis, y=df["LDR_Flicker"].tolist(),
            name="LDR Flicker", line=dict(color=WARN, width=1, dash="dot"), mode="lines"
        ))
    fig_co.update_layout(
        **layout_with_overrides(
        title=dict(text="CO ADC & LDR Flicker", font=dict(size=12, color=TEXT_DIM), x=0, xref="paper")
        )
    )

    # ── Motion bar ────────────────────────────────────────────────────────────
    fig_motion = go.Figure()
    if "Motion" in df.columns:
        fig_motion.add_trace(go.Bar(
            x=t_axis, y=df["Motion"].tolist(),
            marker_color=TEXT_DIM, name="Motion",
            marker_line_width=0
        ))
    fig_motion.update_layout(
        **layout_with_overrides(
        height=180,
        bargap=0.15,
        title=dict(text="Motion", font=dict(size=12, color=TEXT_DIM), x=0, xref="paper")
        )
    )

    # ── Label history ─────────────────────────────────────────────────────────
    label_map = {"NORMAL": 0, "WARNING": 1, "FIRE": 2}
    if "Final_Label" in df.columns:
        label_vals = [label_map.get(str(v).upper(), 0) for v in df["Final_Label"]]
        label_colors = [
            SAFE if v == 0 else WARN if v == 1 else FIRE_CLR
            for v in label_vals
        ]
    else:
        label_vals, label_colors = [], []

    fig_label = go.Figure()
    fig_label.add_trace(go.Bar(
        x=t_axis, y=label_vals,
        marker_color=label_colors, name="State",
        marker_line_width=0
    ))
    fig_label.update_layout(
        **layout_with_overrides(
        height=180,
        bargap=0.1,
        yaxis=dict(
            tickvals=[0, 1, 2],
            ticktext=["NORMAL", "WARNING", "FIRE"],
            gridcolor=BORDER
        ),
        title=dict(text="Detection State History", font=dict(size=12, color=TEXT_DIM), x=0, xref="paper")
        )
    )

    # ── Gauges ────────────────────────────────────────────────────────────────
    try:
        g_temp    = make_gauge(latest["Temperature"], "TEMPERATURE  °C", 200,   g_color)
        g_smoke   = make_gauge(latest["Smoke_ADC"],   "SMOKE  ADC",      4095,  g_color)
        g_co      = make_gauge(latest["CO_ADC"],      "CO  ADC",         4095,  g_color)
        g_flicker = make_gauge(latest["LDR_Flicker"], "LDR FLICKER",     1000,  g_color)
    except Exception:
        g_temp = g_smoke = g_co = g_flicker = empty_fig()

    ml_raw = latest.get("ML_Pred", "—")
    ml_display = {0: "NORMAL", 1: "WARNING", 2: "FIRE"}.get(int(ml_raw) if str(ml_raw).isdigit() else -1, str(ml_raw))

    return (
        label, badge_style,
        safe("Temperature"),
        safe("Humidity"),
        safe("Smoke_ADC",  ".0f"),
        safe("CO_ADC",     ".0f"),
        safe("LDR_ADC",    ".0f"),
        safe("LDR_Flicker",".1f"),
        str(int(latest.get("Flame", 0))),
        str(int(latest.get("Motion", 0))),
        ml_display,
        g_temp, g_smoke, g_co, g_flicker,
        fig_ts, fig_co, fig_motion, fig_label
    )


if __name__ == "__main__":
    print("Dashboard running at  http://127.0.0.1:8050")
    app.run(debug=False)
