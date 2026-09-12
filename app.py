from datetime import datetime, time, timedelta
import json
import os
import pandas as pd
import streamlit as st

# Dateipfad für Version 4.0
SAVE_FILE = "sendeplan_v4.0.json"
FORMATS_FILE = "formats_v4.0.json"

# Seitenkonfiguration
st.set_page_config(
    page_title="Master Control v4.0 | Broadcast Direktion",
    page_icon="📡",
    layout="wide",
)

# --- MODERNES BROADCAST-CONTROL DESIGN (V4.0) ---
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

# --- SMART FILLER DATENBANK (Kurzformate zum Lückenfüllen) ---
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
DAY_OPTIONS = WEEKDAYS + ["Montag bis Freitag (Mo-Fr)"]
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

if "acknowledged_warnings" not in st.session_state:
  st.session_state.acknowledged_warnings = set()


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


# --- PERSISTENZ (Sendeplan) ---
def load_schedule():
  target_file = (
      SAVE_FILE
      if os.path.exists(SAVE_FILE)
      else ("sendeplan_v3.0.json" if os.path.exists("sendeplan_v3.0.json") else None)
  )
  if target_file:
    try:
      with open(target_file, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      pass
  return [
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
          "Uhrzeit": "20:45 - 21:45",
          "Sendung": "Breaking Bad",
          "Staffel": 1,
          "Ep.": 1,
          "Netto": 45,
          "Werbung": 15,
          "Gesamt": 60,
          "Status": "Erstausstrahlung",
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

# --- HEADER & METRIKEN ---
st.title("📡 Master Control v4.0: Programm-Direktion")
st.markdown(
    "**Broadcast-Engine (v4.0)** — Smart Filler Lücken-Generator,"
    " Episoden-Sperre & Kollisionsprüfung."
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
            <div class="metric-value">v4.0 Smart Filler</div>
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
tab_matrix, tab_builder, tab_db = st.tabs([
    "📅 Wochen-Matrix & Editor",
    "⚡ Schnell-Planer (Neuer Slot)",
    "📚 Format-Referenz & Neue Sendungen",
])

with tab_matrix:
  st.subheader("Wochenübersicht & Sendeplan")

  if st.session_state.schedule:
    df = pd.DataFrame(st.session_state.schedule)
    day_sorting = {d: i for i, d in enumerate(WEEKDAYS)}
    if "Wochentag" in df.columns:
      df["_sort"] = df["Wochentag"].map(day_sorting).fillna(9)
      df = df.sort_values(by=["_sort", "Uhrzeit"]).drop(columns=["_sort"])

    st.dataframe(df, use_container_width=True)

    st.markdown("---")

    # --- DROP-UP / EXPANDIERBARER EDITOR ---
    with st.expander(
        "🛠️ Sendeplatz-Feintuner & Lösch-Menü öffnen", expanded=False
    ):
      st.markdown(
          "Wähle einen Programmpunkt aus. Die Netto-Laufzeit wird im"
          " Hintergrund format-abhängig automatisch übernommen. Passe flexibel"
          " Startzeit und Werbezeit an."
      )

      options_labels = [
          f"#{i+1}: {item['Wochentag']} | {item['Uhrzeit']} – {item['Sendung']} (St. {item['Staffel']}, Ep. {item['Ep.']})"
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

      col_e1, col_e2, col_e3, col_e4, col_e5 = st.columns([2, 1, 1.5, 1, 1])

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
      with col_e5:
        st.markdown("<br>", unsafe_allow_html=True)
        delete_clicked = st.button(
            "🗑️ Löschen", use_container_width=True, key="btn_delete_slot"
        )

      total_len = new_net + new_ad
      start_dt = datetime.combine(datetime.today(), new_time_val)
      end_dt = start_dt + timedelta(minutes=total_len)
      new_time_str = (
          f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
      )

      is_exact_slot, slot_msg = get_slot_grid_info(total_len)
      if is_exact_slot:
        st.info(
            f"ℹ️ **Slot-Info:** {current_item['Sendung']} (Netto: {new_net} Min."
            f" fix) + Werbung ({new_ad} Min.) = **{total_len} Min. gesamt** |"
            f" {slot_msg}"
        )
      else:
        st.warning(
            f"ℹ️ **Slot-Hinweis:** {current_item['Sendung']} (Netto: {new_net}"
            f" Min. fix) + Werbung ({new_ad} Min.) = **{total_len} Min. gesamt**"
            f" | {slot_msg}"
        )

      if save_clicked:
        st.session_state.schedule[selected_idx]["Uhrzeit"] = new_time_str
        st.session_state.schedule[selected_idx]["Netto"] = int(new_net)
        st.session_state.schedule[selected_idx]["Werbung"] = int(new_ad)
        st.session_state.schedule[selected_idx]["Gesamt"] = int(total_len)
        st.session_state.schedule[selected_idx]["Status"] = new_status
        save_schedule(st.session_state.schedule)
        st.success("Erfolgreich aktualisiert & dauerhaft gespeichert!")
        st.rerun()

      if delete_clicked:
        st.session_state.schedule.pop(selected_idx)
        save_schedule(st.session_state.schedule)
        st.success("Sendeplatz entfernt!")
        st.rerun()

    # --- STRIKTE LIVE-LOGIK & TAGESBASIERTE KOLLISIONS- & LÜCKENPRÜFUNG ---
    st.markdown("---")
    st.subheader("🔍 Live-Logik & Format-Datenbank-Prüfung")
    errors_found = []
    slot_warnings = []
    gap_actions = []  # Speichert Lücken für den Smart-Filler-Button

    # 1. Format- und Einzel-Slot Checks
    for idx, row in enumerate(st.session_state.schedule):
      show_name = row["Sendung"]
      format_spec = st.session_state.series_db.get(show_name) or FILLER_DATABASE.get(show_name)

      try:
        if not format_spec:
          errors_found.append(
              f"**Unbekanntes Format bei Sendeplatz #{idx+1} ({row['Wochentag']}, {row['Uhrzeit']}):** "
              f"Das Format '{show_name}' existiert nicht in der Format-Datenbank!"
          )
        else:
          expected_net = format_spec["net"]
          actual_net = int(row["Netto"])
          if actual_net != expected_net:
            errors_found.append(
                f"**Episodenlängen-Fehler bei Sendeplatz #{idx+1} ({row['Wochentag']}, {row['Uhrzeit']}) – '{show_name}':** "
                f"Eingetragene Dauer: **{actual_net} Min.** | Das Format '{show_name}' schreibt in der DB exakt **{expected_net} Min.** vor!"
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
              f"**Zeitfenster-Konflikt bei Sendeplatz #{idx+1} ({row['Wochentag']}, {row['Uhrzeit']}) – '{show_name}':** "
              f"Das Sendezeitfenster umfasst **{slot_mins} Min.**, aber Netto ({row['Netto']} Min.) + Werbung ({row['Werbung']} Min.) ergeben **{expected_total} Min.**!"
          )

        is_exact, info_text = get_slot_grid_info(expected_total)
        warn_key = f"raster_{idx}"
        if not is_exact and warn_key not in st.session_state.acknowledged_warnings:
          slot_warnings.append((
              warn_key,
              f"**Raster-Hinweis bei Sendeplatz #{idx+1} ({row['Wochentag']}, {row['Uhrzeit']}) – '{show_name}':** {info_text} (Netto: {row['Netto']}m + Werbung: {row['Werbung']}m)",
          ))

      except Exception:
        errors_found.append(
            f"Formatierungsfehler in Zeile {idx+1}: Ungültiges Zeitformat."
        )

    # 2. Tagesbasierte chronologische Prüfung & Smart Filler Erkennung
    for day in WEEKDAYS:
      day_slots = [
          (i, row)
          for i, row in enumerate(st.session_state.schedule)
          if row["Wochentag"] == day
      ]
      if len(day_slots) > 1:

        def get_mins(item):
          try:
            s_str = item[1]["Uhrzeit"].split(" - ")[0]
            h, m = map(int, s_str.split(":"))
            return h * 60 + m
          except:
            return 0

        day_slots.sort(key=get_mins)

        for k in range(len(day_slots) - 1):
          idx_curr, curr_row = day_slots[k]
          idx_next, next_row = day_slots[k + 1]
          try:
            c_end_str = curr_row["Uhrzeit"].split(" - ")[1]
            n_start_str = next_row["Uhrzeit"].split(" - ")[0]
            ch, cm = map(int, c_end_str.split(":"))
            nh, nm = map(int, n_start_str.split(":"))
            c_end = ch * 60 + cm
            n_start = nh * 60 + nm
            if c_end > 24 * 60:
              c_end -= 24 * 60

            if n_start < c_end:
              errors_found.append(
                  f"**Kollisions-Fehler am {day}:** Sendeplatz #{idx_curr+1} ('{curr_row['Sendung']}', endet {c_end_str}) überschneidet sich direkt mit Sendeplatz #{idx_next+1} ('{next_row['Sendung']}', beginnt {n_start_str})!"
              )
            elif n_start > c_end:
              gap = n_start - c_end
              gap_key = f"gap_{idx_curr}_{idx_next}"
              if (
                  gap_key not in st.session_state.acknowledged_warnings
                  and gap > 0
              ):
                slot_warnings.append((
                    gap_key,
                    f"**Lücke am {day}:** Zwischen Sendeplatz #{idx_curr+1} ('{curr_row['Sendung']}') und #{idx_next+1} ('{next_row['Sendung']}') liegt eine Lücke von **{gap} Minuten** ({c_end_str} bis {n_start_str}).",
                ))
                # Für den Smart Filler merken: Wochentag, Startzeit, Lütkengröße
                gap_actions.append({
                    "day": day,
                    "start_time": c_end_str,
                    "gap_mins": gap,
                    "key": gap_key
                })
          except Exception:
            pass

    # Rendering Fehler
    if errors_found:
      for err in errors_found:
        st.error(f"❌ {err}")
    else:
      st.success(
          "✅ **Keine Laufzeit- oder Kollisionsfehler:** Alle Sendeplätze sind"
          " zeitlich sauber eingetaktet."
      )

    # Rendering Warnungen mit Bestätigungs-Button oder Smart-Filler-Aktion
    if slot_warnings:
      st.markdown("---")
      st.markdown("### ⚠️ Hinweise, Lücken & Raster-Abweichungen")
      for w_key, warn_text in slot_warnings:
        col_w1, col_w2, col_w3 = st.columns([3, 1, 1])
        with col_w1:
          st.warning(warn_text)
        
        # Prüfen, ob es sich um eine Lücke handelt, für die wir einen Smart Filler anbieten können
        matching_gap = next((g for g in gap_actions if g["key"] == w_key), None)
        
        with col_w2:
          if matching_gap:
            # Passenden Filler anhand der Minuten aussuchen
            available_fillers = [f for f, data in FILLER_DATABASE.items() if data["net"] <= matching_gap["gap_mins"]]
            if available_fillers:
              chosen_filler = st.selectbox("Filler wählen", available_fillers, key=f"sel_filler_{w_key}")
              if st.button("✨ Lücke füllen", key=f"fill_{w_key}"):
                f_data = FILLER_DATABASE[chosen_filler]
                # Neuen Filler-Slot einfügen
                sh, sm = map(int, matching_gap["start_time"].split(":"))
                start_dt = datetime.combine(datetime.today(), time(sh, sm))
                end_dt = start_dt + timedelta(minutes=f_data["net"] + f_data["ad"])
                
                new_slot = {
                    "Wochentag": matching_gap["day"],
                    "Uhrzeit": f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}",
                    "Sendung": chosen_filler,
                    "Staffel": 2026,
                    "Ep.": 1,
                    "Netto": f_data["net"],
                    "Werbung": f_data["ad"],
                    "Gesamt": f_data["net"] + f_data["ad"],
                    "Status": "Erstausstrahlung"
                }
                st.session_state.schedule.append(new_slot)
                save_schedule(st.session_state.schedule)
                st.success(f"Lücke mit '{chosen_filler}' geschlossen!")
                st.rerun()
            else:
              st.caption("Kein kleiner Filler verfügbar")
        
        with col_w3:
          if st.button("Als OK markieren", key=f"ack_{w_key}"):
            st.session_state.acknowledged_warnings.add(w_key)
            st.rerun()

    st.markdown("---")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
      if st.button("🗑️ Sendeplan komplett zurücksetzen"):
        st.session_state.schedule = []
        st.session_state.acknowledged_warnings.clear()
        save_schedule([])
        st.rerun()
    with col_a2:
      csv_export = pd.DataFrame(st.session_state.schedule).to_csv(
          index=False
      ).encode("utf-8")
      st.download_button(
          "📥 Bereinigten Sendeplan als CSV exportieren",
          csv_export,
          "sendeplan_v4.0.csv",
          "text/csv",
      )
  else:
    st.info("Der Sendeplan ist aktuell leer.")

with tab_builder:
  st.subheader("Programmpunkt fehlerfrei einplanen")

  col_b1, col_b2 = st.columns(2)
  with col_b1:
    day_selection = st.selectbox("Wochentag / Block", DAY_OPTIONS, key="builder_day")
    show = st.selectbox(
        "Format / Sendung", list(st.session_state.series_db.keys()) + list(FILLER_DATABASE.keys()), key="builder_show"
    )
    
    # Prüfen ob reguläres Format oder Filler
    if show in st.session_state.series_db:
      format_info = st.session_state.series_db[show]
      is_filler = False
    else:
      format_info = FILLER_DATABASE[show]
      is_filler = True

    if not is_filler:
      season = st.selectbox("Staffel", list(format_info["seasons"].keys()), key="builder_season")
      existing_eps = [
          x["Ep."]
          for x in st.session_state.schedule
          if x["Sendung"] == show and x["Staffel"] == season
      ]
      next_ep_suggestion = max(existing_eps) + 1 if existing_eps else 1

      episode = st.number_input(
          "Start-Episodennummer (Automatisch nächste freie Folge)",
          min_value=1,
          max_value=10000,
          value=next_ep_suggestion,
          step=1,
          key="builder_ep"
      )
      if existing_eps:
        st.info(f"📌 Bereits im Plan für '{show}' (Staffel {season}): Episoden {sorted(list(set(existing_eps)))}")
    else:
      season = 2026
      episode = 1
      st.info("💡 Smart Filler Format (keine Episodennummer nötig).")

  with col_b2:
    start_t = st.time_input("Startzeit", time(20, 15), key="builder_time")
    count = st.selectbox("Anzahl Folgen nacheinander", list(range(1, 6)), key="builder_count")
    plan_status = st.selectbox("Status", STATUS_OPTIONS, key="builder_status")

    override_lock = st.checkbox(
        "🔄 Bereits vergebene Episoden für Neuzugänge freischalten (Überschreiben erlauben)",
        value=False,
        key="builder_override"
    )

    net_time = format_info["net"]
    ad_time = format_info["ad"]
    total_block = net_time + ad_time
    st.markdown(
        f"💡 **Voreinstellung für '{show}':** {net_time} Min."
        f" Netto + {ad_time} Min. Werbung = **{total_block} Min."
        f" gesamt**."
    )

  submitted = st.button("Sendung in den Sendeplan aufnehmen", key="builder_submit_btn", type="primary")
  if submitted:
    added_entries = []

    if day_selection == "Montag bis Freitag (Mo-Fr)":
      target_days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
    else:
      target_days = [day_selection]

    current_ep = int(episode)
    conflict_found = False
    conflicting_eps = []

    if not is_filler and not override_lock:
      check_ep = current_ep
      for _ in target_days:
        for _ in range(count):
          if check_ep in existing_eps:
            conflict_found = True
            conflicting_eps.append(check_ep)
          check_ep += 1

    if conflict_found and not override_lock:
      st.error(
          f"🚫 **Episoden-Sperre aktiv:** Die Episoden {list(set(conflicting_eps))}"
          f" für '{show}' (Staffel {season}) sind bereits im Sendeplan"
          " vorhanden! Aktiviere die Checkbox 'Überschreiben erlauben'."
      )
    else:
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
      save_schedule(st.session_state.schedule)
      st.success("Erfolgreich eingeplant & gespeichert!")
      st.rerun()

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
