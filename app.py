import datetime
import pandas as pd
import streamlit as st

# --- SEITENKONFIGURATION ---
st.set_page_config(
    page_title="Profi TV-Sender Master Control Room",
    page_icon="📺",
    layout="wide",
)

# --- INITIALISIERUNG DER GROSSEN TV-DATENBANK (TOP-FORMATE) ---
if "database" not in st.session_state:
  st.session_state.database = pd.DataFrame([
      {
          "Titel": "Tagesschau",
          "Genre": "News",
          "Staffeln": 1,
          "Episoden pro Staffel": "365",
          "Netto-Laufzeit (Min)": 15,
          "Status": "Täglich",
      },
      {
          "Titel": "Gute Zeiten, Schlechte Zeiten (GZSZ)",
          "Genre": "Daily Soap",
          "Staffeln": 34,
          "Episoden pro Staffel": "250",
          "Netto-Laufzeit (Min)": 24,
          "Status": "Täglich",
      },
      {
          "Titel": "Tatort",
          "Genre": "Krimi",
          "Staffeln": 50,
          "Episoden pro Staffel": "35",
          "Netto-Laufzeit (Min)": 88,
          "Status": "Aktiv",
      },
      {
          "Titel": "The Big Bang Theory",
          "Genre": "Comedy",
          "Staffeln": 12,
          "Episoden pro Staffel": "17, 23, 23, 24, 24, 24, 24, 24, 24, 24, 24, 24",
          "Netto-Laufzeit (Min)": 21,
          "Status": "Abgeschlossen",
      },
      {
          "Titel": "Hacks",
          "Genre": "Comedy",
          "Staffeln": 3,
          "Episoden pro Staffel": "10, 8, 9",
          "Netto-Laufzeit (Min)": 28,
          "Status": "Aktiv",
      },
      {
          "Titel": "Grey's Anatomy",
          "Genre": "Drama",
          "Staffeln": 20,
          "Episoden pro Staffel": "9, 27, 25, 22, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 20, 23, 10",
          "Netto-Laufzeit (Min)": 42,
          "Status": "Aktiv",
      },
      {
          "Titel": "Curb Your Enthusiasm",
          "Genre": "Comedy",
          "Staffeln": 12,
          "Episoden pro Staffel": "10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10",
          "Netto-Laufzeit (Min)": 30,
          "Status": "Abgeschlossen",
      },
      {
          "Titel": "Die Simpsons",
          "Genre": "Animation",
          "Staffeln": 35,
          "Episoden pro Staffel": "13, 22, 24, 22, 22, 25, 25, 25, 25, 23, 22, 21, 22, 22, 22, 21, 22, 22, 20, 21, 23, 22, 22, 22, 22, 21, 22, 21, 22, 23, 22, 22, 22, 22, 18",
          "Netto-Laufzeit (Min)": 21,
          "Status": "Aktiv",
      },
      {
          "Titel": "Warentest / Doku-Reihe",
          "Genre": "Doku",
          "Staffeln": 5,
          "Episoden pro Staffel": "10",
          "Netto-Laufzeit (Min)": 45,
          "Status": "Aktiv",
      },
      {
          "Titel": "heute-show",
          "Genre": "Comedy / News",
          "Staffeln": 15,
          "Episoden pro Staffel": "40",
          "Netto-Laufzeit (Min)": 42,
          "Status": "Aktiv",
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
          "Slot-Länge",
          "Netto",
          "Werbung (Min)",
          "Hinweis",
      ]
  )

# --- HAUPTMENÜ ---
st.sidebar.title("📡 Sender Management")
app_mode = st.sidebar.selectbox(
    "Navigation",
    [
        "🎬 Programm-Ansicht (Das Sendeband)",
        "⏱️ Master Control: Sendeplan & Werbung",
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
      "Dein tagesaktuelles Programm im professionellen Sender-Look – inklusive"
      " automatischer Werbezeiten-Berechnung."
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
      tages_plan = tages_plan.sort_values(by="Startzeit")

      for index, row in tages_plan.iterrows():
        with st.container():
          col_zeit, col_info, col_ad = st.columns([1, 3, 1])
          with col_zeit:
            st.markdown(
                f"### **{row['Startzeit']} - {row['Endzeit']}**"
            )
            st.caption(f"Genre: {row['Genre']}")
          with col_info:
            st.markdown(f"#### **{row['Format']}**")
            st.write(f"📌 *{row['Episode / Details']}*")
            if row["Hinweis"] != "OK":
              st.warning(row["Hinweis"])
          with col_ad:
            st.info(
                f"⏱️ Netto: {row['Netto']} Min.\n🟨 Werbung:"
                f" **{row['Werbung (Min)']} Min.**"
            )
          st.divider()
    else:
      st.info(
          f"Für den **{tag_filter}** ist noch kein Programm eingepflegt."
      )
  else:
    st.info("Dein Sender hat noch kein Programm.")

# ==========================================
# 2. MASTER CONTROL: MINUTENGENAU & WERBUNG
# ==========================================
elif app_mode == "⏱️ Master Control: Sendeplan & Werbung":
  st.title("⏱️ Master Control Room: Sendeplan & Automatische Werbung")
  st.write(
      "Wähle eine Sendung aus deinem Archiv. Das System kennt automatisch die"
      " echte Laufzeit und errechnet dir den Werbeblock für deinen"
      " Sende-Slot!"
  )

  col1, col2 = st.columns([1, 1])

  with col1:
    st.subheader("Sendung einplanen")
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

    aktive_formate = st.session_state.database["Titel"].tolist()
    format_wahl = st.selectbox(
        "Format aus Top-Archiv wählen",
        aktive_formate if aktive_formate else ["Keine"],
    )

    # Automatische Netto-Laufzeit des gewählten Formats holen
    format_row = st.session_state.database[
        st.session_state.database["Titel"] == format_wahl
    ].iloc[0]
    standard_netto = int(format_row["Netto-Laufzeit (Min)"])

    st.info(
        f"💡 Hinterlegte Netto-Laufzeit für '{format_wahl}':"
        f" **{standard_netto} Minuten**"
    )

    c_start1, c_start2 = st.columns(2)
    with c_start1:
      start_std = st.selectbox(
          "Start Stunde", [str(i).zfill(2) for i in range(24)], index=20
      )
    with c_start2:
      start_min = st.selectbox(
          "Start Minute",
          [
              "00",
              "05",
              "10",
              "15",
              "20",
              "25",
              "30",
              "35",
              "40",
              "45",
              "50",
              "55",
          ],
      )

    # Slot-Ende (z.B. volle 30 oder 60 Min)
    slot_laenge = st.selectbox(
        "Geplanter Sende-Slot (inkl. Werbung)", [15, 30, 45, 60, 90, 120], index=1
    )

    # Automatische Werbeberechnung: Slot-Länge minus Netto-Laufzeit
    berechnete_werbung = max(0, slot_laenge - standard_netto)

    st.success(
        f"🟨 Automatischer Werbeblock für diesen Slot:"
        f" **{berechnete_werbung} Minuten**"
    )

    staffel_wahl = st.number_input(
        "Staffel", min_value=1, max_value=50, value=1
    )
    episode_wahl = st.number_input(
        "Episode", min_value=1, max_value=300, value=1
    )
    special_wahl = st.selectbox(
        "Special Status", ["Regulär", "🎃 Halloween", "🎄 Weihnachten"]
    )

    if st.button("Ins Programm aufnehmen"):
      if format_wahl != "Keine":
        start_str = f"{start_std}:{start_min}"

        # Endzeit automatisch berechnen
        start_gesamt_min = int(start_std) * 60 + int(start_min)
        end_gesamt_min = start_gesamt_min + slot_laenge
        end_std_calc = str(end_gesamt_min // 60 % 24).zfill(2)
        end_min_calc = str(end_gesamt_min % 60).zfill(2)
        end_str = f"{end_std_calc}:{end_min_calc}"

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
            "Slot-Länge": [f"{slot_laenge} Min"],
            "Netto": [f"{standard_netto} Min"],
            "Werbung (Min)": [berechnete_werbung],
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
                "Slot-Länge",
                "Netto",
                "Werbung (Min)",
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
  st.title("🗄️ Top-Sender Archiv & Laufzeiten")
  edited_df = st.data_editor(
      st.session_state.database, use_container_width=True, num_rows="dynamic"
  )
  st.session_state.database = edited_df

elif app_mode == "➕ Neues Format anlegen":
  st.title("➕ Neues Format ins Top-Archiv aufnehmen")
  with st.form("format_neu"):
    titel = st.text_input("Titel der Serie / Sendung")
    genre = st.selectbox(
        "Genre",
        [
            "Comedy",
            "Drama",
            "Krimi",
            "News",
            "Daily Soap",
            "Animation",
            "Doku",
            "Film",
        ],
    )
    staffeln = st.number_input("Anzahl Staffeln", 1, 60, 1)
    ep_pro_staffel = st.text_input(
        "Episoden pro Staffel (z.B. 22, 22, 20)", "10, 10"
    )
    netto_laufzeit = st.number_input(
        "Netto-Laufzeit pro Folge (Minuten)", 5, 240, 22
    )
    status = st.selectbox("Status", ["Aktiv", "Täglich", "Abgeschlossen"])

    if st.form_submit_button("Speichern"):
      if titel:
        neue_zeile = pd.DataFrame({
            "Titel": [titel],
            "Genre": [genre],
            "Staffeln": [staffeln],
            "Episoden pro Staffel": [ep_pro_staffel],
            "Netto-Laufzeit (Min)": [netto_laufzeit],
            "Status": [status],
        })
        st.session_state.database = pd.concat(
            [st.session_state.database, neue_zeile], ignore_index=True
        )
        st.success(f"'{titel}' wurde erfolgreich im Archiv gespeichert!")
