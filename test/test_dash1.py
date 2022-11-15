#conda install -c conda-forge dash
#conda install -c conda-forge geojson

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

# dataframe pour la vue canton
df1 = pd.read_csv(r"C:\Users\denis\sourcetree\Project_VI_IDC\SCANE_INDICE_MOYENNES_3_ANS.csv", sep=';', usecols= ['ANNEE', 'EGID', 'ADRESSE', 'SRE', 'INDICE'], encoding='latin1')

df2 = pd.read_csv(r"C:\Users\denis\sourcetree\Project_VI_IDC\SCANE_INDICE_MOYENNES_3_ANS.csv", sep=';', usecols= ['ANNEE', 'EGID', 'ADRESSE', 'SRE', 'INDICE'], encoding='latin1')
#df2 = df2[df2['ADRESSE']==filtre_rue]

with open(r"C:\Users\denis\sourcetree\Project_VI_IDC\test\indice3ans_epsg_4326_light.geojson", encoding='latin1') as f:
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
    html.H1(children='Visualisation'),
    #sous-titre
    html.Div(children='''
        Dash: A web application framework for your data.
    '''),
    #dropdown année
    dcc.Dropdown(
                df1['ANNEE'].unique().sort(),
                '2021',
                id='annee_idc',
            ),
    #dropdown rues
    html.Div(children=[html.Br(),
        html.Label('Multi-Select Dropdown'),
        dcc.Dropdown(df1['ADRESSE'],
                    multi=False,
                    id='dropdown_test')],
                    style={'padding': 10, 'flex': 1}),
    #graphique canton
    dcc.Graph(
        id='example-graph',
        figure=fig
    ),
    #graphique petit
        dcc.Graph(
        id='example-graph',
        figure=fig_petit)
])

@app.callback(
    Output(component_id='my-output', component_property='figure'),
    Input(component_id='dropdown_test', component_property='value')
)
def update_graph_rue(nom_rue):
    
    df_rue = df1[df1['ADRESSE']==nom_rue]

    fig = px.choropleth_mapbox(df_rue,
                            geojson=geojson_idc,
                            color="INDICE",
                            locations="ADRESSE",
                            featureidkey="properties.ADRESSE",
                            center={"lat": 46.2022200, "lon": 6.1456900},
                            mapbox_style="carto-positron",
                            zoom=11)
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
