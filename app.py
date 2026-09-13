from datetime import datetime, time, timedelta
import json
import os
import pandas as pd
import streamlit as st

# Dateipfade
SAVE_FILE = "sendeplan_v5.3.json"
FORMATS_FILE = "formats_v5.3.json"

# Seitenkonfiguration
st.set_page_config(
    page_title="Master Control v5.3 | Broadcast Direktion",
    page_icon="📡",
    layout="wide",
)

# --- MODERNES BROADCAST-CONTROL DESIGN ---
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    .block-container { padding-top: 2rem; }
    
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


# --- PERSISTENZ DER FORMATE ---
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


# --- PERSISTENZ DES SENDEPLANS ---
def load_data():
  target_file = (
      SAVE_FILE
      if os.path.exists(SAVE_FILE)
      else ("sendeplan_v5.2.json" if os.path.exists("sendeplan_v5.2.json") else None)
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

  if not schedule:
    # Saubere Standard-Struktur mit Tag, Primetime und Nacht
    schedule = [
        # Tagesprogramm (06:00 - 20:00)
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
        # Primetime (20:00 - 02:00)
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
            "Wochentag": "Montag",
            "Uhrzeit": "00:00 - 00:30",
            "Sendung": "Tagessthemen",
            "Staffel": 2026,
            "Ep.": 1,
            "Netto": 30,
            "Werbung": 0,
            "Gesamt": 30,
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
        # Nachtprogramm (02:00 - 06:00)
        {
            "Wochentag": "Montag",
            "Uhrzeit": "02:00 - 02:30",
            "Sendung": "Tagessthemen",
            "Staffel": 2026,
            "Ep.": 2,
            "Netto": 30,
            "Werbung": 0,
            "Gesamt": 30,
            "Status": "Wiederholung",
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

# --- ZEIT-EINTEILUNG & FILTER ---
def get_slot_category(time_str):
  try:
    start_str = time_str.split(" - ")[0]
    h = int(start_str.split(":")[0])
    if 6 <= h < 20:
      return "day"
    elif h >= 20 or h < 2:
      return "prime"
    elif 2 <= h < 6:
      return "night"
  except Exception:
    pass
  return "prime"


# --- HEADER & METRIKEN ---
st.title("📡 Master Control v5.3: Programmschema-Direktion")
st.markdown(
    "**Broadcast Matrix Core** — Direkte, getrennte Pflege für"
    " **Tagesprogramm (06–20h)**, **Primetime (20–02h je Wochentag)** und"
    " **Nachtprogramm (ab 02h)**."
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
            <div class="metric-label">Schema-Architektur</div>
            <div class="metric-value">3-Sektoren Matrix</div>
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

# --- HAUPTREITER ---
tab_prime, tab_day, tab_night, tab_builder, tab_db = st.tabs([
    "⭐ Primetime (Mo - So Abend)",
    "☀️ Tagesprogramm (06:00 - 20:00)",
    "🌙 Nachtprogramm (ab 02:00)",
    "⚡ Schnell-Planer (Serien-Blöcke)",
    "📚 Format-Referenz & DB",
])

all_shows_list = list(st.session_state.series_db.keys()) + list(
    FILLER_DATABASE.keys()
)


# --- GENERISCHER MATRIX-EDITOR ---
def render_day_matrix_editor(day_name, category, key_prefix):
  current_slots = [
      x
      for x in st.session_state.schedule
      if x["Wochentag"] == day_name
      and get_slot_category(x.get("Uhrzeit", "")) == category
  ]

  def get_start_mins(item):
    try:
      s_str = item["Uhrzeit"].split(" - ")[0]
      h, m = map(int, s_str.split(":"))
      if category == "prime" and h < 6:
        h += 24
      return h * 60 + m
    except:
      return 0

  current_slots.sort(key=get_start_mins)

  df_view = pd.DataFrame(current_slots)
  if df_view.empty:
    df_view = pd.DataFrame(
        columns=[
            "Uhrzeit",
            "Sendung",
            "Staffel",
            "Ep.",
            "Netto",
            "Werbung",
            "Gesamt",
            "Status",
        ]
    )
  else:
    cols = [
        "Uhrzeit",
        "Sendung",
        "Staffel",
        "Ep.",
        "Netto",
        "Werbung",
        "Gesamt",
        "Status",
    ]
    df_view = df_view[[c for c in cols if c in df_view.columns]]

  edited_df = st.data_editor(
      df_view,
      num_rows="dynamic",
      use_container_width=True,
      key=f"{key_prefix}_{day_name}",
      column_config={
          "Uhrzeit": st.column_config.TextColumn(
              "Uhrzeit (z. B. 20:15 - 21:15)", required=True
          ),
          "Sendung": st.column_config.SelectboxColumn(
              "Sendung / Format", options=all_shows_list, required=True
          ),
          "Status": st.column_config.SelectboxColumn(
              "Status", options=STATUS_OPTIONS, required=True
          ),
          "Staffel": st.column_config.NumberColumn("Staffel", min_value=1),
          "Ep.": st.column_config.NumberColumn("Ep.", min_value=1),
          "Netto": st.column_config.NumberColumn("Netto (Min.)", min_value=1),
          "Werbung": st.column_config.NumberColumn(
              "Werbung (Min.)", min_value=0
          ),
          "Gesamt": st.column_config.NumberColumn(
              "Gesamt (Min.)", min_value=1
          ),
      },
  )

  col_s1, col_s2 = st.columns([2, 1])
  with col_s1:
    if st.button(
        f"💾 Änderungen für {day_name} speichern",
        key=f"btn_save_{key_prefix}_{day_name}",
        type="primary",
    ):
      remaining_slots = [
          x
          for x in st.session_state.schedule
          if not (
              x["Wochentag"] == day_name
              and get_slot_category(x.get("Uhrzeit", "")) == category
          )
      ]

      new_slots = edited_df.to_dict(orient="records")
      for row in new_slots:
        row["Wochentag"] = day_name
        show_name = row.get("Sendung")
        fmt = st.session_state.series_db.get(
            show_name
        ) or FILLER_DATABASE.get(show_name)

        if fmt:
          if not row.get("Netto") or row.get("Netto") == 0:
            row["Netto"] = int(fmt["net"])
          if "Werbung" not in row or row.get("Werbung") is None:
            row["Werbung"] = int(fmt["ad"])

        net = int(row.get("Netto", 0) or 0)
        ad = int(row.get("Werbung", 0) or 0)
        row["Gesamt"] = net + ad
        row["Staffel"] = int(row.get("Staffel", 1) or 1)
        row["Ep."] = int(row.get("Ep.", 1) or 1)

      st.session_state.schedule = remaining_slots + new_slots
      save_data(
          st.session_state.schedule, st.session_state.acknowledged_warnings
      )
      st.success(
          f"Matrix für {day_name} erfolgreich aktualisiert & gespeichert!"
      )
      st.rerun()


# --- REITER 1: PRIMETIME (MONTAG BIS SONNTAG) ---
with tab_prime:
  st.subheader("⭐ Primetime-Matrix (20:00 Uhr bis 02:00 Uhr)")
  st.markdown(
      "Wähle den Wochentag, um den Primetime-Ablauf direkt in der Tabelle zu"
      " verändern:"
  )

  prime_day_tabs = st.tabs(WEEKDAYS)
  for idx, day in enumerate(WEEKDAYS):
    with prime_day_tabs[idx]:
      st.markdown(f"#### Primetime am **{day}**")
      render_day_matrix_editor(day, "prime", "prime_matrix")


# --- REITER 2: TAGESPROGRAMM (06:00 BIS 20:00 UHR) ---
with tab_day:
  st.subheader("☀️ Tagesprogramm-Matrix (06:00 Uhr bis 20:00 Uhr)")
  st.markdown(
      "Plane und verwalte die Vormittags-, Mittags- und Vorabend-Schienen für"
      " jeden Tag:"
  )

  day_day_tabs = st.tabs(WEEKDAYS)
  for idx, day in enumerate(WEEKDAYS):
    with day_day_tabs[idx]:
      st.markdown(f"#### Tagesprogramm am **{day}**")
      render_day_matrix_editor(day, "day", "day_matrix")


# --- REITER 3: NACHTPROGRAMM (AB 02:00 UHR BIS 06:00 UHR) ---
with tab_night:
  st.subheader("🌙 Nachtprogramm-Matrix (ab 02:00 Uhr)")
  st.markdown("Late-Night, Dokus und Wiederholungen ab 02:00 Uhr morgens:")

  night_day_tabs = st.tabs(WEEKDAYS)
  for idx, day in enumerate(WEEKDAYS):
    with night_day_tabs[idx]:
      st.markdown(f"#### Nachtprogramm am **{day}** (ab 02:00 Uhr)")
      render_day_matrix_editor(day, "night", "night_matrix")


# --- REITER 4: SCHNELL-PLANER ---
with tab_builder:
  st.subheader("⚡ Programmpunkt über Schnell-Planer einfügen")
  st.markdown(
      "Ideal, um Serienblöcke (z. B. 2 Folgen am Stück) oder Wochentagsschienen"
      " automatisiert einzutakten."
  )

  col_b1, col_b2 = st.columns(2)
  with col_b1:
    day_selection = st.selectbox(
        "Wochentag / Block", DAY_OPTIONS, key="builder_day"
    )
    show = st.selectbox(
        "Format / Sendung", all_shows_list, key="builder_show"
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
      episode = st.number_input(
          "Start-Episodennummer",
          min_value=1,
          max_value=10000,
          value=next_ep_suggestion,
          key="builder_ep_input",
      )
    else:
      season = 2026
      episode = 1
      st.info("💡 Filler Format.")

  with col_b2:
    start_t = st.time_input("Startzeit", value=time(20, 15), key="builder_time")
    count = st.selectbox(
        "Anzahl Folgen nacheinander", list(range(1, 6)), key="builder_count"
    )
    plan_status = st.selectbox("Status", STATUS_OPTIONS, key="builder_status")

    net_time = format_info["net"]
    ad_time = format_info["ad"]
    total_block = net_time + ad_time
    st.markdown(
        f"💡 **Format-Vorgabe:** {net_time}m Netto + {ad_time}m Werbung ="
        f" **{total_block}m gesamt**."
    )

  if st.button(
      "Sendung in den Plan einfügen", key="builder_submit_btn", type="primary"
  ):
    added_entries = []
    target_days = (
        ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
        if day_selection == "Montag bis Freitag (Mo-Fr)"
        else (
            WEEKDAYS
            if day_selection == "Montag bis Sonntag (Ganze Woche)"
            else [day_selection]
        )
    )
    current_ep = int(episode)

    for day_name in target_days:
      current_dt = datetime.combine(datetime.today(), start_t)
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
    st.success("Erfolgreich in den Sendeplan übernommen!")
    st.rerun()


# --- REITER 5: FORMAT-DATENBANK ---
with tab_db:
  st.subheader("📚 Format-Referenz & Verwaltung")
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
  col_d1, col_d2 = st.columns(2)
  with col_d1:
    if st.button("🗑️ Gesamten Sendeplan leeren"):
      st.session_state.schedule = []
      st.session_state.acknowledged_warnings.clear()
      save_data([], set())
      st.rerun()
  with col_d2:
    csv_export = pd.DataFrame(st.session_state.schedule).to_csv(
        index=False
    ).encode("utf-8")
    st.download_button(
        "📥 Sendeplan als CSV herunterladen",
        csv_export,
        "sendeplan_v5.3.csv",
        "text/csv",
    )
