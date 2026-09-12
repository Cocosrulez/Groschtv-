import streamlit as st
import pandas as pd

# Seitengestaltung (Breiteres Layout für die Programm-Tabelle)
st.set_page_config(page_title="Profi Sende- & Programm-Manager", layout="wide")

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
            1: {"totalEpisodes": 9, "duration": 43},
            2: {"totalEpisodes": 27, "duration": 43},
            3: {"totalEpisodes": 25, "duration": 43}
        }
    },
    "Breaking Bad": {
        "seasons": {
            1: {"totalEpisodes": 7, "duration": 47},
            2: {"totalEpisodes": 13, "duration": 47},
            3: {"totalEpisodes": 13, "duration": 47},
            4: {"totalEpisodes": 13, "duration": 47},
            5: {"totalEpisodes": 16, "duration": 47}
        }
    },
    "Curb Your Enthusiasm": {
        "seasons": {
            1: {"totalEpisodes": 10, "duration": 30},
            2: {"totalEpisodes": 10, "duration": 30},
            3: {"totalEpisodes": 10, "duration": 30}
        }
    }
}

# Session State für den Sendeplan initialisieren
if "schedule" not in st.session_state:
    st.session_state.schedule = []

st.title("📺 Profi Sende- & Programm-Manager")
st.markdown("Verwalte deinen Sendeplan mit automatischer Episoden-Prüfung, fester Slot-Logik (Daytime / Primetime) und sauberer Tabellen-Ansicht.")

# Layout: Aufteilung in Eingabe (links) und Programm-Ansicht (rechts)
col_input, col_view = st.columns([1, 1.5], gap="large")

with col_input:
    st.subheader("✍️ Sendung einplanen")
    
    serie_name = st.selectbox("Serie auswählen:", list(SERIE_DATABASE.keys()))
    
    slot_type = st.selectbox(
        "Sende-Slot:", 
        ["Daytime (bis 20:00 Uhr)", "Primetime (ab 20:00 Uhr)"]
    )

    # Standard-Startzeit je nach Slot
    default_time = "16:00" if "Daytime" in slot_type else "20:15"

    c1, c2 = st.columns(2)
    with c1:
        season_num = st.number_input("Staffel:", min_value=1, value=1, step=1)

    # Maximale Episoden für die gewählte Staffel ermitteln
    serie_data = SERIE_DATABASE.get(serie_name, {})
    seasons_data = serie_data.get("seasons", {})
    current_season_data = seasons_data.get(season_num)
    max_eps = current_season_data["totalEpisodes"] if current_season_data else 99

    with c2:
        episode_num = st.number_input(f"Start-Episode (Max: {max_eps}):", min_value=1, value=1, step=1)

    start_time_str = st.text_input("Startzeit (HH:MM):", value=default_time)

    if st.button("🚀 Sendung(en) in Sendeplan übernehmen (Mo–Fr)", use_container_width=True):
        # 1. Validierung: Existiert die Staffel?
        if season_num not in seasons_data:
            st.error(f"Fehler: Staffel {season_num} für '{serie_name}' existiert nicht!")
        # 2. Validierung: Existiert die Episode? (Verhindert z.B. Hacks S1E22)
        elif episode_num > max_eps:
            st.error(f"Fehler: Episode {episode_num} ist ungültig! Staffel {season_num} von '{serie_name}' hat maximal {max_eps} Episoden.")
        else:
            # Endzeit berechnen
            duration = current_season_data["duration"]
            try:
                h, m = map(int, start_time_str.split(":"))
                total_minutes = h * 60 + m + duration
                end_h = (total_minutes // 60) % 24
                end_m = total_minutes % 60
                end_time_str = f"{end_h:02d}:{end_m:02d}"
            except:
                end_time_str = "20:00"

            # Automatische Mo-Fr Verteilung
            days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
            current_ep = episode_num
            slot_label = "Daytime" if "Daytime" in slot_type else "Primetime"

            for day in days:
                if current_ep <= max_eps:
                    st.session_state.schedule.append({
                        "Wochentag": day,
                        "Slot": slot_label,
                        "Uhrzeit": f"{start_time_str} - {end_time_str}",
                        "Serie": serie_name,
                        "Staffel": season_num,
                        "Episode": current_ep,
                        "Laufzeit": f"{duration} Min."
                    })
                    current_ep += 1

            st.success("Erfolgreich eingetragen!")

with col_view:
    st.subheader("📋 Sendeplan & Programm-Tabelle")
    
    if len(st.session_state.schedule) == 0:
        st.info("Bisher noch keine Sendungen im Plan. Nutze das Formular links.")
    else:
        # Als sauberes DataFrame (Sheet-Ansicht) anzeigen
        df_schedule = pd.DataFrame(st.session_state.schedule)
        st.dataframe(df_schedule, use_container_width=True, hide_index=True)
        
        c_reset, c_download = st.columns(2)
        with c_reset:
            if st.button("🗑️ Sendeplan leeren"):
                st.session_state.schedule = []
                st.rerun()
        with c_download:
            csv = df_schedule.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Als CSV herunterladen",
                data=csv,
                file_name='sendeplan.csv',
                mime='text/csv',
            )
