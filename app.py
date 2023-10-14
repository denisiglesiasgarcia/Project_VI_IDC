# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import os
# Set the environment variables for PROJ_LIB and PROJ_DATA
os.environ['PROJ_LIB'] = r'C:\OSGeo4W\share\proj'

from pyproj import Transformer
import shapely
from geoalchemy2 import Geometry, WKTElement
from sqlalchemy import *
from dash import Dash, html, dcc, Input, Output, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import State
import plotly.express as px
import pandas as pd
import geojson
import numpy as np
import plotly.graph_objects as go
import psycopg2
from psycopg2 import sql
import psycopg2.extras
import geopandas as gpd
import json
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import seaborn as sns
from skimage import io
import base64
import datetime

from graphics.performance_par_site import performance_par_site
from graphics.performance_site_general import performance_site_general

app = Dash(__name__, suppress_callback_exceptions=True)


# --------------------------------------------------------------
# data AMOén
# --------------------------------------------------------------

df_amoen = pd.read_excel(r"C:\Users\denis.iglesias\OneDrive - HESSO\01 Institution\02 Projets\12 AMOén\03 Projets\Suivi_projets_AMOen_dernier.xlsx",sheet_name="Vue ensemble")
df_amoen = df_amoen.dropna(subset=['Nom_projet'])
df_amoen = df_amoen.drop(columns=['N°', 'résèrve', 'COP', 'AMO\nrex', 'Priorité',])

dropdown_projet = [{"label": val, "value": val} for val in df_amoen['Nom_projet'].unique() if val is not None]

# préparer df pour stacked bar
df_analyse_stacked = df_amoen
df_analyse_stacked = df_analyse_stacked[['statut',
                                        'Nom_projet',
                                         'Ef,obj*fp (Objectif en EF pondérée après) [MJ/m²]',
                                         'Ef,après,corr*fp (Conso. mesurée après) [MJ/m²]',
                                         ]]
df_analyse_stacked = df_analyse_stacked.groupby(['statut']).count()
df_analyse_stacked = df_analyse_stacked.reset_index()
# Objectif fixé / Réception d'index
df_analyse_stacked = df_analyse_stacked.rename(columns={'Ef,obj*fp (Objectif en EF pondérée après) [MJ/m²]': 'Objectif fixé',
                                                        'Ef,après,corr*fp (Conso. mesurée après) [MJ/m²]': 'Réception d\'index'})
df_analyse_stacked['Objectif fixé'] = df_analyse_stacked['Objectif fixé'] - df_analyse_stacked['Réception d\'index']
# Finalisé
df_analyse_stacked["Finalisé"] = df_analyse_stacked[df_analyse_stacked["statut"] == "Terminé"]['Nom_projet']
df_analyse_stacked["Finalisé"] = df_analyse_stacked["Finalisé"].fillna(0)
df_analyse_stacked["Finalisé"] = df_analyse_stacked["Finalisé"].astype(int)
df_analyse_stacked.loc[df_analyse_stacked["statut"] == "Terminé", 'Objectif fixé'] = 0
df_analyse_stacked.loc[df_analyse_stacked["statut"] == "Terminé", 'Réception d\'index'] = 0
# Pas d'objectif fixé
df_analyse_stacked["Pas d'objectif fixé"] = df_analyse_stacked['Nom_projet'] - \
                                            df_analyse_stacked['Objectif fixé'] - \
                                            df_analyse_stacked['Réception d\'index'] - \
                                            df_analyse_stacked['Finalisé']
df_analyse_stacked["Pas d'objectif fixé"] = df_analyse_stacked["Pas d'objectif fixé"].fillna(0)
df_analyse_stacked["Pas d'objectif fixé"] = df_analyse_stacked["Pas d'objectif fixé"].astype(int)
#df_analyse_stacked = df_analyse_stacked.drop(columns=['Nom_projet'])
df_analyse_stacked['total'] = df_analyse_stacked['Objectif fixé'] + df_analyse_stacked['Réception d\'index'] + df_analyse_stacked["Pas d'objectif fixé"] + df_analyse_stacked["Finalisé"]
# add in column status at the end a row total that sums all the values
df_analyse_stacked = df_analyse_stacked[['statut','Pas d\'objectif fixé','Objectif fixé', 'Réception d\'index', 'Finalisé']] #,'total','Nom_projet'
# changer ordre des statuts
# https://stackoverflow.com/questions/57161380/changing-row-order-in-pandas-dataframe-without-losing-or-messing-up-data
cats = ['Etude', "Demande d’autorisation", "En travaux", "En exploitation","Terminé"]
df_analyse_stacked['statut'] = pd.CategoricalIndex(df_analyse_stacked['statut'], ordered=True, categories=cats)
df_analyse_stacked = df_analyse_stacked.sort_values('statut')
# replace in column statut the value Terminé by Finalisé
df_analyse_stacked['statut'] = df_analyse_stacked['statut'].replace('Demande d’autorisation', 'Autor.')
df_analyse_stacked['statut'] = df_analyse_stacked['statut'].replace('En travaux', 'Travaux')
df_analyse_stacked['statut'] = df_analyse_stacked['statut'].replace('En exploitation', 'Exploit.')
# reset index
df_analyse_stacked = df_analyse_stacked.reset_index(drop=True)


LISTE_TERMINE_EXPLOITATION = ['Saule 99-101 et 81-85',
                              'Bossons 82-88_RG',
                              'Michel-Chauvet 6-8_Rentes Genevoises',
                              'Lully 2_coopérative',
                              'Lausanne 42-44_Implenia',
                              'Clochette 6_CAP',
                              'Golette 20_Meyrin',
                              'Montagne 4-10_Mathez',
                              'Lamartine 27_Bersier',
                              'Prulay 37 à 41_Batineg',
                              'Prulay 43 à 47_Batineg']
# --------------------------------------------------------------
# data SITG
# --------------------------------------------------------------


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

# image performance globales
image_filename_performance_site_general = performance_site_general(df_amoen, LISTE_TERMINE_EXPLOITATION)
#encoded_image_site_general = base64.b64encode(open(image_filename_performance_site_general, 'rb').read())
with open(image_filename_performance_site_general, "rb") as image:
    encoded_image_site_general = base64.b64encode(image.read()).decode('utf-8')
#os.remove(image_filename_performance_site_general) # delete the image file

# --------------------------------------------------------------

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

projects_layout = html.Div(
    children=[
        # Header
        html.Div(
            children=[
                html.H1(children="Dashboard AMOén", className="header-title"),

                # Navigation links/buttons
                html.Div(
                    children=[
                        dcc.Link(html.Button("Vue d'ensemble", className='link-button', id='link-overview'), href='/overview'),
                        dcc.Link(html.Button('Par projet', className='link-button', id='link-projects'), href='/projects')
                    ],
                    className="header-navigation"
                )
            ],
            className="header",
        ),
        # menu
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Adresse",
                                 className="menu-title",
                                 ),
                        dcc.Dropdown(
                            id="dropdown_nom_rue",
                            options=dropdown_rues,
                            value=None,
                            clearable=True,
                            multi=True,
                            className="dropdown",
                            style={'width': '1000px'},
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Nom Projet",
                                className="menu-title",
                                ),
                        dcc.Dropdown(
                            id="dropdown_nom_projet",
                            options=dropdown_projet,
                            value="Prulay 43 à 47_Batineg",
                            clearable=True,
                            searchable=True,
                            className="dropdown",
                            style={'width': '500px'},
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
                        id="plan_vue_rue", config={"displayModeBar": True},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="graphique_bars_idc",
                        config={"displayModeBar": True},
                    ),
                    className="card",
                ),
                html.Div(
                    children=html.Img(id='performance-site-image',
                                      style={'width': '75%', 'height': '75%'}),
                    className="card",
                    style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'}
                ),
                html.Div(
                    children=dash_table.DataTable(
                        id='table'
                    ),
                    className="card",
                ),
                 # Add download component and button
                dcc.Download(id="download"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dcc.Dropdown(
                                    options=[
                                        {"label": "Excel file", "value": "excel"},
                                        {"label": "CSV file", "value": "csv"},
                                    ],
                                    id="dropdown",
                                    placeholder="Choose download file type. Default is CSV format!",
                                )
                            ]
                        ),
                        dbc.Col(
                            [
                                dbc.Button(
                                    "Download Data", id="btn_csv"
                                ),
                            ]
                        ),
                    ]
                ),
            ],
            className="wrapper",
        ),
    ]
)

@app.callback(
    [Output('link-overview', 'className'),
     Output('link-projects', 'className')],
    [Input('url', 'pathname')]
)
def update_button_style(pathname):
    if pathname == '/projects':
        return 'link-button', 'link-button active-button'
    elif pathname == '/overview':
        return 'link-button active-button', 'link-button'
    else:
        return 'link-button', 'link-button'


# stacked bar chart
bars = []
for col in df_analyse_stacked.columns[1:]:    # Iterate over all columns except 'statut'
    serie = df_analyse_stacked[col]
    bars.append(go.Bar(name=col, x=df_analyse_stacked['statut'] , y=serie, 
                       text=serie,   # display the serie value as hover text 
                       textposition='auto',   # automate the position
                       hoverinfo='name+x+text'))    # decide what info appears on hover
layout_bar_stacked = go.Layout(
    barmode='stack', 
    xaxis=dict(title='Statut'),
    yaxis=dict(title='Nombre de projets'),
)
fig_bars_stacked = go.Figure(data=bars, layout=layout_bar_stacked)
fig_bars_stacked.update_layout(
    barmode="stack",
    title="Statut des projets AMOén")  # set your title here

# --------------------------------------------------------------
# overview layout
# --------------------------------------------------------------
overview_layout = html.Div(
    children=[
        # Header
        html.Div(
            children=[
                html.H1(children="Dashboard AMOén", className="header-title"),
                # Navigation links/buttons
                html.Div(
                    children=[
                        dcc.Link(html.Button("Vue d'ensemble", className='link-button', id='link-overview'), href='/overview'),
                        dcc.Link(html.Button('Par projet', className='link-button', id='link-projects'), href='/projects')
                    ],
                    className="header-navigation"
                )
            ],
            className="header",
        ),
        # Overview section
        html.Div(  # Wrap the overview content in its own container
            children=[
                dcc.Graph(
                    id='statut-chart',
                    figure=fig_bars_stacked,
                    style={'marginTop': '20px'},  # Add some margin above the chart
                ),
                html.Div(
                    children=html.Img(
                        id='performance_site_general-image',
                        src=f'data:image/png;base64,{encoded_image_site_general}',
                        style={'width': '120%', 'display': 'block', 'margin': '0 auto'}
                    ),
                    className="card",
                ),
                html.H2('Overview of All Projects', className="overview-title"),  # Add a class for styling
                dash_table.DataTable(
                    id='table',
                    columns=[{"name": i, "id": i} for i in df_amoen.columns],
                    data=df_amoen.to_dict('records'),
                    filter_action="native",  # enable filtering
                    sort_action="native",     # enable sorting
                    style_table={'margin': '20px 0'},  # Add some margin around the table
                ),
            ],
            style={'padding': '20px'},  # Add some padding around the overview section
        )
    ],
    style={'margin': '0px', 'padding': '0px'}
)

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/projects':
        return projects_layout
    elif pathname == '/overview':
        return overview_layout
    else:
        # This can be a custom 404 layout
        return html.Div([
            html.H3('404: Page not found')
        ])

# --------------------------------------------------------------
# overview
# --------------------------------------------------------------

@app.callback(Output('graph-container', 'children'),
              [Input('table', 'derived_virtual_data'),
               Input('table', 'derived_virtual_selected_rows')])
def update_graphs(rows, derived_virtual_selected_rows):
    # When table is first rendered 'derived_virtual_data' and
    # 'derived_virtual_selected_rows' will be None, so, skip those updates.
    if derived_virtual_selected_rows is None:
        derived_virtual_selected_rows = []

    selected_df = pd.DataFrame(rows).iloc[derived_virtual_selected_rows]

    # Now you can use the selected subset of data in 'selected_df' DataFrame
    # and update your graph accordingly. Example:
    _, ax = plt.subplots()
    for i in range(len(selected_df)):
        selected_df.iloc[i].plot(ax=ax)
    fig = go.Figure(data=go.Scatter(x=selected_df[0], y=selected_df[1]))
    return dcc.Graph(figure=fig)

# --------------------------------------------------------------
# projets
# --------------------------------------------------------------

# remplir adresses avec nom des projets AMOén
@app.callback(
    [Output('dropdown_nom_rue', 'options'),
     Output('dropdown_nom_rue', 'value')],  # Added this line to also update the value property
    Input('dropdown_nom_projet', 'value')
)
def update_adresse_dropdown(selected_project):
    if selected_project:
        # Filter the dataframe based on selected project
        relevant_rows = df_amoen[df_amoen['Nom_projet'] == selected_project]
        
        # Extract addresses
        all_addresses = relevant_rows['Rues'].iloc[0].split("\n")
        options = [{"label": addr, "value": addr} for addr in all_addresses]
        
        return options, all_addresses  # Also return all_addresses as the value
    else:
        # Return an empty list if no project is selected
        return [], []  # Return empty list for the value as well

# plan rue
@app.callback(
    Output('plan_vue_rue', 'figure'),
    Input('dropdown_nom_rue', 'value')
)
def update_graph(nom_rues):
    conn = psycopg2.connect(
        host="localhost",
        database="postgis_sitg",
        user="postgres",
        password="postgres",
        port="5432")

    table_name = "SCANE_INDICE_MOYENNES_3_ANS"
    schema_name = "sitg"

    with conn.cursor() as cur:
        if len(nom_rues) == 1:
            cur.execute(f"SELECT * FROM {schema_name}.{table_name} WHERE adresse = %s", (nom_rues[0],))
        else:
            cur.execute(f"SELECT * FROM {schema_name}.{table_name} WHERE adresse = ANY(%s)", (nom_rues,))
        headers = cur.fetchall()

    df = pd.DataFrame(headers, columns=[desc[0] for desc in cur.description])
    df['geometry'] = gpd.GeoSeries.from_wkb(df['geometry'])
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    gdf.set_crs("EPSG:2056", inplace=True)
    gdf = gdf.to_crs("EPSG:4326")

    unique_addresses = gdf['adresse'].unique()
    colors = px.colors.qualitative.Set1
    address_to_color = {addr: colors[i % len(colors)] for i, addr in enumerate(unique_addresses)}
    gdf['color'] = gdf['adresse'].map(address_to_color)

    geojson = gdf.geometry.__geo_interface__

    fig1 = px.choropleth_mapbox(gdf, 
                                geojson=geojson, 
                                locations=gdf.index, 
                                color="adresse",  
                                color_discrete_map=address_to_color,
                                hover_name="adresse", 
                                hover_data=["indice"],
                                mapbox_style="carto-positron", 
                                center={"lat": gdf.geometry.centroid.y.mean(), "lon": gdf.geometry.centroid.x.mean()},
                                zoom=16,
                                labels={"adresse": "Adresse"},
                                title="Vue en plan"
                                )
    cur.close()
    conn.close()

    return fig1

# graphique bars
@app.callback(
    Output('graphique_bars_idc', 'figure'),
    Input('dropdown_nom_rue', 'value'))
def update_bars(nom_rues):
    conn = psycopg2.connect(
        host="localhost",
        database="postgis_sitg",
        user="postgres",
        password="postgres",
        port="5432")

    table_name = "SCANE_INDICE_MOYENNES_3_ANS"
    schema_name = "sitg"

    dfs = []  # A list to hold dataframes for each building
    with conn.cursor() as cur:
        for nom_rue in nom_rues:
            cur.execute(f"SELECT annee, indice, adresse FROM {schema_name}.{table_name} WHERE adresse = %s ORDER BY annee ASC", (nom_rue,))
            rows = cur.fetchall()
            df = pd.DataFrame(rows, columns=['annee', 'indice', 'adresse'])
            
            # Ensure the data types are correct
            df['annee'] = df['annee'].astype(int)
            df['indice'] = df['indice'].astype(float)
            
            dfs.append(df)

    # Combine all dataframes into a single one
    all_data = pd.concat(dfs, ignore_index=True)

    # Get unique addresses from the data
    unique_addresses = all_data['adresse'].unique()

    # Generate a list of colors for each unique address.
    all_colors = plt.cm.tab10.colors + plt.cm.tab20c.colors + plt.cm.Set3.colors
    if len(unique_addresses) > len(all_colors):
        print("Error: Number of unique addresses exceed available colors.")
        return go.Figure()

    # Simple color palette for debugging
    color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
                     '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'] * 3  # This is just a repeat of the default color cycle

    fig = go.Figure()

    for idx, address in enumerate(unique_addresses):
        df_address = all_data[all_data['adresse'] == address]
        fig.add_trace(
            go.Bar(
                x=df_address['annee'],
                y=df_address['indice'],
                name=address,
                marker_color=color_palette[idx]
            )
        )

    fig.update_layout(
        barmode='group',
        title="Indice de dépense de chaleur [MJ/(m²*an)] par bâtiment",
        xaxis_title="Années",
        yaxis_title="Indice de dépense de chaleur [MJ/(m²*an)]",
        xaxis=dict(tickmode='linear', dtick=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        modebar=dict(bgcolor='rgba(0, 0, 0, 0)'),
        bargap=0.10
    )

    return fig


# graphique performance
@app.callback(
    Output('performance-site-image', 'src'),
    [Input('dropdown_nom_projet', 'value')])
def performance_site(nom_projet):
    image_filename = performance_par_site(df_amoen, nom_projet)
    encoded_image = base64.b64encode(open(image_filename, 'rb').read())
    
    # delete the image file
    os.remove(image_filename)
    
    return f'data:image/png;base64,{encoded_image.decode()}'

# table
@app.callback(
    Output('table', 'data'),  # Change this to 'data' as you're updating the table's data
    Input('dropdown_nom_rue', 'value'),)
def update_histo(nom_rue):
    conn = psycopg2.connect(
            host="localhost",
            database="postgis_sitg",
            user="postgres",
            password="postgres",
            port="5432")

    table_name = "SCANE_INDICE_MOYENNES_3_ANS"
    schema_name = "sitg"

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get the rows with the applied filters
            cur.execute(f"SELECT * FROM {schema_name}.{table_name} WHERE adresse = ANY(%s) ORDER BY annee ASC", (nom_rue,))
            rows = cur.fetchall()

            # Get column names
            column_names = [desc[0] for desc in cur.description]

        # Convert rows to DataFrame
        df = pd.DataFrame(rows, columns=column_names)

        column_names1 = ['annee',
                'indice',
                'annees_concernees_moy_3',
                'indice_moy3',
                'sre',
                'egid',
                'adresse',
                'npa',
                'commune',
                'destination',
                'nbre_preneur',
                'date_debut_periode',
                'date_fin_periode',
                'agent_energetique_1',
                'quantite_agent_energetique_1',
                'unite_agent_energetique_1',
                'agent_energetique_2',
                'quantite_agent_energetique_2',
                'unite_agent_energetique_2',
                'agent_energetique_3',
                'quantite_agent_energetique_3',
                'unite_agent_energetique_3',
                'date_saisie',
                'id_concessionnaire',
                ]
        
        df = df[column_names1]

        df['date_saisie'] = pd.to_datetime(df['date_saisie'], unit='ms')
        df['date_saisie'] = df['date_saisie'].dt.strftime('%Y-%m-%d')
        
        df['date_debut_periode'] = pd.to_datetime(df['date_debut_periode'])
        df['date_debut_periode'] = df['date_debut_periode'].dt.strftime('%Y-%m-%d')

        df['date_fin_periode'] = pd.to_datetime(df['date_fin_periode'])
        df['date_fin_periode'] = df['date_fin_periode'].dt.strftime('%Y-%m-%d')

        # round sre column to 1 decimal place
        df['sre'] = df['sre'].astype(float).round(1)

        # Convert DataFrame to a list of dictionaries for Dash DataTable
        table_data = df.to_dict('records')
    finally:
        conn.close()

    # Return the data for Dash DataTable
    return table_data

# download
@app.callback(
    Output("download", "data"),
    Input("btn_csv", "n_clicks"),
    State("dropdown", "value"),
    State("table", "data"),  # Get the data from the table
    prevent_initial_call=True,
)
def download_data(n_clicks, download_type, table_data):
    if n_clicks:
        df = pd.DataFrame(table_data)  # Convert data back to DataFrame

        if download_type == "csv":
            return dcc.send_data_frame(df.to_csv, "table_data.csv")
        else:  # 'excel'
            return dcc.send_data_frame(df.to_excel, "table_data.xlsx")

# --------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
