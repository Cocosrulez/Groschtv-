from datetime import datetime, time, timedelta
import json
import os
import pandas as pd
import streamlit as st

# Dateipfad für Version 2.0
SAVE_FILE = "sendeplan_v2.json"

# Seitenkonfiguration
st.set_page_config(
    page_title="Master Control v2.0 | Broadcast Direktion",
    page_icon="🎬",
    layout="wide",
)

# --- MODERNES TV-DESIGN (CSS) ---
st.markdown(
    """
    <style>
    .main { background-color: #f4f6f9; }
    .stMetric { background-color: #ffffff; padding: 12px; border-radius: 6px; border-left: 4px solid #1f77b4; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .block-container { padding-top: 1.5rem; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- MASTER FORMAT-DATENBANK ---
SERIES_DATABASE = {
    "Hacks": {
        "genre": "Comedy",
        "seasons": {1: 10, 2: 8, 3: 9},
        "net": 24,
        "ad": 6,
    },
    "Breaking Bad": {
        "genre": "Drama",
        "seasons": {1: 7, 2: 13, 3: 13, 4: 13, 5: 16},
        "net": 45,
        "ad": 15,
    },
    "Grey's Anatomy": {
        "genre": "Medical Drama",
        "seasons": {1: 9, 2: 27, 3: 25, 4: 17},
        "net": 42,
        "ad": 15,
    },
    "Curb Your Enthusiasm": {
        "genre": "Comedy",
        "seasons": {1: 10, 2: 10, 3: 10},
        "net": 28,
        "ad": 5,
    },
    "GZSZ": {
        "genre": "Daily Soap",
        "seasons": {1: 250},
        "net": 22,
        "ad": 8,
    },
    "Tatort": {
        "genre": "Krimi",
        "seasons": {2026: 35},
        "net": 88,
        "ad": 12,
    },
    "Spielfilm / Blockbuster": {
        "genre": "Film",
        "seasons": {2026: 1},
        "net": 105,
        "ad": 15,
    },
    "The Big Bang Theory": {
        "genre": "Sitcom",
        "seasons": {1: 17, 2: 23},
        "net": 21,
        "ad": 9,
    },
}

WEEKDAYS = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]


# --- PERSISTENZ (LADEN & SPEICHERN) ---
def load_schedule():
  if os.path.exists(SAVE_FILE):
    try:
      with open(SAVE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except:
                pass
  # Sinnvoller Standard-Sendeplan
  return [
      {
          "Wochentag": "Montag",
          "Uhrzeit": "20:15 - 21:00",
          "Sendung": "Hacks",
          "Staffel": 1,
          "Ep.": 1,
          "Netto": 24,
          "Werbung": 6,
          "Gesamt": 30,
      },
      {
          "Wochentag": "Montag",
          "Uhrzeit": "21:00 - 22:00",
          "Sendung": "Breaking Bad",
          "Staffel": 1,
          "Ep.": 1,
          "Netto": 45,
          "Werbung": 15,
          "Gesamt": 60,
      },
  ]


def save_schedule(data):
  try:
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=4)
  except Exception as e:
    st.error(f"Speicherfehler: {e}")


if "schedule" not in st.session_state:
  st.session_state.schedule = load_schedule()

# --- HEADER & KERN-METRIKEN ---
st.title("🎬 Master Control v2.0: Programm-Direktion")
st.markdown(
    "**Streamlined Scheduling Engine** — Optimiert für schnelle Taktung und"
    " nahtlose Wochen-Programmierung."
)

total_items = len(st.session_state.schedule)
total_mins = sum([x.get("Gesamt", 0) for x in st.session_state.schedule])

c1, c2, c3, c4 = st.columns(4)
with c1:
  st.metric("Sendeplätze", total_items)
with c2:
  st.metric("Wochen-Sendezeit", f"{total_mins} Min.")
with c3:
  st.metric("Engine-Status", "v2.0 (Aktiv & Sicher)")
with c4:
  st.metric("Planungs-Modus", "Wochen-Matrix")

st.markdown("---")

# --- HAUPTMENÜ (TABS) ---
tab_matrix, tab_builder, tab_db = st.tabs([
    "📅 Wochen-Matrix & Bearbeitung",
    "⚡ Schnell-Planer (Neuer Slot)",
    "📚 Format-Referenz",
])

with tab_matrix:
  st.subheader("Wochenübersicht & Live-Tabelle")
  st.markdown(
      "Passe Sendezeiten oder Sendungen direkt hier an. Änderungen werden"
      " sofort gesichert."
  )

  if st.session_state.schedule:
    df = pd.DataFrame(st.session_state.schedule)

    # Sortier-Helper für Wochentage
    day_sorting = {d: i for i, d in enumerate(WEEKDAYS)}
    if "Wochentag" in df.columns:
      df["_sort"] = df["Wochentag"].map(day_sorting).fillna(9)
      df = df.sort_values(by=["_sort", "Uhrzeit"]).drop(columns=["_sort"])

    # Interaktiver Editor
    edited_df = st.data_editor(
        df, use_container_width=True, key="v2_editor", num_rows="dynamic"
    )

    # Synchronisation bei Änderung
    new_records = edited_df.to_dict(orient="records")
    if new_records != st.session_state.schedule:
      st.session_state.schedule = new_records
      save_schedule(st.session_state.schedule)
      st.rerun()

    # Schnell-Aktionen
    col_a1, col_a2 = st.columns(2)
    with col_a1:
      if st.button("🗑️ Gesamten Sendeplan leeren"):
        st.session_state.schedule = []
        save_schedule([])
        st.rerun()
    with col_a2:
      csv_export = edited_df.to_csv(index=False).encode("utf-8")
      st.download_button(
          "📥 Sendeplan als CSV exportieren",
          csv_export,
          "sendeplan_v2.csv",
          "text/csv",
      )
  else:
    st.info(
        "Der Sendeplan ist aktuell leer. Füge über den Reiter 'Schnell-Planer'"
        " neue Formate hinzu."
    )

with tab_builder:
  st.subheader("Neuen Programmpunkt einpflegen")
  st.markdown(
      "Wähle Format und Sendezeit. Das System berechnet Laufzeiten und"
      " Werbeblöcke automatisch."
  )

  with st.form("builder_v2"):
    col_b1, col_b2 = st.columns(2)

    with col_b1:
      day = st.selectbox("Wochentag", WEEKDAYS)
      show = st.selectbox("Format / Sendung", list(SERIES_DATABASE.keys()))

      format_info = SERIES_DATABASE[show]
      seasons = list(format_info["seasons"].keys())
      season = st.selectbox("Staffel", seasons)

      max_ep = format_info["seasons"][season]
      episode = st.selectbox(
          "Episodennummer", list(range(1, max_ep + 1))
      )

    with col_b2:
      start_t = st.time_input("Startzeit", time(20, 15))
      count = st.selectbox(
          "Anzahl Folgen hintereinander", list(range(1, 6))
      )

      net_time = format_info["net"]
      ad_time = format_info["ad"]
      total_block = net_time + ad_time

      st.markdown(
          f"💡 **Standard-Laufzeit:** {net_time} Min. Netto + {ad_time} Min."
          f" Werbung = **{total_block} Min. gesamt pro Folge**."
      )

    submitted = st.form_submit_button("Sendung in den Sendeplan aufnehmen")

    if submitted:
      current_time_dt = datetime.combine(datetime.today(), start_t)
      added_entries = []

      for i in range(count):
        ep_num = episode + i
        start_str = current_time_dt.strftime("%H:%M")
        current_time_dt += timedelta(minutes=total_block)
        end_str = current_time_dt.strftime("%H:%M")

        entry = {
            "Wochentag": day,
            "Uhrzeit": f"{start_str} - {end_str}",
            "Sendung": show,
            "Staffel": season,
            "Ep.": ep_num,
            "Netto": net_time,
            "Werbung": ad_time,
            "Gesamt": total_block,
        }
        added_entries.append(entry)

      st.session_state.schedule.extend(added_entries)
      save_schedule(st.session_state.schedule)
      st.success(
          f"Erfolgreich {count} Folge(n) für {day} eingeplant & gespeichert!"
      )
      st.rerun()

with tab_db:
  st.subheader("Hinterlegte Formate & Parameter")
  st.markdown(
      "Übersicht aller verifizierten Serien und deren Standard-Laufzeiten."
  )

  db_rows = []
  for k, v in SERIES_DATABASE.items():
    db_rows.append({
        "Sendung": k,
        "Genre": v["genre"],
        "Netto (Min.)": v["net"],
        "Werbung (Min.)": v["ad"],
        "Gesamt (Min.)": v["net"] + v["ad"],
    })
  st.table(pd.DataFrame(db_rows))
