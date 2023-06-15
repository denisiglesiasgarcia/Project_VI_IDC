# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import os
# Set the environment variables for PROJ_LIB and PROJ_DATA
os.environ['PROJ_LIB'] = r'C:\OSGeo4W\share\proj'

from pyproj import Transformer
import shapely
from geoalchemy2 import Geometry, WKTElement
from sqlalchemy import *
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import geojson
import numpy as np
import plotly.graph_objects as go
import psycopg2
from psycopg2 import sql
import geopandas as gpd
import json
from sqlalchemy import create_engine

app = Dash(__name__)

# Establish a connection to the database
conn = psycopg2.connect(
    host="localhost",
    database="postgis_sitg",
    user="postgres",
    password="postgres",
    port="5432")

# Set the schema and table names
table_name = "SCANE_INDICE_MOYENNES_3_ANS"
schema_name = "sitg"

with conn.cursor() as cur:
    # année dropdown
    cur.execute(f"SELECT DISTINCT ANNEE FROM {schema_name}.{table_name} ORDER BY ANNEE ASC")
    results_dropdown_annee = cur.fetchall()

    # Get the headers
    #cur.execute(f"SELECT * FROM {schema_name}.{table_name} WHERE egid::integer = '{egid}' ORDER BY annee ASC")
    cur.execute(f"SELECT DISTINCT ADRESSE FROM {schema_name}.{table_name} ORDER BY ADRESSE ASC")
    results_dropdown_rues = cur.fetchall()

    '''
    # Reno obligatoire
    cur.execute(f"ALTER TABLE {schema_name}.{table_name} ADD COLUMN IF NOT EXISTS renovation TEXT")
    conn.commit()
    cur.execute(f"""UPDATE {schema_name}.{table_name}\
                SET renovation = \
                    CASE\
                        WHEN CAST(INDICE AS INTEGER) < 450 THEN 'En dessous du seuil limite légal de 450 MJ/(m²*an)'\
                        ELSE 'Audit énergétique et travaux obligatoires'\
                    END;
                """)
    conn.commit()
    '''
    
    # SRID
    srid = 4326
    cur.execute(f"UPDATE {schema_name}.{table_name} SET geometry = ST_SetSRID(geometry, {srid})")
    conn.commit()

# année dropdown
dropdown_annee = [{"label": i[0], "value": i[0]} for i in results_dropdown_annee]

# rues dropdown
dropdown_rues = [{"label": i[0], "value": i[0]} for i in results_dropdown_rues]

# Close the connection
cur.close()
conn.close()

# histogramme
## limiter les outliers
limite_outlier = 1000

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
                            value='2021',
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

# --------------------------------------------------------------
# plan rue
@app.callback(
    Output('plan_vue_rue', 'figure'),
    Input('dropdown_nom_rue', 'value'),
    Input('dropdown_annee_idc', 'value'))
def update_graph(nom_rue, annee_idc):
    conn = psycopg2.connect(
        host="localhost",
        database="postgis_sitg",
        user="postgres",
        password="postgres",
        port="5432")

    # Set the schema and table names
    table_name = "SCANE_INDICE_MOYENNES_3_ANS"
    schema_name = "sitg"

    with conn.cursor() as cur:
        # Get the column names
        cur.execute(f"SELECT * FROM {schema_name}.{table_name} LIMIT 1")
        columns = [desc[0] for desc in cur.description]

        # Get the headers with the applied filters
        cur.execute(f"SELECT * FROM {schema_name}.{table_name} WHERE adresse = %s AND annee = %s", (nom_rue, annee_idc))
        headers = cur.fetchall()

    # Print the results
    df = pd.DataFrame(headers, columns=columns)

    # Ensure 'geometry' is a GeoSeries object
    df['geometry'] = gpd.GeoSeries.from_wkb(df['geometry'])

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry='geometry')

    # Set the current CRS for the GeoDataFrame
    gdf.set_crs("EPSG:2056", inplace=True)

    # convert to WGS84
    gdf = gdf.to_crs("EPSG:4326")

    # # Transform the coordinates to WGS84 (EPSG:4326)
    # gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.ops.transform(transformer.transform, geom))

    # Calculate centroid and assign to new columns
    gdf['coordonnees_rue_lat'] = gdf['geometry'].centroid.y
    gdf['coordonnees_rue_lon'] = gdf['geometry'].centroid.x

    mean_lat = gdf['coordonnees_rue_lat'].mean()
    mean_lon = gdf['coordonnees_rue_lon'].mean()

    # convert gdf to geojson
    geojson = gdf.__geo_interface__

    # convert gdf to pandas dataframe and remove geometry column
    df_plot = gdf.drop(columns=['geometry'])

    # Plan
    fig1 = px.choropleth_mapbox(df_plot,
                                geojson=geojson,
                                color="indice",
                                locations="egid",
                                featureidkey="properties.egid",
                                center={"lat": mean_lat, "lon": mean_lon},
                                mapbox_style="carto-positron",
                                title="Plan de situation d'indice pour " + str(nom_rue),
                                zoom=17,
                                labels={'adresse': 'npa'})
    
    # Close the connection
    cur.close()
    conn.close()
    
    return fig1

# graphique bars
@app.callback(
    Output('graphique_bars_idc', 'figure'),
    Input('dropdown_nom_rue', 'value'))
def update_bars(nom_rue):
    conn = psycopg2.connect(
            host="localhost",
            database="postgis_sitg",
            user="postgres",
            password="postgres",
            port="5432")

    # Set the schema and table names
    table_name = "SCANE_INDICE_MOYENNES_3_ANS"
    schema_name = "sitg"

    with conn.cursor() as cur:
        # Get the headers with the applied filters
        cur.execute(f"SELECT annee, indice FROM {schema_name}.{table_name} WHERE adresse = %s ORDER BY annee ASC", (nom_rue,))
        headers = cur.fetchall()

    # Print the results
    df_plot2 = pd.DataFrame(headers, columns=['annee', 'indice'])
    df_plot2['indice'] = df_plot2['indice'].astype(int)
    df_plot2['annee'] = df_plot2['annee'].astype(int)

    # close the connection
    conn.close()
    cur.close()

    fig2 = px.bar(df_plot2, x='annee', y='indice', text_auto=True)

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
    conn = psycopg2.connect(
            host="localhost",
            database="postgis_sitg",
            user="postgres",
            password="postgres",
            port="5432")

    # Set the schema and table names
    table_name = "SCANE_INDICE_MOYENNES_3_ANS"
    schema_name = "sitg"

    limite_outlier = 1000

    with conn.cursor() as cur:
        # Get the headers with the applied filters
        cur.execute(f"SELECT annee, indice FROM {schema_name}.{table_name} WHERE adresse = %s AND annee = %s", (nom_rue, annee_idc))
        headers_idc = cur.fetchall()

        # Get the headers with the applied filters
        cur.execute(f"SELECT annee, indice, renovation FROM {schema_name}.{table_name} WHERE indice::integer < {limite_outlier} AND annee = %s", (annee_idc,))
        headers_histo = cur.fetchall()

    # ligne idc du bâtiment sur histogramme
    idc_annee_calcul = pd.DataFrame(headers_idc, columns=['annee', 'indice'])
    idc_annee_calcul['indice'] = idc_annee_calcul['indice'].astype(int)
    idc_annee_calcul['annee'] = idc_annee_calcul['annee'].astype(int)
    idc_annee_calcul = idc_annee_calcul.iloc[0][1]

    # data histogramme
    df_plot3  = pd.DataFrame(headers_histo, columns=['annee', 'indice', 'renovation'])
    df_plot3['indice'] = df_plot3['indice'].astype(int)
    df_plot3['annee'] = df_plot3['annee'].astype(int)

    # histo
    fig3 = px.histogram(df_plot3, x='indice', pattern_shape='renovation', nbins=25, pattern_shape_sequence=["", "/"])
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
