import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import os

LOG_CSV = "fire_sensor_data.csv"
MAX_ROWS = 300  # ✅ Auto-trim old data

app = dash.Dash(__name__)
app.title = "Fire Detection Digital Twin"

dark_bg = "#0E0E0E"
text_color = "#EAEAEA"

app.layout = html.Div(style={'backgroundColor': dark_bg, 'color': text_color, 'padding': '20px'}, children=[
    
    html.H1(" Smart Fire Detection - Digital Twin Dashboard",
            style={'textAlign': 'center', 'color': '#FF5733'}),
    html.Audio(id="alarm-audio", src="/assets/alarm.mp3", autoPlay=False, controls=False),


    html.Div(id="status", style={
        'textAlign': 'center', 'fontSize': 32,
        'padding': '12px', 'fontWeight': 'bold',
        'marginBottom': 25, 'borderRadius': '12px'
    }),

    html.Div([
        dcc.Graph(id="gauge-temp", style={'width': '24%', 'display': 'inline-block'}),
        dcc.Graph(id="gauge-smoke", style={'width': '24%', 'display': 'inline-block'}),
        dcc.Graph(id="gauge-humidity", style={'width': '24%', 'display': 'inline-block'}),
        dcc.Graph(id="gauge-co", style={'width': '24%', 'display': 'inline-block'})
    ]),

    html.Div([
        dcc.Graph(id="graph-temp-smoke", style={'width': '48%', 'display': 'inline-block'}),
        dcc.Graph(id="graph-gas-pressure", style={'width': '48%', 'display': 'inline-block'})
    ]),

    dcc.Graph(id="graph-motion", style={'height': '240px'}),
    
    html.Div(id="latest-values", style={
        'textAlign': 'center', 'fontSize': 18,
        'marginTop': 20, 'padding': '10px',
        'backgroundColor': "#1A1A1A",
        'borderRadius': "10px"
    }),

    dcc.Interval(id='update-interval', interval=2000, n_intervals=0)
])


def read_latest():
    if not os.path.exists(LOG_CSV):
        return pd.DataFrame()
    df = pd.read_csv(LOG_CSV)

    # ✅ Trim file to max 300 rows only
    if len(df) > MAX_ROWS:
        df = df.tail(MAX_ROWS)
        df.to_csv(LOG_CSV, index=False)

    return df.tail(MAX_ROWS)


@app.callback(
    Output("status", "children"),
    Output("status", "style"),
    Output("gauge-temp", "figure"),
    Output("gauge-smoke", "figure"),
    Output("gauge-humidity", "figure"),
    Output("gauge-co", "figure"),
    Output("graph-temp-smoke", "figure"),
    Output("graph-gas-pressure", "figure"),
    Output("graph-motion", "figure"),
    Output("latest-values", "children"),
    Input("update-interval", "n_intervals")
)
def update(n):
    df = read_latest()
    if df.empty:
        return "Waiting for Data...", {'color': "yellow"}, {}, {}, {}, {}, {}, {}, {}, ""

    latest = df.iloc[-1]

    label = latest.get("Final_Label", "SAFE")
    color = {"FIRE": "red", "WARNING": "orange"}.get(label, "lime")

    status_style = {
        'textAlign': 'center', 'fontSize': 32, 'fontWeight': 'bold',
        'padding': '12px', 'borderRadius': '12px',
        'border': f'3px solid {color}', 'color': color,
        'backgroundColor': "#222"
    }

    status_text = f"🔥 Current Status: {label}"

    def gauge(value, title, maxv):
        return go.Figure(go.Indicator(
            mode="gauge+number",
            value=float(value),
            title={'text': title},
            gauge={'axis': {'range': [0, maxv]}, 'bar': {'color': color}}
        )).update_layout(paper_bgcolor=dark_bg, font={'color': text_color})

    gauge_temp = gauge(latest["Temperature"], "Temperature °C", 200)
    gauge_smoke = gauge(latest["Smoke"], "Smoke ppm", 2000)
    gauge_humidity = gauge(latest["Humidity"], "Humidity %", 100)
    gauge_co = gauge(latest["CO"], "CO ppm", 100)

    graph_temp_smoke = go.Figure()
    graph_temp_smoke.add_trace(go.Scatter(x=df.index, y=df["Temperature"], name="Temperature"))
    graph_temp_smoke.add_trace(go.Scatter(x=df.index, y=df["Smoke"], name="Smoke", line={'dash': 'dot'}))
    graph_temp_smoke.update_layout(title="Temperature + Smoke Trend", paper_bgcolor=dark_bg, font={'color': text_color})

    graph_gas_pressure = go.Figure()
    graph_gas_pressure.add_trace(go.Scatter(x=df.index, y=df["CO"], name="CO Gas"))
    graph_gas_pressure.add_trace(go.Scatter(x=df.index, y=df["Pressure"], name="Pressure"))
    graph_gas_pressure.update_layout(title="CO + Pressure Trend", paper_bgcolor=dark_bg, font={'color': text_color})

    graph_motion = go.Figure()
    graph_motion.add_trace(go.Bar(x=df.index, y=df["Motion"], name="Motion Sensor"))
    graph_motion.update_layout(title="Motion Activity", paper_bgcolor=dark_bg, font={'color': text_color})

    latest_vals = (
        f"Temperature: {latest['Temperature']}°C | Humidity: {latest['Humidity']}% | "
        f"Smoke: {latest['Smoke']} ppm | CO: {latest['CO']} ppm | "
        f"Flame: {latest['Flame']} | Pressure: {latest['Pressure']} hPa | Motion: {latest['Motion']}"
    )

    return status_text, status_style, gauge_temp, gauge_smoke, gauge_humidity, gauge_co, graph_temp_smoke, graph_gas_pressure, graph_motion, latest_vals


if __name__ == "__main__":
    print("Live Dashboard: http://127.0.0.1:8050")
    app.run(debug=True)
