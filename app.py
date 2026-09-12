import datetime
import pandas as pd
import streamlit as st

# --- SEITENKONFIGURATION ---
st.set_page_config(
    page_title="Profi TV-Sender Master Control Room",
    page_icon="📺",
    layout="wide",
)

# --- INITIALISIERUNG DER DATENBANK ---
if "database" not in st.session_state:
  st.session_state.database = pd.DataFrame([
      {
          "Titel": "Hacks",
          "Genre": "Comedy",
          "Staffeln": 3,
          "Episoden pro Staffel": "10, 8, 9",
          "Laufzeit (Min)": 30,
          "Status": "Aktiv",
      },
      {
          "Titel": "Grey's Anatomy",
          "Genre": "Drama",
          "Staffeln": 20,
          "Episoden pro Staffel": "24, 27, 25, 22, 24",
          "Laufzeit (Min)": 45,
          "Status": "Aktiv",
      },
      {
          "Titel": "Tagesschau",
          "Genre": "News",
          "Staffeln": 1,
          "Episoden pro Staffel": "365",
          "Laufzeit (Min)": 15,
          "Status": "Täglich (Daily)",
      },
  ])

if "schedule" not in st.session_state:
  st.session_state.schedule = pd.DataFrame(
      columns=[
          "Wochentag",
          "Startzeit",
          "Endzeit",
          "Format",
          "Genre",
          "Episode / Details",
          "Werbeblock (Min)",
          "Hinweis",
      ]
  )

# --- HAUPTMENÜ ---
st.sidebar.title("📡 Sender Management")
app_mode = st.sidebar.selectbox(
    "Navigation",
    [
        "🎬 Programm-Ansicht (Das Sendeband)",
        "⏱️ Master Control: Minutengenau planen",
        "🗄️ Detailliertes Archiv & Staffeln",
        "➕ Neues Format anlegen",
    ],
)

# ==========================================
# 1. PROGRAMM-ANSICHT (DAS SCHÖNE INTERFACE)
# ==========================================
if app_mode == "🎬 Programm-Ansicht (Das Sendeband)":
  st.title("📺 On-Air Programm-Übersicht")
  st.write(
      "Hier siehst du deinen Sendeplan in schön – sortiert nach Sendetagen und"
      " exakten Uhrzeiten, inklusive Werbezeiten."
  )

  if not st.session_state.schedule.empty:
    tag_filter = st.selectbox(
        "Wähle den Sendetag",
        [
            "Montag",
            "Dienstag",
            "Mittwoch",
            "Donnerstag",
            "Freitag",
            "Samstag",
            "Sonntag",
        ],
    )

    tages_plan = st.session_state.schedule[
        st.session_state.schedule["Wochentag"] == tag_filter
    ]

    if not tages_plan.empty:
      # Sortiere nach Startzeit
      tages_plan = tages_plan.sort_values(by="Startzeit")

      for index, row in tages_plan.iterrows():
        with st.container():
          col_zeit, col_info, col_ad = st.columns([1, 3, 1])
          with col_zeit:
            st.markdown(
                f"### **{row['Startzeit']} - {row['Endzeit']}**"
            )
            st.caption(f"Laufzeit: {row['Genre']}")
          with col_info:
            st.markdown(f"#### **{row['Format']}**")
            st.write(f"📌 *{row['Episode / Details']}*")
            if row["Hinweis"] != "OK":
              st.warning(row["Hinweis"])
          with col_ad:
            st.info(f"🟨 Werbung: {row['Werbeblock (Min)']} Min.")
          st.divider()
    else:
      st.info(
          f"Für den **{tag_filter}** ist noch kein Programm eingetragen. Nutze"
          " das Master Control, um Slots zu füllen!"
      )
  else:
    st.info("Dein Sender hat noch kein Programm. Starte im Master Control!")

# ==========================================
# 2. MASTER CONTROL: MINUTENGENAU PLANEN
# ==========================================
elif app_mode == "⏱️ Master Control: Minutengenau planen":
  st.title("⏱️ Master Control Room: Minutengenaue Sendeplanung")
  st.write(
      "Lege Startzeiten, Endzeiten und Werbeblöcke völlig frei fest – egal ob"
      " um 14:05 Uhr oder zur Primetime."
  )

  col1, col2 = st.columns([1, 1])

  with col1:
    st.subheader("Sendung platzieren")
    wochentag = st.selectbox(
        "Wochentag",
        [
            "Montag",
            "Dienstag",
            "Mittwoch",
            "Donnerstag",
            "Freitag",
            "Samstag",
            "Sonntag",
        ],
        key="mc_tag",
    )

    c_start1, c_start2 = st.columns(2)
    with c_start1:
      start_std = st.selectbox(
          "Start Stunde", [str(i).zfill(2) for i in range(24)], index=20
      )
    with c_start2:
      start_min = st.selectbox(
          "Start Minute", ["00", "05", "10", "15", "20", "25", "30", "35", "40", "45", "50", "55", "01", "02", "03", "04", "06", "07", "08", "09", "11", "12", "13", "14", "16", "17", "18", "19", "21", "22", "23", "24", "26", "27", "28", "29", "31", "32", "33", "34", "36", "37", "38", "39", "41", "42", "43", "44", "46", "47", "48", "49", "51", "52", "53", "54", "56", "57", "58", "59"]
      )

    c_end1, c_end2 = st.columns(2)
    with c_end1:
      end_std = st.selectbox(
          "Ende Stunde", [str(i).zfill(2) for i in range(24)], index=21
      )
    with c_end2:
      end_min = st.selectbox(
          "Ende Minute", ["00", "05", "10", "15", "20", "25", "30", "35", "40", "45", "50", "55", "01", "02", "03", "04", "06", "07", "08", "09", "11", "12", "13", "14", "16", "17", "18", "19", "21", "22", "23", "24", "26", "27", "28", "29", "31", "32", "33", "34", "36", "37", "38", "39", "41", "42", "43", "44", "46", "47", "48", "49", "51", "52", "53", "54", "56", "57", "58", "59"], index=2
      )

    aktive_formate = st.session_state.database["Titel"].tolist()
    format_wahl = st.selectbox(
        "Format", aktive_formate if aktive_formate else ["Keine"]
    )

    staffel_wahl = st.number_input(
        "Staffel", min_value=1, max_value=30, value=1
    )
    episode_wahl = st.number_input(
        "Episode", min_value=1, max_value=50, value=1
    )
    werbung_min = st.number_input(
        "Werbeblock-Anteil (Minuten)", min_value=0, max_value=30, value=4
    )

    special_wahl = st.selectbox(
        "Special Status", ["Regulär", "🎃 Halloween", "🎄 Weihnachten"]
    )

    if st.button("Ins Programm aufnehmen"):
      if format_wahl != "Keine":
        format_row = st.session_state.database[
            st.session_state.database["Titel"] == format_wahl
        ].iloc[0]

        start_str = f"{start_std}:{start_min}"
        end_str = f"{end_std}:{end_min}"

        aktueller_monat = datetime.datetime.now().month
        hinweis = "OK"
        if "Weihnachten" in special_wahl and aktueller_monat not in [11, 12]:
          hinweis = "⚠️ Weihnachts-Special im Sommer!"
        elif "Halloween" in special_wahl and aktueller_monat != 10:
          hinweis = "⚠️ Halloween-Special außerhalb des Oktobers!"

        ep_details = (
            f"Staffel {staffel_wahl}, Folge {episode_wahl} ({special_wahl})"
        )

        neuer_eintrag = pd.DataFrame({
            "Wochentag": [wochentag],
            "Startzeit": [start_str],
            "Endzeit": [end_str],
            "Format": [format_wahl],
            "Genre": [format_row["Genre"]],
            "Episode / Details": [ep_details],
            "Werbeblock (Min)": [werbung_min],
            "Hinweis": [hinweis],
        })
        st.session_state.schedule = pd.concat(
            [st.session_state.schedule, neuer_eintrag], ignore_index=True
        )
        st.success(
            f"'{format_wahl}' erfolgreich von {start_str} bis {end_str} Uhr"
            " eingeplant!"
        )

  with col2:
    st.subheader("Aktuelle Sendeplan-Tabelle")
    if not st.session_state.schedule.empty:
      st.dataframe(st.session_state.schedule, use_container_width=True)
      if st.button("Gesamten Sendeplan löschen"):
        st.session_state.schedule = pd.DataFrame(
            columns=[
                "Wochentag",
                "Startzeit",
                "Endzeit",
                "Format",
                "Genre",
                "Episode / Details",
                "Werbeblock (Min)",
                "Hinweis",
            ]
        )
        st.rerun()
    else:
      st.info("Noch keine Sendungen im Plan.")

# ==========================================
# 3. ARCHIV & 4. NEUES FORMAT
# ==========================================
elif app_mode == "🗄️ Detailliertes Archiv & Staffeln":
  st.title("🗄️ Sender-Archiv & Staffeln")
  edited_df = st.data_editor(
      st.session_state.database, use_container_width=True, num_rows="dynamic"
  )
  st.session_state.database = edited_df

elif app_mode == "➕ Neues Format anlegen":
  st.title("➕ Neues Format anlegen")
  with st.form("format_neu"):
    titel = st.text_input("Titel der Serie / Sendung")
    genre = st.selectbox(
        "Genre",
        ["Comedy", "Drama", "Krimi", "News", "Show / Quiz", "Reality", "Film"],
    )
    staffeln = st.number_input("Anzahl Staffeln", 1, 50, 1)
    ep_pro_staffel = st.text_input(
        "Episoden pro Staffel (z.B. 22, 20, 18)", "10, 10"
    )
    laufzeit = st.number_input("Standard-Laufzeit (Min)", 5, 240, 30)
    status = st.selectbox("Status", ["Aktiv", "Pausiert", "Abgeschlossen"])

    if st.form_submit_button("Speichern"):
      if titel:
        neue_zeile = pd.DataFrame({
            "Titel": [titel],
            "Genre": [genre],
            "Staffeln": [staffeln],
            "Episoden pro Staffel": [ep_pro_staffel],
            "Laufzeit (Min)": [laufzeit],
            "Status": [status],
        })
        st.session_state.database = pd.concat(
            [st.session_state.database, neue_zeile], ignore_index=True
        )
        st.success(f"'{titel}' wurde dem Archiv hinzugefügt!")
