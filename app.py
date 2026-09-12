import streamlit as st
import pandas as pd

# Seitengestaltung (Breiteres Layout für die Programm-Tabelle)
st.set_page_config(page_title="Profi Sende- & Programm-Manager", layout="wide")

# Linke Seitenleiste (Navigation / Bereich zum Klicken)
st.sidebar.title("Navigation")
page = st.sidebar.radio("Auswahl", ["Programm-Übersicht", "Serien-Datenbank", "Einstellungen"])

# Umfassende Serien-Datenbank (Staffeln, Episoden & Laufzeiten)
SERIE_DATABASE = {
    "Hacks": {
        "seasons": {
            1: {"totalEpisodes": 10, "duration": 30},
            2: {"totalEpisodes": 8, "duration": 30},
            3: {"totalEpisodes": 9, "duration": 30}
        }
    },
    "Grey's Anatomy": {
        "seasons": {
            # Weitere Staffeln hier erweiterbar
        }
    }
}

# Hauptbereich basierend auf der linken Navigation
if page == "Programm-Übersicht":
    st.title("Profi Sende- & Programm-Manager")
    st.markdown("Willkommen zurück! Hier ist deine aktuelle Programm-Übersicht.")
    
    # Beispiel-Tabelle
    data = {
        "Format": ["Hacks", "Grey's Anatomy"],
        "Sendeplatz": ["20:15 Uhr", "21:15 Uhr"],
        "Status aktiv": [True, True]
    }
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

elif page == "Serien-Datenbank":
    st.title("Serien-Datenbank")
    st.write("Hier siehst du die hinterlegten Staffeln und Episoden-Details:")
    st.json(SERIE_DATABASE)

elif page == "Einstellungen":
    st.title("Einstellungen")
    st.write("Hier kannst du Anpassungen für das Tool vornehmen.")
