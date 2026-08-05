# layout.py
import os
import base64
import io
import pandas as pd
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc


class TemplateLayout:
    """Class-based layout generator for the template tool."""
    spin_css = """
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .spin-animation {
        animation: spin 10s linear infinite;
    }
    """

    def __init__(self, temp_dir):
        self.temp_dir = temp_dir

    # ---------------------- Common UI ----------------------
    def navbar(self):
        return dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink("Home", href="/", style={"color": "#FFFFFF", "font-weight": "bold"})),
                dbc.NavItem(
                    dbc.NavLink("Main Menu", href="/main-menu", style={"color": "#FFFFFF", "font-weight": "bold"})),
                dbc.NavItem(dbc.NavLink("Plots", href="/plots", style={"color": "#FFFFFF", "font-weight": "bold"})),
                dbc.NavItem(dbc.NavLink("Export", href="/export", style={"color": "#FFFFFF", "font-weight": "bold"})),
                dbc.NavItem(dbc.NavLink("Help", href="/help", style={"color": "#FFFFFF", "font-weight": "bold"})),
                dbc.NavItem(dbc.NavLink("Modify Charts", href="/s", style={"color": "#FFFFFF", "font-weight": "bold"})),
                dbc.NavItem(
                    dbc.Button(
                        "Invert Colors",
                        id="invert-toggle-btn",
                        color="light",
                        outline=True,
                        size="sm",
                        className="ms-2",
                        n_clicks=0,
                    )
                ),
            ],
            brand=html.Div([
                html.Span("GUI-Template", style={
                    "font-weight": "bold",
                    "background": "linear-gradient(to right, white)",
                    "WebkitBackgroundClip": "text",
                    "WebkitTextFillColor": "transparent",
                    "font-size": "28px",
                }),
            ]),
            brand_href="/",
            dark=True,
            className="mb-4",
            style={
                "background": "linear-gradient(to right, #ff00ef, #00fcff)",
                "border-radius": "0px",
                "padding": "10px",
                "width": "100%",
                "margin": "0",
            },
        )

    # ---------------------- Pages ----------------------
    def create_home_page(self):
        return dbc.Container([
            html.Div(style={
                "position": "fixed",
                "top": 0,
                "left": 0,
                "width": "100%",
                "height": "100%",
                "backgroundImage": "url('https://corru.works/img/static.gif')",
                "backgroundSize": "repeat",
                "backgroundPosition": "center",
                "backgroundRepeat": "repeat",
                "zIndex": -1,
                "opacity": 1,
            }),
            html.Div([
                html.H1([
                    "Welcome to ",
                    html.Span(
                        "Hector's Template",
                        style={
                            "font-weight": "bold",
                            "background": "linear-gradient(to right, #00fcff, #ff00ef)",
                            "WebkitBackgroundClip": "text",
                            "WebkitTextFillColor": "transparent",
                            "font-size": "40px",
                        },
                    ),
                ], style={"font-size": "36px", "text-align": "center", "margin-bottom": "10px"}),
            ], className="mb-2"),
            html.Div([
                html.P(
                    "A template for building software tools using Dash.",
                    style={"font-size": "16px", "line-height": "1.8", "color": "#34495E", "text-align": "center"},
                )
            ], className="mb-2",
                style={"width": "80%", "margin-left": "auto", "margin-right": "auto", "text-align": "center"}),
            html.Div([
                html.H3("Key Features", style={"color": "#000000", "font-weight": "bold"}),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Front-end GUI", className="card-title", style={"color": "#000000"}),
                                html.P("A user-friendly interface for interacting with the tool.",
                                       className="card-text", style={"color": "#7F8C8D"}),
                            ])
                        ], className="shadow-sm mb-2 h-100")
                    ], width=4, className="d-flex"),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Dash Features", className="card-title", style={"color": "#000000"}),
                                html.P("Interactive visualizations with Plotly Dash.", className="card-text",
                                       style={"color": "#7F8C8D"}),
                            ])
                        ], className="shadow-sm mb-2 h-100")
                    ], width=4, className="d-flex"),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Python Development", className="card-title", style={"color": "#000000"}),
                                html.P("Build and deploy Python applications with ease.", className="card-text",
                                       style={"color": "#7F8C8D"}),
                            ])
                        ], className="shadow-sm mb-2 h-100")
                    ], width=4, className="d-flex"),
                ])
            ], className="mb-2"),
            html.Div([
                html.Img(src="https://corru.works/img/mcontours.gif", style={
                    "display": "block",
                    "margin-left": "auto",
                    "margin-right": "auto",
                    "height": "auto",
                    "border-radius": "10000px",
                    "transform": "spin_css",
                })
            ], className="mb-2"),
            html.Div([
                html.H3("Get Started", style={"color": "#000000", "font-weight": "bold", "text-align": "center"}),
                dbc.Button(
                    "Start Now",
                    href="/main-menu",
                    className="mt-2",
                    style={
                        "background-color": "#000000",
                        "color": "white",
                        "border-color": "#000000",
                        "width": "200px",
                        "font-size": "16px",
                        "display": "block",
                        "margin": "0 auto",
                    },
                ),
            ])
        ], style={"padding-top": "10px", "padding-bottom": "10px"})

    def create_main_menu_page(self):
        return dbc.Container([
            html.Div(style={
                "position": "fixed",
                "top": 0,
                "left": 0,
                "width": "100%",
                "height": "100%",
                "backgroundImage": "url('https://corru.works/img/static.gif')",
                "backgroundSize": "repeat",
                "backgroundPosition": "center",
                "backgroundRepeat": "repeat",
                "zIndex": -1,
                "opacity": 1,
            }),
            html.H2("Main Menu", className="mt-3 text-center"),
            html.P("Upload a dataset and preview it.", className="text-center mb-4",
                   style={"font-size": "18px", "color": "#555"}),
            dbc.Row([
                dbc.Col([
                    dcc.Upload(
                        id="upload-data",
                        children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
                        style={
                            "width": "100%",
                            "height": "120px",
                            "lineHeight": "120px",
                            "borderWidth": "2px",
                            "borderStyle": "dashed",
                            "borderRadius": "10px",
                            "textAlign": "center",
                            "margin": "10px",
                            "backgroundColor": "#FBFBFB",
                        },
                        multiple=False,
                    ),
                    html.Div(id="upload-status", className="mt-2"),
                ], width=12),
            ]),
            html.Hr(),
            html.H4("Preview (first 5,000 rows)", className="mt-3"),
            html.Div(id="table-preview"),
            html.Br(),
            dbc.Button("Go to Plots", href="/plots", color="primary", className="me-3"),
            dbc.Button(
                [html.Img(
                    src="https://preview.redd.it/how-it-feels-pressing-refresh-server-list-for-the-500th-v0-31rikka4hyfh1.jpeg?auto=webp&s=bba6c9e463807e1f9271447b8bea0fbf3359187f",
                    style={"height": "20px", "marginRight": "6px"}),
                    "Transpose"],
                id="transpose-btn",
                color="secondary",
                className="me-3",
            ),
        ], fluid=True, style={"padding-bottom": "40px", "padding-left": "10px"})

    def create_plots_page(self):
        return dbc.Container([
            html.Div(style={
                "position": "fixed",
                "top": 0,
                "left": 0,
                "width": "100%",
                "height": "100%",
                "backgroundImage": "url('https://corru.works/img/static.gif')",
                "backgroundSize": "repeat",
                "backgroundPosition": "center",
                "backgroundRepeat": "repeat",
                "zIndex": -1,
                "opacity": 1,
            }),
            html.H2("Plots", className="mt-3 text-center"),
            html.P("Choose a plot type and columns, then explore.", className="text-center mb-4"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Plot type"),
                    dcc.Dropdown(id="plot-kind", options=[
                        {"label": "Scatter", "value": "scatter"},
                        {"label": "Line", "value": "line"},
                        {"label": "Histogram", "value": "hist"},
                        {"label": "Box", "value": "box"},
                    ], value="scatter"),
                ], md=4),
                dbc.Col([
                    dbc.Label("X column"),
                    dcc.Dropdown(id="plot-column-x", options=[]),
                ], md=4),
                dbc.Col([
                    dbc.Label("Y column(s)"),
                    dcc.Dropdown(
                        id="plot-column-y",
                        options=[],
                        multi=True,
                        placeholder="Select one or more columns…",
                    ),
                ], md=4),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Checklist(
                        options=[{"label": " Show Moving Average", "value": "ma"}],
                        value=[],
                        id="ma-toggle",
                        switch=True,
                        inline=True,
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Window size", id="ma-window-label",
                              style={"display": "none"}),
                    dbc.Input(
                        id="ma-window",
                        type="number",
                        value=10,
                        min=2,
                        step=1,
                        style={"width": "120px", "display": "none"},
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Trendline (scatter only)"),
                    # This component was missing entirely, which broke the
                    # whole update_plots callback: every Input listed in a
                    # Dash callback must exist in the current layout, so a
                    # missing "trendline-kind" component caused the callback
                    # to error out every time it tried to fire — meaning
                    # NOTHING plotted, not just the trendline/MA features.
                    dcc.Dropdown(
                        id="trendline-kind",
                        options=[
                            {"label": "None", "value": "none"},
                            {"label": "OLS (linear)", "value": "ols"},
                            {"label": "LOWESS", "value": "lowess"},
                        ],
                        value="none",
                        clearable=False,
                    ),
                ], md=4),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col(dcc.Graph(id="plot-figure"), md=9),
                dbc.Col([
                    html.H5("Summary"),
                    html.Div(id="plot-summary"),
                ], md=3),
            ]),
            html.Br(),
            dbc.Button("Download Figure PNG", id="btn-download-fig",
                       color="secondary", className="me-2"),
            dcc.Download(id="download-fig"),
        ], fluid=True, style={"padding-bottom": "40px"})

    def create_help_page(self):
        return dbc.Container([
            html.Div(style={
                "position": "fixed",
                "top": 0,
                "left": 0,
                "width": "100%",
                "height": "100%",
                "backgroundImage": "url('https://corru.works/img/static.gif')",
                "backgroundSize": "repeat",
                "backgroundPosition": "center",
                "backgroundRepeat": "repeat",
                "zIndex": -1,
                "opacity": 1,
            }),
            html.H1("Help & Documentation", className="text-center mb-4"),
            html.P("Quick tips:", className="text-center mb-4"),
            html.Ul([
                html.Li("Upload CSV/XLSX/JSON on Main Menu."),
                html.Li("Pick plot type/columns on Plots page."),
                html.Li("Export the uploaded data or the current figure."),
                html.Li("This is a template—extend callbacks as needed."),
            ], className="mb-4"),
            dbc.Alert("Need a custom feature? Add new Stores and callbacks.", color="info"),
        ], fluid=True)

    def create_export_page(self):
        return dbc.Container([
            html.Div(style={
                "position": "fixed",
                "top": 0,
                "left": 0,
                "width": "100%",
                "height": "100%",
                "backgroundImage": "url('https://corru.works/img/static.gif')",
                "backgroundSize": "repeat",
                "backgroundPosition": "center",
                "backgroundRepeat": "repeat",
                "zIndex": -1,
                "opacity": 1,
            }),
            html.H1("Export Page", className="text-center mt-4"),
            html.H2("View Spreadsheet", className="mt-3 text-center"),
            html.P("This shows whatever dataset is currently loaded (uploaded or transposed "
                   "on the Main Menu).", className="text-center mb-4",
                   style={"font-size": "18px", "color": "#555"}),
            html.Hr(),
            html.H4("Preview (first 5,000 rows)", className="mt-3"),
            # Populated from store-data by a dedicated callback (see app.py:
            # populate_export_preview) rather than re-using the Main Menu's
            # "table-preview"/"upload-data" ids, which would either require
            # a confusing duplicate upload control here or a second
            # callback writing to the same Output (not allowed without
            # allow_duplicate).
            dcc.Loading(html.Div(id="export-table-preview"), type="default"),
            html.Br(),
            dbc.Button("Go to Main Menu", href="/main-menu", color="secondary", className="me-3"),
            dbc.Button("Go to Plots", href="/plots", color="primary", className="me-3"),
            dbc.Button("Download CSV", id="btn-download-csv", color="primary", className="m-3"),
            dcc.Download(id="download-data")
        ])

    def create_s_page(self):
        return dbc.Container([
            html.Div(style={

                "position": "fixed",
                "top": 0,
                "left": 0,
                "width": "100%",
                "height": "100%",
                "backgroundImage": "url('https://corru.works/img/static.gif')",
                "backgroundSize": "repeat",
                "backgroundPosition": "center",
                "backgroundRepeat": "repeat",
                "zIndex": -1,
                "opacity": 1,
            }),
            html.Div([
                html.H1([
                    "Welcome to ",
                    html.Span(
                        "kyle's Template",
                        style={
                            "font-weight": "bold",
                            "background": "linear-gradient(to right, red, orange, yellow, green, blue, indigo, violet)",
                            "WebkitBackgroundClip": "text",
                            "WebkitTextFillColor": "transparent",
                            "font-size": "40px",
                        },
                    ),
                ], style={"font-size": "36px", "text-align": "center", "margin-bottom": "10px"}),
            ], className="mb-2"),
            html.Div([
                html.P(
                    "A template for building software tools using Dash.",
                    style={"font-size": "16px", "line-height": "1.8", "color": "#34495E", "text-align": "center"},
                )
            ], className="mb-2",
                style={"width": "80%", "margin-left": "auto", "margin-right": "auto", "text-align": "center"}),
            html.Div([
                html.H3("Key Features", style={"color": "#000000", "font-weight": "bold"}),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Front-end GUI", className="card-title", style={"color": "#000000"}),
                                html.P("A user-friendly interface for interacting with the tool.",
                                       className="card-text", style={"color": "#7F8C8D"}),
                            ])
                        ], className="shadow-sm mb-2 h-100")
                    ], width=4, className="d-flex"),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Dash Features", className="card-title", style={"color": "#000000"}),
                                html.P("Interactive visualizations with Plotly Dash.", className="card-text",
                                       style={"color": "#7F8C8D"}),
                            ])
                        ], className="shadow-sm mb-2 h-100")
                    ], width=4, className="d-flex"),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Python Development", className="card-title", style={"color": "#000000"}),
                                html.P("Build and deploy Python applications with ease.", className="card-text",
                                       style={"color": "#7F8C8D"}),
                            ])
                        ], className="shadow-sm mb-2 h-100")
                    ], width=4, className="d-flex"),
                ])
            ], className="mb-2"),
            html.Div([
                html.Img(src="https://static.wikitide.net/corruwiki/8/81/Funfriend.gif", style={
                    "display": "block",
                    "margin-left": "auto",
                    "margin-right": "auto",
                    "max-width": "120%",
                    "height": "auto",
                    "border-radius": "10px",
                    "box-shadow": "0 0px 0px rgba(0, 0, 0, 0.1)",
                })
            ], className="mb-2"),
            html.Div([
                html.H3("Get Started", style={"color": "#000000", "font-weight": "bold", "text-align": "center"}),
                dbc.Button(
                    "Start Now",
                    href="/main-menu",
                    className="mt-2",
                    style={
                        "background-color": "#000000",
                        "color": "white",
                        "border-color": "#000000",
                        "width": "200px",
                        "font-size": "16px",
                        "display": "block",
                        "margin": "0 auto",
                    },
                ),
            ])
        ], style={"padding-top": "10px", "padding-bottom": "10px"})