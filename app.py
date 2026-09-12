import streamlit as st

# Seitengestaltung
st.set_page_config(page_title="Sendeplan & Programm-Manager", layout="centered")

# Integrierte Datenbank mit Serien, Staffeln, max. Episoden und Laufzeiten
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
            2: {"totalEpisodes": 27, "duration": 43}
        }
    },
    "Curb Your Enthusiasm": {
        "seasons": {
            1: {"totalEpisodes": 10, "duration": 30},
            2: {"totalEpisodes": 10, "duration": 30}
        }
    }
}

st.title("📺 Sendeplan & Programm-Manager")
st.write("Plane deine Serien mit automatischer Episoden-Prüfung und festen Sende-Slots (Daytime & Primetime).")

# Session State initialisieren, damit der Sendeplan beim Klicken erhalten bleibt
if "schedule" not in st.session_state:
    st.session_state.schedule = []

# Layout der Eingabefelder
col1, col2 = st.columns(2)

with col1:
    serie_name = st.selectbox("Serie auswählen:", list(SERIE_DATABASE.keys()))

with col2:
    slot_type = st.selectbox(
        "Sende-Slot:", 
        ["Daytime (bis 20:00 Uhr)", "Primetime (ab 20:00 Uhr)"]
    )

# Dynamische Startzeit je nach Slot anpassen
default_time = "16:00" if "Daytime" in slot_type else "20:15"

col_s, col_e, col_t = st.columns(3)

with col_s:
    season_num = st.number_input("Staffel:", min_value=1, value=1, step=1)

# Maximale Episoden für die ausgewählte Staffel ermitteln
serie_data = SERIE_DATABASE.get(serie_name, {})
seasons_data = serie_data.get("seasons", {})
current_season_data = seasons_data.get(season_num)

max_eps = current_season_data["totalEpisodes"] if current_season_data else 99

with col_e:
    episode_num = st.number_input(f"Episode (Max: {max_eps}):", min_value=1, value=1, step=1)

with col_t:
    start_time_str = st.text_input("Startzeit (HH:MM):", value=default_time)

# Button zum Eintragen
if st.button("Sendung einfügen (Mo–Fr Template)"):
    # 1. Validierung: Existiert die Staffel?
    if season_num not in seasons_data:
        st.error(f"Fehler: Staffel {season_num} für '{serie_name}' existiert nicht!")
    # 2. Validierung: Existiert die Episode?
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

        # Mo-Fr Template automatisch generieren
        days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
        current_ep = episode_num
        slot_label = "Daytime" if "Daytime" in slot_type else "Primetime"

        for day in days:
            if current_ep <= max_eps:
                st.session_state.schedule.append({
                    "day": day,
                    "slot": slot_label,
                    "serie": serie_name,
                    "season": season_num,
                    "episode": current_ep,
                    "time": f"{start_time_str} - {end_time_str}"
                })
                current_ep += 1

        st.success("Erfolgreich als Mo-Fr Template eingetragen!")

# Sendeplan anzeigen
st.divider()
st.subheader("📋 Aktueller Sendeplan")

if len(st.session_state.schedule) == 0:
    st.info("Noch keine Sendungen eingetragen.")
else:
    for item in st.session_state.schedule:
        st.write(f"**[{item['day']}]** ({item['slot']}) | {item['time']} Uhr ➔ **{item['serie']}** (Staffel {item['season']}, Episode {item['episode']})")
    
    if st.button("Sendeplan zurücksetzen"):
        st.session_state.schedule = []
        st.rerun()
