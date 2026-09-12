from datetime import datetime, time, timedelta
import json
import os
import pandas as pd
import streamlit as st

# Dateipfad für Version 3.0
SAVE_FILE = "sendeplan_v3.0.json"

# Seitenkonfiguration
st.set_page_config(
    page_title="Master Control v3.0 | Broadcast Direktion",
    page_icon="📡",
    layout="wide",
)

# --- MODERNES BROADCAST-CONTROL DESIGN (V3.0) ---
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

# --- MASTER FORMAT-DATENBANK (Individuelle Standard-Laufzeiten je Format) ---
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
DAY_OPTIONS = WEEKDAYS + ["Montag bis Freitag (Mo-Fr)"]
STATUS_OPTIONS = ["Erstausstrahlung", "Wiederholung", "Live"]


# --- HILFSFUNKTION FÜR SLOT-HINWEISE ---
def get_slot_grid_info(total_mins):
  """Ermittelt, ob und wie weit ein Gesamt-Block von einem Standard-Halbstunden-Raster abweicht."""
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


# --- PERSISTENZ (Mit Migration von v2.7) ---
def load_schedule():
  target_file = (
      SAVE_FILE
      if os.path.exists(SAVE_FILE)
      else ("sendeplan_v2.7.json" if os.path.exists("sendeplan_v2.7.json") else None)
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

# --- HEADER & NEUE DESIGN-METRIKEN ---
st.title("📡 Master Control v3.0: Programm-Direktion")
st.markdown(
    "**Broadcast-Engine (v3.0)** — Format-abhängige fixe Netto-Laufzeiten,"
    " optimiertes Studio-Layout & Slot-Rasterkontrolle."
)

total_items = len(st.session_state.schedule)
total_mins = sum([x.get("Gesamt", 0) for x in st.session_state.schedule])

# Saubere, optisch ansprechende Control-Room Metric Cards
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
            <div class="metric-value">v3.0 Studio</div>
        </div>
        <div class="metric-card" style="border-left-color: #f59e0b;">
            <div class="metric-label">Persistenz</div>
            <div class="metric-value">Aktiv (v3.0)</div>
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
    "📚 Format-Referenz",
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

      # Automatische Netto-Laufzeit aus der Format-DB im Hintergrund
      current_format = SERIES_DATABASE.get(current_item["Sendung"])
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

      # Layout ohne Netto-Feld (5 aufgeräumte Spalten)
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

      # --- LIVE-FEEDBACK FÜR WERBUNG & SLOT-ABWEICHUNG ---
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

    # --- STRIKTE LIVE-LOGIK & KONSISTENZ-PRÜFUNG ---
    st.markdown("---")
    st.subheader("🔍 Live-Logik & Format-Datenbank-Prüfung")
    errors_found = []
    slot_warnings = []

    for idx, row in enumerate(st.session_state.schedule):
      show_name = row["Sendung"]
      format_spec = SERIES_DATABASE.get(show_name)

      try:
        # 1. Strikter Check: Stimmt die Netto-Dauer EXAKT mit dem jeweiligen Format überein?
        if format_spec:
          expected_net = format_spec["net"]
          actual_net = int(row["Netto"])
          if actual_net != expected_net:
            errors_found.append(
                f"**Episodenlängen-Fehler bei Sendeplatz #{idx+1} ({row['Wochentag']}, {row['Uhrzeit']}) – '{show_name}':** "
                f"Eingetragene Dauer: **{actual_net} Min.** | Das Format '{show_name}' schreibt in der DB exakt **{expected_net} Min.** vor!"
            )

        # 2. Check: Reines Zeitfenster (Start- bis Endzeit)
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

        # 3. Check: Slot-Rasterhinweis bei variierender Werbung
        is_exact, info_text = get_slot_grid_info(expected_total)
        if not is_exact:
          slot_warnings.append(
              f"**Sendeplatz #{idx+1} ({row['Wochentag']}, {row['Uhrzeit']}) – '{show_name}':** {info_text} (Netto: {row['Netto']}m + Werbung: {row['Werbung']}m)"
          )

      except Exception:
        errors_found.append(
            f"Formatierungsfehler in Zeile {idx+1}: Ungültiges Zeitformat."
        )

    # Rendering Fehler
    if errors_found:
      for err in errors_found:
        st.error(f"❌ {err}")
    else:
      st.success(
          "✅ **Keine Laufzeitfehler:** Alle Episoden entsprechen exakt ihren"
          " format-spezifischen Datenbank-Vorgaben."
      )

    # Rendering Warnungen / Slot-Infos
    if slot_warnings:
      with st.container():
        for warn in slot_warnings:
          st.warning(f"⚠️ {warn}")

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
          "sendeplan_v3.0.csv",
          "text/csv",
      )
  else:
    st.info("Der Sendeplan ist aktuell leer.")

with tab_builder:
  st.subheader("Programmpunkt fehlerfrei einplanen")
  with st.form("builder_v30"):
    col_b1, col_b2 = st.columns(2)
    with col_b1:
      day_selection = st.selectbox("Wochentag / Block", DAY_OPTIONS)
      show = st.selectbox("Format / Sendung", list(SERIES_DATABASE.keys()))
      format_info = SERIES_DATABASE[show]
      season = st.selectbox("Staffel", list(format_info["seasons"].keys()))
      episode = st.selectbox(
          "Start-Episodennummer",
          list(range(1, format_info["seasons"][season] + 1)),
      )
    with col_b2:
      start_t = st.time_input("Startzeit", time(20, 15))
      count = st.selectbox("Anzahl Folgen nacheinander", list(range(1, 6)))
      plan_status = st.selectbox("Status", STATUS_OPTIONS)

      net_time = format_info["net"]
      ad_time = format_info["ad"]
      total_block = net_time + ad_time
      st.markdown(
          f"💡 **Voreinstellung aus Format-DB für '{show}':** {net_time} Min."
          f" Netto (fix) + {ad_time} Min. Werbung = **{total_block} Min."
          f" gesamt**."
      )

    submitted = st.form_submit_button("Sendung in den Sendeplan aufnehmen")
    if submitted:
      added_entries = []

      # Unterscheidung ob einzelner Tag oder Mo-Fr Block
      if day_selection == "Montag bis Freitag (Mo-Fr)":
        target_days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
      else:
        target_days = [day_selection]

      for d_idx, day_name in enumerate(target_days):
        current_dt = datetime.combine(datetime.today(), start_t)
        for i in range(count):
          start_str = current_dt.strftime("%H:%M")
          current_dt += timedelta(minutes=total_block)
          end_str = current_dt.strftime("%H:%M")

          # Episodennummerierung bei Mo-Fr über die Wochentage hinweg fortlaufend anpassen
          ep_num = (
              episode
              + i
              + (
                  d_idx * count
                  if day_selection == "Montag bis Freitag (Mo-Fr)"
                  else 0
              )
          )

          added_entries.append({
              "Wochentag": day_name,
              "Uhrzeit": f"{start_str} - {end_str}",
              "Sendung": show,
              "Staffel": season,
              "Ep.": ep_num,
              "Netto": net_time,
              "Werbung": ad_time,
              "Gesamt": total_block,
              "Status": plan_status,
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
