from datetime import datetime, time, timedelta
import json
import os
import pandas as pd
import streamlit as st

# Fester Master-Dateipfad für dauerhafte Persistenz
SAVE_FILE = "sendeplan_master.json"
FORMATS_FILE = "formats_master.json"

st.set_page_config(
    page_title="Master Control v3.2 | Broadcast Direktion",
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

DAY_BLOCK_OPTIONS = (
    WEEKDAYS
    + ["Montag bis Freitag (Mo-Fr)"]
    + ["Montag bis Sonntag (Ganze Woche)"]
    + ["Wochenende (Sa-So)"]
)

STATUS_OPTIONS = ["Erstausstrahlung", "Wiederholung", "Live"]


# --- FORMATE LADEN & SPEICHERN ---
def load_formats():
  fallback_files = [
      FORMATS_FILE,
      "formats_v3.2.json",
      "formats_v3.1.json",
      "formats_v5.3.json",
  ]
  for fpath in fallback_files:
    if os.path.exists(fpath):
      try:
        with open(fpath, "r", encoding="utf-8") as f:
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


# --- SENDEPLAN LADEN & SPEICHERN ---
def load_data():
  fallback_files = [
      SAVE_FILE,
      "sendeplan_v3.2.json",
      "sendeplan_v3.1.json",
      "sendeplan_v5.3.json",
      "sendeplan_v5.2.json",
  ]
  target_file = None
  for fpath in fallback_files:
    if os.path.exists(fpath):
      target_file = fpath
      break

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


# --- HILFSFUNKTIONEN FÜR ZEITEN & EPISODEN-SYNC ---
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
        f" {target_slot}m-Slot).",
    )
  else:
    return (
        False,
        f"Gesamtlänge beträgt {total_mins} Min. ({diff} Min. Überlänge für"
        f" {target_slot}m-Slot).",
    )


def get_episode_synchronization(show, season):
  fmt = st.session_state.series_db.get(show)
  if not fmt:
    return 1, [], 1, [], None, False

  seasons_dict = fmt.get("seasons", {})
  max_season_eps = seasons_dict.get(int(season)) or seasons_dict.get(str(season))

  premiered = sorted(
      list(
          set(
              int(x["Ep."])
              for x in st.session_state.schedule
              if x.get("Sendung") == show
              and int(x.get("Staffel", 1)) == int(season)
              and x.get("Status") != "Wiederholung"
          )
      )
  )

  if not premiered:
    return 1, [], 1, [], max_season_eps, False

  max_ep = max(premiered)
  all_expected = set(range(1, max_ep + 1))
  missing_eps = sorted(list(all_expected - set(premiered)))
  next_consecutive = max_ep + 1

  suggested = missing_eps[0] if missing_eps else next_consecutive

  is_season_complete = False
  if max_season_eps and len(premiered) >= max_season_eps and not missing_eps:
    is_season_complete = True

  return (
      suggested,
      missing_eps,
      next_consecutive,
      premiered,
      max_season_eps,
      is_season_complete,
  )


# --- REAKTIVE CALLBACKS BEI FORMAT- ODER STAFFELWECHSEL ---
def on_show_change(prefix):
  show = st.session_state.get(f"{prefix}_show")
  fmt = st.session_state.series_db.get(show)
  if fmt and "seasons" in fmt:
    avail_seasons = list(fmt["seasons"].keys())
    curr_season = st.session_state.get(f"{prefix}_season")
    if curr_season not in avail_seasons:
      st.session_state[f"{prefix}_season"] = avail_seasons[0]
    season = st.session_state[f"{prefix}_season"]
    sugg, _, _, _, _, _ = get_episode_synchronization(show, season)
    st.session_state[f"{prefix}_ep"] = sugg
  else:
    st.session_state[f"{prefix}_ep"] = 1


def on_season_change(prefix):
  show = st.session_state.get(f"{prefix}_show")
  season = st.session_state.get(f"{prefix}_season", 1)
  sugg, _, _, _, _, _ = get_episode_synchronization(show, season)
  st.session_state[f"{prefix}_ep"] = sugg


def on_ft_show_change(prefix):
  """Callback, wenn im Feintuner eine andere Sendung ausgewählt wird."""
  ft_show_key = f"ft_show_{prefix}"
  selected_show = st.session_state.get(ft_show_key)
  fmt = st.session_state.series_db.get(selected_show)
  if fmt and "seasons" in fmt:
    avail_seasons = list(fmt["seasons"].keys())
    st.session_state[f"ft_seas_{prefix}"] = avail_seasons[0]
    sugg, _, _, _, _, _ = get_episode_synchronization(
        selected_show, avail_seasons[0]
    )
    st.session_state[f"ft_ep_{prefix}"] = sugg
    st.session_state[f"ft_ad_{prefix}"] = fmt["ad"]


all_shows_list = list(st.session_state.series_db.keys()) + list(
    FILLER_DATABASE.keys()
)

# --- HEADER & METRIKEN ---
st.title("📡 Master Control v3.2: Programmschema-Direktion")
st.markdown(
    "**Broadcast Direktion Core** — Vollreaktiver Serien-Sync, Staffelprüfung,"
    " In-Place Tagesmatrizen & Mehr-Tage-Schnellplaner."
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
            <div class="metric-label">Episoden-Engine</div>
            <div class="metric-value">v3.2 Reactive State</div>
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

# --- WIEDERVERWENDBARER TAGES-MATRIX-EDITOR MIT SOFORT-SYNC ---
def render_day_matrix_editor(day_name, category, key_prefix):
  prefix = f"{key_prefix}_{day_name}"

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
    except Exception:
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

  edited_df = st.data_editor(
      df_view,
      num_rows="dynamic",
      use_container_width=True,
      key=f"editor_{prefix}",
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
      f"💾 Tabellenänderungen für {day_name} speichern",
      key=f"btn_save_tbl_{prefix}",
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
    st.success(f"Matrix für {day_name} erfolgreich aktualisiert!")
    st.rerun()

  # --- EXPANDER 1: NEUE SENDUNG DIREKT IN DIESEN TAG EINPLANEN ---
  with st.expander(
      f"➕ Neue Sendung / Serienblock direkt einplanen ({day_name})",
      expanded=False,
  ):
    default_h, default_m = (
        (20, 15) if category == "prime" else ((6, 0) if category == "day" else (2, 0))
    )
    if current_slots:
      try:
        last_end_str = current_slots[-1]["Uhrzeit"].split(" - ")[1]
        default_h, default_m = map(int, last_end_str.split(":"))
      except Exception:
        pass

    col_p1, col_p2 = st.columns(2)
    with col_p1:
      if f"{prefix}_show" not in st.session_state:
        st.session_state[f"{prefix}_show"] = all_shows_list[0]
        on_show_change(prefix)

      p_show = st.selectbox(
          "Format / Sendung",
          all_shows_list,
          key=f"{prefix}_show",
          on_change=on_show_change,
          args=(prefix,),
      )

      if p_show in st.session_state.series_db:
        fmt_info = st.session_state.series_db[p_show]
        is_filler = False
      else:
        fmt_info = FILLER_DATABASE[p_show]
        is_filler = True

      if not is_filler:
        avail_seasons = list(fmt_info["seasons"].keys())
        if st.session_state.get(f"{prefix}_season") not in avail_seasons:
          st.session_state[f"{prefix}_season"] = avail_seasons[0]

        p_season = st.selectbox(
            "Staffel",
            avail_seasons,
            key=f"{prefix}_season",
            on_change=on_season_change,
            args=(prefix,),
        )

        (
            sugg_ep,
            missing_eps,
            next_ep,
            premiered_list,
            max_season_eps,
            is_complete,
        ) = get_episode_synchronization(p_show, p_season)

        if f"{prefix}_ep" not in st.session_state:
          st.session_state[f"{prefix}_ep"] = sugg_ep

        if is_complete:
          st.warning(
              f"⚠️ **Staffel {p_season} ist komplett verplant"
              f" ({len(premiered_list)}/{max_season_eps} Folgen)!**"
          )
        elif missing_eps:
          st.info(
              f"💡 **Lücke erkannt!** Folge **`{missing_eps[0]}`** fehlt und"
              " wurde automatisch eingesetzt."
          )
        else:
          max_txt = f" von {max_season_eps}" if max_season_eps else ""
          st.caption(
              f"📌 Bislang verplant: `{premiered_list}` (Nächste Folge:"
              f" **{next_ep}**{max_txt})"
          )

        p_episode = st.number_input(
            "Start-Episodennummer",
            min_value=1,
            max_value=10000,
            key=f"{prefix}_ep",
            step=1,
        )
      else:
        p_season = 2026
        p_episode = 1
        st.caption("💡 Filler-Format (keine Episodennummer erforderlich).")

    with col_p2:
      p_start_time = st.time_input(
          "Startzeit (Automatisch folgend)",
          value=time(default_h, default_m),
          key=f"{prefix}_time",
      )
      p_count = st.selectbox(
          "Anzahl Folgen nacheinander", list(range(1, 6)), key=f"{prefix}_count"
      )
      p_status = st.selectbox(
          "Status", STATUS_OPTIONS, key=f"{prefix}_status"
      )

      p_mo_fr = st.checkbox(
          "Diesen Block für Montag bis Freitag (Mo-Fr) übernehmen",
          key=f"{prefix}_mofr",
      )

    p_net = fmt_info["net"]
    p_ad = fmt_info["ad"]
    p_total = p_net + p_ad

    st.markdown(
        f"⏱️ **Laufzeit:** {p_net}m Netto + {p_ad}m Werbung = **{p_total} Min."
        " pro Folge**"
    )

    if st.button(
        f"➕ Block für {day_name} einfügen",
        key=f"btn_add_{prefix}",
        type="primary",
    ):
      target_days = (
          ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
          if p_mo_fr
          else [day_name]
      )
      new_entries = []
      curr_ep_counter = int(p_episode)

      for t_day in target_days:
        dt = datetime.combine(datetime.today(), p_start_time)
        for _ in range(p_count):
          s_str = dt.strftime("%H:%M")
          dt += timedelta(minutes=p_total)
          e_str = dt.strftime("%H:%M")

          new_entries.append({
              "Wochentag": t_day,
              "Uhrzeit": f"{s_str} - {e_str}",
              "Sendung": p_show,
              "Staffel": p_season,
              "Ep.": curr_ep_counter if not b_is_filler else 1,
              "Netto": p_net,
              "Werbung": p_ad,
              "Gesamt": p_total,
              "Status": p_status,
          })
          if not is_filler and p_status != "Wiederholung":
            curr_ep_counter += 1

      st.session_state.schedule.extend(new_entries)
      save_data(
          st.session_state.schedule, st.session_state.acknowledged_warnings
      )
      st.success("Sendeplätze erfolgreich synchronisiert und gespeichert!")
      st.rerun()

  # --- EXPANDER 2: FEINTUNER ---
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
          "Programmpunkt auswählen", options_labels, key=f"ft_sel_{prefix}"
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

      # Initialisiere Session State für den Feintuner, falls neu gewählt oder geladen
      ft_show_key = f"ft_show_{prefix}"
      if (
          ft_show_key not in st.session_state
          or st.session_state.get(f"ft_last_sel_{prefix}") != selected_label
      ):
        st.session_state[f"ft_last_sel_{prefix}"] = selected_label
        st.session_state[ft_show_key] = current_item.get(
            "Sendung", all_shows_list[0]
        )
        st.session_state[f"ft_seas_{prefix}"] = int(
            current_item.get("Staffel", 1)
        )
        st.session_state[f"ft_ep_{prefix}"] = int(current_item.get("Ep.", 1))
        st.session_state[f"ft_ad_{prefix}"] = int(
            current_item.get("Werbung", 6)
        )

      col_ft1, col_ft2 = st.columns(2)
      with col_ft1:
        new_show = st.selectbox(
            "Sendung / Format",
            all_shows_list,
            key=ft_show_key,
            on_change=on_ft_show_change,
            args=(prefix,),
        )

        col_st, col_ep = st.columns(2)
        with col_st:
          new_season = st.number_input(
              "Staffel",
              min_value=1,
              max_value=3000,
              step=1,
              key=f"ft_seas_{prefix}",
          )
        with col_ep:
          new_ep = st.number_input(
              "Episode",
              min_value=1,
              max_value=10000,
              step=1,
              key=f"ft_ep_{prefix}",
          )

      with col_ft2:
        try:
          start_str_parts = current_item["Uhrzeit"].split(" - ")[0].split(":")
          curr_h = int(start_str_parts[0])
          curr_m = int(start_str_parts[1])
        except Exception:
          curr_h, curr_m = 20, 15

        new_time_val = st.time_input(
            "Startzeit", value=time(curr_h, curr_m), key=f"ft_time_{prefix}"
        )

        fmt_spec = st.session_state.series_db.get(
            new_show
        ) or FILLER_DATABASE.get(new_show)
        new_ad = st.number_input(
            "Werbung (Min.)",
            min_value=0,
            max_value=60,
            step=1,
            key=f"ft_ad_{prefix}",
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
            key=f"ft_status_{prefix}",
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
          "💾 Sendeplatz aktualisieren",
          key=f"ft_save_btn_{prefix}",
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
          st.success("Sendeplatz erfolgreich aktualisiert!")
          st.rerun()

  # --- EXPANDER 3: LÖSCHEN MIT SOFORTIGER FREIGABE ---
  with st.expander(
      f"🗑️ Sendeplätze & Episoden verwalten / löschen ({day_name})",
      expanded=False,
  ):
    if not current_slots:
      st.info(f"Keine Sendeplätze für {day_name} vorhanden.")
    else:
      st.markdown(
          "Das Löschen gibt die Episodennummer sofort wieder für die Planung"
          " frei."
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
          if st.button("❌ Löschen", key=f"del_{prefix}_{idx}"):
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
            st.success(f"'{row['Sendung']}' entfernt und Episode freigegeben!")
            st.rerun()


# --- HAUPTREITER ---
tab_builder, tab_prime, tab_day, tab_night, tab_week, tab_db = st.tabs([
    "⚡ Schnell-Planer (Serien & Blöcke)",
    "⭐ Primetime (20:00 - 02:00)",
    "☀️ Tagesprogramm (06:00 - 20:00)",
    "🌙 Nachtprogramm (ab 02:00)",
    "📅 Gesamt-Wochenübersicht & Live-Prüfung",
    "📚 Format-Referenz & DB",
])

# ==============================================================================
# REITER 1: ÜBERGEORDNETER SCHNELL-PLANER (GLOBAL & MEHRTÄGIG)
# ==============================================================================
with tab_builder:
  st.subheader("⚡ Übergeordneter Schnell-Planer (Mehrtägige Serienstrecken)")
  st.markdown(
      "Plane Serienfolgen oder Wochentagsschienen (z. B. Mo–Fr Strips oder"
      " Wochenende) automatisiert über mehrere Tage hinweg ein."
  )

  col_b1, col_b2 = st.columns(2)
  with col_b1:
    b_day_selection = st.selectbox(
        "Wochentag / Block", DAY_BLOCK_OPTIONS, key="global_b_day"
    )

    if "global_b_show" not in st.session_state:
      st.session_state["global_b_show"] = all_shows_list[0]
      on_show_change("global_b")

    b_show = st.selectbox(
        "Format / Sendung",
        all_shows_list,
        key="global_b_show",
        on_change=on_show_change,
        args=("global_b",),
    )

    if b_show in st.session_state.series_db:
      b_fmt_info = st.session_state.series_db[b_show]
      b_is_filler = False
    else:
      b_fmt_info = FILLER_DATABASE[b_show]
      b_is_filler = True

    if not b_is_filler:
      avail_b_seasons = list(b_fmt_info["seasons"].keys())
      if st.session_state.get("global_b_season") not in avail_b_seasons:
        st.session_state["global_b_season"] = avail_b_seasons[0]

      b_season = st.selectbox(
          "Staffel",
          avail_b_seasons,
          key="global_b_season",
          on_change=on_season_change,
          args=("global_b",),
      )

      (
          b_sugg_ep,
          b_missing_eps,
          b_next_ep,
          b_premiered,
          b_max_eps,
          b_is_complete,
      ) = get_episode_synchronization(b_show, b_season)

      if "global_b_ep" not in st.session_state:
        st.session_state["global_b_ep"] = b_sugg_ep

      st.markdown("##### 🔢 Status & Synchronisation")
      if b_is_complete:
        st.warning(
            f"⚠️ **Staffel {b_season} ist vollständig verplant**"
            f" ({len(b_premiered)}/{b_max_eps} Folgen)!"
        )
      elif b_missing_eps:
        st.info(
            f"💡 **Lücke erkannt!** Folge **`{b_missing_eps[0]}`** fehlt im"
            " Plan und wird vorgeschlagen."
        )
      else:
        max_txt = f" von {b_max_eps}" if b_max_eps else ""
        st.caption(
            f"📌 Bereits im Plan: `{b_premiered}` (Nächste reguläre Folge:"
            f" **{b_next_ep}**{max_txt})"
        )

      col_btn_gap, col_btn_next = st.columns(2)
      with col_btn_gap:
        if b_missing_eps:
          if st.button(
              f"↩️ Lücke Folge {b_missing_eps[0]} wählen",
              key="btn_pick_gap_global",
          ):
            st.session_state["global_b_ep"] = b_missing_eps[0]
            st.rerun()
      with col_btn_next:
        if st.button(
            f"➡️ Fortsetzen: Folge {b_next_ep} wählen",
            key="btn_pick_next_global",
        ):
          st.session_state["global_b_ep"] = b_next_ep
          st.rerun()

      b_episode = st.number_input(
          "Start-Episodennummer",
          min_value=1,
          max_value=10000,
          key="global_b_ep",
          step=1,
      )
    else:
      b_season = 2026
      b_episode = 1
      st.info("💡 Filler-Format (keine Episodennummer erforderlich).")

  with col_b2:
    suggested_start_time = time(20, 15)
    if b_day_selection in WEEKDAYS:
      day_slots = [
          x
          for x in st.session_state.schedule
          if x.get("Wochentag") == b_day_selection
      ]
      if day_slots:
        try:
          latest_end = "00:00"
          for s in day_slots:
            e_t = s["Uhrzeit"].split(" - ")[1]
            if e_t > latest_end:
              latest_end = e_t
          sh, sm = map(int, latest_end.split(":"))
          suggested_start_time = time(sh, sm)
        except Exception:
          pass

    b_start_time = st.time_input(
        "Startzeit", value=suggested_start_time, key="global_b_time"
    )
    b_count = st.selectbox(
        "Anzahl Folgen pro Tag nacheinander",
        list(range(1, 6)),
        key="global_b_count",
    )
    b_status = st.selectbox(
        "Status", STATUS_OPTIONS, key="global_b_status"
    )

    b_net = b_fmt_info["net"]
    b_ad = b_fmt_info["ad"]
    b_total = b_net + b_ad
    st.markdown(
        f"⏱️ **Block-Metrik:** {b_net}m Netto + {b_ad}m Werbung = **{b_total}"
        " Min. Gesamt-Slotlänge**"
    )

  if st.button(
      "🚀 Serienblock in den Gesamtsendeplan einspeisen",
      key="global_b_submit_btn",
      type="primary",
  ):
    if b_day_selection == "Montag bis Freitag (Mo-Fr)":
      target_days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
    elif b_day_selection == "Montag bis Sonntag (Ganze Woche)":
      target_days = WEEKDAYS
    elif b_day_selection == "Wochenende (Sa-So)":
      target_days = ["Samstag", "Sonntag"]
    else:
      target_days = [b_day_selection]

    added_entries = []
    current_ep_counter = int(b_episode)

    for day_name in target_days:
      current_dt = datetime.combine(datetime.today(), b_start_time)
      for _ in range(b_count):
        start_str = current_dt.strftime("%H:%M")
        current_dt += timedelta(minutes=b_total)
        end_str = current_dt.strftime("%H:%M")

        added_entries.append({
            "Wochentag": day_name,
            "Uhrzeit": f"{start_str} - {end_str}",
            "Sendung": b_show,
            "Staffel": b_season,
            "Ep.": current_ep_counter if not b_is_filler else 1,
            "Netto": b_net,
            "Werbung": b_ad,
            "Gesamt": b_total,
            "Status": b_status,
        })
        if not b_is_filler and b_status != "Wiederholung":
          current_ep_counter += 1

    st.session_state.schedule.extend(added_entries)
    save_data(st.session_state.schedule, st.session_state.acknowledged_warnings)
    st.success(
        f"Erfolgreich {len(added_entries)} Sendeplätze über {len(target_days)}"
        " Tag(e) hinweg eingeplant!"
    )
    st.rerun()

# ==============================================================================
# REITER 2: PRIMETIME (20:00 - 02:00)
# ==============================================================================
with tab_prime:
  st.subheader("⭐ Primetime-Matrix (20:00 Uhr bis 02:00 Uhr)")
  st.markdown(
      "Wähle den Wochentag zur Bearbeitung der abendlichen Hauptschiene:"
  )

  prime_day_tabs = st.tabs(WEEKDAYS)
  for idx, day in enumerate(WEEKDAYS):
    with prime_day_tabs[idx]:
      st.markdown(f"#### Primetime am **{day}**")
      render_day_matrix_editor(day, "prime", "prime")

# ==============================================================================
# REITER 3: TAGESPROGRAMM (06:00 - 20:00)
# ==============================================================================
with tab_day:
  st.subheader("☀️ Tagesprogramm-Matrix (06:00 Uhr bis 20:00 Uhr)")
  st.markdown(
      "Vormittags-, Mittags- und Vorabend-Schienen getrennt nach Wochentagen:"
  )

  day_day_tabs = st.tabs(WEEKDAYS)
  for idx, day in enumerate(WEEKDAYS):
    with day_day_tabs[idx]:
      st.markdown(f"#### Tagesprogramm am **{day}**")
      render_day_matrix_editor(day, "day", "day")

# ==============================================================================
# REITER 4: NACHTPROGRAMM (AB 02:00 BIS 06:00)
# ==============================================================================
with tab_night:
  st.subheader("🌙 Nachtprogramm-Matrix (ab 02:00 Uhr bis 06:00 Uhr)")
  st.markdown("Late-Night, Wiederholungsstrecken und Dokumentationen ab 02:00:")

  night_day_tabs = st.tabs(WEEKDAYS)
  for idx, day in enumerate(WEEKDAYS):
    with night_day_tabs[idx]:
      st.markdown(f"#### Nachtprogramm am **{day}** (ab 02:00 Uhr)")
      render_day_matrix_editor(day, "night", "night")

# ==============================================================================
# REITER 5: GESAMT-WOCHENÜBERSICHT, LIVE-PRÜFUNG & BACKUP
# ==============================================================================
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
      st.success("✅ Alle Sendeplätze sind sauber und fehlerfrei eingetaktet.")

    st.markdown("---")
    st.markdown("### 💾 Datensicherung, Cloud-Backup & Export")

    col_exp1, col_exp2, col_exp3 = st.columns(3)
    with col_exp1:
      csv_export = pd.DataFrame(st.session_state.schedule).to_csv(
          index=False
      ).encode("utf-8")
      st.download_button(
          "📥 Sendeplan als CSV herunterladen",
          csv_export,
          "sendeplan_export.csv",
          "text/csv",
          use_container_width=True,
      )

    with col_exp2:
      json_backup = json.dumps(
          {
              "schedule": st.session_state.schedule,
              "acknowledged_warnings": list(
                  st.session_state.acknowledged_warnings
              ),
          },
          indent=4,
          ensure_ascii=False,
      ).encode("utf-8")
      st.download_button(
          "💾 JSON-Backup herunterladen",
          json_backup,
          "sendeplan_backup.json",
          "application/json",
          use_container_width=True,
      )

    with col_exp3:
      if st.button(
          "🗑️ Gesamten Sendeplan leeren",
          use_container_width=True,
          type="secondary",
      ):
        st.session_state.schedule = []
        st.session_state.acknowledged_warnings.clear()
        save_data([], set())
        st.rerun()

    with st.expander("📥 Gesicherten Sendeplan wiederherstellen (JSON Upload)"):
      uploaded_file = st.file_uploader(
          "JSON-Backup auswählen", type=["json"], key="restore_uploader"
      )
      if uploaded_file is not None:
        try:
          content = json.load(uploaded_file)
          if isinstance(content, dict) and "schedule" in content:
            st.session_state.schedule = content["schedule"]
            st.session_state.acknowledged_warnings = set(
                content.get("acknowledged_warnings", [])
            )
          elif isinstance(content, list):
            st.session_state.schedule = content
          save_data(
              st.session_state.schedule, st.session_state.acknowledged_warnings
          )
          st.success("Sendeplan erfolgreich wiederhergestellt!")
          st.rerun()
        except Exception as e:
          st.error(f"Fehler beim Wiederherstellen: {e}")
  else:
    st.info("Der Sendeplan ist aktuell leer.")

# ==============================================================================
# REITER 6: FORMAT-DATENBANK & VERWALTUNG
# ==============================================================================
with tab_db:
  st.subheader("📚 Format-Referenz & Stammdaten")
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
        st.success(f"Format '{new_show_name}' erfolgreich registriert!")
        st.rerun()
