from app import app
from app import server
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
from datetime import datetime
import pandas as pd
from PriceIndices import MarketHistory, Indices
import dash_table

history = MarketHistory()
df = history.get_price("tezos", "2017-04-28", "2021-05-07")  # Get Bitcoin price data
df["date"] = pd.to_datetime(df["date"])
colors = {"background": "#111111", "background2": "#FF0", "text": "yellow"}


def get_data_table():
    data_table = dash_table.DataTable(
        id="datatable-data",
        data=df.to_dict("records"),
        columns=[{"id": c, "name": c} for c in df.columns],
        style_table={"overflowY": "scroll"},
        fixed_rows={"headers": True, "data": 10},
        style_cell={"width": "100px"},
        style_header={"backgroundColor": "rgb(230, 230, 230)", "fontWeight": "bold"},
    )
    return data_table


app.layout = html.Div(
    [
        html.H1(
            "Bitcoin Price Graph", style={"textAlign": "center", "background": "yellow"}
        ),
        html.Div(
            [
                "Date selector for graphs.",  # add DateRangePicker here
                dcc.DatePickerRange(
                    id="date-input",
                    stay_open_on_select=False,
                    min_date_allowed=datetime(2013, 4, 28),
                    max_date_allowed=datetime.now(),
                    initial_visible_month=datetime.now(),
                    start_date=datetime(2019, 1, 1),
                    end_date=datetime.now(),
                    number_of_months_shown=2,
                    month_format="MMMM,YYYY",
                    display_format="YYYY-MM-DD",
                    style={"color": "#11ff3b", "font-size": "18px"},
                ),
                html.Div(id="date-output"),
            ],
            className="row ",
            style={
                "marginTop": 0,
                "marginBottom": 0,
                "font-size": 30,
                "color": "white",
            },
        ),
        html.Div(id="graph-output"),
        html.Div(
            children=[
                html.H1(
                    children="Data Table",  # html for table
                    style={"textAlign": "center", "background": "yellow"},
                ),
                get_data_table(),
            ]
        ),
        html.Div(
            children=[dcc.Markdown("This guy cannot pick colors")],  # markdown
            style={"textAlign": "center", "background": "black"},
        ),
    ],
    style={"background": "#000080"},
)


@app.callback(
    Output("graph-output", "children"),
    [
        Input("date-input", "start_date"),  # Add start date
        Input("date-input", "end_date"),
    ],
)  # Add end date
def render_graph(start_date, end_date):
    data = df[(df.date >= start_date) & (df.date <= end_date)]
    return dcc.Graph(
        id="graph-1",
        figure={
            "data": [
                {
                    "x": data["date"],
                    "y": data["price"],
                    "type": "line",
                    "name": "value1",
                },
            ],
            "layout": {
                "title": "Simple Line Graph",
                "plot_bgcolor": colors["background"],
                "paper_bgcolor": colors["background"],
                "font": {"color": colors["text"], "size": 18},
                "xaxis": {
                    "title": "Price",
                    "showspikes": True,
                    "spikedash": "dot",
                    "spikemode": "across",
                    "spikesnap": "cursor",
                },
                "yaxis": {
                    "title": "Time",
                    "showspikes": True,
                    "spikedash": "dot",
                    "spikemode": "across",
                    "spikesnap": "cursor",
                },
            },
        },
    )


if __name__ == "__main__":
    app.run_server(debug=True)
