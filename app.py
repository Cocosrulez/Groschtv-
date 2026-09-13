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


# --- SLOT-RASTER HILFSFUNKTION ---
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
        f"Gesamtlänge beträgt {total_mins} Min. ({abs(diff)} Min. kürzer als"
        f" ein regulärer {target_slot}-Minuten-Slot).",
    )
  else:
    return (
        False,
        f"Gesamtlänge beträgt {total_mins} Min. ({diff} Min. Überlänge für"
        f" einen regulären {target_slot}-Minuten-Slot).",
    )


# --- DATEN-PERSISTENZ ---
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
    schedule = [
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
            "Uhrzeit": "02:00 - 02:30",
            "Sendung": "Tagessthemen",
            "Staffel": 2026,
            "Ep.": 1,
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


# --- ZEIT-EINTEILUNG & KATEGORIE ---
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
    "**Broadcast Matrix Core** — Voll synchronisierte Bearbeitung mit"
    " Schnell-Löschung, Feintuner & automatischer Episoden-Lückenerkennung."
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
            <div class="metric-label">Episoden-Sync</div>
            <div class="metric-value">Aktiv (Lücken-Check)</div>
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
tab_prime, tab_day, tab_night, tab_week, tab_builder, tab_db = st.tabs([
    "⭐ Primetime (20:00 - 02:00)",
    "☀️ Tagesprogramm (06:00 - 20:00)",
    "🌙 Nachtprogramm (ab 02:00)",
    "📅 Gesamt-Wochenübersicht & Live-Prüfung",
    "⚡ Schnell-Planer (Serien-Blöcke)",
    "📚 Format-Referenz & DB",
])

all_shows_list = list(st.session_state.series_db.keys()) + list(
    FILLER_DATABASE.keys()
)


# --- WIEDERVERWENDBARER MATRIX-EDITOR MIT LÖSCH-MENÜ & FEINTUNER ---
def render_day_matrix_editor(day_name, category, key_prefix):
  # Alle Sendeplätze für den gewählten Tag und die Kategorie filtern
  current_slots = [
      x
      for x in st.session_state.schedule
      if x.get("Wochentag") == day_name
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

  if current_slots:
    df_view = pd.DataFrame(current_slots)
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
  else:
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

  # Interaktive Matrix-Tabelle
  edited_df = st.data_editor(
      df_view,
      num_rows="dynamic",
      use_container_width=True,
      key=f"{key_prefix}_{day_name}",
      column_config={
          "Uhrzeit": st.column_config.TextColumn(
              "Uhrzeit (z. B. 20:15 - 20:45)", required=True
          ),
          "Sendung": st.column_config.SelectboxColumn(
              "Sendung / Format", options=all_shows_list, required=True
          ),
          "Status": st.column_config.SelectboxColumn(
              "Status", options=STATUS_OPTIONS, required=True
          ),
          "Staffel": st.column_config.NumberColumn(
              "Staffel", min_value=1, step=1
          ),
          "Ep.": st.column_config.NumberColumn("Ep.", min_value=1, step=1),
          "Netto": st.column_config.NumberColumn(
              "Netto (Min.)", min_value=0, step=1
          ),
          "Werbung": st.column_config.NumberColumn(
              "Werbung (Min.)", min_value=0, step=1
          ),
          "Gesamt": st.column_config.NumberColumn(
              "Gesamt (Min.)", min_value=0, step=1
          ),
      },
  )

  if st.button(
      f"💾 Änderungen für {day_name} speichern",
      key=f"btn_save_{key_prefix}_{day_name}",
      type="primary",
  ):
    remaining_slots = [
        x
        for x in st.session_state.schedule
        if not (
            x.get("Wochentag") == day_name
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
      row["Status"] = row.get("Status", "Erstausstrahlung")

    st.session_state.schedule = remaining_slots + new_slots
    save_data(st.session_state.schedule, st.session_state.acknowledged_warnings)
    st.success(f"Matrix für {day_name} erfolgreich gespeichert!")
    st.rerun()

  # --- DROP-DOWN / EXPANDER 1: SENDUNGEN ENTFERNEN (LÖSCHEN) ---
  with st.expander(
      f"🗑️ Sendeplätze & Episoden verwalten / löschen ({day_name})",
      expanded=False,
  ):
    if not current_slots:
      st.info(f"Keine Sendeplätze für {day_name} vorhanden.")
    else:
      st.markdown(
          "Klicke auf **❌ Löschen**, um einen Sendeplatz sofort zu entfernen."
          " Die entsprechende Episode wird sofort wieder im Schnell-Planer"
          " freigegeben."
      )
      for idx, row in enumerate(current_slots):
        col_m1, col_m2 = st.columns([5, 1])
        with col_m1:
          st.write(
              f"• **{row['Uhrzeit']}** – **{row['Sendung']}** (St."
              f" {row.get('Staffel', 1)}, Ep. {row.get('Ep.', 1)}) |"
              f" *{row.get('Status', 'Erstausstrahlung')}* [{row.get('Gesamt', 0)}"
              " Min.]"
          )
        with col_m2:
          if st.button("❌ Löschen", key=f"del_{key_prefix}_{day_name}_{idx}"):
            if row in st.session_state.schedule:
              st.session_state.schedule.remove(row)
            else:
              for g_i, s in enumerate(st.session_state.schedule):
                if (
                    s.get("Wochentag") == row.get("Wochentag")
                    and s.get("Uhrzeit") == row.get("Uhrzeit")
                    and s.get("Sendung") == row.get("Sendung")
                    and s.get("Ep.") == row.get("Ep.")
                ):
                  st.session_state.schedule.pop(g_i)
                  break
            save_data(
                st.session_state.schedule,
                st.session_state.acknowledged_warnings,
            )
            st.success(
                f"'{row['Sendung']}' (Ep. {row.get('Ep.', 1)}) entfernt &"
                " freigegeben!"
            )
            st.rerun()

  # --- DROP-DOWN / EXPANDER 2: SENDEPLATZ-FEINTUNER ---
  with st.expander(
      f"🛠️ Sendeplatz-Feintuner (Details anpassen) ({day_name})",
      expanded=False,
  ):
    if not current_slots:
      st.info(f"Keine Sendeplätze für {day_name} vorhanden.")
    else:
      options_labels = [
          f"#{i+1}: {item['Uhrzeit']} – {item['Sendung']} (St."
          f" {item.get('Staffel', 1)}, Ep. {item.get('Ep.', 1)})"
          for i, item in enumerate(current_slots)
      ]
      selected_label = st.selectbox(
          "Programmpunkt zum Feintuning auswählen",
          options_labels,
          key=f"ft_select_{key_prefix}_{day_name}",
      )
      selected_sub_idx = options_labels.index(selected_label)
      current_item = current_slots[selected_sub_idx]

      global_idx = None
      if current_item in st.session_state.schedule:
        global_idx = st.session_state.schedule.index(current_item)
      else:
        for g_i, s in enumerate(st.session_state.schedule):
          if (
              s.get("Wochentag") == current_item.get("Wochentag")
              and s.get("Uhrzeit") == current_item.get("Uhrzeit")
              and s.get("Sendung") == current_item.get("Sendung")
              and s.get("Ep.") == current_item.get("Ep.")
          ):
            global_idx = g_i
            break

      col_ft1, col_ft2 = st.columns(2)
      with col_ft1:
        curr_show = current_item.get("Sendung", all_shows_list[0])
        show_idx = (
            all_shows_list.index(curr_show)
            if curr_show in all_shows_list
            else 0
        )
        new_show = st.selectbox(
            "Sendung / Format",
            all_shows_list,
            index=show_idx,
            key=f"ft_show_{key_prefix}_{day_name}",
        )

        col_sub_st, col_sub_ep = st.columns(2)
        with col_sub_st:
          new_season = st.number_input(
              "Staffel",
              min_value=1,
              max_value=3000,
              value=int(current_item.get("Staffel", 1)),
              step=1,
              key=f"ft_seas_{key_prefix}_{day_name}",
          )
        with col_sub_ep:
          new_ep = st.number_input(
              "Episode",
              min_value=1,
              max_value=10000,
              value=int(current_item.get("Ep.", 1)),
              step=1,
              key=f"ft_ep_{key_prefix}_{day_name}",
          )

      with col_ft2:
        try:
          start_str_parts = current_item["Uhrzeit"].split(" - ")[0].split(":")
          curr_h = int(start_str_parts[0])
          curr_m = int(start_str_parts[1])
        except Exception:
          curr_h, curr_m = 20, 15

        new_time_val = st.time_input(
            "Startzeit",
            value=time(curr_h, curr_m),
            key=f"ft_time_{key_prefix}_{day_name}",
        )

        fmt_spec = st.session_state.series_db.get(
            new_show
        ) or FILLER_DATABASE.get(new_show)
        default_ad = (
            fmt_spec["ad"]
            if fmt_spec
            else int(current_item.get("Werbung", 6))
        )
        new_ad = st.number_input(
            "Werbung (Min.)",
            min_value=0,
            max_value=60,
            value=int(current_item.get("Werbung", default_ad)),
            step=1,
            key=f"ft_ad_{key_prefix}_{day_name}",
        )

        curr_status = current_item.get("Status", "Erstausstrahlung")
        status_idx = (
            STATUS_OPTIONS.index(curr_status)
            if curr_status in STATUS_OPTIONS
            else 0
        )
        new_status = st.selectbox(
            "Status",
            STATUS_OPTIONS,
            index=status_idx,
            key=f"ft_stat_{key_prefix}_{day_name}",
        )

      fixed_net = (
          fmt_spec["net"]
          if fmt_spec
          else int(current_item.get("Netto", 30))
      )
      total_len = fixed_net + new_ad
      start_dt = datetime.combine(datetime.today(), new_time_val)
      end_dt = start_dt + timedelta(minutes=total_len)
      new_time_str = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"

      is_exact, slot_msg = get_slot_grid_info(total_len)
      if is_exact:
        st.info(
            f"ℹ️ **Slot:** {new_show} | Netto: {fixed_net}m + Werbung: {new_ad}m"
            f" = **{total_len} Min. ({new_time_str})** | {slot_msg}"
        )
      else:
        st.warning(
            f"⚠️ **Slot:** {new_show} | Netto: {fixed_net}m + Werbung: {new_ad}m"
            f" = **{total_len} Min. ({new_time_str})** | {slot_msg}"
        )

      if st.button(
          "💾 Sendeplatz aktualisieren & speichern",
          key=f"ft_save_btn_{key_prefix}_{day_name}",
          type="primary",
      ):
        if global_idx is not None and global_idx < len(
            st.session_state.schedule
        ):
          st.session_state.schedule[global_idx]["Sendung"] = new_show
          st.session_state.schedule[global_idx]["Staffel"] = int(new_season)
          st.session_state.schedule[global_idx]["Ep."] = int(new_ep)
          st.session_state.schedule[global_idx]["Uhrzeit"] = new_time_str
          st.session_state.schedule[global_idx]["Netto"] = int(fixed_net)
          st.session_state.schedule[global_idx]["Werbung"] = int(new_ad)
          st.session_state.schedule[global_idx]["Gesamt"] = int(total_len)
          st.session_state.schedule[global_idx]["Status"] = new_status
          save_data(
              st.session_state.schedule, st.session_state.acknowledged_warnings
          )
          st.success("Sendeplatz erfolgreich aktualisiert & gespeichert!")
          st.rerun()


# --- REITER 1: PRIMETIME (20:00 - 02:00) ---
with tab_prime:
  st.subheader("⭐ Primetime-Matrix (20:00 Uhr bis 02:00 Uhr)")
  st.markdown("Wähle den Wochentag zum Bearbeiten des Abendprogramms:")

  prime_day_tabs = st.tabs(WEEKDAYS)
  for idx, day in enumerate(WEEKDAYS):
    with prime_day_tabs[idx]:
      st.markdown(f"#### Primetime am **{day}**")
      render_day_matrix_editor(day, "prime", "prime_matrix")


# --- REITER 2: TAGESPROGRAMM (06:00 - 20:00) ---
with tab_day:
  st.subheader("☀️ Tagesprogramm-Matrix (06:00 Uhr bis 20:00 Uhr)")
  st.markdown("Vormittags-, Mittags- und Vorabend-Schienen je Wochentag:")

  day_day_tabs = st.tabs(WEEKDAYS)
  for idx, day in enumerate(WEEKDAYS):
    with day_day_tabs[idx]:
      st.markdown(f"#### Tagesprogramm am **{day}**")
      render_day_matrix_editor(day, "day", "day_matrix")


# --- REITER 3: NACHTPROGRAMM (AB 02:00 BIS 06:00) ---
with tab_night:
  st.subheader("🌙 Nachtprogramm-Matrix (ab 02:00 Uhr bis 06:00 Uhr)")
  st.markdown("Late-Night, Dokus und Wiederholungen ab 02:00 Uhr:")

  night_day_tabs = st.tabs(WEEKDAYS)
  for idx, day in enumerate(WEEKDAYS):
    with night_day_tabs[idx]:
      st.markdown(f"#### Nachtprogramm am **{day}** (ab 02:00 Uhr)")
      render_day_matrix_editor(day, "night", "night_matrix")


# --- REITER 4: GESAMT-WOCHENÜBERSICHT & LIVE-PRÜFUNG ---
with tab_week:
  st.subheader("📅 Gesamter Wochen-Sendeplan & Kollisionsprüfung")

  if st.session_state.schedule:
    df_all = pd.DataFrame(st.session_state.schedule)
    day_sorting = {d: i for i, d in enumerate(WEEKDAYS)}
    if "Wochentag" in df_all.columns:
      df_all["_sort"] = df_all["Wochentag"].map(day_sorting).fillna(9)
      df_all = df_all.sort_values(by=["_sort", "Uhrzeit"]).drop(
          columns=["_sort"]
      )

    disp_cols = [
        "Wochentag",
        "Uhrzeit",
        "Sendung",
        "Staffel",
        "Ep.",
        "Netto",
        "Werbung",
        "Gesamt",
        "Status",
    ]
    st.dataframe(
        df_all[[c for c in disp_cols if c in df_all.columns]],
        use_container_width=True,
        hide_index=True,
    )

    # Validierungs-Logik
    errors_found = []
    for idx, row in enumerate(st.session_state.schedule):
      sh = row.get("Sendung")
      fmt = st.session_state.series_db.get(sh) or FILLER_DATABASE.get(sh)
      if not fmt:
        errors_found.append(
            f"Sendeplatz #{idx+1} ({row.get('Wochentag')}): Unbekanntes Format"
            f" '{sh}'."
        )

    if errors_found:
      for err in errors_found:
        st.error(f"❌ {err}")
    else:
      st.success("✅ Keine Kollisionen oder Format-Fehler im Gesamtsendeplan.")

    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
      csv_export = pd.DataFrame(st.session_state.schedule).to_csv(
          index=False
      ).encode("utf-8")
      st.download_button(
          "📥 Sendeplan als CSV herunterladen",
          csv_export,
          "sendeplan_v5.3.csv",
          "text/csv",
      )
    with col_exp2:
      if st.button("🗑️ Gesamten Sendeplan leeren"):
        st.session_state.schedule = []
        st.session_state.acknowledged_warnings.clear()
        save_data([], set())
        st.rerun()
  else:
    st.info("Der Sendeplan ist aktuell leer.")


# --- REITER 5: SCHNELL-PLANER (EPISODEN-SYNC) ---
with tab_builder:
  st.subheader("⚡ Programmpunkt über Schnell-Planer einfügen")
  st.markdown(
      "Plane Serienfolgen oder Wochentagsschienen fehlerfrei und automatisiert"
      " ein."
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

      # --- AUTOMATISCHER EPISODEN-SYNC & LÜCKENERKENNUNG ---
      existing_eps = sorted(
          list(
              set(
                  x["Ep."]
                  for x in st.session_state.schedule
                  if x["Sendung"] == show and x["Staffel"] == season
              )
          )
      )
      max_ep = max(existing_eps) if existing_eps else 0
      all_expected = set(range(1, max_ep + 1))
      missing_eps = sorted(list(all_expected - set(existing_eps)))
      next_consecutive_ep = max_ep + 1

      # Zustand synchron halten
      sync_sig = (
          show,
          season,
          len(st.session_state.schedule),
          tuple(existing_eps),
      )
      if (
          "builder_sync_sig" not in st.session_state
          or st.session_state.builder_sync_sig != sync_sig
      ):
        st.session_state.builder_sync_sig = sync_sig
        # Bei erkannter Lücke schlagen wir sofort die fehlende Folge vor, sonst die nächste am Ende
        st.session_state.builder_ep_input = (
            missing_eps[0] if missing_eps else next_consecutive_ep
        )

      st.markdown("##### 🔢 Episoden-Status & Synchronisation")
      if existing_eps:
        st.info(f"📌 **Bereits im Sendeplan:** Episoden `{existing_eps}`")
      else:
        st.info(
            f"📌 **Noch keine Episoden** für '{show}' (Staffel {season}) im"
            " Plan."
        )

      if missing_eps:
        st.warning(
            f"⚠️ **Freie Lücke erkannt:** Episode(n) **`{missing_eps}`** fehlen"
            " im Ablauf (z. B. gelöscht)!"
        )

      col_q1, col_q2 = st.columns(2)
      with col_q1:
        if missing_eps:
          if st.button(
              f"↩️ Lücke füllen: Folge {missing_eps[0]} wählen",
              key=f"btn_gap_{show}_{season}",
          ):
            st.session_state.builder_ep_input = missing_eps[0]
            st.rerun()
        else:
          st.caption("Keine Lücken im Ablauf.")
      with col_q2:
        if st.button(
            f"➡️ Fortsetzen: Folge {next_consecutive_ep} wählen",
            key=f"btn_next_{show}_{season}",
        ):
          st.session_state.builder_ep_input = next_consecutive_ep
          st.rerun()

      episode = st.number_input(
          "Start-Episodennummer",
          min_value=1,
          max_value=10000,
          value=st.session_state.get(
              "builder_ep_input",
              missing_eps[0] if missing_eps else next_consecutive_ep,
          ),
          step=1,
          key="builder_ep_input",
      )
    else:
      season = 2026
      episode = 1
      st.info("💡 Smart Filler Format (keine Episodennummer nötig).")

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


# --- REITER 6: FORMAT-DATENBANK ---
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
  st.subheader("➕ Neues Format zur Datenbank hinzufügen")
  with st.form("new_format_form"):
    col_f1, col_f2 = st.columns(2)
    with col_f1:
      new_show_name = st.text_input("Name der Sendung / Serie")
      new_genre = st.text_input("Genre")
    with col_f2:
      new_net = st.number_input("Netto-Laufzeit (Min.)", value=30)
      new_ad = st.number_input("Werbezeit (Min.)", value=6)

    if st.form_submit_button("Format speichern"):
      if new_show_name.strip():
        st.session_state.series_db[new_show_name] = {
            "genre": new_genre or "Allgemein",
            "seasons": {1: 20},
            "net": int(new_net),
            "ad": int(new_ad),
        }
        save_formats(st.session_state.series_db)
        st.success(f"Format '{new_show_name}' gespeichert!")
        st.rerun()
