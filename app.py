import streamlit as st
from streamlit_folium import folium_static
import geopandas as gpd
import numpy as np
import os
from geopy.geocoders import Nominatim
from pyproj import Transformer

st.markdown("# BDNB Viz 🗺")

address = st.text_input("Adresse recherchée", "11 rue de Charonne, 75011 Paris, France")
radius = st.slider(
    "Sélectionnez un rayon (en km) autour de l'adresse recherchée. Restez à 1km pour de meilleures performances :)",
    1,
    5,
    1,
)
# Get bbox coordinates
geolocator = Nominatim(user_agent="bnbviz")
location = geolocator.geocode(address)
x, y = location.latitude, location.longitude
xmin = x - radius / (2 * 110.574)
xmax = x + radius / (2 * 110.574)
ymin = y - radius / (2 * 111.320 * np.cos(np.pi * x / 180))
ymax = y + radius / (2 * 111.320 * np.cos(np.pi * x / 180))
transformer = Transformer.from_crs("epsg:4326", "epsg:2154")
xmin, ymin = transformer.transform(xmin, ymin)
xmax, ymax = transformer.transform(xmax, ymax)

gdf = gpd.read_file(
    os.path.join(
        os.path.dirname((os.path.realpath(__file__))),
        os.path.join("data", "bdnb.gpkg"),
    ),
    bbox=(xmin, ymin, xmax, ymax),
)
gdf = gdf[
    [
        "geometry",
        "cerffo2020_annee_construction",
        "adedpe202006_mean_class_conso_ener",
        "adedpe202006_mean_conso_ener",
        "adedpe202006_mean_class_estim_ges",
        "adedpe202006_mean_estim_ges",
    ]
]
gdf.rename(
    columns={
        "cerffo2020_annee_construction": "Année de construction",
        "adedpe202006_mean_class_conso_ener": "Etiquette énergétique (DPE)",
        "adedpe202006_mean_conso_ener": "Consommations énergétiques, kWhEP/m².an (DPE)",
        "adedpe202006_mean_class_estim_ges": "Etiquette carbone (DPE)",
        "adedpe202006_mean_estim_ges": "Emissions de GES, kgC02eq/m².an (DPE)",
    },
    inplace=True,
)
option = st.selectbox(
    "Quel critère souhaitez-vous afficher sur la carte ?",
    ("Etiquette énergétique", "Etiquette carbone"),
)
if option == "Etiquette énergétique":
    feature = "Etiquette énergétique (DPE)"
else:
    feature = "Etiquette carbone (DPE)"

gdf[feature].fillna(value="N", inplace=True)
color = [
    "#309C6C",
    "#5FB14E",
    "#80BD73",
    "#F2E600",
    "#EAB400",
    "#E3812A",
    "#CE1E15",
    "#C3C3C3",
]
m = gdf.explore(
    feature,
    cmap=color,
    tiles="CartoDB positron",
    zoom_start=18,
    location=(x, y),
    legend=True,
)
folium_static(m)
