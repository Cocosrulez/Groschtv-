import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# Seitenkonfiguration
st.set_page_config(
    page_title="TV-Sender Master Control & Programmdirektion",
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

# --- HILFSFUNKTIONEN FÜR ZEIT-KOLLISIONEN ---
def time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute

def check_time_conflict(new_start_min: int, new_end_min: int, new_pattern: str, new_date: str, existing_schedule: list) -> bool:
    """Prüft, ob sich der neue Sendeplatz mit bestehenden Einträgen zeitlich überschneidet."""
    for item in existing_schedule:
        # Prüfe nur, wenn Muster oder Datum übereinstimmen (Kollisionsprüfung im selben Zeitsfenster)
        if item["Muster"] == new_pattern or (new_pattern == "Einmalig (Datum wählbar)" and item["Datum"] == new_date):
            # Parse bestehende Start- und Endzeit aus dem String "HH:MM - HH:MM"
            times_part = item["Zeit"].split(" - ")
            ex_start_parts = list(map(int, times_part[0].split(":")))
            ex_end_parts = list(map(int, times_part[1].split(":")))
            
            ex_start_min = ex_start_parts[0] * 60 + ex_start_parts[1]
            ex_end_min = ex_end_parts[0] * 60 + ex_end_parts[1]
            
            # Überschneidungs-Logik: (StartA < EndB) und (EndA > StartB)
            if (new_start_min < ex_end_min) and (new_end_min > ex_start_min):
                return True
    return False

# --- UI HEADER ---
st.title("📺 Programmdirektion: Master Control & Sendeplan")
st.markdown("Professioneller Sendeplan-Builder mit automatischer Endzeit-Berechnung und intelligenter Kollisionsprüfung.")
st.markdown("---")

tab_builder, tab_view, tab_database = st.tabs(["⚡ Sendeplan bauen", "📋 Programmschema & Bearbeitung", "📚 Serien-Datenbank"])

with tab_builder:
    st.subheader("Sendung / Block minutengenau einplanen")
    
    with st.form("schedule_builder_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            show_name = st.selectbox("Sendung auswählen", list(SERIES_DATABASE.keys()))
            
            default_net = SERIES_DATABASE[show_name]["default_net"]
            default_ad = SERIES_DATABASE[show_name]["default_ad"]
            
            available_seasons = list(SERIES_DATABASE[show_name]["seasons"].keys())
            season_num = st.selectbox("Staffel", available_seasons)
            
            max_eps = SERIES_DATABASE[show_name]["seasons"][season_num]
            episode_num = st.number_input("Episodennummer", min_value=1, max_value=max_eps, step=1)

        with col2:
            day_option = st.selectbox(
                "Wochentag / Sende-Muster", 
                ["Einmalig (Datum wählbar)", "Montag bis Freitag (Mo-Fr Serie)", "Samstag", "Sonntag", "Jeden Tag"]
            )
            
            if day_option == "Einmalig (Datum wählbar)":
                schedule_date = st.date_input("Sendedatum", datetime.today())
                date_str = schedule_date.strftime("%Y-%m-%d")
            else:
                date_str = "Wiederkehrend"
                
            start_time = st.time_input("Startzeit", time(20, 15))
                
        st.markdown("#### Laufzeit & Werbe-Details")
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            net_runtime = st.number_input("Netto-Laufzeit (Min.)", min_value=1, max_value=300, value=default_net)
        with col_r2:
            ad_runtime = st.number_input("Werbezeit (Min.)", min_value=0, max_value=120, value=default_ad)
        with col_r3:
            total_duration = net_runtime + ad_runtime
            st.metric("Gesamtdauer (Netto + Werbung)", f"{total_duration} Min.")

        # Automatische Endzeit-Berechnung anzeigen
        start_dt = datetime.combine(datetime.today(), start_time)
        calculated_end_dt = start_dt + timedelta(minutes=total_duration)
        calculated_end_time = calculated_end_dt.time()
        
        st.info(f"💡 Automatisch berechnete Sendezeit: **{start_time.strftime('%H:%M')} bis {calculated_end_time.strftime('%H:%M')} Uhr**")

        submitted = st.form_submit_button("Sendung in den Plan schreiben")
        
        if submitted:
            start_min = time_to_minutes(start_time)
            end_min = time_to_minutes(calculated_end_time)
            
            # Kollisionsprüfung ausführen
            has_conflict = check_time_conflict(start_min, end_min, day_option, date_str, st.session_state.master_schedule)
            
            if has_conflict:
                st.error(f"❌ **Sendeplatz-Konflikt!** Um {start_time.strftime('%H:%M')} Uhr ist der Sendeplatz im gewählten Muster bereits belegt. Bitte wähle eine andere Zeit.")
            else:
                entry = {
                    "Muster": day_option,
                    "Datum": date_str,
                    "Zeit": f"{start_time.strftime('%H:%M')} - {calculated_end_time.strftime('%H:%M')}",
                    "Sendung": show_name,
                    "Staffel": season_num,
                    "Episode": episode_num,
                    "Netto (Min.)": net_runtime,
                    "Werbung (Min.)": ad_runtime,
                    "Gesamt (Min.)": total_duration
                }
                st.session_state.master_schedule.append(entry)
                st.success(f"Erfolgreich eingeplant: {show_name} (St. {season_num}, Ep. {episode_num}) von {start_time.strftime('%H:%M')} bis {calculated_end_time.strftime('%H:%M')} Uhr!")
                st.rerun()

with tab_view:
    st.subheader("Programmschema verwalten & bearbeiten")
    
    if len(st.session_state.master_schedule) > 0:
        df_plan = pd.DataFrame(st.session_state.master_schedule)
        st.dataframe(df_plan, use_container_width=True)
        
        st.markdown("### Einzelnen Eintrag löschen")
        row_options = [f"[{i}] {row['Zeit']} - {row['Sendung']} (Staffel {row['Staffel']}, Ep. {row['Episode']})" for i, row in enumerate(st.session_state.master_schedule)]
        selected_to_delete = st.selectbox("Wähle den Programmpunkt aus, der entfernt werden soll:", row_options)
        
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if st.button("Ausgewählten Eintrag löschen"):
                index_to_remove = row_options.index(selected_to_delete)
                removed_item = st.session_state.master_schedule.pop(index_to_remove)
                st.success(f"Eintrag gelöscht: {removed_item['Sendung']} ({removed_item['Zeit']})")
                st.rerun()
        
        with col_del2:
            if st.button("Kompletten Sendeplan leeren"):
                st.session_state.master_schedule = []
                st.rerun()
                
        st.markdown("---")
        csv_data = df_plan.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Sendeplan als CSV herunterladen",
            data=csv_data,
            file_name="tv_sendeplan.csv",
            mime="text/csv",
        )
    else:
        st.info("Dein Sendeplan ist aktuell leer. Füge im Tab 'Sendeplan bauen' Einträge hinzu.")

with tab_database:
    st.subheader("Hinterlegte Serien & Validierungsregeln")
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
