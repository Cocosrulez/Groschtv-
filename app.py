import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# Seitenkonfiguration für professionelles UX-Design
st.set_page_config(
    page_title="Master Control | TV-Programmdirektion",
    page_icon="📡",
    layout="wide"
)

# --- CUSTOM CSS FÜR PROFESSIONELLES UI ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# --- UMFASSENDE SERIEN- & FORMAT-DATENBANK ---
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
    "Spielfilm / Blockbuster": {
        "genre": "Film",
        "seasons": {2026: 1},
        "default_net": 105,
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
    st.session_state.master_schedule = [
        {
            "Tag / Wochentag": "Montag",
            "Zeitfenster": "20:15 - 21:00",
            "Sendung": "Hacks",
            "Staffel": 1,
            "Episode": 1,
            "Netto (Min.)": 24,
            "Werbung (Min.)": 6,
            "Gesamt (Min.)": 30
        },
        {
            "Tag / Wochentag": "Montag",
            "Zeitfenster": "21:00 - 22:00",
            "Sendung": "Breaking Bad",
            "Staffel": 1,
            "Episode": 1,
            "Netto (Min.)": 45,
            "Werbung (Min.)": 15,
            "Gesamt (Min.)": 60
        }
    ]

# --- HILFSFUNKTIONEN ---
def time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute

def check_time_conflict(new_start_min: int, new_end_min: int, target_day: str, existing_schedule: list) -> bool:
    """Prüft, ob am selben Wochentag zur gleichen Uhrzeit bereits ein Sendeplatz belegt ist."""
    for item in existing_schedule:
        if item["Tag / Wochentag"] == target_day:
            times_part = item["Zeitfenster"].split(" - ")
            ex_start_parts = list(map(int, times_part[0].split(":")))
            ex_end_parts = list(map(int, times_part[1].split(":")))
            
            ex_start_min = ex_start_parts[0] * 60 + ex_start_parts[1]
            ex_end_min = ex_end_parts[0] * 60 + ex_end_parts[1]
            
            if (new_start_min < ex_end_min) and (new_end_min > ex_start_min):
                return True
    return False

# --- HEADER & KPI DASHBOARD ---
st.title("📡 Master Control: Primetime- & Sendeplan-Direktion")
st.markdown("**Tagesgenaue Programmierung** — Plane dein Abendprogramm (20:15 Uhr, 21:15 Uhr, etc.) flexibel nach Wochentagen mit variablen Laufzeiten und automatischer Kollisionsprüfung.")

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
with col_kpi1:
    st.metric(label="Eingetragene Sendeplätze", value=len(st.session_state.master_schedule))
with col_kpi2:
    st.metric(label="Verfügbare Formate in DB", value=len(SERIES_DATABASE))
with col_kpi3:
    st.metric(label="Modus", value="Wöchentliche Primetime-Steuerung")

st.markdown("---")

# --- NAVIGATION TABS ---
tab_builder, tab_view, tab_database = st.tabs([
    "⚡ Programmpunkt hinzufügen (Primetime / Tag)", 
    "📋 Sendeplan nach Wochentagen verwalten", 
    "📚 Serien- & Format-Datenbank"
])

with tab_builder:
    st.subheader("Sendeplatz minutengenau einplanen (Mo–So)")
    st.markdown("Wähle den Wochentag, die Startzeit, passe Netto- sowie Werbezeiten an und plane optional direkt mehrere Episoden in Folge ein.")
    
    with st.form("primetime_builder_form"):
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            target_day = st.selectbox(
                "Wochentag", 
                ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag", "Montag bis Freitag (Mo-Fr Serie)"]
            )
            show_name = st.selectbox("Sendung / Format", list(SERIES_DATABASE.keys()))
            
            default_net = SERIES_DATABASE[show_name]["default_net"]
            default_ad = SERIES_DATABASE[show_name]["default_ad"]
            
            available_seasons = list(SERIES_DATABASE[show_name]["seasons"].keys())
            season_num = st.selectbox("Staffel", available_seasons)
            
            max_eps = SERIES_DATABASE[show_name]["seasons"][season_num]
            episode_num = st.number_input("Start-Episodennummer", min_value=1, max_value=max_eps, step=1)

        with col_f2:
            st.markdown("#### ⏰ Sendezeit-Fenster & Mehrfachauswahl")
            start_time = st.time_input("Startzeit (z.B. 20:15)", time(20, 15))
            
            # NEU: Anzahl der Episoden für automatische Verkettung
            episodes_count = st.number_input("Anzahl Folgen (gleich mehrere nacheinander einplanen)", min_value=1, max_value=10, value=1, step=1)
            
            st.markdown("---")
            net_runtime = st.number_input("Netto-Laufzeit pro Folge (Min.)", min_value=1, max_value=300, value=default_net)
            ad_runtime = st.number_input("Werbezeit pro Folge (Min.)", min_value=0, max_value=120, value=default_ad)
            
        total_duration = net_runtime + ad_runtime
        
        # Vorschau für die erste Episode berechnen
        start_dt = datetime.combine(datetime.today(), start_time)
        calculated_end_dt = start_dt + timedelta(minutes=total_duration * episodes_count)
        
        if episodes_count > 1:
            st.info(f"💡 **Mehrfach-Planung aktiv:** Es werden **{episodes_count} Folgen** nacheinander eingeplant. Gesamtdauer von {start_time.strftime('%H:%M')} bis ca. **{calculated_end_dt.time().strftime('%H:%M')} Uhr**.")
        else:
            single_end_dt = start_dt + timedelta(minutes=total_duration)
            st.info(f"💡 **Sende-Fenster:** Von **{start_time.strftime('%H:%M')} Uhr** bis **{single_end_dt.time().strftime('%H:%M')} Uhr** ({total_duration} Min.).")

        submitted = st.form_submit_button("Sendung(en) in das tagesgenaue Schema aufnehmen")
        
        if submitted:
            temp_entries = []
            current_dt = datetime.combine(datetime.today(), start_time)
            conflict_found = False
            
            # Schleife für die automatische Zeitverkettung bei mehreren Episoden
            for i in range(episodes_count):
                current_ep_num = episode_num + i
                
                ep_start_dt = current_dt
                ep_end_dt = current_dt + timedelta(minutes=total_duration)
                
                start_min = time_to_minutes(ep_start_dt.time())
                end_min = time_to_minutes(ep_end_dt.time())
                
                # Kollisionsprüfung gegen bestehenden Plan und bereits in dieser Schleife erstellte Einträge
                if check_time_conflict(start_min, end_min, target_day, st.session_state.master_schedule + temp_entries):
                    conflict_found = True
                    break
                
                entry = {
                    "Tag / Wochentag": target_day,
                    "Zeitfenster": f"{ep_start_dt.strftime('%H:%M')} - {ep_end_dt.strftime('%H:%M')}",
                    "Sendung": show_name,
                    "Staffel": season_num,
                    "Episode": current_ep_num,
                    "Netto (Min.)": net_runtime,
                    "Werbung (Min.)": ad_runtime,
                    "Gesamt (Min.)": total_duration
                }
                temp_entries.append(entry)
                current_dt = ep_end_dt # Nächste Episode startet genau hier
            
            if conflict_found:
                st.error(f"❌ **Sendeplatz-Kollision am {target_day}!** Einer der Sendeplätze überschneidet sich mit einer bereits eingetragenen Sendung.")
            else:
                st.session_state.master_schedule.extend(temp_entries)
                st.success(f"Erfolgreich für **{target_day}** eingepflegt: {episodes_count} Folge(n) von {show_name} ab {start_time.strftime('%H:%M')} Uhr!")
                st.rerun()

with tab_view:
    st.subheader("Wochen- & Primetime-Sendeplan im Überblick")
    st.markdown("Hier siehst du alle geplanten Sendungen nach Wochentagen sortiert. Du kannst einzelne Einträge gezielt prüfen oder fehlerhafte Blöcke sofort löschen.")
    
    if len(st.session_state.master_schedule) > 0:
        df_plan = pd.DataFrame(st.session_state.master_schedule)
        
        # Nach Wochentag sortieren für bessere Übersicht
        day_order = {"Montag": 1, "Dienstag": 2, "Mittwoch": 3, "Donnerstag": 4, "Freitag": 5, "Samstag": 6, "Sonntag": 7, "Montag bis Freitag (Mo-Fr Serie)": 0}
        if "Tag / Wochentag" in df_plan.columns:
            df_plan["Sort"] = df_plan["Tag / Wochentag"].map(day_order).fillna(8)
            df_plan = df_plan.sort_values(by=["Sort", "Zeitfenster"]).drop(columns=["Sort"])
        
        st.dataframe(df_plan, use_container_width=True)
        
        st.markdown("### 🛠️ Programmpunkte gezielt bearbeiten oder löschen")
        row_options = [f"[{i}] {row['Tag / Wochentag']} | {row['Zeitfenster']} - {row['Sendung']} (St. {row['Staffel']}, Ep. {row['Episode']})" for i, row in enumerate(st.session_state.master_schedule)]
        selected_to_delete = st.selectbox("Wähle den zu löschenden Programmpunkt aus:", row_options)
        
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("Ausgewählten Programmpunkt entfernen"):
                idx = row_options.index(selected_to_delete)
                removed = st.session_state.master_schedule.pop(idx)
                st.success(f"Entfernt: {removed['Sendung']} am {removed['Tag / Wochentag']} ({removed['Zeitfenster']})")
                st.rerun()
        with col_act2:
            if st.button("Komplettes Schema zurücksetzen"):
                st.session_state.master_schedule = []
                st.rerun()
                
        st.markdown("---")
        csv_data = df_plan.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Sendeplan als CSV / Excel exportieren",
            data=csv_data,
            file_name="wochen_tv_sendeplan.csv",
            mime="text/csv",
        )
    else:
        st.info("Das Programmschema ist aktuell leer. Füge im ersten Tab die ersten Sendungen hinzu.")

with tab_database:
    st.subheader("Verifizierte Serien- & Laufzeit-Referenz")
    st.markdown("Übersicht aller hinterlegten Formate mit echten Staffellimits, Netto- und Werbezeiten.")
    
    db_list = []
    for s_name, s_info in SERIES_DATABASE.items():
        db_list.append({
            "Format / Sendung": s_name,
            "Genre": s_info["genre"],
            "Staffeln verfügbar": ", ".join(map(str, s_info["seasons"].keys())),
            "Std. Netto": f"{s_info['default_net']} Min.",
            "Std. Werbung": f"{s_info['default_ad']} Min."
        })
    st.table(pd.DataFrame(db_list))
