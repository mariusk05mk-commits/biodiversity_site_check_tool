import pandas as pd
import plotly.express as px
import streamlit as st
from gbif_client import get_species_nearby
from species_info import get_many

KINGDOM_DE = {"Plantae": "Flora", "Animalia": "Fauna", "Fungi": "Pilze & Flechten"}
CLASS_DE = {
    "Aves": "Vögel", "Insecta": "Insekten", "Mammalia": "Säugetiere",
    "Amphibia": "Amphibien", "Reptilia": "Reptilien",
}
KATEGORIE = {
    "CR": "bedroht", "EN": "bedroht", "VU": "bedroht",
    "NT": "Vorwarnliste", "LC": "ungefährdet",
}
FARBEN = {
    "bedroht": "#d62728", "Vorwarnliste": "#f2c230",
    "ungefährdet": "#2ca02c", "nicht bewertet": "#9e9e9e",
}


@st.cache_data(show_spinner=False)
def lade_infos(namen):
    return get_many(list(namen))


st.title("Biodiversitäts-Check für Standorte")

lat = st.number_input("Breitengrad", value=49.293, format="%.4f")
lon = st.number_input("Längengrad", value=8.642, format="%.4f")
radius = st.slider("Radius (Meter)", 100, 2000, 500, step=100)

if st.button("Standort prüfen"):
    st.session_state["result"] = get_species_nearby(lat, lon, radius)
    st.session_state["radius"] = radius

if "result" in st.session_state:
    result = st.session_state["result"]
    df = pd.DataFrame.from_dict(result["species"], orient="index")
    df.index.name = "Art (lat.)"
    df["Bereich"] = df["kingdom"].map(KINGDOM_DE).fillna("Sonstige")
    df["Gruppe"] = df["class"].map(CLASS_DE).fillna("Andere")

    with st.spinner("Lade deutsche Namen und Gefährdungsstatus (beim ersten Mal ca. 1 Minute) ..."):
        infos = pd.DataFrame(lade_infos(tuple(df.index))).set_index("Art (lat.)")
    df = df.join(infos)
    df["Kategorie"] = df["IUCN"].map(KATEGORIE).fillna("nicht bewertet")

    st.metric("Nachgewiesene Arten", len(df))
    cols = st.columns(3)
    for col, bereich in zip(cols, ["Flora", "Fauna", "Pilze & Flechten"]):
        col.metric(bereich, int((df["Bereich"] == bereich).sum()))

    st.subheader("Gefährdungsstatus (IUCN, global)")
    zaehlung = df["Kategorie"].value_counts().reset_index()
    zaehlung.columns = ["Kategorie", "Anzahl"]
    fig = px.bar(zaehlung, x="Kategorie", y="Anzahl", color="Kategorie", color_discrete_map=FARBEN)
    st.plotly_chart(fig, use_container_width=True)

    bedroht = df[df["Kategorie"] == "bedroht"]
    if len(bedroht):
        st.error(f"{len(bedroht)} bedrohte Art(en) nachgewiesen")
        st.dataframe(bedroht[["Deutscher Name", "Gruppe", "IUCN", "beobachtungen"]])
    else:
        st.success("Keine bedrohten Arten (IUCN) in den Daten gefunden")

    st.subheader("Fundorte der Beobachtungen")
    st.map(pd.DataFrame(result["points"]))

    st.subheader("Artenliste")
    st.dataframe(
        df[["Deutscher Name", "Bereich", "Gruppe", "Kategorie", "beobachtungen"]]
        .sort_values("beobachtungen", ascending=False)
    )

    st.caption(
        f"Basierend auf {result['used_observations']} von {result['total_observations']} "
        f"Beobachtungen im Radius von {st.session_state['radius']} m. "
        "Gefährdungsstatus: IUCN Red List (global), nicht die Rote Liste Deutschlands."
    )
    