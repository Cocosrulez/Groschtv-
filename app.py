import datetime
import pandas as pd
import streamlit as st

# --- SEITENKONFIGURATION ---
st.set_page_config(
    page_title="Profi TV-Sender Master Control",
    page_icon="📺",
    layout="wide",
)

# --- INITIALISIERUNG DER ERWEITERTEN DATENBANK ---
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
          "Episoden pro Staffel": "24, 27, 25, 22, 24, 11, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 20, 23, 10",
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
          "Sendeplatz",
          "Format",
          "Genre",
          "Laufzeit",
          "Aktuelle Episode",
          "Hinweis",
      ]
  )

# --- HAUPTMENÜ ---
st.sidebar.title("📡 Sender Management")
app_mode = st.sidebar.selectbox(
    "Navigation",
    [
        "Sendeplan (Master Control)",
        "Detailliertes Archiv & Staffeln",
        "Neues Format anlegen",
    ],
)

# ==========================================
# 1. SENDEPLAN (MASTER CONTROL)
# ==========================================
if app_mode == "Sendeplan (Master Control)":
  st.title("🎬 Master Control Room: Profi-Sendeplan")
  st.write(
      "Plane dein Programm. Das System trackt automatisch die Episoden und"
      " warnt bei saisonalen Konflikten."
  )

  col1, col2 = st.columns([1, 2])

  with col1:
    st.subheader("Sendeplatz belegen")
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
    )
    sendeplatz = st.selectbox(
        "Sende-Block / Uhrzeit",
        [
            "Daytime (14:00)",
            "Access Prime (18:00)",
            "News / Info (20:00)",
            "Primetime (20:15)",
            "Late Prime (22:15)",
            "Late Night (23:30)",
        ],
    )

    aktive_formate = st.session_state.database["Titel"].tolist()
    ausgewähltes_format = st.selectbox(
        "Format auswählen", aktive_formate if aktive_formate else ["Keine"]
    )

    # Zusatzeinstellungen für die Episode
    staffel_wahl = st.number_input(
        "Welche Staffel?", min_value=1, max_value=30, value=1
    )
    episoden_wahl = st.number_input(
        "Welche Episodennummer?", min_value=1, max_value=50, value=1
    )

    special_typ = st.selectbox(
        "Special / Feiertagsepisode?",
        ["Kein Special", "🎃 Halloween-Special", "🎄 Weihnachts-Special"],
    )

    if st.button("Ins Programm nehmen"):
      if ausgewähltes_format != "Keine":
        format_row = st.session_state.database[
            st.session_state.database["Titel"] == ausgewähltes_format
        ].iloc[0]

        # Logik-Check: Monat vs. Special
        aktueller_monat = datetime.datetime.now().month
        hinweis = "OK"

        if "Weihnachts" in special_typ and aktueller_monat not in [11, 12]:
          hinweis = f"⚠️ Achtung: Weihnachts-Special im Monat {aktueller_monat} (Sommer/Frühling)!"
        elif "Halloween" in special_typ and aktueller_monat != 10:
          hinweis = (
              f"⚠️ Achtung: Halloween-Special im Monat {aktueller_monat}!"
          )

        ep_anzeige = f"Staffel {staffel_wahl}, Folge {episoden_wahl}"
        if special_typ != "Kein Special":
          ep_anzeige += f" ({special_typ})"

        neuer_eintrag = pd.DataFrame({
            "Wochentag": [wochentag],
            "Sendeplatz": [sendeplatz],
            "Format": [ausgewähltes_format],
            "Genre": [format_row["Genre"]],
            "Laufzeit": [format_row["Laufzeit (Min)"]],
            "Aktuelle Episode": [ep_anzeige],
            "Hinweis": [hinweis],
        })
        st.session_state.schedule = pd.concat(
            [st.session_state.schedule, neuer_eintrag], ignore_index=True
        )
        st.success(f"'{ausgewähltes_format}' ({ep_anzeige}) eingeplant!")

  with col2:
    st.subheader("Aktueller Programm-Überblick")
    if not st.session_state.schedule.empty:
      filter_tag = st.selectbox(
          "Ansicht für Tag filtern",
          [
              "Alle",
              "Montag",
              "Dienstag",
              "Mittwoch",
              "Donnerstag",
              "Freitag",
              "Samstag",
              "Sonntag",
          ],
      )

      display_df = st.session_state.schedule
      if filter_tag != "Alle":
        display_df = display_df[display_df["Wochentag"] == filter_tag]

      st.dataframe(display_df, use_container_width=True)

      if st.button("Sendeplan komplett zurücksetzen"):
        st.session_state.schedule = pd.DataFrame(
            columns=[
                "Wochentag",
                "Sendeplatz",
                "Format",
                "Genre",
                "Laufzeit",
                "Aktuelle Episode",
                "Hinweis",
            ]
        )
        st.rerun()
    else:
      st.info("Dein Sendeplan ist noch leer.")

# ==========================================
# 2. DETAILLIERTES ARCHIV & STAFFELN
# ==========================================
elif app_mode == "Detailliertes Archiv & Staffeln":
  st.title("🗄️ Detailliertes Sender-Archiv")
  st.write(
      "Hier siehst du alle Formate mit ihren flexiblen Staffellängen und"
      " Episodenstrukturen. Du kannst die Tabelle direkt anpassen."
  )

  edited_df = st.data_editor(
      st.session_state.database, use_container_width=True, num_rows="dynamic"
  )
  st.session_state.database = edited_df

# ==========================================
# 3. NEUES FORMAT ANLEGEN
# ==========================================
elif app_mode == "Neues Format anlegen":
  st.title("➕ Neues Format mit Episodenstruktur anlegen")

  with st.form("neues_format_form"):
    titel = st.text_input("Titel der Serie / Sendung")
    genre = st.selectbox(
        "Genre",
        [
            "Comedy",
            "Drama",
            "Krimi",
            "News",
            "Show / Quiz",
            "Doku",
            "Reality",
            "Film",
        ],
    )
    staffeln = st.number_input(
        "Anzahl Staffeln gesamt", min_value=1, max_value=50, value=1
    )
    ep_pro_staffel = st.text_input(
        "Episoden pro Staffel (kommagetrennt, z.B. 22, 22, 20)",
        value="10, 10",
    )
    laufzeit = st.number_input(
        "Laufzeit pro Folge (Minuten)", min_value=5, max_value=240, value=30
    )
    status = st.selectbox(
        "Status / Ausstrahlung",
        ["Aktiv", "Täglich (Daily)", "Pausiert", "Abgeschlossen", "Abgesetzt"],
    )

    submitted = st.form_submit_button("Format ins Archiv aufnehmen")
    if submitted:
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
        st.success(f"Format '{titel}' erfolgreich mit Episodenstruktur angelegt!")
      else:
        st.error("Bitte gib einen Titel ein.")
