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
import psycopg2
from psycopg2 import sql
import geopandas as gpd
import json

POSTGRES_PASSWORD='postgis'
POSTGRES_USER='postgis'
POSTGRES_DB='mydatabase'
POSTGRES_table_name='indice3ans_epsg_4326_superlight'
POSTGRES_HOST='localhost'
POSTGRES_PORT='5432'



app = Dash(__name__)

# année dropdown
with psycopg2.connect(database=POSTGRES_DB,
                      user=POSTGRES_USER,
                      password=POSTGRES_PASSWORD,
                      host=POSTGRES_HOST,
                      port=POSTGRES_PORT) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ANNEE 
            FROM """ + POSTGRES_table_name + """
            ORDER BY ANNEE ASC;
        """)
        results_dropdown_annee = cur.fetchall()
dropdown_annee = [{"label": i[0], "value": i[0]} for i in results_dropdown_annee]

# rues dropdown
with psycopg2.connect(database=POSTGRES_DB,
                      user=POSTGRES_USER,
                      password=POSTGRES_PASSWORD,
                      host=POSTGRES_HOST,
                      port=POSTGRES_PORT) as conn:
       with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ADRESSE 
            FROM """ + POSTGRES_table_name + """
            ORDER BY ADRESSE ASC;
        """)
        results_dropdown_rues = cur.fetchall()
dropdown_rues = [{"label": i[0], "value": i[0]} for i in results_dropdown_rues]


# histogramme
## limiter les outliers
limite_outlier = 1000
## colonnes pour indiquer si réno obligatoire
# alter and update table
with psycopg2.connect(database=POSTGRES_DB,
                      user=POSTGRES_USER,
                      password=POSTGRES_PASSWORD,
                      host=POSTGRES_HOST,
                      port=POSTGRES_PORT) as conn:
      with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE """ + POSTGRES_table_name + """
            ADD COLUMN IF NOT EXISTS renovation TEXT;
        """)
        conn.commit() # We commit the transaction because ALTER is a DDL(Data Definition Language) command.

        cur.execute("""
            UPDATE """ + POSTGRES_table_name + """
            SET renovation = 
                CASE
                    WHEN INDICE < 450 THEN 'En dessous du seuil limite légal de 450 MJ/(m²*an)'
                    ELSE 'Audit énergétique et travaux obligatoires'
                END;
        """)
        conn.commit() # commit this transaction as well

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

# --------------------------------------------------------------
# plan rue
@app.callback(
    Output('plan_vue_rue', 'figure'),
    Input('dropdown_nom_rue', 'value'),
    Input('dropdown_annee_idc', 'value'))
def update_graph(nom_rue, annee_idc):
    
    conn = psycopg2.connect(
        dbname="mydatabase",
        user="postgis",
        password="postgis",
        host="localhost",
        port="5432"
    )

    sql_query = f"""
        SELECT *,
            ST_Y(ST_Centroid(ST_Transform(geometry, 4326))) AS coordonnees_rue_lat,
            ST_X(ST_Centroid(ST_Transform(geometry, 4326))) AS coordonnees_rue_lon
        FROM indice3ans_epsg_4326_superlight
        WHERE "ADRESSE" = %s AND "ANNE" = %s
    """

    df_rue = gpd.read_postgis(sql_query, params=(nom_rue, annee_idc), con=conn, geom_col='geometry')

    conn.close()

    # Convert the GeoDataFrame to GeoJSON
    geojson_idc = json.loads(df_rue.to_json())

    # Plan
    fig1 = px.choropleth_mapbox(df_rue,
                                geojson=geojson_idc,
                                color="INDICE",
                                locations="ADRESSE",
                                featureidkey="properties.ADRESSE",
                                center={"lat": df_rue['coordonnees_rue_lat'].iloc[0], "lon": df_rue['coordonnees_rue_lon'].iloc[0]},
                                mapbox_style="carto-positron",
                                title="Plan de situation d'indice pour " + str(nom_rue),
                                zoom=17)
    return fig1

# graphique bars
@app.callback(
    Output('graphique_bars_idc', 'figure'),
    Input('dropdown_nom_rue', 'value'))
def update_bars(nom_rue):
    conn = psycopg2.connect(
        dbname="mydatabase",
        user="postgis",
        password="postgis",
        host="localhost",
        port="5432"
    )

    sql_query = f"""
        SELECT "ANNEE", "INDICE"
        FROM indice3ans_epsg_4326_superlight
        WHERE "ADRESSE" = %s
        ORDER BY "ANNEE"
    """

    df_plot2 = pd.read_sql_query(sql_query, params=(nom_rue,), con=conn)

    conn.close()

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
    conn = psycopg2.connect(
        dbname="mydatabase",
        user="postgis",
        password="postgis",
        host="localhost",
        port="5432"
    )

    sql_query = f"""
        SELECT "ANNEE", "INDICE", "renovation"
        FROM your_table_name
        WHERE "INDICE" < %s AND "ANNEE" = %s
        ORDER BY "ANNEE"
    """

    df_plot3 = pd.read_sql_query(sql_query, params=(limite_outlier, annee_idc), con=conn)

    sql_query_idc = f"""
        SELECT "INDICE"
        FROM your_table_name
        WHERE "ADRESSE" = %s AND "ANNEE" = %s
    """

    idc_annee_calcul = pd.read_sql_query(sql_query_idc, params=(nom_rue, annee_idc), con=conn).iloc[0][0]

    conn.close()

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
