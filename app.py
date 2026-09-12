import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# Seitenkonfiguration
st.set_page_config(
    page_title="TV-Sendeplan Generator & Master Control",
    page_icon="📺",
    layout="wide"
)

# --- UMFASSENDE SERIEN-DATENBANK (Verifizierte Staffeln & Episoden) ---
SERIES_DATABASE = {
    "Hacks": {
        "genre": "Comedy",
        "seasons": {1: 10, 2: 8, 3: 9},
        "default_net": 24,
        "default_ad": 6
    },
    "Breaking Bad": {
        "genre": "Drama",
        "seasons": {1: 7, 2: 13, 3: 13, 4: 13, 5: 16},
        "default_net": 45,
        "default_ad": 12
    },
    "Grey's Anatomy": {
        "genre": "Medical Drama",
        "seasons": {1: 9, 2: 27, 3: 25, 4: 17, 5: 24},
        "default_net": 42,
        "default_ad": 15
    },
    "Curb Your Enthusiasm": {
        "genre": "Comedy",
        "seasons": {1: 10, 2: 10, 3: 10, 4: 10},
        "default_net": 28,
        "default_ad": 5
    },
    "GZSZ": {
        "genre": "Daily Soap",
        "seasons": {1: 250, 2: 250},
        "default_net": 22,
        "default_ad": 8
    },
    "Tatort": {
        "genre": "Krimi",
        "seasons": {2024: 35, 2025: 35, 2026: 35},
        "default_net": 88,
        "default_ad": 15
    },
    # Weitere Formate für den echten Senderbetrieb
    "The Big Bang Theory": {
        "genre": "Sitcom",
        "seasons": {1: 17, 2: 23, 3: 23, 4: 24},
        "default_net": 21,
        "default_ad": 9
    },
    "Friends": {
        "genre": "Sitcom",
        "seasons": {1: 24, 2: 24, 3: 25},
        "default_net": 22,
        "default_ad": 8
    }
}

# --- SESSION STATE INITIALISIERUNG ---
if "master_schedule" not in st.session_state:
    st.session_state.master_schedule = []

# --- UI HEADER ---
st.title("📺 TV-Sendeplan & Programmier-Konsole")
st.markdown("Erstelle deinen Programmschema-Sendeplan minutengenau, mit wiederkehrenden Slots (Mo–Fr) und exakter Werbeintegration.")
st.markdown("---")

# Tabs für schnelle Bedienung
tab_builder, tab_view, tab_database = st.tabs(["⚡ Sendeplan bauen", "📋 Programmschema & Ansicht", "📚 Serien-Datenbank"])

with tab_builder:
    st.subheader("Sendung / Block minutengenau einplanen")
    
    with st.form("schedule_builder_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            show_name = st.selectbox("Sendung auswählen", list(SERIES_DATABASE.keys()))
            
            # Automatische Vorauswahl basierend auf Serie
            default_net = SERIES_DATABASE[show_name]["default_net"]
            default_ad = SERIES_DATABASE[show_name]["default_ad"]
            
            available_seasons = list(SERIES_DATABASE[show_name]["seasons"].keys())
            season_num = st.selectbox("Staffel", available_seasons)
            
            max_eps = SERIES_DATABASE[show_name]["seasons"][season_num]
            episode_num = st.number_input("Episodennummer", min_value=1, max_value=max_eps, step=1)

        with col2:
            day_option = st.selectbox(
                "Wochentag / Muster", 
                ["Einmalig (Datum wählbar)", "Montag bis Freitag (Mo-Fr Serie)", "Samstag", "Sonntag", "Jeden Tag"]
            )
            
            if day_option == "Einmalig (Datum wählbar)":
                schedule_date = st.date_input("Sendedatum", datetime.today())
            else:
                schedule_date = None
                
            # Minutengenaue Zeiten
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                start_time = st.time_input("Startzeit", time(20, 15))
            with col_t2:
                end_time = st.time_input("Endezeit", time(21, 15))
                
        st.markdown("#### Laufzeit & Werbe-Details")
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            net_runtime = st.number_input("Netto-Laufzeit (Min.)", min_value=1, max_value=300, value=default_net)
        with col_r2:
            ad_runtime = st.number_input("Werbezeit (Min.)", min_value=0, max_value=120, value=default_ad)
        with col_r3:
            total_duration = net_runtime + ad_runtime
            st.metric("Gesamt-Slot-Dauer", f"{total_duration} Min.")

        submitted = st.form_submit_button("Sendung in den Plan schreiben")
        
        if submitted:
            entry = {
                "Muster": day_option,
                "Datum": schedule_date.strftime("%Y-%m-%d") if schedule_date else "Wiederkehrend",
                "Zeit": f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                "Sendung": show_name,
                "Staffel": season_num,
                "Episode": episode_num,
                "Netto (Min.)": net_runtime,
                "Werbung (Min.)": ad_runtime,
                "Gesamt (Min.)": total_duration
            }
            st.session_state.master_schedule.append(entry)
            st.success(f"Erfolgreich hinzugefügt: {show_name} (St. {season_num}, Ep. {episode_num}) um {start_time.strftime('%H:%M')} Uhr!")

with tab_view:
    st.subheader("Aktueller Programmschema-Sendeplan")
    
    if len(st.session_state.master_schedule) > 0:
        df_plan = pd.DataFrame(st.session_state.master_schedule)
        
        # Schöne Tabelle ausgeben
        st.dataframe(df_plan, use_container_width=True)
        
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("Sendeplan komplett leeren"):
                st.session_state.master_schedule = []
                st.rerun()
        with col_act2:
            csv_data = df_plan.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Sendeplan als CSV herunterladen",
                data=csv_data,
                file_name="tv_sendeplan.csv",
                mime="text/csv",
            )
    else:
        st.info("Dein Sendeplan ist aktuell noch leer. Nutze den Tab 'Sendeplan bauen', um Einträge hinzuzufügen.")

with tab_database:
    st.subheader("Hinterlegte Serien & Validierungsregeln")
    st.markdown("Hier siehst du alle verfügbaren Formate mit ihren echten Staffeln und maximalen Episoden, damit keine falschen Eingaben passieren.")
    
    db_list = []
    for s_name, s_info in SERIES_DATABASE.items():
        db_list.append({
            "Sendung": s_name,
            "Genre": s_info["genre"],
            "Anzahl Staffeln": len(s_info["seasons"]),
            "Standard Netto": f"{s_info['default_net']} Min.",
            "Standard Werbung": f"{s_info['default_ad']} Min."
        })
    st.table(pd.DataFrame(db_list))
