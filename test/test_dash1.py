# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import geojson
import gzip

app = Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

df1 = pd.read_csv(r"C:\Users\denis.iglesias\Documents\Project_VI_IDC\SCANE_INDICE_MOYENNES_3_ANS.csv", sep=';', usecols= ['ANNEE', 'EGID', 'ADRESSE', 'SRE', 'INDICE'], encoding='latin1')

with open(r"C:\Users\denis.iglesias\Documents\Project_VI_IDC\test\indice3ans_epsg_4326_light.geojson", encoding='latin1') as f:
    geojson_idc = geojson.load(f)

fig = px.choropleth_mapbox(df1,
                            geojson=geojson_idc,
                            color="INDICE",
                            locations="ADRESSE",
                            featureidkey="properties.ADRESSE",
                            center={"lat": 46.2022200, "lon": 6.1456900},
                            mapbox_style="carto-positron",
                            zoom=11)

app.layout = html.Div(children=[
    #titre
    html.H1(children='Hello Dash'),
    #sous-titre
    html.Div(children='''
        Dash: A web application framework for your data.
    '''),
    #dropdown
    html.Div(children=[html.Br(),
        html.Label('Multi-Select Dropdown'),
        dcc.Dropdown(df1['ADRESSE'],
                    multi=False,
                    id='dropdown_test')],
                    style={'padding': 10, 'flex': 1}),
    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

@app.callback(
    Output(component_id='my-output', component_property='children'),
    Input(component_id='dropdown_test', component_property='value')
)
def update_output_div(input_value):
    return f'Output: {input_value}'

if __name__ == '__main__':
    app.run_server(debug=True)
