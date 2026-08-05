# app.py
'''GUI TEMPLATE — Complete Example'''
'''Created by Kyle Territo, AUGUST 2025'''
'''Revised: fixed duplicate callback outputs, direct-tab-navigation bug,
   moving-average/trendline handling, and static-type-checker warnings.'''

import os
import io
import tempfile
import atexit
import base64
from typing import Any

# Dash & Flask Imports
from dash import Dash, html, dcc, Input, Output, State, dash_table, ctx
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# Plotting
import plotly.express as px
import plotly.graph_objects as go

# Data Handling
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
    dcc.Store(id="store-data", storage_type="memory"),
    dcc.Store(id="store-filtered", storage_type="memory"),
    dcc.Store(id="invert-state", storage_type="memory"),
    dbc.Container(id="page-content", fluid=True)
])


# ------------------------------------------------------------
# Invert-colors toggle (fully client-side - no Flask round trip).
# The button lives in the navbar (present on every page), so it works
# regardless of which page is currently shown. It just flips the
# "inverted" class on <html>; the actual color-inversion is CSS-only,
# defined in assets/custom.css.
app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) {
            return window.dash_clientside.no_update;
        }
        const isInverted = document.documentElement.classList.toggle('inverted');
        return isInverted;
    }
    """,
    Output("invert-state", "data"),
    Input("invert-toggle-btn", "n_clicks"),
    prevent_initial_call=True,
)


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
# Helpers
def _records_for_table(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Cast DataFrame records to plain str-keyed dicts so DataTable's
    `data` prop matches its declared type (avoids the
    'list[dict[Hashable, Any]]' type-checker warning)."""
    preview_df = df.head(5000)
    records = preview_df.to_dict("records")
    return [{str(k): v for k, v in row.items()} for row in records]


def _clean_to_numeric(series: pd.Series) -> pd.Series:
    """Strip thousands separators / whitespace and coerce to numeric,
    turning anything unparseable into NaN."""
    s = series.astype(str).str.replace(',', '', regex=False).str.strip()
    return pd.to_numeric(s, errors='coerce')


def _numeric_or_original(series: pd.Series) -> pd.Series:
    """Try to convert a series to numeric; if that fails for (almost)
    everything, keep the original values instead. Replaces the old
    `pd.to_numeric(..., errors='ignore')` call, which newer pandas
    versions no longer accept."""
    s = series.astype(str).str.strip()
    converted = pd.to_numeric(s, errors='coerce')
    if converted.notna().sum() == 0:
        return series
    return converted


def _sanitize_labels(values, prefix: str = "Row") -> list[str]:
    """Turn a sequence of row/column labels into non-empty, unique strings.
    Blank/NaN labels become "{prefix} {n}"; duplicates get a "(2)", "(3)"...
    suffix. This is what a blank cell (e.g. an unlabeled row in the source
    CSV) needs before it's used as an index that will later become
    DataTable column headers - DataTable requires every column to have a
    non-null `name`, and will hard-error (as seen with
    'columns[N].name ... required but not provided') otherwise."""
    seen: dict[str, int] = {}
    out: list[str] = []
    for i, v in enumerate(values):
        if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "":
            label = f"{prefix} {i + 1}"
        else:
            label = str(v).strip()
        if label in seen:
            seen[label] += 1
            label = f"{label} ({seen[label]})"
        else:
            seen[label] = 1
        out.append(label)
    return out


def _sanitize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Apply _sanitize_labels to a DataFrame's column headers."""
    df = df.copy()
    df.columns = _sanitize_labels(df.columns, prefix="Column")
    return df


def _numeric_for_trendline(series: pd.Series) -> pd.Series:
    """Best-effort numeric encoding of an x column so a trendline can
    still be fit even when x is text like "day 12" or fully categorical.
    Tries, in order: (1) direct numeric coercion, (2) extracting the
    first embedded number from each value (so "day 12" -> 12), then
    (3) falling back to positional rank (0, 1, 2, ...) so a trend can
    still be computed against a purely categorical axis, in the same
    left-to-right order it's plotted in.

    This replaces a previous strict `pd.to_numeric(..., errors='coerce')`
    call with no fallback, which turned an entire text column (e.g. "day
    1", "day 2", ...) into NaN, emptied the working dataframe, and caused
    the trendline to be silently skipped with no error message."""
    s = series.astype(str).str.strip()
    threshold = max(2, int(len(s) * 0.5))

    direct = pd.to_numeric(s, errors='coerce')
    if direct.notna().sum() >= threshold:
        return direct

    extracted = pd.to_numeric(s.str.extract(r'(-?\d+\.?\d*)', expand=False), errors='coerce')
    if extracted.notna().sum() >= threshold:
        return extracted

    return pd.Series(range(len(s)), index=series.index, dtype=float)


def _lowess_numpy(x: np.ndarray, y: np.ndarray, frac: float = 0.3) -> np.ndarray:
    """Minimal, dependency-free LOWESS (locally weighted linear regression)
    smoother. This exists specifically so the lowess trendline never
    depends on statsmodels being installed - that was the actual reason
    lowess trendlines were failing: statsmodels isn't in this project's
    environment, so the previous statsmodels-based implementation
    silently gave up as soon as the import failed, regardless of how
    much valid data there was."""
    n = len(x)
    if n < 2:
        return y.copy()
    k = max(2, int(np.ceil(frac * n)))
    fitted = np.empty(n)
    for i in range(n):
        distances = np.abs(x - x[i])
        idx = np.argsort(distances)[:k]
        d = distances[idx]
        d_max = d.max()
        weights = np.ones_like(d) if d_max <= 0 else np.clip(1 - (d / d_max) ** 3, 0, None) ** 3
        X = np.column_stack([np.ones(k), x[idx]])
        WX = X * weights[:, None]
        try:
            beta, *_ = np.linalg.lstsq(WX.T @ X, WX.T @ y[idx], rcond=None)
            fitted[i] = beta[0] + beta[1] * x[i]
        except np.linalg.LinAlgError:
            fitted[i] = y[i]
    return fitted


def _fit_trendline(x_numeric: pd.Series, y: pd.Series, kind: str) -> pd.Series | None:
    """Fit a trendline ('ols' or 'lowess') and return fitted y-values
    aligned to the input index (NaN where a fit point isn't available).
    Returns None only if there isn't enough valid, distinct-x data -
    both 'ols' and 'lowess' use plain numpy, so no optional package is
    required for either."""
    mask = x_numeric.notna() & y.notna()
    if mask.sum() < 2 or x_numeric[mask].nunique() < 2:
        return None

    xv = x_numeric[mask].to_numpy(dtype=float)
    yv = y[mask].to_numpy(dtype=float)
    fitted = pd.Series(index=x_numeric.index, dtype=float)

    if kind == "ols":
        coeffs = np.polyfit(xv, yv, 1)
        fitted.loc[mask] = np.polyval(coeffs, xv)
        return fitted

    if kind == "lowess":
        fitted.loc[mask] = _lowess_numpy(xv, yv)
        return fitted

    return None


def _is_ma_enabled(ma_toggle) -> bool:
    """Normalize the moving-average toggle value regardless of whether
    the layout uses a dbc.Switch (bool), a dcc.Checklist (list), or a
    single-value dcc.Checkbox."""
    if ma_toggle is None:
        return False
    if isinstance(ma_toggle, bool):
        return ma_toggle
    if isinstance(ma_toggle, (list, tuple)):
        return len(ma_toggle) > 0
    return bool(ma_toggle)


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

    try:
        _, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)
    except Exception as e:
        return dbc.Alert(f"Decode error: {e}", color="danger"), dash_table.DataTable(), None

    df = None
    try:
        name = filename.lower()
        if name.endswith(".csv"):
            try:
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            except UnicodeDecodeError:
                df = pd.read_csv(io.StringIO(decoded.decode("latin-1")))
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(decoded))
        elif name.endswith(".json"):
            try:
                df = pd.read_json(io.StringIO(decoded.decode("utf-8")))
            except UnicodeDecodeError:
                df = pd.read_json(io.StringIO(decoded.decode("latin-1")))
        else:
            return dbc.Alert(f"Unsupported file: {filename}", color="danger"), dash_table.DataTable(), None
    except Exception as e:
        return dbc.Alert(f"Error reading file: {e}", color="danger"), dash_table.DataTable(), None

    df = _sanitize_columns(df)

    table = dash_table.DataTable(
        columns=[{"name": c, "id": c} for c in df.head(5000).columns],
        data=_records_for_table(df),
        page_size=10,
        style_table={"overflowX": "auto"},
    )
    status = dbc.Alert([html.B("Uploaded: "), filename, html.Span(f"  |  {df.shape[0]} rows, {df.shape[1]} cols")],
                       color="success")
    return status, table, df.to_json(date_format="iso", orient="split")


# ============================================================
# PLOTS TRANSPOSITION
@app.callback(
    Output("store-data", "data", allow_duplicate=True),
    Output("table-preview", "children", allow_duplicate=True),
    Input("transpose-btn", "n_clicks"),
    State("store-data", "data"),
    prevent_initial_call=True,
)
def handle_transpose(n_clicks, data_json):
    if not n_clicks or not data_json:
        raise PreventUpdate

    df = pd.read_json(io.StringIO(data_json), orient="split")

    # 1. Catch existing index columns and set them properly before transposing.
    # IMPORTANT: sanitize this column FIRST. Its values become the new
    # column headers after transposing, so a blank/NaN cell here (e.g. an
    # unlabeled row in the source spreadsheet) would otherwise produce a
    # DataTable column with no name and crash the table with
    # "columns[N].name ... required but not provided".
    label_col = None
    for col in ['index', 'Unnamed: 0', 'Attributes/Rows', 'Variable']:
        if col in df.columns:
            label_col = col
            break

    if label_col is not None:
        df[label_col] = _sanitize_labels(df[label_col])
        df = df.set_index(label_col)
    else:
        # No recognizable label column - sanitize the existing index instead
        df.index = _sanitize_labels(list(df.index))

    # 2. Prevent the old index name from becoming a new row
    df.index.name = None

    # 3. Transpose
    df_transposed = df.T.reset_index()

    # 4. Rename the newly generated column 0 and ensure headers are strings
    df_transposed.rename(columns={'index': 'Variable'}, inplace=True)
    df_transposed.columns = df_transposed.columns.astype(str)

    # 5. Clean out any lingering junk rows named "index" or "Unnamed: 0"
    df_transposed = df_transposed[~df_transposed['Variable'].isin(['index', 'Unnamed: 0'])]

    # 6. Safety net: guarantee unique, non-empty column headers no matter
    # what the source data looked like.
    df_transposed = _sanitize_columns(df_transposed)

    updated_table = dash_table.DataTable(
        columns=[{"name": c, "id": c} for c in df_transposed.head(5000).columns],
        data=_records_for_table(df_transposed),
        page_size=10,
        style_table={"overflowX": "auto"},
    )
    return df_transposed.to_json(date_format="iso", orient="split"), updated_table


# ============================================================
# PLOTS CALLBACKS
# Single source of truth for populating the X/Y dropdowns.
# NOTE: the original file registered TWO callbacks with the exact same
# Outputs (plot-column-x.options / plot-column-y.options). Dash does not
# allow two callbacks to write to the same Output pair without
# allow_duplicate=True, so the app was raising a DuplicateCallbackOutput
# error at startup — this is almost certainly why the Plots tab behaved
# strangely, including when navigating straight to it. That duplicate has
# been removed and merged into a single callback below.
#
# We also add `url.pathname` as a second Input so the dropdowns get
# (re)populated the moment you land on /plots directly (e.g. via URL bar
# or a link that isn't the "Go to Plots" button), not only when
# store-data changes.
@app.callback(
    Output("plot-column-x", "options"),
    Output("plot-column-y", "options"),
    Input("store-data", "data"),
    Input("url", "pathname"),
)
def populate_plot_dropdowns(data_json, pathname):
    if not data_json:
        return [], []
    try:
        df = pd.read_json(io.StringIO(data_json), orient="split")
        cols = [{"label": str(c), "value": str(c)} for c in df.columns]
        return cols, cols
    except Exception:
        return [], []


# ============================================================
# FULLY FEATURED PLOTS CALLBACK
@app.callback(
    Output("plot-figure", "figure"),
    Output("plot-summary", "children"),
    Input("store-data", "data"),
    Input("plot-kind", "value"),
    Input("plot-column-x", "value"),
    Input("plot-column-y", "value"),
    Input("ma-toggle", "value"),
    Input("ma-window", "value"),
    Input("trendline-kind", "value"),
    # Requires matching components in layout.py:
    #   ma-toggle      -> dbc.Switch / dcc.Checklist (values truthy when ON)
    #   ma-window      -> numeric input for the rolling window size
    #   trendline-kind -> dcc.Dropdown with options like
    #                      [{"label": "None", "value": "none"},
    #                       {"label": "OLS", "value": "ols"},
    #                       {"label": "LOWESS", "value": "lowess"}]
)
def update_plots(data_json, kind, col_x, col_y, ma_toggle, ma_window, trendline_kind):
    if not data_json:
        return go.Figure(), dbc.Alert("Upload or transpose data first.", color="warning")

    try:
        df = pd.read_json(io.StringIO(data_json), orient="split")
        df.columns = df.columns.astype(str)

        fig = go.Figure()
        summary = "Configure your plot options above."

        # Parse Moving Average parameters safely
        show_ma = _is_ma_enabled(ma_toggle)
        try:
            window = max(2, int(ma_window)) if ma_window else 10
        except (TypeError, ValueError):
            window = 10

        # Parse Y columns
        if not col_y:
            y_cols = []
        elif isinstance(col_y, list):
            y_cols = [str(c) for c in col_y]
        else:
            y_cols = [str(col_y)]
        y_cols = [c for c in y_cols if c in df.columns]

        if col_x is not None:
            col_x = str(col_x)
            if col_x not in df.columns:
                col_x = None

        if kind in ("scatter", "line"):
            if col_x and y_cols:
                x_data = _numeric_or_original(df[col_x])
                # For line charts, draw left-to-right in x order rather than
                # raw row order, so the line doesn't zigzag if the source
                # rows aren't already sorted by x.
                if kind == "line":
                    order = _numeric_for_trendline(df[col_x]).sort_values().index
                else:
                    order = df.index

                trace_mode = "markers" if kind == "scatter" else "lines+markers"

                for y in y_cols:
                    y_data = _clean_to_numeric(df[y])
                    fig.add_trace(go.Scatter(
                        x=x_data.loc[order], y=y_data.loc[order],
                        mode=trace_mode, name=y, opacity=0.85
                    ))

                    # Moving-average overlay
                    if show_ma:
                        ma_series = y_data.rolling(window=window, min_periods=1).mean()
                        fig.add_trace(go.Scatter(
                            x=x_data.loc[order], y=ma_series.loc[order], mode="lines",
                            name=f"{y} (MA-{window})", line=dict(width=2, dash="dash")
                        ))

                # Optional trendline (fit ourselves so it still works when
                # x is text like "day 12" or otherwise non-numeric)
                trendline_note = ""
                if trendline_kind and trendline_kind in ["ols", "lowess"]:
                    x_numeric = _numeric_for_trendline(df[col_x])
                    y_for_trend = _clean_to_numeric(df[y_cols[0]])
                    fitted = _fit_trendline(x_numeric, y_for_trend, trendline_kind)

                    if fitted is None:
                        trendline_note = " — trendline unavailable (need at least 2 points with distinct, valid x/y values)"
                    else:
                        # Draw left-to-right along the fitted axis instead of
                        # raw row order, so the line doesn't zigzag.
                        trend_order = x_numeric.sort_values().index
                        fig.add_trace(go.Scatter(
                            x=x_data.loc[trend_order],
                            y=fitted.loc[trend_order],
                            mode="lines",
                            name=f"{y_cols[0]} ({trendline_kind.upper()} Trend)",
                            line=dict(width=2, dash="dot"),
                        ))

                kind_label = "Scatter" if kind == "scatter" else "Line"
                summary = f"{kind_label}: {', '.join(y_cols)} vs {col_x} (n={len(df)}){trendline_note}"
            else:
                summary = "Pick an X column and at least one Y column."

        elif kind == "hist":
            # Use whichever the user actually picked - Y (as with
            # scatter/line) if set, else fall back to X. Previously this
            # only ever read col_x, so selecting a value via the Y dropdown
            # (the natural choice) produced an empty chart.
            cols = y_cols if y_cols else ([col_x] if col_x else [])
            if cols:
                for c in cols:
                    data = _clean_to_numeric(df[c]).dropna()
                    fig.add_trace(go.Histogram(x=data, name=c, opacity=0.65, nbinsx=50))
                if len(cols) > 1:
                    fig.update_layout(barmode="overlay")
                summary = f"Histogram of {', '.join(cols)} (n={len(df)})"
            else:
                summary = "Pick at least one column (X or Y) to plot a histogram."

        elif kind == "box":
            # Same fix as histogram: read Y columns (with X fallback),
            # and support multiple columns as separate boxes.
            cols = y_cols if y_cols else ([col_x] if col_x else [])
            if cols:
                for c in cols:
                    data = _clean_to_numeric(df[c]).dropna()
                    fig.add_trace(go.Box(y=data, name=c, boxpoints="outliers"))
                summary = f"Box plot of {', '.join(cols)} (n={len(df)})"
            else:
                summary = "Pick at least one column (X or Y) to plot a box plot."

        fig.update_yaxes(type="linear")
        fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=450,
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        return fig, dbc.Badge(summary, color="secondary", className="p-2")

    except Exception as e:
        return go.Figure(), dbc.Alert(f"Plotting Error: {str(e)}", color="danger")


@app.callback(
    Output("plot-column-x", "value"),
    Output("plot-column-y", "value"),
    Input("store-data", "data"),
)
def reset_plot_selections(data_json):
    return None, []


# ============================================================
# EXPORT & UI TOGGLES CALLBACKS

# Renders whatever is currently in store-data on the Export page. Fires on
# both store-data changes (upload/transpose elsewhere) and on url.pathname
# so it's populated immediately on direct navigation to /export, same fix
# as applied to the Plots dropdowns.
@app.callback(
    Output("export-table-preview", "children"),
    Input("store-data", "data"),
    Input("url", "pathname"),
)
def populate_export_preview(data_json, pathname):
    if pathname != "/export":
        raise PreventUpdate
    if not data_json:
        return dbc.Alert(
            ["No data loaded yet. Upload or transpose a file on the ",
             dcc.Link("Main Menu", href="/main-menu"), " first."],
            color="warning",
        )
    try:
        df = pd.read_json(io.StringIO(data_json), orient="split")
    except Exception as e:
        return dbc.Alert(f"Couldn't read the current data: {e}", color="danger")

    df = _sanitize_columns(df)
    return [
        dbc.Alert([html.B("Currently loaded: "), f"{df.shape[0]} rows, {df.shape[1]} cols"], color="success"),
        dash_table.DataTable(
            columns=[{"name": c, "id": c} for c in df.head(5000).columns],
            data=_records_for_table(df),
            page_size=10,
            style_table={"overflowX": "auto"},
        ),
    ]


@app.callback(
    Output("download-data", "data"),
    Input("btn-download-csv", "n_clicks"),
    State("store-data", "data"),
    prevent_initial_call=True,
)
def download_csv(n, data_json):
    if not data_json:
        raise PreventUpdate
    df = pd.read_json(io.StringIO(data_json), orient="split")
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


@app.callback(
    Output("ma-window-label", "style"),
    Output("ma-window", "style"),
    Input("ma-toggle", "value"),
)
def toggle_ma_window(ma_value):
    # Shows/hides the moving average window size input
    if _is_ma_enabled(ma_value):
        return {"display": "block"}, {"width": "120px", "display": "block"}
    return {"display": "none"}, {"width": "120px", "display": "none"}


# ============================================================
# Run
if __name__ == "__main__":
    atexit.register(temp_dir.cleanup)
    app.run(debug=True, port=4838)