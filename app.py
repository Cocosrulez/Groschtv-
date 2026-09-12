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

# --- UMFASSENDE SERIEN-DATENBANK ---
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
    # Vordefiniertes Standard-Regelprogramm (Mo-Fr Daytime) als Basis, damit nicht alles leer ist
    st.session_state.master_schedule = [
        {
            "Bereich": "Daytime",
            "Muster": "Montag bis Freitag (Mo-Fr)",
            "Zeit": "18:00 - 18:30",
            "Sendung": "GZSZ",
            "Staffel": 1,
            "Episode": 1,
            "Netto (Min.)": 22,
            "Werbung (Min.)": 8,
            "Gesamt (Min.)": 30
        }
    ]

# --- HILFSFUNKTIONEN ---
def time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute

def check_time_conflict(new_start_min: int, new_end_min: int, new_pattern: str, existing_schedule: list) -> bool:
    for item in existing_schedule:
        if item["Muster"] == new_pattern:
            times_part = item["Zeit"].split(" - ")
            ex_start_parts = list(map(int, times_part[0].split(":")))
            ex_end_parts = list(map(int, times_part[1].split(":")))
            
            ex_start_min = ex_start_parts[0] * 60 + ex_start_parts[1]
            ex_end_min = ex_end_parts[0] * 60 + ex_end_parts[1]
            
            if (new_start_min < ex_end_min) and (new_end_min > ex_start_min):
                return True
    return False

# --- HEADER & KPI DASHBOARD ---
st.title("📡 Master Control: Sender- & Programmdirektion")
st.markdown("**Regelprogramm-Automation & Primetime-Feinsteuerung** — Verwalte Sendeplätze, wiederkehrende Muster und individuelle Episoden-Laufzeiten.")

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
with col_kpi1:
    st.metric(label="Aktive Programmpunkte", value=len(st.session_state.master_schedule))
with col_kpi2:
    st.metric(label="Verfügbare Serien in DB", value=len(SERIES_DATABASE))
with col_kpi3:
    st.metric(label="Modus", value="Live-Sendebetrieb")

st.markdown("---")

# --- NAVIGATION TABS ---
tab_builder, tab_view, tab_database = st.tabs([
    "⚡ Programmpunkt hinzufügen", 
    "📋 Sendeplan & Wochenmuster verwalten", 
    "📚 Serien-Datenbank"
])

with tab_builder:
    st.subheader("Neuen Sendeplatz im Schema definieren")
    st.markdown("Erstelle feste Daytime-Blöcke (wiederkehrend Mo–Fr) oder flexible Primetime-Highlights mit individuellen Laufzeiten.")
    
    with st.form("professional_builder_form"):
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            section_type = st.selectbox("Programm-Bereich", ["Primetime (Abendprogramm)", "Daytime / Vorabend (Mo-Fr Standard)", "Weekend Special"])
            show_name = st.selectbox("Sendung / Format", list(SERIES_DATABASE.keys()))
            
            default_net = SERIES_DATABASE[show_name]["default_net"]
            default_ad = SERIES_DATABASE[show_name]["default_ad"]
            
            available_seasons = list(SERIES_DATABASE[show_name]["seasons"].keys())
            season_num = st.selectbox("Staffel", available_seasons)
            
            max_eps = SERIES_DATABASE[show_name]["seasons"][season_num]
            episode_num = st.number_input("Episodennummer", min_value=1, max_value=max_eps, step=1)

        with col_f2:
            day_pattern = st.selectbox(
                "Wiederholungs-Muster", 
                ["Montag bis Freitag (Mo-Fr)", "Einmalig (Spezialdatum)", "Samstag", "Sonntag", "Jeden Tag"]
            )
            
            if day_pattern == "Einmalig (Spezialdatum)":
                schedule_date = st.date_input("Sendedatum", datetime.today())
                pattern_str = f"Einmalig ({schedule_date.strftime('%Y-%m-%d')})"
            else:
                pattern_str = day_pattern
                
            start_time = st.time_input("Startzeit", time(20, 15))
                
        st.markdown("#### ⏱️ Erweiterte Laufzeit- & Werbe-Steuerung (Individueller Episoden-Cut)")
        st.markdown("Du kannst die Netto- und Werbezeiten für diese spezielle Episode bei Bedarf anpassen (z. B. bei Überlänge).")
        
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            net_runtime = st.number_input("Netto-Laufzeit (Min.)", min_value=1, max_value=300, value=default_net)
        with col_r2:
            ad_runtime = st.number_input("Werbezeit (Min.)", min_value=0, max_value=120, value=default_ad)
        with col_r3:
            total_duration = net_runtime + ad_runtime
            st.metric("Gesamt-Slot", f"{total_duration} Min.")

        # Berechnete Endzeit
        start_dt = datetime.combine(datetime.today(), start_time)
        calculated_end_dt = start_dt + timedelta(minutes=total_duration)
        calculated_end_time = calculated_end_dt.time()
        
        st.info(f"💡 Sendezeit-Fenster: **{start_time.strftime('%H:%M')} bis {calculated_end_time.strftime('%H:%M')} Uhr**")

        submitted = st.form_submit_button("In das Programmschema aufnehmen")
        
        if submitted:
            start_min = time_to_minutes(start_time)
            end_min = time_to_minutes(calculated_end_time)
            
            has_conflict = check_time_conflict(start_min, end_min, pattern_str, st.session_state.master_schedule)
            
            if has_conflict:
                st.error(f"❌ **Sendeplatz-Kollision!** Im Muster '{pattern_str}' ist um {start_time.strftime('%H:%M')} Uhr bereits ein Programmpunkt aktiv.")
            else:
                entry = {
                    "Bereich": section_type,
                    "Muster": pattern_str,
                    "Zeit": f"{start_time.strftime('%H:%M')} - {calculated_end_time.strftime('%H:%M')}",
                    "Sendung": show_name,
                    "Staffel": season_num,
                    "Episode": episode_num,
                    "Netto (Min.)": net_runtime,
                    "Werbung (Min.)": ad_runtime,
                    "Gesamt (Min.)": total_duration
                }
                st.session_state.master_schedule.append(entry)
                st.success(f"Erfolgreich eingepflegt: {show_name} (St. {season_num}, Ep. {episode_num}) im Schema gespeichert!")
                st.rerun()

with tab_view:
    st.subheader("Master-Sendeplan & Wochenmuster")
    st.markdown("Hier siehst du dein vollständiges Programm. Wiederkehrende Mo-Fr Blöcke bilden das stabile Grundgerüst, während die Primetime flexibel gesteuert wird.")
    
    if len(st.session_state.master_schedule) > 0:
        df_plan = pd.DataFrame(st.session_state.master_schedule)
        st.dataframe(df_plan, use_container_width=True)
        
        st.markdown("### 🛠️ Programmpunkte gezielt bearbeiten oder löschen")
        row_options = [f"[{i}] {row['Muster']} | {row['Zeit']} - {row['Sendung']} (St. {row['Staffel']}, Ep. {row['Episode']})" for i, row in enumerate(st.session_state.master_schedule)]
        selected_to_delete = st.selectbox("Wähle den zu löschenden Programmpunkt:", row_options)
        
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("Ausgewählten Programmpunkt entfernen"):
                idx = row_options.index(selected_to_delete)
                removed = st.session_state.master_schedule.pop(idx)
                st.success(f"Entfernt: {removed['Sendung']} ({removed['Zeit']})")
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
            file_name="master_tv_sendeplan.csv",
            mime="text/csv",
        )
    else:
        st.info("Das Programmschema ist aktuell leer. Füge im ersten Tab die ersten Blöcke hinzu.")

with tab_database:
    st.subheader("Verifizierte Serien- & Laufzeit-Referenz")
    st.markdown("Übersicht aller hinterlegten Top-Formate mit ihren echten Staffellimits und Standardwerten.")
    
    db_list = []
    for s_name, s_info in SERIES_DATABASE.items():
        db_list.append({
            "Sendung": s_name,
            "Genre": s_info["genre"],
            "Staffeln": ", ".join(map(str, s_info["seasons"].keys())),
            "Std. Netto": f"{s_info['default_net']} Min.",
            "Std. Werbung": f"{s_info['default_ad']} Min."
        })
    st.table(pd.DataFrame(db_list))
