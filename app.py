from datetime import datetime, time, timedelta
import json
import os
import pandas as pd
import streamlit as st

# Dateipfad für Version 5.2
SAVE_FILE = "sendeplan_v5.2.json"
FORMATS_FILE = "formats_v5.2.json"

# Seitenkonfiguration
st.set_page_config(
    page_title="Master Control v5.2 | Broadcast Direktion",
    page_icon="📡",
    layout="wide",
)

# --- MODERNES BROADCAST-CONTROL DESIGN (V5.2) ---
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    .block-container { padding-top: 2rem; }
    
    /* Edles Control-Room Dashboard Grid für Metriken */
    .metric-grid {
        display: flex;
        gap: 15px;
        margin-bottom: 25px;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 4px solid #0066cc;
        padding: 16px 20px;
        border-radius: 10px;
        flex: 1;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    .metric-label {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #f8fafc;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- MASTER FORMAT-DATENBANK ---
DEFAULT_SERIES_DATABASE = {
    "Tagesschau / News": {
        "genre": "Nachrichten",
        "seasons": {2026: 365},
        "net": 15,
        "ad": 0,
    },
    "Tagessthemen": {
        "genre": "Information",
        "seasons": {2026: 365},
        "net": 30,
        "ad": 0,
    },
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
    "Deutschland - 100!": {
        "genre": "Information",
        "seasons": {1: 20},
        "net": 75,
        "ad": 0,
    },
    "Deutschland - die reportage!": {
        "genre": "Information",
        "seasons": {1: 50},
        "net": 30,
        "ad": 0,
    },
    "Deutschland - die doku!": {
        "genre": "Information",
        "seasons": {1: 30},
        "net": 45,
        "ad": 0,
    },
    "Deutschlandmagazin": {
        "genre": "Information",
        "seasons": {1: 50},
        "net": 45,
        "ad": 0,
    },
}

# --- SMART FILLER DATENBANK ---
FILLER_DATABASE = {
    "Sender-Trailer": {"net": 1, "ad": 0, "genre": "Promo"},
    "Programm-Vorschau": {"net": 2, "ad": 0, "genre": "Promo"},
    "Musik-Intermezzo": {"net": 3, "ad": 0, "genre": "Musik"},
    "Kurz-Doku / Teaser": {"net": 5, "ad": 0, "genre": "Doku"},
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
DAY_OPTIONS = (
    WEEKDAYS
    + ["Montag bis Freitag (Mo-Fr)"]
    + ["Montag bis Sonntag (Ganze Woche)"]
)
STATUS_OPTIONS = ["Erstausstrahlung", "Wiederholung", "Live"]


# --- FORMAT-PERSISTENZ ---
def load_formats():
  if os.path.exists(FORMATS_FILE):
    try:
      with open(FORMATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      pass
  return DEFAULT_SERIES_DATABASE


def save_formats(db):
  try:
    with open(FORMATS_FILE, "w", encoding="utf-8") as f:
      json.dump(db, f, ensure_ascii=False, indent=4)
  except Exception as e:
    st.error(f"Fehler beim Speichern der Formate: {e}")


if "series_db" not in st.session_state:
  st.session_state.series_db = load_formats()


# --- HILFSFUNKTION FÜR SLOT-HINWEISE ---
def get_slot_grid_info(total_mins):
  target_slot = round(total_mins / 30) * 30
  if target_slot == 0:
    target_slot = 30

  diff = total_mins - target_slot
  if diff == 0:
    return True, f"Passt exakt in ein {target_slot}-Minuten-Raster."
  elif diff < 0:
    return (
        False,
        f"Gesamtlänge beträgt nur {total_mins} Min. ({abs(diff)} Min. kürzer"
        f" als ein regulärer {target_slot}-Minuten-Slot).",
    )
  else:
    return (
        False,
        f"Gesamtlänge beträgt {total_mins} Min. ({diff} Min. Überlänge für einen"
        f" regulären {target_slot}-Minuten-Slot).",
    )


# --- PERSISTENZ (Sendeplan & Bestätigte Warnungen gemeinsam in v5.2 JSON) ---
def load_data():
  target_file = (
      SAVE_FILE
      if os.path.exists(SAVE_FILE)
      else ("sendeplan_v5.1.json" if os.path.exists("sendeplan_v5.1.json") else None)
  )
  schedule = []
  acknowledged = set()

  if target_file:
    try:
      with open(target_file, "r", encoding="utf-8") as f:
        content = json.load(f)
        if isinstance(content, dict):
          schedule = content.get("schedule", [])
          acknowledged = set(content.get("acknowledged_warnings", []))
        elif isinstance(content, list):
          schedule = content
    except Exception:
      pass

  for item in schedule:
    if (
        item.get("Sendung") in ["Tagessthemen", "Tagesschau / News"]
        and item.get("Staffel") == 1
    ):
      item["Staffel"] = 2026

  if not schedule:
    schedule = [
        {
            "Wochentag": "Montag",
            "Uhrzeit": "20:15 - 20:45",
            "Sendung": "Hacks",
            "Staffel": 1,
            "Ep.": 1,
            "Netto": 24,
            "Werbung": 6,
            "Gesamt": 30,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Montag",
            "Uhrzeit": "21:15 - 22:15",
            "Sendung": "Breaking Bad",
            "Staffel": 1,
            "Ep.": 1,
            "Netto": 45,
            "Werbung": 15,
            "Gesamt": 60,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Montag",
            "Uhrzeit": "20:00 - 20:15",
            "Sendung": "Tagesschau / News",
            "Staffel": 2026,
            "Ep.": 1,
            "Netto": 15,
            "Werbung": 0,
            "Gesamt": 15,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Dienstag",
            "Uhrzeit": "20:00 - 20:15",
            "Sendung": "Tagesschau / News",
            "Staffel": 2026,
            "Ep.": 2,
            "Netto": 15,
            "Werbung": 0,
            "Gesamt": 15,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Mittwoch",
            "Uhrzeit": "20:00 - 20:15",
            "Sendung": "Tagesschau / News",
            "Staffel": 2026,
            "Ep.": 3,
            "Netto": 15,
            "Werbung": 0,
            "Gesamt": 15,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Donnerstag",
            "Uhrzeit": "20:00 - 20:15",
            "Sendung": "Tagesschau / News",
            "Staffel": 2026,
            "Ep.": 4,
            "Netto": 15,
            "Werbung": 0,
            "Gesamt": 15,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Freitag",
            "Uhrzeit": "20:00 - 20:15",
            "Sendung": "Tagesschau / News",
            "Staffel": 2026,
            "Ep.": 5,
            "Netto": 15,
            "Werbung": 0,
            "Gesamt": 15,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Samstag",
            "Uhrzeit": "20:15 - 20:30",
            "Sendung": "Tagesschau / News",
            "Staffel": 2026,
            "Ep.": 6,
            "Netto": 15,
            "Werbung": 0,
            "Gesamt": 15,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Sonntag",
            "Uhrzeit": "20:15 - 20:30",
            "Sendung": "Tagesschau / News",
            "Staffel": 2026,
            "Ep.": 7,
            "Netto": 15,
            "Werbung": 0,
            "Gesamt": 15,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Montag",
            "Uhrzeit": "19:30 - 20:00",
            "Sendung": "GZSZ",
            "Staffel": 1,
            "Ep.": 1,
            "Netto": 22,
            "Werbung": 8,
            "Gesamt": 30,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Dienstag",
            "Uhrzeit": "19:30 - 20:00",
            "Sendung": "GZSZ",
            "Staffel": 1,
            "Ep.": 2,
            "Netto": 22,
            "Werbung": 8,
            "Gesamt": 30,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Mittwoch",
            "Uhrzeit": "19:30 - 20:00",
            "Sendung": "GZSZ",
            "Staffel": 1,
            "Ep.": 3,
            "Netto": 22,
            "Werbung": 8,
            "Gesamt": 30,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Donnerstag",
            "Uhrzeit": "19:30 - 20:00",
            "Sendung": "GZSZ",
            "Staffel": 1,
            "Ep.": 4,
            "Netto": 22,
            "Werbung": 8,
            "Gesamt": 30,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Freitag",
            "Uhrzeit": "19:30 - 20:00",
            "Sendung": "GZSZ",
            "Staffel": 1,
            "Ep.": 5,
            "Netto": 22,
            "Werbung": 8,
            "Gesamt": 30,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Montag",
            "Uhrzeit": "20:45 - 21:15",
            "Sendung": "Hacks",
            "Staffel": 1,
            "Ep.": 2,
            "Netto": 24,
            "Werbung": 6,
            "Gesamt": 30,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Montag",
            "Uhrzeit": "22:15 - 23:30",
            "Sendung": "Deutschland - 100!",
            "Staffel": 1,
            "Ep.": 1,
            "Netto": 75,
            "Werbung": 0,
            "Gesamt": 75,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Montag",
            "Uhrzeit": "23:30 - 00:00",
            "Sendung": "Deutschland - die reportage!",
            "Staffel": 1,
            "Ep.": 1,
            "Netto": 30,
            "Werbung": 0,
            "Gesamt": 30,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Dienstag",
            "Uhrzeit": "00:30 - 01:15",
            "Sendung": "Deutschland - die doku!",
            "Staffel": 1,
            "Ep.": 1,
            "Netto": 45,
            "Werbung": 0,
            "Gesamt": 45,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Dienstag",
            "Uhrzeit": "01:15 - 02:00",
            "Sendung": "Deutschlandmagazin",
            "Staffel": 1,
            "Ep.": 1,
            "Netto": 45,
            "Werbung": 0,
            "Gesamt": 45,
            "Status": "Erstausstrahlung",
        },
        {
            "Wochentag": "Montag",
            "Uhrzeit": "02:00 - 02:30",
            "Sendung": "Tagessthemen",
            "Staffel": 2026,
            "Ep.": 1,
            "Netto": 30,
            "Werbung": 0,
            "Gesamt": 30,
            "Status": "Erstausstrahlung",
        },
    ]
  return schedule, acknowledged


def save_data(schedule, acknowledged):
  try:
    data = {
        "schedule": schedule,
        "acknowledged_warnings": list(acknowledged),
    }
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=4)
  except Exception as e:
    st.error(f"Speicherfehler: {e}")


if "schedule" not in st.session_state:
  loaded_sched, loaded_ack = load_data()
  st.session_state.schedule = loaded_sched
  st.session_state.acknowledged_warnings = loaded_ack

# --- HEADER & METRIKEN ---
st.title("📡 Master Control v5.2: Programm-Direktion")
st.markdown(
    "**Broadcast-Engine (v5.2)** — Integrierte Matrix für Tagesprogramm"
    " (06-20h), Primetime (Mo-So) & Nachtprogramm (ab 02:00h)."
)

total_items = len(st.session_state.schedule)
total_mins = sum([x.get("Gesamt", 0) for x in st.session_state.schedule])

st.markdown(
    f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">Aktive Sendeplätze</div>
            <div class="metric-value">{total_items}</div>
        </div>
        <div class="metric-card" style="border-left-color: #10b981;">
            <div class="metric-label">Gesamtsendezeit</div>
            <div class="metric-value">{total_mins} Min.</div>
        </div>
        <div class="metric-card" style="border-left-color: #8b5cf6;">
            <div class="metric-label">Engine Core</div>
            <div class="metric-value">v5.2 Structured Matrix</div>
        </div>
        <div class="metric-card" style="border-left-color: #f59e0b;">
            <div class="metric-label">Verfügbare Formate</div>
            <div class="metric-value">{len(st.session_state.series_db)}</div>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

st.markdown("---")

# --- TABS ---
tab_matrix, tab_prog_matrix, tab_builder, tab_db = st.tabs([
    "📅 Wochen-Matrix & Sendeplan",
    "🎛️ Programmschema-Matrix (Tag / Prime / Nacht)",
    "⚡ Schnell-Planer (Neuer Slot)",
    "📚 Format-Referenz & Bearbeitung",
])

# --- TAB 1: WOCHEN-MATRIX & SENDEPLAN ---
with tab_matrix:
  st.subheader("Wochenübersicht & Sendeplan")

  if st.session_state.schedule:
    df = pd.DataFrame(st.session_state.schedule)
    day_sorting = {d: i for i, d in enumerate(WEEKDAYS)}
    if "Wochentag" in df.columns:
      df["_sort"] = df["Wochentag"].map(day_sorting).fillna(9)
      df = df.sort_values(by=["_sort", "Uhrzeit"]).drop(columns=["_sort"])

    display_df = df[[
        "Wochentag",
        "Uhrzeit",
        "Sendung",
        "Staffel",
        "Ep.",
        "Netto",
        "Werbung",
        "Gesamt",
        "Status",
    ]].copy()
    display_df.columns = [
        "Tag",
        "Uhrzeit",
        "Sendung",
        "St.",
        "Ep.",
        "Netto",
        "Werb.",
        "Ges.",
        "Status",
    ]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    with st.expander("🗑️ Sendeplätze & Episoden verwalten / löschen", expanded=True):
      st.markdown(
          "Wähle einen Sendeplatz aus, um ihn gezielt aus dem Sendeplan zu"
          " entfernen."
      )

      for idx, row in df.iterrows():
        col_m1, col_m2 = st.columns([5, 1])
        with col_m1:
          st.text(
              f"• {row['Wochentag']} | {row['Uhrzeit']} – {row['Sendung']}"
              f" (St. {row['Staffel']}, Ep. {row['Ep.']})"
          )
        with col_m2:
          if st.button("❌ Löschen", key=f"mgmt_del_{idx}"):
            orig_idx = st.session_state.schedule.index(
                row.drop(labels=["_sort"], errors="ignore").to_dict()
            )
            st.session_state.schedule.pop(orig_idx)
            save_data(
                st.session_state.schedule, st.session_state.acknowledged_warnings
            )
            st.success("Sendeplatz entfernt!")
            st.rerun()

    st.markdown("---")

    with st.expander("🛠️ Sendeplatz-Feintuner (Details anpassen)", expanded=False):
      if st.session_state.schedule:
        options_labels = [
            f"#{i+1}: {item['Wochentag']} | {item['Uhrzeit']} –"
            f" {item['Sendung']} (St. {item['Staffel']}, Ep. {item['Ep.']})"
            for i, item in enumerate(st.session_state.schedule)
        ]
        selected_label = st.selectbox(
            "Programmpunkt auswählen", options_labels, key="compact_select"
        )
        selected_idx = options_labels.index(selected_label)
        current_item = st.session_state.schedule[selected_idx]

        current_format = st.session_state.series_db.get(current_item["Sendung"])
        fixed_net = (
            current_format["net"]
            if current_format
            else int(current_item["Netto"])
        )
        new_net = fixed_net

        try:
          start_str_parts = current_item["Uhrzeit"].split(" - ")[0].split(":")
          curr_h = int(start_str_parts[0])
          curr_m = int(start_str_parts[1])
        except Exception:
          curr_h, curr_m = 20, 15

        col_e1, col_e2, col_e3, col_e4 = st.columns([2, 1, 1.5, 1])

        with col_e1:
          new_time_val = st.time_input(
              "Startzeit", value=time(curr_h, curr_m), key="edit_single_time"
          )
        with col_e2:
          new_ad = st.number_input(
              "Werbung (Min.)",
              min_value=0,
              max_value=60,
              value=int(current_item["Werbung"]),
              key="edit_ad",
          )
        with col_e3:
          current_status = current_item.get("Status", "Erstausstrahlung")
          status_idx = (
              STATUS_OPTIONS.index(current_status)
              if current_status in STATUS_OPTIONS
              else 0
          )
          new_status = st.selectbox(
              "Status", STATUS_OPTIONS, index=status_idx, key="edit_status"
          )
        with col_e4:
          st.markdown("<br>", unsafe_allow_html=True)
          save_clicked = st.button(
              "💾 Speichern", use_container_width=True, key="btn_save_slot"
          )

        total_len = new_net + new_ad
        start_dt = datetime.combine(datetime.today(), new_time_val)
        end_dt = start_dt + timedelta(minutes=total_len)
        new_time_str = (
            f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
        )

        if save_clicked:
          st.session_state.schedule[selected_idx]["Uhrzeit"] = new_time_str
          st.session_state.schedule[selected_idx]["Netto"] = int(new_net)
          st.session_state.schedule[selected_idx]["Werbung"] = int(new_ad)
          st.session_state.schedule[selected_idx]["Gesamt"] = int(total_len)
          st.session_state.schedule[selected_idx]["Status"] = new_status
          save_data(
              st.session_state.schedule, st.session_state.acknowledged_warnings
          )
          st.success("Erfolgreich aktualisiert!")
          st.rerun()

    # Validierung & Live-Logik
    st.markdown("---")
    st.subheader("🔍 Live-Logik & Format-Datenbank-Prüfung")
    errors_found = []
    slot_warnings = []
    gap_actions = []

    for idx, row in enumerate(st.session_state.schedule):
      show_name = row["Sendung"]
      format_spec = st.session_state.series_db.get(
          show_name
      ) or FILLER_DATABASE.get(show_name)

      try:
        if not format_spec:
          errors_found.append(
              f"**Unbekanntes Format bei Sendeplatz #{idx+1} ({row['Wochentag']},"
              f" {row['Uhrzeit']}):** '{show_name}' existiert nicht in der"
              " DB!"
          )
        else:
          expected_net = format_spec["net"]
          actual_net = int(row["Netto"])
          if actual_net != expected_net:
            errors_found.append(
                f"**Episodenlängen-Fehler bei Sendeplatz #{idx+1} ("
                f"{row['Wochentag']}, {row['Uhrzeit']}) – '{show_name}':**"
                f" Eingetragen: {actual_net} Min. | DB fordert"
                f" {expected_net} Min."
            )

        t_parts = row["Uhrzeit"].split(" - ")
        s_parts = list(map(int, t_parts[0].split(":")))
        e_parts = list(map(int, t_parts[1].split(":")))

        end_total_mins = e_parts[0] * 60 + e_parts[1]
        start_total_mins = s_parts[0] * 60 + s_parts[1]
        if end_total_mins < start_total_mins:
          end_total_mins += 24 * 60
        slot_mins = end_total_mins - start_total_mins

        expected_total = int(row["Netto"]) + int(row["Werbung"])
        if slot_mins != expected_total:
          errors_found.append(
              f"**Zeitfenster-Konflikt bei Sendeplatz #{idx+1}:** Fenster"
              f" umfasst {slot_mins} Min., Netto+Werbung ergeben"
              f" {expected_total} Min."
          )
      except Exception:
        errors_found.append(
            f"Formatierungsfehler in Zeile {idx+1}: Ungültiges Zeitformat."
        )

    if errors_found:
      for err in errors_found:
        st.error(f"❌ {err}")
    else:
      st.success(
          "✅ **Keine Laufzeit- oder Kollisionsfehler:** Alle Sendeplätze sind"
          " sauber eingetaktet."
      )

    st.markdown("---")
    if st.button("🗑️ Sendeplan komplett zurücksetzen"):
      st.session_state.schedule = []
      st.session_state.acknowledged_warnings.clear()
      save_data([], set())
      st.rerun()
  else:
    st.info("Der Sendeplan ist aktuell leer.")


# --- TAB 2: PROGRAMMSCHEMA-MATRIX (TAG / PRIME / NACHT) ---
with tab_prog_matrix:
  st.subheader(
      "🎛️ Strukturierte Programmschema-Matrix (Tagesprogramm, Primetime,"
      " Nachtprogramm)"
  )
  st.markdown(
      "Hier siehst du die drei dedizierten Programmbereiche, unterteilt nach"
      " **Tagesprogramm (06:00 - 20:00 Uhr)**, **Primetime (Montag bis"
      " Sonntag)** und **Nachtprogramm (ab 02:00 Uhr)**."
  )

  matrix_tab_day, matrix_tab_prime, matrix_tab_night = st.tabs([
      "☀️ Tagesprogramm (06:00 - 20:00)",
      "⭐ Primetime (Mo - So)",
      "🌙 Nachtprogramm (ab 02:00)",
  ])

  # --- BEREICH 1: TAGESPROGRAMM (06:00 bis 20:00 Uhr) ---
  with matrix_tab_day:
    st.markdown(
        "### Tagesprogramm-Slots (06:00 - 20:00 Uhr) über die Woche"
    )
    # Filtere Sendeplätze, die im Bereich 06:00 bis 20:00 Uhr liegen
    day_program_slots = []
    for item in st.session_state.schedule:
      try:
        start_h = int(item["Uhrzeit"].split(" - ")[0].split(":")[0])
        if 6 <= start_h < 20:
          day_program_slots.append(item)
      except:
        pass

    if day_program_slots:
      dp_df = pd.DataFrame(day_program_slots)
      st.dataframe(
          dp_df[[
              "Wochentag",
              "Uhrzeit",
              "Sendung",
              "Staffel",
              "Ep.",
              "Netto",
              "Werbung",
              "Gesamt",
              "Status",
          ]],
          use_container_width=True,
          hide_index=True,
      )
    else:
      st.info(
          "Keine Sendeplätze im Tagesprogramm (06:00 - 20:00) eingetragen."
          " Nutze den Schnell-Planer, um Sendungen hinzuzufügen."
      )

  # --- BEREICH 2: PRIMETIME (Montag bis Sonntag) ---
  with matrix_tab_prime:
    st.markdown("### Primetime-Übersicht (Abendprogramm Mo - So)")
    # Zeige Primetime-Slots (typischerweise ab 20:00 / 20:15 Uhr)
    prime_slots = []
    for item in st.session_state.schedule:
      try:
        start_h = int(item["Uhrzeit"].split(" - ")[0].split(":")[0])
        if 20 <= start_h < 2:  # Abendstunden
          prime_slots.append(item)
      except:
        pass

    if prime_slots:
      prime_df = pd.DataFrame(prime_slots)
      day_sorting = {d: i for i, d in enumerate(WEEKDAYS)}
      prime_df["_sort"] = prime_df["Wochentag"].map(day_sorting).fillna(9)
      prime_df = prime_df.sort_values(by=["_sort", "Uhrzeit"]).drop(
          columns=["_sort"]
      )

      st.dataframe(
          prime_df[[
              "Wochentag",
              "Uhrzeit",
              "Sendung",
              "Staffel",
              "Ep.",
              "Netto",
              "Werbung",
              "Gesamt",
              "Status",
          ]],
          use_container_width=True,
          hide_index=True,
      )
    else:
      st.info("Keine Primetime-Slots gefunden.")

  # --- BEREICH 3: NACHTLICHT / NACHTPROGRAMM (ab 02:00 Uhr) ---
  with matrix_tab_night:
    st.markdown("### Nachtprogramm (ab 02:00 Uhr bis 06:00 Uhr)")
    night_slots = []
    for item in st.session_state.schedule:
      try:
        start_h = int(item["Uhrzeit"].split(" - ")[0].split(":")[0])
        if 2 <= start_h < 6:
          night_slots.append(item)
      except:
        pass

    if night_slots:
      night_df = pd.DataFrame(night_slots)
      st.dataframe(
          night_df[[
              "Wochentag",
              "Uhrzeit",
              "Sendung",
              "Staffel",
              "Ep.",
              "Netto",
              "Werbung",
              "Gesamt",
              "Status",
          ]],
          use_container_width=True,
          hide_index=True,
      )
    else:
      st.info(
          "Keine Sendeplätze im Nachtprogramm (ab 02:00 Uhr) eingetragen. Du"
          " kannst über den Schnell-Planer Sendungen ab 02:00 Uhr anlegen."
      )


# --- TAB 3: SCHNELL-PLANER (NEUER SLOT) ---
with tab_builder:
  st.subheader("Programmpunkt fehlerfrei einplanen")

  col_b1, col_b2 = st.columns(2)
  with col_b1:
    day_selection = st.selectbox(
        "Wochentag / Block", DAY_OPTIONS, key="builder_day"
    )
    show = st.selectbox(
        "Format / Sendung",
        list(st.session_state.series_db.keys())
        + list(FILLER_DATABASE.keys()),
        key="builder_show",
    )

    if show in st.session_state.series_db:
      format_info = st.session_state.series_db[show]
      is_filler = False
    else:
      format_info = FILLER_DATABASE[show]
      is_filler = True

    if not is_filler:
      season = st.selectbox(
          "Staffel", list(format_info["seasons"].keys()), key="builder_season"
      )

      existing_eps = [
          x["Ep."]
          for x in st.session_state.schedule
          if x["Sendung"] == show and x["Staffel"] == season
      ]
      next_ep_suggestion = max(existing_eps) + 1 if existing_eps else 1

      if (
          "builder_last_show" not in st.session_state
          or st.session_state.builder_last_show != show
          or "builder_last_season" not in st.session_state
          or st.session_state.builder_last_season != season
          or "builder_sched_len" not in st.session_state
          or st.session_state.builder_sched_len != len(st.session_state.schedule)
      ):
        st.session_state.builder_last_show = show
        st.session_state.builder_last_season = season
        st.session_state.builder_sched_len = len(st.session_state.schedule)
        st.session_state.builder_ep_input = next_ep_suggestion

      episode = st.number_input(
          "Start-Episodennummer (Automatisch nächste freie Folge)",
          min_value=1,
          max_value=10000,
          value=st.session_state.get("builder_ep_input", next_ep_suggestion),
          step=1,
          key="builder_ep_input",
      )
    else:
      season = 2026
      episode = 1
      st.info("💡 Smart Filler Format (keine Episodennummer nötig).")

  with col_b2:
    suggested_time = time(20, 15)
    if day_selection in WEEKDAYS:
      day_sched = [
          x for x in st.session_state.schedule if x["Wochentag"] == day_selection
      ]
      if day_sched:
        latest_end = "00:00"
        for slot in day_sched:
          try:
            end_t_str = slot["Uhrzeit"].split(" - ")[1]
            if end_t_str > latest_end:
              latest_end = end_t_str
          except:
            pass
        if latest_end != "00:00":
          try:
            h, m = map(int, latest_end.split(":"))
            suggested_time = time(h, m)
          except:
            pass

    start_t = st.time_input(
        "Startzeit (Automatisch im Anschluss)",
        value=suggested_time,
        key="builder_time",
    )
    count = st.selectbox(
        "Anzahl Folgen nacheinander", list(range(1, 6)), key="builder_count"
    )
    plan_status = st.selectbox("Status", STATUS_OPTIONS, key="builder_status")

    net_time = format_info["net"]
    ad_time = format_info["ad"]
    total_block = net_time + ad_time
    st.markdown(
        f"💡 **Voreinstellung für '{show}':** {net_time} Min."
        f" Netto + {ad_time} Min. Werbung = **{total_block} Min."
        f" gesamt**."
    )

  submitted = st.button(
      "Sendung in den Sendeplan aufnehmen",
      key="builder_submit_btn",
      type="primary",
  )
  if submitted:
    added_entries = []

    if day_selection == "Montag bis Freitag (Mo-Fr)":
      target_days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
    elif day_selection == "Montag bis Sonntag (Ganze Woche)":
      target_days = WEEKDAYS
    else:
      target_days = [day_selection]

    current_ep = int(episode)

    for day_name in target_days:
      day_specific_time = start_t
      if (
          day_selection == "Montag bis Sonntag (Ganze Woche)"
          or day_selection == "Montag bis Freitag (Mo-Fr)"
      ):
        day_sched = [
            x for x in st.session_state.schedule if x["Wochentag"] == day_name
        ]
        if day_sched:
          latest_end = "00:00"
          for slot in day_sched:
            try:
              end_t_str = slot["Uhrzeit"].split(" - ")[1]
              if end_t_str > latest_end:
                latest_end = end_t_str
            except:
              pass
          if latest_end != "00:00":
            try:
              h, m = map(int, latest_end.split(":"))
              day_specific_time = time(h, m)
            except:
              pass

      current_dt = datetime.combine(datetime.today(), day_specific_time)
      for i in range(count):
        start_str = current_dt.strftime("%H:%M")
        current_dt += timedelta(minutes=total_block)
        end_str = current_dt.strftime("%H:%M")

        added_entries.append({
            "Wochentag": day_name,
            "Uhrzeit": f"{start_str} - {end_str}",
            "Sendung": show,
            "Staffel": season,
            "Ep.": current_ep if not is_filler else 1,
            "Netto": net_time,
            "Werbung": ad_time,
            "Gesamt": total_block,
            "Status": plan_status,
        })
        if not is_filler:
          current_ep += 1

    st.session_state.schedule.extend(added_entries)
    save_data(
        st.session_state.schedule, st.session_state.acknowledged_warnings
    )
    st.success("Erfolgreich eingeplant & gespeichert!")
    st.rerun()


# --- TAB 4: FORMAT-REFERENZ & BEARBEITUNG ---
with tab_db:
  st.subheader("📚 Verifizierte Formate & Standard-Laufzeiten")

  db_rows = [
      {
          "Format": k,
          "Genre": v["genre"],
          "Netto (Min.)": v["net"],
          "Werbung (Min.)": v["ad"],
          "Gesamt (Min.)": v["net"] + v["ad"],
      }
      for k, v in st.session_state.series_db.items()
  ]
  st.table(pd.DataFrame(db_rows))

  st.markdown("---")
  st.subheader("🛠️ Format bearbeiten oder löschen")

  selected_format_to_edit = st.selectbox(
      "Format auswählen", list(st.session_state.series_db.keys())
  )
  if selected_format_to_edit:
    fmt_data = st.session_state.series_db[selected_format_to_edit]
    with st.form("edit_format_form"):
      col_ed1, col_ed2 = st.columns(2)
      with col_ed1:
        edit_genre = st.text_input("Genre", value=fmt_data.get("genre", ""))
        edit_net = st.number_input(
            "Netto-Laufzeit (Min. fix)",
            min_value=1,
            max_value=300,
            value=int(fmt_data.get("net", 30)),
        )
      with col_ed2:
        edit_ad = st.number_input(
            "Standard-Werbezeit (Min.)",
            min_value=0,
            max_value=60,
            value=int(fmt_data.get("ad", 6)),
        )

      col_sub1, col_sub2 = st.columns(2)
      with col_sub1:
        update_clicked = st.form_submit_button("💾 Format aktualisieren")
      with col_sub2:
        delete_format_clicked = st.form_submit_button("🗑️ Format löschen")

      if update_clicked:
        st.session_state.series_db[selected_format_to_edit][
            "genre"
        ] = edit_genre
        st.session_state.series_db[selected_format_to_edit]["net"] = int(
            edit_net
        )
        st.session_state.series_db[selected_format_to_edit]["ad"] = int(edit_ad)
        save_formats(st.session_state.series_db)
        st.success(
            f"Format '{selected_format_to_edit}' erfolgreich aktualisiert!"
        )
        st.rerun()

      if delete_format_clicked:
        if len(st.session_state.series_db) > 1:
          del st.session_state.series_db[selected_format_to_edit]
          save_formats(st.session_state.series_db)
          st.success(f"Format '{selected_format_to_edit}' wurde gelöscht!")
          st.rerun()
        else:
          st.error("Die Datenbank muss mindestens ein Format enthalten.")

  st.markdown("---")
  st.subheader("➕ Neues Format / Sendung zur Datenbank hinzufügen")

  with st.form("new_format_form"):
    col_f1, col_f2 = st.columns(2)
    with col_f1:
      new_show_name = st.text_input("Name der Sendung / Serie")
      new_genre = st.text_input("Genre (z. B. Sitcom, Dokumentation)")
    with col_f2:
      new_net = st.number_input(
          "Netto-Laufzeit (Min. fix)", min_value=1, max_value=300, value=30
      )
      new_ad = st.number_input(
          "Standard-Werbezeit (Min.)", min_value=0, max_value=60, value=6
      )

    format_submitted = st.form_submit_button("Format in Datenbank speichern")
    if format_submitted:
      if new_show_name.strip():
        if new_show_name in st.session_state.series_db:
          st.warning(
              f"Das Format '{new_show_name}' existiert bereits in der Datenbank!"
          )
        else:
          st.session_state.series_db[new_show_name] = {
              "genre": new_genre if new_genre else "Allgemein",
              "seasons": {1: 20},
              "net": int(new_net),
              "ad": int(new_ad),
          }
          save_formats(st.session_state.series_db)
          st.success(
              f"Format '{new_show_name}' erfolgreich hinzugefügt und dauerhaft"
              " gespeichert!"
          )
          st.rerun()
      else:
        st.error("Bitte gib einen gültigen Namen für das Format ein.")
