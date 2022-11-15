'''
conda install -c conda-forge dash
conda install -c conda-forge geojson
fichier requirements?
'''

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import geojson
import numpy as np

app = Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

# dataframe pour la vue canton
df1 = pd.read_csv(r"C:\Users\denis.iglesias\sourcetree\Project_VI_IDC\SCANE_INDICE_MOYENNES_3_ANS.csv", sep=';', usecols= ['ANNEE', 'EGID', 'ADRESSE', 'SRE', 'INDICE'], encoding='latin1')

# année dropdown
dropdown_annee = df1.ANNEE.unique()
dropdown_annee.sort()
# rues dropdown
df1['ADRESSE'] = df1['ADRESSE'].astype(str)
dropdown_rues = df1.ADRESSE.unique()
dropdown_rues = np.sort(dropdown_rues)

with open(r"C:\Users\denis.iglesias\sourcetree\Project_VI_IDC\test\indice3ans_epsg_4326_light.geojson", encoding='latin1') as f:
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
        Année IDC.
    '''),
    #dropdown rues
    html.Div(children=[html.Br(),
        html.Label('Sélectionner nom de rue'),
        dcc.Dropdown(dropdown_rues,
                    'Rue CAVOUR 20',
                    multi=False,
                    id='dropdown_nom_rue')],
                    style={'padding': 10, 'flex': 1}),
    #graphique canton
    dcc.Graph(
        id='plan_canton',
        figure=fig
        ),
    #graphique zoom sur rue
    dcc.Graph(
        id='plan_vue_rue'
        ),
    #dropdown année
    dcc.Dropdown(dropdown_annee,
                '2021',
                id='dropdown_annee_idc'),
    #graphique de bars idc
    dcc.Graph(
        id='graphique_bars_idc'
        )
])

# plan rue
@app.callback(
    Output('plan_vue_rue', 'figure'),
    Input('dropdown_nom_rue', 'value')
)
def update_graph(nom_rue):
    # filter les données. Pas sur que ça soit utile
    df_rue = df1[df1['ADRESSE']==nom_rue]
    # boucle pour avoir les coordonnées lat/lon pour le plan zoom
    for i in range(1000000):
        if geojson_idc['features'][i]['properties']['ADRESSE'] == nom_rue:
            coordonnees_rue_lon = geojson_idc['features'][i]['geometry']['coordinates'][0][0][0][0]
            coordonnees_rue_lat = geojson_idc['features'][i]['geometry']['coordinates'][0][0][0][1]
            break
    # Plan        
    fig1 = px.choropleth_mapbox(df_rue,
                            geojson=geojson_idc,
                            color="INDICE",
                            locations="ADRESSE",
                            featureidkey="properties.ADRESSE",
                            center={"lat": coordonnees_rue_lat, "lon": coordonnees_rue_lon},
                            mapbox_style="carto-positron",
                            zoom=17)
    return fig1

# graphique bars
@app.callback(
    Output('graphique_bars_idc', 'figure'),
    Input('dropdown_nom_rue', 'value')
)
def update_bars(nom_rue):
    # filtrer dataframe
    df_plot = df1[df1['ADRESSE']==nom_rue]
    df_plot = df_plot[['ANNEE','INDICES']]
    df_plot = df_plot.sort_values(by=['ANNEE'])

    fig2 = px.bar(df_plot, x='ANNEE', y='INDICE')

    return fig2

# graphique histogramme
@app.callback(
    Output('graphique_bars_idc', 'figure'),
    Input('dropdown_nom_rue', 'value')
    Input('dropdown_annee_idc', 'value')
)
def update_bars(nom_rue, annee_idc):
    # filtrer dataframe
    df_plot = df1[df1['ADRESSE']==nom_rue] # ajouter le filtre de l'année
    df_plot = df_plot[['ANNEE','INDICES']]
    df_plot = df_plot.sort_values(by=['ANNEE'])

    fig2 = px.histogram(df1, x="INDICE", nbins=20,\
        labels={'x':'Indice de dépense de chaleur [MJ/(m²*an)]', 'y':'Nombre de bâtiments'})
    fig.add_vline(x=np.median(df.total_bill), line_dash = 'dash', line_color = 'firebrick')

    return fig2


if __name__ == '__main__':
    app.run_server(debug=True)
