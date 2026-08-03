''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''GUI TEMPLATE — Complete Example'''

'''Created by Kyle Territo, AUGUST 2025'''
'''Email: kterri3@lsu.edu'''
'''Github: https://github.com/KyleTerrito'''
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# This is a fuller app that wires up all pages and common utilities: upload/preview data,
# quick plots, simple clustering, and export. Keep/modify whatever you like.

# Standard Library Imports
import os
import io
import tempfile
import atexit
import json
import base64

# Dash & Flask Imports
from dash import Dash, html, dcc, Input, Output, State, dash_table, ALL, MATCH, ctx
import dash_bootstrap_components as dbc
from flask import send_file
from dash.exceptions import PreventUpdate

# Plotting
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# Data Handling & Scientific Computing
import pandas as pd
import numpy as np

# Logging / Warnings (quiet noisy libs)
import logging, warnings
logging.getLogger('matplotlib').setLevel(logging.ERROR)
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)
warnings.simplefilter(action='ignore', category=UserWarning)

# Local layout manager
from layout import TemplateLayout
from dash import callback_context
from dash.exceptions import PreventUpdate

# ============================================================
# App bootstrap
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "TEMPLATE"

# Temporary dir
temp_dir = tempfile.TemporaryDirectory()
print(f"Temporary directory: {temp_dir.name}")

layout_manager = TemplateLayout(temp_dir)

# Page router
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    layout_manager.navbar(),
    # cross-page stores
    dcc.Store(id="store-data", storage_type="memory"),     # holds uploaded/prepared dataframe
    dcc.Store(id="store-filtered", storage_type="memory"), # holds filtered dataframe (plots page)
    dbc.Container(id="page-content", fluid=True)
])

# ------------------------------------------------------------
# Routing
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/":
        return layout_manager.create_home_page()
    elif pathname == "/main-menu":
        return layout_manager.create_main_menu_page()
    elif pathname == "/plots":
        return layout_manager.create_plots_page()
    elif pathname == "/export":
        return layout_manager.create_export_page()
    elif pathname == "/help":
        return layout_manager.create_help_page()
    elif pathname == "/s":
        return layout_manager.create_s_page()
    else:
        return layout_manager.create_home_page()

# ============================================================
# MAIN MENU CALLBACKS — Upload & preview

@app.callback(
    Output("upload-status", "children"),
    Output("table-preview", "children"),
    Output("store-data", "data"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def handle_upload(contents, filename):
    if not contents or not filename:
        raise PreventUpdate

    # contents is like: "data:<mime>;base64,<base64-string>"
    try:
        _, content_string = contents.split(",", 1)
    except ValueError:
        return dbc.Alert("Invalid upload payload.", color="danger"), dash_table.DataTable(), None

    try:
        decoded = base64.b64decode(content_string)
    except Exception as e:
        return dbc.Alert(f"Base64 decode error: {e}", color="danger"), dash_table.DataTable(), None

    df = None
    try:
        name = filename.lower()

        if name.endswith(".csv"):
            # Try utf-8, fallback to latin-1 for odd encodings
            try:
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            except UnicodeDecodeError:
                df = pd.read_csv(io.StringIO(decoded.decode("latin-1")))

        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(decoded))

        elif name.endswith(".json"):
            # JSON must be decoded to text first
            try:
                df = pd.read_json(io.StringIO(decoded.decode("utf-8")))
            except UnicodeDecodeError:
                df = pd.read_json(io.StringIO(decoded.decode("latin-1")))

        else:
            return (
                dbc.Alert(f"Unsupported file type: {filename}", color="danger"),
                dash_table.DataTable(),
                None,
            )
    except Exception as e:
        return dbc.Alert(f"Error reading file: {e}", color="danger"), dash_table.DataTable(), None

    # Build a preview table (cap rows for performance)
    preview_df = df.head(5000)
    table = dash_table.DataTable(
        columns=[{"name": c, "id": c} for c in preview_df.columns],
        data=preview_df.to_dict("records"),
        page_size=10,
        style_table={"overflowX": "auto"},
    )

    status = dbc.Alert(
        [html.B("Uploaded: "), filename, html.Span(f"  |  {df.shape[0]} rows, {df.shape[1]} cols")],
        color="success",
    )

    # Persist full dataframe in memory store
    return status, table, df.to_json(date_format="iso", orient="split")


# ============================================================
# PLOTS TRANSPOSITION
from dash.exceptions import PreventUpdate


@app.callback(
    Output("store-data", "data", allow_duplicate=True),
    Output("table-preview", "children", allow_duplicate=True),
    Input("transpose-btn", "n_clicks"),
    State("store-data", "data"),
    prevent_initial_call=True,
)
def handle_transpose(n_clicks, data_json):
    """
    Fires when the Transpose button is clicked. Flips rows and columns,
    saves the new layout to memory, and refreshes the preview window.
    """
    if not n_clicks or not data_json:
        raise PreventUpdate

    # 1. Parse current data back into a DataFrame
    df = pd.read_json(data_json, orient="split")

    # 2. Check if a column looks like an existing index/row-header
    potential_index = next((col for col in ['index', 'Unnamed: 0', 'Attributes/Rows'] if col in df.columns), None)
    if potential_index:
        df = df.set_index(potential_index)

    # 3. Transpose matrix and reset the index so headers become a row
    df_transposed = df.T.reset_index()

    # Clean up the name of the new first column
    df_transposed.rename(columns={'index': 'Attributes/Rows'}, inplace=True)

    # 4. Generate the updated DataTable component for the UI
    preview_df = df_transposed.head(5000)
    updated_table = dash_table.DataTable(
        columns=[{"name": str(c), "id": str(c)} for c in preview_df.columns],
        data=preview_df.to_dict("records"),
        page_size=10,
        style_table={"overflowX": "auto"},
    )

    # 5. Return BOTH the updated raw JSON storage and the new visual table view
    return df_transposed.to_json(date_format="iso", orient="split"), updated_table

# ============================================================
# PLOTS CALLBACKS — Separated to avoid infinite rendering loops

@app.callback(
    Output("plot-column-x", "options"),
    Output("plot-column-y", "options"),
    Input("store-data", "data"),
)
def populate_dropdown_options(data_json):
    """Fires ONLY when data is uploaded. Sets up column selections."""
    if not data_json:
        return [], []

    df = pd.read_json(data_json, orient="split")
    options = [{"label": str(c), "value": str(c)} for c in df.columns]
    return options, options


@app.callback(
    Output("plot-figure", "figure"),
    Output("plot-summary", "children"),
    Input("store-data", "data"),
    Input("plot-kind", "value"),
    Input("plot-column-x", "value"),
    Input("plot-column-y", "value"),
)
def update_plots(data_json, kind, col_x, col_y):
    """Fires when configurations or data changes to redraw the figure."""
    if not data_json:
        return go.Figure(), dbc.Alert("Upload data on the Main Menu page.", color="warning")

    df = pd.read_json(data_json, orient="split")
    fig = go.Figure()
    summary = "Choose a plot type and column(s)."

    if kind == "scatter":
        if col_x and col_y:
            fig = px.scatter(df, x=col_x, y=col_y, opacity=0.8)
            summary = f"Scatter of {col_x} vs {col_y} (n={len(df)})"
    elif kind == "hist":
        if col_x:
            fig = px.histogram(df, x=col_x, nbins=50)
            summary = f"Histogram of {col_x} (n={len(df)})"
    elif kind == "box":
        if col_x:
            fig = px.box(df, y=col_x)
            summary = f"Box plot of {col_x}"

    fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=450)
    return fig, dbc.Badge(summary, color="secondary")

# ============================================================
# EXPORT CALLBACKS — download filtered data / figure as PNG

@app.callback(
    Output("download-data", "data"),
    Input("btn-download-csv", "n_clicks"),
    State("store-data", "data"),
    prevent_initial_call=True,
)
def download_csv(n, data_json):
    if not data_json:
        raise PreventUpdate
    df = pd.read_json(data_json, orient="split")
    path = os.path.join(temp_dir.name, "export.csv")
    df.to_csv(path, index=False)
    return dcc.send_file(path)

@app.callback(
    Output("download-fig", "data"),
    Input("btn-download-fig", "n_clicks"),
    State("plot-figure", "figure"),
    prevent_initial_call=True,
)
def download_fig(n, fig_dict):
    if not fig_dict:
        raise PreventUpdate
    fig = go.Figure(fig_dict)
    path = os.path.join(temp_dir.name, "figure.png")
    fig.write_image(path, scale=2, width=1000, height=600)
    return dcc.send_file(path)

# ============================================================
# Run
if __name__ == "__main__":
    app.run(debug=True, port=4838)

atexit.register(temp_dir.cleanup)
