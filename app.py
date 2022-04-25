import streamlit as st
from streamlit_folium import folium_static
import folium
import geopandas as gpd
import math
import requests
import os
import json
import re
from geopy.geocoders import Nominatim
from pyproj import Transformer
import plotly.express as px
import plotly.figure_factory as ff


st.markdown("# BDNB Viz 🗺")

address = st.text_input("Adresse recherchée", "5 rue de Charonne, 75011 Paris, France")
geolocator = Nominatim(user_agent="bnbviz")
location = geolocator.geocode(address)
if (location is None) or ("France" not in location.address):
    st.markdown("❌ **Veuillez entrer une adresse valide en France métropolitaine**")
else:
    radius = st.slider(
        "Sélectionnez un rayon (en km) autour de l'adresse recherchée. Restez à 1km pour de meilleures performances :)",
        1,
        3,
        1,
    )
    option = st.selectbox(
        "Quel critère souhaitez-vous afficher sur la carte ?",
        ("Etiquette énergétique", "Etiquette carbone"),
    )
    if option == "Etiquette énergétique":
        feature = "Etiquette énergétique (DPE)"
    else:
        feature = "Etiquette carbone (DPE)"

    if address == "5 rue de Charonne, 75011 Paris, France":
        with open(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), f"default_gdf{radius}.json"
            )
        ) as default_data:
            data = json.load(default_data)
            x, y = (48.852364, 2.3740465)
            xmin, ymin = (653563.2887607021, 6861052.527666945)
            xmax, ymax = (654573.017029733, 6862050.167185774)
    else:
        # Get bbox coordinates
        geolocator = Nominatim(user_agent="bnbviz")
        location = geolocator.geocode(address)
        if location is None:
            st.markdown("**Veuillez entrer une adresse valide**")
        else:
            x, y = location.latitude, location.longitude
            xmin = x - radius / (2 * 110.574)
            xmax = x + radius / (2 * 110.574)
            ymin = y - radius / (2 * 111.320 * math.cos(math.pi * x / 180))
            ymax = y + radius / (2 * 111.320 * math.cos(math.pi * x / 180))
            transformer = Transformer.from_crs("epsg:4326", "epsg:2154")
            xmin, ymin = transformer.transform(xmin, ymin)
            xmax, ymax = transformer.transform(xmax, ymax)

        url = "https://bdnb-image-fzyx4l7upa-ew.a.run.app/"
        url += f"getbbox?xmin={xmin}&xmax={xmax}&ymin={ymin}&ymax={ymax}"
        data = requests.get(url).json()

    gdf = gpd.GeoDataFrame.from_features(data["features"])
    gdf = gdf.set_crs(epsg=2154)
    gdf = gdf[
        [
            "geometry",
            "Adresse",
            "Type de batiment",
            "Année de construction",
            "Surface habitable (estimée)",
            "Nombre de logements",
            "Etiquette énergétique (DPE)",
            "Consommation énergétique [kWhEP/m².an] (DPE)",
            "Etiquette carbone (DPE)",
            "Emissions de GES [kgC02eq/m².an] (DPE)",
            "Types d'énergie",
            "Consommation électrique totale [kwhEF/an] (MTEDLE)",
            "Consommation de gaz totale [kwhEF/an] (MTEDLE)",
            "Générateurs de chauffage",
            "Générateurs d'ECS",
        ]
    ]
    gdf = gdf.rename(
        columns={
            "Consommation énergétique [kWhEP/m².an] (DPE)": "Conso énergétique [kWhEP/m².an] (DPE)",
            "Consommation électrique totale [kwhEF/an] (MTEDLE)": "Conso électrique [kwhEF/an] (MTEDLE)",
            "Consommation de gaz totale [kwhEF/an] (MTEDLE)": "Conso de gaz [kwhEF/an] (MTEDLE)",
        }
    )
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
    folium.Marker(
        location=[x, y], icon=folium.Icon(color="darkblue", icon="map-pin", prefix="fa")
    ).add_to(m)
    folium_static(m)

    st.markdown("# Données sur la zone")
    st.markdown("### Consommations énergétiques [kWhEP/m².an] (DPE)")
    gdf_plt = gdf.drop("geometry", axis=1)
    gdf_plt = gdf_plt.replace(to_replace="N.C.", value=None)
    gdf_plt = gdf_plt.astype(
        {
            "Année de construction": "float32",
            "Surface habitable (estimée)": "float32",
            "Nombre de logements": "float32",
            "Conso énergétique [kWhEP/m².an] (DPE)": "float64",
            "Emissions de GES [kgC02eq/m².an] (DPE)": "float64",
            "Conso électrique [kwhEF/an] (MTEDLE)": "float64",
            "Conso de gaz [kwhEF/an] (MTEDLE)": "float64",
        }
    )
    fig_nrj = px.histogram(
        gdf_plt,
        x="Conso énergétique [kWhEP/m².an] (DPE)",
        marginal="box",  # or violin, rug
        hover_data=gdf_plt.columns,
        color_discrete_sequence=["sandybrown"],
        histnorm="percent",
    )
    st.plotly_chart(fig_nrj, use_container_width=True)

    st.markdown("### Emissions de GES [kgC02eq/m².an] (DPE)")
    fig_co2 = px.histogram(
        gdf_plt,
        x="Emissions de GES [kgC02eq/m².an] (DPE)",
        marginal="box",  # or violin, rug
        hover_data=gdf_plt.columns,
        color_discrete_sequence=["mediumpurple"],
        histnorm="percent",
    )
    st.plotly_chart(fig_co2, use_container_width=True)

    st.markdown("### Corrélation entre plusieurs caractéristiques")
    feat_x = st.selectbox("Caractéristique 1 (axe x)", gdf_plt.columns, index=2)
    feat_y = st.selectbox("Caractéristique 2 (axe y)", gdf_plt.columns, index=8)
    feat_size = st.selectbox(
        "Caractéristique 3 (taille des bulles)",
        [
            "-",
            "Année de construction",
            "Surface habitable (estimée)",
            "Nombre de logements",
            "Conso énergétique [kWhEP/m².an] (DPE)",
            "Emissions de GES [kgC02eq/m².an] (DPE)",
            "Conso électrique [kwhEF/an] (MTEDLE)",
            "Conso de gaz [kwhEF/an] (MTEDLE)",
        ],
        index=4,
    )
    if feat_x == feat_y or feat_x == feat_size or feat_y == feat_size:
        st.markdown("❌ **Vous ne pouvez pas choisir 2 caractéristiques identiques**")
    else:
        if feat_size == "-":
            gdf_corr = gdf_plt[[feat_x, feat_y]].dropna()
            feat_size_corr = None
        else:
            gdf_corr = gdf_plt[[feat_x, feat_y, feat_size]].dropna()
            feat_size_corr = feat_size
        fig_corr = px.scatter(
            x=feat_x,
            y=feat_y,
            size=feat_size_corr,
            size_max=20,
            width=1100,
            height=700,
            data_frame=gdf_corr,
        )
        if feat_x == "Année de construction":
            fig_corr.update_layout(xaxis_range=[1700, 2021])
        st.plotly_chart(fig_corr, use_container_width=True)
