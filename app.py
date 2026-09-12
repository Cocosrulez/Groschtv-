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
            "Zeitfenster": "20:15 - 21:00", # Absichtlich als Test für den Logikfehler
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
            try:
                ex_start_parts = list(map(int, times_part[0].split(":")))
                ex_end_parts = list(map(int, times_part[1].split(":")))
                
                ex_start_min = ex_start_parts[0] * 60 + ex_start_parts[1]
                ex_end_min = ex_end_parts[0] * 60 + ex_end_parts[1]
                
                if (new_start_min < ex_end_min) and (new_end_min > ex_start_min):
                    return True
            except Exception:
                continue
    return False

# --- HEADER & KPI DASHBOARD ---
st.title("📡 Master Control: Primetime- & Sendeplan-Direktion")
st.markdown("**Tagesgenaue Programmierung** — Sendeplan direkt bearbeiten mit automatischer Echtzeit-Logikprüfung.")

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
with col_kpi1:
    st.metric(label="Eingetragene Sendeplätze", value=len(st.session_state.master_schedule))
with col_kpi2:
    st.metric(label="Verfügbare Formate in DB", value=len(SERIES_DATABASE))
with col_kpi3:
    st.metric(label="Logik-Engine", value="Aktiv (Live-Korrektur)")

st.markdown("---")

# --- NAVIGATION TABS ---
tab_builder, tab_view, tab_database = st.tabs([
    "⚡ Programmpunkt hinzufügen (Primetime / Tag)", 
    "📋 Sendeplan & Live-Logikprüfung", 
    "📚 Serien- & Format-Datenbank"
])

with tab_builder:
    st.subheader("Sendeplatz präzise per Dropdown einplanen (Mo–So)")
    st.markdown("Wähle alle Parameter bequem über feste Auswahllisten aus.")
    
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
            episode_choices = list(range(1, max_eps + 1))
            episode_num = st.selectbox("Start-Episodennummer", episode_choices)

        with col_f2:
            st.markdown("#### ⏰ Sendezeit-Fenster & Mehrfachauswahl")
            start_time = st.time_input("Startzeit (z.B. 20:15)", time(20, 15))
            
            episodes_count = st.selectbox(
                "Anzahl Folgen (gleich mehrere nacheinander einplanen)", 
                options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            )
            
            st.markdown("---")
            net_options = [15, 20, 21, 22, 24, 28, 30, 42, 45, 50, 60, 90, 105, 120]
            net_default_idx = net_options.index(default_net) if default_net in net_options else 6
            net_runtime = st.selectbox("Netto-Laufzeit pro Folge (Min.)", options=net_options, index=net_default_idx)
            
            ad_options = [0, 3, 5, 6, 8, 9, 10, 12, 15, 20]
            ad_default_idx = ad_options.index(default_ad) if default_ad in ad_options else 3
            ad_runtime = st.selectbox("Werbezeit pro Folge (Min.)", options=ad_options, index=ad_default_idx)
            
        total_duration = net_runtime + ad_runtime
        
        start_dt = datetime.combine(datetime.today(), start_time)
        calculated_end_dt = start_dt + timedelta(minutes=total_duration * episodes_count)
        
        if episodes_count > 1:
            st.info(f"💡 **Mehrfach-Planung aktiv:** Es werden **{episodes_count} Folgen** eingeplant. Sende-Ende ca. **{calculated_end_dt.time().strftime('%H:%M')} Uhr**.")
        else:
            st.info(f"💡 **Sende-Fenster Vorschau:** Von **{start_time.strftime('%H:%M')} Uhr** bis **{calculated_end_dt.time().strftime('%H:%M')} Uhr**.")

        submitted = st.form_submit_button("Sendung(en) in das tagesgenaue Schema aufnehmen")
        
        if submitted:
            temp_entries = []
            current_dt = datetime.combine(datetime.today(), start_time)
            conflict_found = False
            
            for i in range(episodes_count):
                current_ep_num = episode_num + i
                
                ep_start_dt = current_dt
                ep_end_dt = current_dt + timedelta(minutes=total_duration)
                
                start_min = time_to_minutes(ep_start_dt.time())
                end_min = time_to_minutes(ep_end_dt.time())
                
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
                current_dt = ep_end_dt
            
            if conflict_found:
                st.error(f"❌ **Sendeplatz-Kollision am {target_day}!** Überschneidung mit einem anderen Sendeplatz.")
            else:
                st.session_state.master_schedule.extend(temp_entries)
                st.success(f"Erfolgreich für **{target_day}** eingepflegt!")
                st.rerun()

with tab_view:
    st.subheader("Wochen-Sendeplan & Live-Logikprüfung")
    st.markdown("Du kannst die Tabelle hier direkt bearbeiten (z.B. das **Zeitfenster** anpassen, wenn ein Logikfehler angezeigt wird). Das System prüft die Werte in Echtzeit!")
    
    if len(st.session_state.master_schedule) > 0:
        df_plan = pd.DataFrame(st.session_state.master_schedule)
        
        day_order = {"Montag": 1, "Dienstag": 2, "Mittwoch": 3, "Donnerstag": 4, "Freitag": 5, "Samstag": 6, "Sonntag": 7, "Montag bis Freitag (Mo-Fr Serie)": 0}
        if "Tag / Wochentag" in df_plan.columns:
            df_plan["Sort"] = df_plan["Tag / Wochentag"].map(day_order).fillna(8)
            df_plan = df_plan.sort_values(by=["Sort", "Zeitfenster"]).drop(columns=["Sort"])
        
        # NEU: Interaktiver Data Editor, damit der Nutzer direkt im Plan Änderungen vornehmen kann!
        edited_df = st.data_editor(
            df_plan, 
            use_container_width=True, 
            key="schedule_editor",
            num_rows="dynamic"
        )
        
        # Wenn der Nutzer etwas in der Tabelle direkt geändert hat, aktualisieren wir den Session State sofort
        updated_records = edited_df.to_dict(orient="records")
        if updated_records != st.session_state.master_schedule:
            st.session_state.master_schedule = updated_records
            st.rerun()

        # LOGIK-PRÜFUNG in Echtzeit auf Basis der aktuellen Daten
        logik_meldungen = []
        for idx, row in edited_df.iterrows():
            try:
                t_parts = row["Zeitfenster"].split(" - ")
                s_parts = list(map(int, t_parts[0].split(":")))
                e_parts = list(map(int, t_parts[1].split(":")))
                slot_duration = (e_parts[0] * 60 + e_parts[1]) - (s_parts[0] * 60 + s_parts[1])
                
                if slot_duration != row["Gesamt (Min.)"]:
                    logik_meldungen.append(
                        f"⚠️ **Logikfehler bei '{row['Sendung']}' (Staffel {row['Staffel']}, Ep. {row['Episode']}) am {row['Tag / Wochentag']} ({row['Zeitfenster']}):** "
                        f"Das Zeitfenster ist **{slot_duration} Min.** lang, aber die Sendung benötigt laut Laufzeit exakt **{row['Gesamt (Min.)']} Min.**! "
                        f"*(Tipp: Passe das Zeitfenster oben direkt in der Tabelle an, um den Fehler zu beheben)*"
                    )
            except Exception:
                logik_meldungen.append(f"⚠️ Ungültiges Zeitformat bei Zeile {idx+1}. Bitte im Format 'HH:MM - HH:MM' angeben.")

        if logik_meldungen:
            st.markdown("---")
            st.error("### 🚨 Aktive Logikfehler im Sendeplan:")
            for m in logik_meldungen:
                st.markdown(m)
        else:
            st.markdown("---")
            st.success("✅ **Alles perfekt!** Alle Zeitfenster stimmen exakt mit den Programmdauern überein. Keine Logikfehler vorhanden.")

        st.markdown("### 🛠️ Zusätzliche Verwaltung")
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("Komplettes Schema zurücksetzen"):
                st.session_state.master_schedule = []
                st.rerun()
        with col_act2:
            csv_data = edited_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Sendeplan als CSV / Excel exportieren",
                data=csv_data,
                file_name="wochen_tv_sendeplan.csv",
                mime="text/csv",
            )
    else:
        st.info("Das Programmschema ist aktuell leer.")

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
