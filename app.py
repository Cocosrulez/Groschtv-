from datetime import datetime, time, timedelta
import json
import os
import pandas as pd
import streamlit as st

# Dateipfad für Version 2.1
SAVE_FILE = "sendeplan_v2.1.json"

# Seitenkonfiguration
st.set_page_config(
    page_title="Master Control v2.1 | Broadcast Direktion",
    page_icon="📡",
    layout="wide",
)

# --- MODERNES TV-DESIGN (CLEAN & PROFESSIONAL) ---
st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 14px; border-radius: 8px; border-left: 4px solid #0066cc; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    .block-container { padding-top: 2rem; }
    .error-card { background-color: #fff3f3; border-left: 5px solid #d9534f; padding: 12px 16px; border-radius: 6px; margin-bottom: 10px; }
    .success-card { background-color: #f0f9f4; border-left: 5px solid #28a745; padding: 12px 16px; border-radius: 6px; margin-bottom: 10px; }
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
  # Beispiel mit absichtlichem Fehler (Hacks: 45 Min Fenster bei 30 Min Laufzeit), um die Live-Engine zu demonstrieren
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
st.title("📡 Master Control v2.1: Programm-Direktion")
st.markdown(
    "**Smart Scheduling & Live Validation Engine** — Automatische"
    " Laufzeit-Prüfung, Werbe-Kontrolle und sofortige Persistenz."
)

total_items = len(st.session_state.schedule)
total_mins = sum([x.get("Gesamt", 0) for x in st.session_state.schedule])

c1, c2, c3, c4 = st.columns(4)
with c1:
  st.metric("Sendeplätze", total_items)
with c2:
  st.metric("Gesamt-Sendezeit", f"{total_mins} Min.")
with c3:
  st.metric("Engine-Status", "v2.1 (Live-Prüfung aktiv)")
with c4:
  st.metric("Persistenz", "Automatisch gesichert")

st.markdown("---")

# --- HAUPTMENÜ (TABS) ---
tab_matrix, tab_builder, tab_db = st.tabs([
    "📅 Wochen-Matrix & Live-Fehlerprüfung",
    "⚡ Schnell-Planer (Neuer Slot)",
    "📚 Format-Referenz",
])

with tab_matrix:
  st.subheader("Wochenübersicht & Interaktive Fehlerkorrektur")
  st.markdown(
      "Passe Zeiten, Netto- oder Werbezeiten direkt in der Tabelle an. Das"
      " System berechnet die Gesamtlaufzeit und prüft auf Logikfehler in"
      " Echtzeit!"
  )

  if st.session_state.schedule:
    df = pd.DataFrame(st.session_state.schedule)

    # Wochentag-Sortierung
    day_sorting = {d: i for i, d in enumerate(WEEKDAYS)}
    if "Wochentag" in df.columns:
      df["_sort"] = df["Wochentag"].map(day_sorting).fillna(9)
      df = df.sort_values(by=["_sort", "Uhrzeit"]).drop(columns=["_sort"])

    # Interaktiver Data Editor
    edited_df = st.data_editor(
        df, use_container_width=True, key="v21_editor", num_rows="dynamic"
    )

    # Automatische Neuberechnung der Spalten bei Tabellen-Änderung
    processed_records = []
    for idx, row in edited_df.iterrows():
      r_dict = row.to_dict()
      # Automatische Gesamt-Kalkulation: Netto + Werbung = Gesamt
      try:
        net = int(r_dict.get("Netto", 0))
        ad = int(r_dict.get("Werbung", 0))
        r_dict["Gesamt"] = net + ad
      except:
        pass
      processed_records.append(r_dict)

    # Bei Änderungen sofort speichern und aktualisieren
    if processed_records != st.session_state.schedule:
      st.session_state.schedule = processed_records
      save_schedule(st.session_state.schedule)
      st.rerun()

    # --- ELEGANTE LIVE-LOGIKPRÜFUNG (FEHLER-DIREKTION) ---
    st.markdown("### 🔍 Live-Logik & Konsistenz-Prüfung")
    errors_found = []

    for idx, row in pd.DataFrame(st.session_state.schedule).iterrows():
      try:
        # Prüfe Zeitfenster-Länge vs. Gesamt-Laufzeit (Netto + Werbung)
        time_parts = row["Uhrzeit"].split(" - ")
        start_parts = list(map(int, time_parts[0].split(":")))
        end_parts = list(map(int, time_parts[1].split(":")))
        slot_mins = (end_parts[0] * 60 + end_parts[1]) - (
            start_parts[0] * 60 + start_parts[1]
        )

        expected_total = int(row["Netto"]) + int(row["Werbung"])

        if slot_mins != expected_total:
          errors_found.append(
              f"⚠️ **Sendeplatz-Fehler bei '{row['Sendung']}' (Staffel {row['Staffel']}, Ep. {row['Ep.']}) am {row['Wochentag']} ({row['Uhrzeit']}):** "
              f"Das Zeitfenster ist **{slot_mins} Minuten** lang, aber die Format-Laufzeit (Netto {row['Netto']} Min. + Werbung {row['Werbung']} Min.) beträgt exakt **{expected_total} Minuten**! "
              f"*(Tipp: Korrigiere oben in der Tabelle die Uhrzeit oder passe die Werbe-/Nettozeit an, um den Fehler zu beheben)*"
          )
      except Exception:
        errors_found.append(
            f"⚠️ **Formatierungsfehler** in Zeile {idx+1}: Ungültiges"
            " Zeitformat (Bitte 'HH:MM - HH:MM' nutzen)."
        )

    if errors_found:
      for err in errors_found:
        st.markdown(f'<div class="error-card">{err}</div>', unsafe_allow_html=True)
    else:
      st.markdown(
          '<div class="success-card">✅ **Alles perfekt!** Sendezeiten und'
          " Laufzeiten stimmen absolut überein. Keine Logikfehler im Schema."
          "</div>",
          unsafe_allow_html=True,
      )

    st.markdown("---")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
      if st.button("🗑️ Sendeplan komplett zurücksetzen"):
        st.session_state.schedule = []
        save_schedule([])
        st.rerun()
    with col_a2:
      csv_export = pd.DataFrame(st.session_state.schedule).to_csv(index=False).encode("utf-8")
      st.download_button(
          "📥 Bereinigten Sendeplan als CSV exportieren",
          csv_export,
          "sendeplan_v2.1.csv",
          "text/csv",
      )
  else:
    st.info("Der Sendeplan ist aktuell leer. Füge im Tab 'Schnell-Planer' neue Formate hinzu.")

with tab_builder:
  st.subheader("Programmpunkt fehlerfrei einplanen")
  st.markdown(
      "Wähle Wochentag, Format und Startzeit. Das System berechnet die"
      " passenden Blöcke automatisch vor."
  )

  with st.form("builder_v21"):
    col_b1, col_b2 = st.columns(2)

    with col_b1:
      day = st.selectbox("Wochentag", WEEKDAYS)
      show = st.selectbox("Format / Sendung", list(SERIES_DATABASE.keys()))

      format_info = SERIES_DATABASE[show]
      seasons = list(format_info["seasons"].keys())
      season = st.selectbox("Staffel", seasons)

      max_ep = format_info["seasons"][season]
      episode = st.selectbox(
          "Start-Episodennummer", list(range(1, max_ep + 1))
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
          f"Erfolgreich {count} Folge(n) für {day} fehlerfrei eingeplant &"
          " gespeichert!"
      )
      st.rerun()

with tab_db:
  st.subheader("Verifizierte Formate & Standard-Laufzeiten")
  st.markdown(
      "Referenztabelle aller hinterlegten Serien mit Netto- und Werbezeiten."
  )

  db_rows = []
  for k, v in SERIES_DATABASE.items():
    db_rows.append({
        "Format / Sendung": k,
        "Genre": v["genre"],
        "Standard Netto (Min.)": v["net"],
        "Standard Werbung (Min.)": v["ad"],
        "Gesamt-Laufzeit (Min.)": v["net"] + v["ad"],
    })
  st.table(pd.DataFrame(db_rows))
