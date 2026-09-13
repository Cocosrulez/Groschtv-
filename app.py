from datetime import datetime, time, timedelta
import json
import os
import pandas as pd
import streamlit as st

# Dateipfad für Version 5.1
SAVE_FILE = "sendeplan_v5.1.json"
FORMATS_FILE = "formats_v5.1.json"

# Seitenkonfiguration
st.set_page_config(
    page_title="Master Control v5.1 | Broadcast Direktion",
    page_icon="📡",
    layout="wide",
)

# --- MODERNES BROADCAST-CONTROL DESIGN (V5.1) ---
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
    
    /* Kompakte Tabellen-Zeilen im edlen Look */
    .schedule-row {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        font-size: 0.9rem;
        color: #e2e8f0;
    }
    .schedule-header {
        display: flex;
        align-items: center;
        padding: 10px 12px;
        border-bottom: 2px solid rgba(255, 255, 255, 0.15);
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
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


# --- PERSISTENZ (Sendeplan & Bestätigte Warnungen gemeinsam in v5.1 JSON) ---
def load_data():
  target_file = (
      SAVE_FILE
      if os.path.exists(SAVE_FILE)
      else ("sendeplan_v5.0.json" if os.path.exists("sendeplan_v5.0.json") else None)
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
    if item.get("Sendung") in ["Tagessthemen", "Tagesschau / News"] and item.get("Staffel") == 1:
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
st.title("📡 Master Control v5.1: Programm-Direktion")
st.markdown(
    "**Broadcast-Engine (v5.1)** — Elegante Tabellenoptik mit dezentem"
    " **×**-Löschbutton pro Zeile, korrigierte Staffeln & Episoden-Sync."
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
            <div class="metric-value">v5.1 Sleek Table</div>
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
    "📚 Format-Referenz & Bearbeitung",
])

with tab_matrix:
  st.subheader("Wochenübersicht & Sendeplan")

  if st.session_state.schedule:
    df = pd.DataFrame(st.session_state.schedule)
    day_sorting = {d: i for i, d in enumerate(WEEKDAYS)}
    if "Wochentag" in df.columns:
      df["_sort"] = df["Wochentag"].map(day_sorting).fillna(9)
      df = df.sort_values(by=["_sort", "Uhrzeit"]).drop(columns=["_sort"])

    st.markdown(
        "Übersicht aller eingeplanten Sendeplätze. Klicke in einer Zeile ganz"
        " rechts auf **×**, um den Eintrag sofort zu löschen."
    )

    # Schönes, elegantes Tabellen-Layout mit feinen Spaltenbreiten
    cols_width = [1.2, 1.2, 2.2, 0.6, 0.6, 0.6, 0.6, 0.6, 1.2, 0.4]

    # Tabellen-Header
    h = st.columns(cols_width)
    h[0].markdown("**Tag**")
    h[1].markdown("**Uhrzeit**")
    h[2].markdown("**Sendung**")
    h[3].markdown("**St.**")
    h[4].markdown("**Ep.**")
    h[5].markdown("**Netto**")
    h[6].markdown("**Werb.**")
    h[7].markdown("**Ges.**")
    h[8].markdown("**Status**")
    h[9].markdown("**×**")

    st.markdown(
        "<hr style='margin: 0px 0px 8px 0px; border-color: rgba(255,255,255,0.12);'>",
        unsafe_allow_html=True,
    )

    # Tabellen-Zeilen
    for idx, row in df.iterrows():
      r = st.columns(cols_width)
      r[0].write(row["Wochentag"])
      r[1].write(f"`{row['Uhrzeit']}`")
      r[2].write(row["Sendung"])
      r[3].write(str(row["Staffel"]))
      r[4].write(str(row["Ep."]))
      r[5].write(f"{row['Netto']}m")
      r[6].write(f"{row['Werbung']}m")
      r[7].write(f"**{row['Gesamt']}m**")
      r[8].write(row["Status"])
      with r[9]:
        if st.button("×", key=f"tbl_del_{idx}", help="Eintrag löschen"):
          orig_idx = st.session_state.schedule.index(
              row.drop(labels=["_sort"], errors="ignore").to_dict()
          )
          st.session_state.schedule.pop(orig_idx)
          save_data(
              st.session_state.schedule, st.session_state.acknowledged_warnings
          )
          st.success("Gelöscht & Episode freigegeben!")
          st.rerun()

    st.markdown("---")

    # --- FEINTUNER EXPANDER ---
    with st.expander("🛠️ Sendeplatz-Feintuner (Details anpassen)", expanded=False):
      if st.session_state.schedule:
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

        is_exact_slot, slot_msg = get_slot_grid_info(total_len)
        if is_exact_slot:
          st.info(
              f"ℹ️ **Slot-Info:** {current_item['Sendung']} (Netto: {new_net}"
              f" Min. fix) + Werbung ({new_ad} Min.) = **{total_len} Min."
              f" gesamt** | {slot_msg}"
          )
        else:
          st.warning(
              f"ℹ️ **Slot-Hinweis:** {current_item['Sendung']} (Netto: {new_net}"
              f" Min. fix) + Werbung ({new_ad} Min.) = **{total_len} Min."
              f" gesamt** | {slot_msg}"
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
          st.success("Erfolgreich aktualisiert & dauerhaft gespeichert!")
          st.rerun()

    # --- STRIKTE LIVE-LOGIK & PERSISTENTE WARNUNGEN ---
    st.markdown("---")
    st.subheader("🔍 Live-Logik & Format-Datenbank-Prüfung")
    errors_found = []
    slot_warnings = []
    gap_actions = []

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
        warn_key = f"raster_{row['Wochentag']}_{row['Uhrzeit']}_{row['Sendung']}_Ep{row['Ep.']}"
        if not is_exact and warn_key not in st.session_state.acknowledged_warnings:
          slot_warnings.append((
              warn_key,
              f"**Raster-Hinweis bei Sendeplatz #{idx+1} ({row['Wochentag']}, {row['Uhrzeit']}) – '{show_name}':** {info_text} (Netto: {row['Netto']}m + Werbung: {row['Werbung']}m)",
          ))

      except Exception:
        errors_found.append(
            f"Formatierungsfehler in Zeile {idx+1}: Ungültiges Zeitformat."
        )

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
              gap_key = f"gap_{day}_{curr_row['Sendung']}_{curr_row['Uhrzeit']}_{next_row['Sendung']}_{next_row['Uhrzeit']}"
              if (
                  gap_key not in st.session_state.acknowledged_warnings
                  and gap > 0
              ):
                slot_warnings.append((
                    gap_key,
                    f"**Lücke am {day}:** Zwischen Sendeplatz #{idx_curr+1} ('{curr_row['Sendung']}') und #{idx_next+1} ('{next_row['Sendung']}') liegt eine Lücke von **{gap} Minuten** ({c_end_str} bis {n_start_str}).",
                ))
                gap_actions.append({
                    "day": day,
                    "start_time": c_end_str,
                    "gap_mins": gap,
                    "key": gap_key,
                })
          except Exception:
            pass

    if errors_found:
      for err in errors_found:
        st.error(f"❌ {err}")
    else:
      st.success(
          "✅ **Keine Laufzeit- oder Kollisionsfehler:** Alle Sendeplätze sind"
          " zeitlich sauber eingetaktet."
      )

    if slot_warnings:
      st.markdown("---")
      st.markdown("### ⚠️ Hinweise, Lücken & Raster-Abweichungen")
      for w_key, warn_text in slot_warnings:
        col_w1, col_w2, col_w3 = st.columns([3, 1, 1])
        with col_w1:
          st.warning(warn_text)

        matching_gap = next(
            (g for g in gap_actions if g["key"] == w_key), None
        )

        with col_w2:
          if matching_gap:
            available_fillers = [
                f
                for f, data in FILLER_DATABASE.items()
                if data["net"] <= matching_gap["gap_mins"]
            ]
            if available_fillers:
              chosen_filler = st.selectbox(
                  "Filler wählen", available_fillers, key=f"sel_filler_{w_key}"
              )
              if st.button("✨ Lücke füllen", key=f"fill_{w_key}"):
                f_data = FILLER_DATABASE[chosen_filler]
                sh, sm = map(int, matching_gap["start_time"].split(":"))
                start_dt = datetime.combine(datetime.today(), time(sh, sm))
                end_dt = start_dt + timedelta(
                    minutes=f_data["net"] + f_data["ad"]
                )

                new_slot = {
                    "Wochentag": matching_gap["day"],
                    "Uhrzeit": (
                        f"{start_dt.strftime('%H:%M')} -"
                        f" {end_dt.strftime('%H:%M')}"
                    ),
                    "Sendung": chosen_filler,
                    "Staffel": 2026,
                    "Ep.": 1,
                    "Netto": f_data["net"],
                    "Werbung": f_data["ad"],
                    "Gesamt": f_data["net"] + f_data["ad"],
                    "Status": "Erstausstrahlung",
                }
                st.session_state.schedule.append(new_slot)
                save_data(
                    st.session_state.schedule,
                    st.session_state.acknowledged_warnings,
                )
                st.success(f"Lücke mit '{chosen_filler}' geschlossen!")
                st.rerun()
            else:
              st.caption("Kein kleiner Filler verfügbar")

        with col_w3:
          if st.button("Als OK markieren", key=f"ack_{w_key}"):
            st.session_state.acknowledged_warnings.add(w_key)
            save_data(
                st.session_state.schedule,
                st.session_state.acknowledged_warnings,
            )
            st.rerun()

    st.markdown("---")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
      if st.button("🗑️ Sendeplan komplett zurücksetzen"):
        st.session_state.schedule = []
        st.session_state.acknowledged_warnings.clear()
        save_data([], set())
        st.rerun()
    with col_a2:
      csv_export = pd.DataFrame(st.session_state.schedule).to_csv(
          index=False
      ).encode("utf-8")
      st.download_button(
          "📥 Bereinigten Sendeplan als CSV exportieren",
          csv_export,
          "sendeplan_v5.1.csv",
          "text/csv",
      )
  else:
    st.info("Der Sendeplan ist aktuell leer.")

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

      # Automatische Ermittlung der nächsten freien Episodennummer
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

      if existing_eps:
        st.info(
            f"📌 Bereits im Plan für '{show}' (Staffel {season}): Episoden"
            f" {sorted(list(set(existing_eps)))}"
        )
    else:
      season = 2026
      episode = 1
      st.info("💡 Smart Filler Format (keine Episodennummer nötig).")

  with col_b2:
    start_t = st.time_input("Startzeit", time(20, 15), key="builder_time")
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
  st.subheader("🛠️ Format bearbeiten oder löschen")

  selected_format_to_edit = st.selectbox(
      "Format ausählen", list(st.session_state.series_db.keys())
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
