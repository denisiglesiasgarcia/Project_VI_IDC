import plotly.express as px
import pandas as pd
import geojson
import json


df1 = pd.read_csv(r"C:\Users\denis.iglesias\Documents\Project_VI_IDC\SCANE_INDICE_MOYENNES_3_ANS.csv", sep=';', usecols= ['ANNEE', 'EGID', 'ADRESSE', 'SRE', 'INDICE'], encoding='latin1')
#df1 = df[df['ANNEE'] == 2021]
#df1 = df[df['INDICE'] < 1000]

with open(r"C:\Users\denis.iglesias\Documents\Project_VI_IDC\test\indice3ans_epsg_4326_light.geojson", encoding='latin1') as f:
    geojson_idc = geojson.load(f)

#f = open (r"C:\Users\denis.iglesias\Documents\Project_VI_IDC\test\indice3ans_epsg_2056.geojson", "r", encoding='latin1')
#geojson_idc = json.loads(f)

fig = px.choropleth_mapbox(df1,
                            geojson=geojson_idc,
                            color="INDICE",
                            locations="ADRESSE",
                            featureidkey="properties.ADRESSE",
                            center={"lat": 46.2022200, "lon": 6.1456900},
                            mapbox_style="carto-positron",
                            zoom=11)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()