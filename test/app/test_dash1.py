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
import plotly.graph_objects as go
import geopandas as gpd
import psycopg2


#conn = psycopg2.connect(database='postgres', user='postgres', password='docker', host='127.0.0.1', port='5432')
#curs = conn.cursor()


app = Dash(__name__)

# dataframe pour la vue canton
df1 = pd.read_csv(r"../data/SCANE_INDICE_MOYENNES_3_ANS.csv", sep=';', usecols= ['ANNEE', 'EGID', 'ADRESSE', 'SRE', 'INDICE'], encoding='latin1')
# geojson
with open(r"../data/indice3ans_epsg_4326_superlight.geojson", encoding='latin1') as f:
    geojson_idc = geojson.load(f)
# geodataframe du geojson
gdf = gpd.read_file(r"../data/indice3ans_epsg_4326_superlight.geojson")

# année dropdown
dropdown_annee = gdf.ANNEE.unique()
dropdown_annee.sort()
# rues dropdown
gdf['ADRESSE'] = gdf['ADRESSE'].astype(str)
dropdown_rues = gdf.ADRESSE.unique()
dropdown_rues = np.sort(dropdown_rues)

# histogramme
## limiter les outliers
limite_outlier = 1000
## colonnes pour indiquer si réno obligatoire
def categorise(row):
    if row['INDICE'] < 450:
        return 'En dessous du seuil limite légal de 450 MJ/(m²*an)'
    else:
        return 'Audit énergétique et travaux obligatoires'
df1['renovation'] = df1.apply(lambda row: categorise(row), axis=1)



'''
fig = px.choropleth_mapbox(df1,
                            geojson=geojson_idc,
                            color="INDICE",
                            locations="ADRESSE",
                            featureidkey="properties.ADRESSE",
                            center={"lat": 46.2022200, "lon": 6.1456900},
                            mapbox_style="carto-positron",
                            zoom=11)
'''


# --------------------------------------------------------------

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

app.layout = html.Div(
    children=[
        # en-tête
        html.Div(
            children=[
                html.P(children="🥑", className="header-emoji"),
                html.H1(
                    children="Consommation d'énergie des bâtiments à Genève", className="header-title"
                ),
                html.P(
                    children="Dashboard pour permettre de voir l'évolution de la consommation d'énergie des bâtiments à Genève.",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        # menu
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Adresse", className="menu-title"),
                        dcc.Dropdown(
                            id="dropdown_nom_rue",
                            options=dropdown_rues,
                            value="Rue CAVOUR 20",
                            clearable=True,
                            multi=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Année IDC", className="menu-title"),
                        dcc.Dropdown(
                            id="dropdown_annee_idc",
                            options=dropdown_annee,
                            value=2021,
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        # graphiques
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="plan_vue_rue", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="graphique_bars_idc", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="graphique_histo_canton", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
    ]
)
'''    
    #dropdown rues
    html.Div(children=[html.Br(),
        html.Label('Sélectionner nom de rue'),
        dcc.Dropdown(dropdown_rues,
                    'Rue CAVOUR 20',
                    multi=False,
                    id='dropdown_nom_rue')],
                    style={'padding': 10, 'flex': 1}),
    #dropdown année
    dcc.Dropdown(dropdown_annee,
        '2021',
        id='dropdown_annee_idc'),
    
    #graphique zoom sur rue
    dcc.Graph(
        id='plan_vue_rue'
        ),
    #graphique de bars idc
    dcc.Graph(
        id='graphique_bars_idc'
        ),
    #graphique histo comparatif
    dcc.Graph(
        id='graphique_histo_canton'
        )
])
'''

# --------------------------------------------------------------
# plan rue
@app.callback(
    Output('plan_vue_rue', 'figure'),
    Input('dropdown_nom_rue', 'value'),
    Input('dropdown_annee_idc', 'value'))
def update_graph(nom_rue, annee_idc):
    # filter les données. Pas sur que ça soit utile
    df_rue = df1[df1['ADRESSE']==nom_rue]
    df_rue = df_rue[df_rue['ANNE']==annee_idc]
    # avoir les coordonnées lat/lon pour le plan zoom. Sûrement on peut simplifier
    gdf1 = gdf[['ADRESSE', 'geometry']]
    gdf1 = gdf1.drop_duplicates(subset=['ADRESSE'])
    gdf1 = gdf1.sort_values(by=['ADRESSE'])
    gdf1 = gdf1[gdf1['ADRESSE']==nom_rue]
    multipolygon = gdf1['geometry'].iloc[0]

    points = []
    #todo optimize?
    for polygon in multipolygon:
        points.extend(polygon.exterior.coords[:-1])
    coordonnees_rue_lon = points[0][0]
    coordonnees_rue_lat = points[0][1]

    # Plan        
    fig1 = px.choropleth_mapbox(df_rue,
                            geojson=geojson_idc,
                            color="INDICE",
                            locations="ADRESSE",
                            featureidkey="properties.ADRESSE",
                            center={"lat": coordonnees_rue_lat, "lon": coordonnees_rue_lon},
                            mapbox_style="carto-positron",
                            title="Plan de situation d'indice pour " + str(nom_rue),
                            zoom=17)
    return fig1

# graphique bars
@app.callback(
    Output('graphique_bars_idc', 'figure'),
    Input('dropdown_nom_rue', 'value'))
def update_bars(nom_rue):
    # filtrer dataframe
    df_plot2 = df1[df1['ADRESSE']==nom_rue]
    df_plot2 = df_plot2[['ANNEE','INDICE']]
    df_plot2 = df_plot2.sort_values(by=['ANNEE'])
    # bars
    fig2 = px.bar(df_plot2, x='ANNEE', y='INDICE', text_auto=True)

    fig2.update_layout(
        title="Indice de dépense de chaleur [MJ/(m²*an)] le bâtiment situé: " + str(nom_rue),
        xaxis_title="Années",
        yaxis_title="Indice de dépense de chaleur [MJ/(m²*an)]",
        legend_title="Légende",
        xaxis = dict(tickmode = 'linear', dtick = 1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        modebar = dict(bgcolor='rgba(0, 0, 0, 0)') # RGB (224,215,255) rgba(0, 0, 0, 0)
        #bargap=0.0
        )
    fig2.update_traces(marker=dict(
        color="teal"), #teal
        width = 0.1, #0.2
        textfont_size=12,
        textangle=0,
        textposition="outside",
        cliponaxis=True)
    fig2.update_layout(uniformtext_minsize=12, uniformtext_mode='show')
    fig2.update_yaxes(visible=False)
    return fig2

# graphique histogramme général
@app.callback(
    Output('graphique_histo_canton', 'figure'),
    Input('dropdown_nom_rue', 'value'),
    Input('dropdown_annee_idc', 'value'))
def update_histo(nom_rue, annee_idc):
    df_plot3 = df1[['ANNEE','INDICE','renovation']]
    df_plot3 = df_plot3[df_plot3['INDICE']< limite_outlier]
    df_plot3 = df_plot3.sort_values(by=['ANNEE'])
    df_plot3 = df_plot3[df_plot3['ANNEE']==annee_idc]
    # calcul valeur idc sur histogramme
    idc_annee_calcul = df1[['ADRESSE','ANNEE','INDICE']]
    idc_annee_calcul = idc_annee_calcul[(idc_annee_calcul['ADRESSE']==nom_rue) & (idc_annee_calcul['ANNEE'] == annee_idc)]
    idc_annee_calcul = idc_annee_calcul.iloc[0][2]
    # histo
    fig3 = px.histogram(df_plot3, x='INDICE', pattern_shape='renovation', nbins=25, pattern_shape_sequence=["", "/"])
    ## ligne verticale
    #fig3.add_vline(x=idc_annee_calcul, line_dash = 'dash', line_color = 'black', name=nom_rue)
    fig3.add_trace(go.Scatter(x=[idc_annee_calcul,idc_annee_calcul],
        y=[25,2500], 
        mode='lines', 
        line=dict(color='black', width=3, dash='dash'),
        name=nom_rue + ' IDC ' + str(annee_idc)))
    ## rendre joli le truc
    fig3.update_layout(
        title="Histogramme des bâtiments du canton " + str(annee_idc),
        xaxis_title="Indice de dépense de chaleur [MJ/(m²*an)]",
        yaxis_title="Nombre de bâtiments",
        legend_title="Légende",
        ### xticks
        xaxis = dict(tickmode = 'linear', dtick = 50),
        ### modifier couleur fond et style
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        modebar = dict(bgcolor='rgba(0, 0, 0, 0)'),
        bargap=0.10)
    ## couleur de histo
    fig3.update_traces(marker=dict(color="teal", line_color="black"))
    return fig3

# --------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
