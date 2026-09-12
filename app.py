from datetime import datetime, time, timedelta
import json
import os
import pandas as pd
import streamlit as st

# Dateipfad für Version 2.3
SAVE_FILE = "sendeplan_v2.3.json"

# Seitenkonfiguration
st.set_page_config(
    page_title="Master Control v2.3 | Broadcast Direktion",
    page_icon="📡",
    layout="wide",
)

# --- SAUBERES, MODERNES TV-DESIGN ---
st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 12px; border-radius: 8px; border-left: 4px solid #0066cc; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .block-container { padding-top: 2rem; }
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
  # Standardbeispiel mit absichtlichem Fehler zur Demonstration
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
st.title("📡 Master Control v2.3: Programm-Direktion")
st.markdown(
    "**Smart Scheduling & Touch-Dropdown Engine** — Sendeplan-Direktion mit"
    " integrierter Live-Fehlerprüfung."
)

total_items = len(st.session_state.schedule)
total_mins = sum([x.get("Gesamt", 0) for x in st.session_state.schedule])

c1, c2, c3, c4 = st.columns(4)
with c1:
  st.metric("Sendeplätze", total_items)
with c2:
  st.metric("Gesamt-Sendezeit", f"{total_mins} Min.")
with c3:
  st.metric("Engine-Status", "v2.3 (Aktiv)")
with c4:
  st.metric("Persistenz", "Live gesichert")

st.markdown("---")

# --- HAUPTMENÜ (TABS) ---
tab_matrix, tab_builder, tab_db = st.tabs([
    "📅 Wochen-Matrix & Dropdown-Editor",
    "⚡ Schnell-Planer (Neuer Slot)",
    "📚 Format-Referenz",
])

with tab_matrix:
  st.subheader("Wochenübersicht & Sendeplan")

  if st.session_state.schedule:
    # 1. Übersichtstabelle (Clean & Read-only)
    df = pd.DataFrame(st.session_state.schedule)
    day_sorting = {d: i for i, d in enumerate(WEEKDAYS)}
    if "Wochentag" in df.columns:
      df["_sort"] = df["Wochentag"].map(day_sorting).fillna(9)
      df = df.sort_values(by=["_sort", "Uhrzeit"]).drop(columns=["_sort"])

    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("🛠️ Sendeplatz-Feintuning per Kombi-Dropdown")

    # Auswahl des zu bearbeitenden Eintrags im großen Dropdown
    options_labels = [
        f"#{i+1}: {item['Wochentag']} | {item['Uhrzeit']} – {item['Sendung']} (St. {item['Staffel']}, Ep. {item['Ep.']})"
        for i, item in enumerate(st.session_state.schedule)
    ]
    selected_label = st.selectbox(
        "1. Programmpunkt aus der Liste auswählen", options_labels
    )
    selected_idx = options_labels.index(selected_label)
    current_item = st.session_state.schedule[selected_idx]

    # Startstunde und -minute ermitteln
    try:
      start_str_parts = current_item["Uhrzeit"].split(" - ")[0].split(":")
      curr_h = int(start_str_parts[0])
      curr_m = int(start_str_parts[1])
    except:
      curr_h, curr_m = 20, 15

    # 2. Die süßen kleinen Dropdown-Menüs für Stunde & Minute direkt darunter
    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    with col_e1:
      new_h = st.selectbox(
          "Start-Stunde", list(range(0, 24)), index=curr_h, key="edit_h"
      )
    with col_e2:
      minute_options = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
      closest_m = min(minute_options, key=lambda x: abs(x - curr_m))
      new_m = st.selectbox(
          "Start-Minute",
          minute_options,
          index=minute_options.index(closest_m),
          key="edit_m",
      )
    with col_e3:
      new_net = st.number_input(
          "Netto-Laufzeit (Min.)",
          min_value=1,
          max_value=300,
          value=int(current_item["Netto"]),
          key="edit_net",
      )
    with col_e4:
      new_ad = st.number_input(
          "Werbezeit (Min.)",
          min_value=0,
          max_value=60,
          value=int(current_item["Werbung"]),
          key="edit_ad",
      )

    # Berechne neue Zeiten
    total_len = new_net + new_ad
    start_dt = datetime.combine(datetime.today(), time(new_h, new_m))
    end_dt = start_dt + timedelta(minutes=total_len)
    new_time_str = (
        f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
    )

    if st.button("💾 Änderungen für diesen Sendeplatz speichern"):
      st.session_state.schedule[selected_idx]["Uhrzeit"] = new_time_str
      st.session_state.schedule[selected_idx]["Netto"] = int(new_net)
      st.session_state.schedule[selected_idx]["Werbung"] = int(new_ad)
      st.session_state.schedule[selected_idx]["Gesamt"] = int(total_len)
      save_schedule(st.session_state.schedule)
      st.success("Erfolgreich aktualisiert & dauerhaft gespeichert!")
      st.rerun()

    # --- ECHTZEIT-LOGIKPRÜFUNG (DETAILMELDUNGEN WIEDER DA) ---
    st.markdown("---")
    st.subheader("🔍 Live-Logik & Konsistenz-Prüfung")
    errors_found = []

    for idx, row in enumerate(st.session_state.schedule):
      try:
        t_parts = row["Uhrzeit"].split(" - ")
        s_parts = list(map(int, t_parts[0].split(":")))
        e_parts = list(map(int, t_parts[1].split(":")))
        slot_mins = (e_parts[0] * 60 + e_parts[1]) - (
            s_parts[0] * 60 + s_parts[1]
        )

        expected_total = int(row["Netto"]) + int(row["Werbung"])

        if slot_mins != expected_total:
          errors_found.append(
              f"**Sendeplatz #{idx+1} ({row['Wochentag']}, {row['Uhrzeit']}) – Format '{row['Sendung']}':** "
              f"Das Zeitfenster ist **{slot_mins} Min.** lang, aber Netto ({row['Netto']} Min.) + Werbung ({row['Werbung']} Min.) ergeben exakt **{expected_total} Min.**! "
              f"*(Hinweis: Wenn du z.B. die Werbung von 6 auf 8 Minuten änderst, stimmt das Zeitfenster nicht mehr überein)*"
          )
      except Exception:
        errors_found.append(
            f"Formatierungsfehler in Zeile {idx+1}: Ungültiges Zeitformat."
        )

    if errors_found:
      for err in errors_found:
        st.error(f"⚠️ {err}")
    else:
      st.success(
          "✅ **Alles perfekt!** Alle Sendezeiten und Laufzeiten stimmen"
          " überein. Keine Logikfehler vorhanden."
      )

    st.markdown("---")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
      if st.button("🗑️ Sendeplan komplett zurücksetzen"):
        st.session_state.schedule = []
        save_schedule([])
        st.rerun()
    with col_a2:
      csv_export = pd.DataFrame(st.session_state.schedule).to_csv(
          index=False
      ).encode("utf-8")
      st.download_button(
          "📥 Bereinigten Sendeplan als CSV exportieren",
          csv_export,
          "sendeplan_v2.3.csv",
          "text/csv",
      )
  else:
    st.info("Der Sendeplan ist aktuell leer.")

with tab_builder:
  st.subheader("Programmpunkt fehlerfrei einplanen")
  with st.form("builder_v23"):
    col_b1, col_b2 = st.columns(2)
    with col_b1:
      day = st.selectbox("Wochentag", WEEKDAYS)
      show = st.selectbox("Format / Sendung", list(SERIES_DATABASE.keys()))
      format_info = SERIES_DATABASE[show]
      season = st.selectbox(
          "Staffel", list(format_info["seasons"].keys())
      )
      episode = st.selectbox(
          "Start-Episodennummer",
          list(range(1, format_info["seasons"][season] + 1)),
      )
    with col_b2:
      start_t = st.time_input("Startzeit", time(20, 15))
      count = st.selectbox(
          "Anzahl Folgen nacheinander", list(range(1, 6))
      )
      net_time = format_info["net"]
      ad_time = format_info["ad"]
      total_block = net_time + ad_time
      st.markdown(
          f"💡 **Voreinstellung:** {net_time} Min. Netto + {ad_time} Min."
          f" Werbung = **{total_block} Min. gesamt**."
      )

    submitted = st.form_submit_button("Sendung in den Sendeplan aufnehmen")
    if submitted:
      current_dt = datetime.combine(datetime.today(), start_t)
      added_entries = []
      for i in range(count):
        start_str = current_dt.strftime("%H:%M")
        current_dt += timedelta(minutes=total_block)
        end_str = current_dt.strftime("%H:%M")
        added_entries.append({
            "Wochentag": day,
            "Uhrzeit": f"{start_str} - {end_str}",
            "Sendung": show,
            "Staffel": season,
            "Ep.": episode + i,
            "Netto": net_time,
            "Werbung": ad_time,
            "Gesamt": total_block,
        })
      st.session_state.schedule.extend(added_entries)
      save_schedule(st.session_state.schedule)
      st.success("Erfolgreich eingeplant & gespeichert!")
      st.rerun()

with tab_db:
  st.subheader("Verifizierte Formate & Standard-Laufzeiten")
  db_rows = [
      {
          "Format": k,
          "Genre": v["genre"],
          "Netto (Min.)": v["net"],
          "Werbung (Min.)": v["ad"],
          "Gesamt (Min.)": v["net"] + v["ad"],
      }
      for k, v in SERIES_DATABASE.items()
  ]
  st.table(pd.DataFrame(db_rows))
