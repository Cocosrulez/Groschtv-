import pandas as pd
import streamlit as st

# --- SEITENKONFIGURATION ---
st.set_page_config(
    page_title="TV-Sender & Streaming Management",
    page_icon="📺",
    layout="wide",
)

# --- INITIALISIERUNG DER TESTDATEN (DATENBANK) ---
if "database" not in st.session_state:
  st.session_state.database = pd.DataFrame([
      {
          "Titel": "Hacks",
          "Genre": "Comedy",
          "Staffeln": 3,
          "Episoden gesamt": 26,
          "Laufzeit (Min)": 30,
          "Status": "Aktiv",
      },
      {
          "Titel": "Grey's Anatomy",
          "Genre": "Drama",
          "Staffeln": 20,
          "Episoden gesamt": 420,
          "Laufzeit (Min)": 45,
          "Status": "Aktiv",
      },
      {
          "Titel": "Curb Your Enthusiasm",
          "Genre": "Comedy",
          "Staffeln": 12,
          "Episoden gesamt": 120,
          "Laufzeit (Min)": 30,
          "Status": "Abgeschlossen",
      },
      {
          "Titel": "Tagesschau",
          "Genre": "News",
          "Staffeln": 1,
          "Episoden gesamt": 365,
          "Laufzeit (Min)": 15,
          "Status": "Aktiv",
      },
      {
          "Titel": "Tatort",
          "Genre": "Krimi",
          "Staffeln": 1,
          "Episoden gesamt": 35,
          "Laufzeit (Min)": 90,
          "Status": "Aktiv",
      },
  ])

if "schedule" not in st.session_state:
  st.session_state.schedule = pd.DataFrame(
      columns=["Wochentag", "Sendeplatz", "Format", "Genre", "Laufzeit"]
  )

# --- HAUPTMENÜ ---
st.sidebar.title("📡 Sender Management")
app_mode = st.sidebar.selectbox(
    "Navigation",
    ["Sendeplan (Master Control)", "Datenbank / Archiv", "Neues Format anlegen"],
)

# ==========================================
# 1. SENDEPLAN (MASTER CONTROL)
# ==========================================
if app_mode == "Sendeplan (Master Control)":
  st.title("🎬 Master Control Room: Sendeplan")
  st.write(
      "Plane hier das lineare Programm deines Senders nach klassischen"
      " Blöcken."
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
            "Early Daytime (14:00)",
            "Access Prime (18:00)",
            "News (20:00)",
            "Primetime (20:15)",
            "Late Prime (22:15)",
            "Late Night (23:30)",
        ],
    )

    aktive_formate = st.session_state.database["Titel"].tolist()
    ausgewähltes_format = st.selectbox(
        "Format auswählen", aktive_formate if aktive_formate else ["Keine"]
    )

    if st.button("Ins Programm nehmen"):
      if ausgewähltes_format != "Keine":
        format_row = st.session_state.database[
            st.session_state.database["Titel"] == ausgewähltes_format
        ].iloc[0]
        neuer_eintrag = pd.DataFrame({
            "Wochentag": [wochentag],
            "Sendeplatz": [sendeplatz],
            "Format": [ausgewähltes_format],
            "Genre": [format_row["Genre"]],
            "Laufzeit": [format_row["Laufzeit (Min)"]],
        })
        st.session_state.schedule = pd.concat(
            [st.session_state.schedule, neuer_eintrag], ignore_index=True
        )
        st.success(f"'{ausgewähltes_format}' erfolgreich eingeplant!")

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

      if st.button("Sendeplan für diesen Tag zurücksetzen"):
        st.session_state.schedule = pd.DataFrame(
            columns=["Wochentag", "Sendeplatz", "Format", "Genre", "Laufzeit"]
        )
        st.rerun()
    else:
      st.info(
          "Dein Sendeplan ist noch leer. Füge links deine ersten Sendungen"
          " hinzu!"
      )

# ==========================================
# 2. DATENBANK / ARCHIV
# ==========================================
elif app_mode == "Datenbank / Archiv":
  st.title("🗄️ Sender-Archiv & Datenbank")
  st.write(
      "Hier siehst du alle verfügbaren Formate. Du kannst die Tabelle direkt"
      " bearbeiten (z.B. Staffeln anpassen oder Status ändern)."
  )

  edited_df = st.data_editor(
      st.session_state.database, use_container_width=True, num_rows="dynamic"
  )
  st.session_state.database = edited_df

# ==========================================
# 3. NEUES FORMAT ANLEGEN
# ==========================================
elif app_mode == "Neues Format anlegen":
  st.title("➕ Neues Format ins Archiv aufnehmen")

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
        "Anzahl Staffeln", min_value=1, max_value=50, value=1
    )
    episoden = st.number_input(
        "Episoden gesamt", min_value=1, max_value=1000, value=10
    )
    laufzeit = st.number_input(
        "Laufzeit pro Folge (Minuten)", min_value=5, max_value=240, value=30
    )
    status = st.selectbox(
        "Status", ["Aktiv", "Pausiert", "Abgeschlossen", "Abgesetzt"]
    )

    submitted = st.form_submit_button("Format speichern")
    if submitted:
      if titel:
        neue_zeile = pd.DataFrame({
            "Titel": [titel],
            "Genre": [genre],
            "Staffeln": [staffeln],
            "Episoden gesamt": [episoden],
            "Laufzeit (Min)": [laufzeit],
            "Status": [status],
        })
        st.session_state.database = pd.concat(
            [st.session_state.database, neue_zeile], ignore_index=True
        )
        st.success(
            f"Format '{titel}' wurde erfolgreich zur Datenbank hinzugefügt!"
        )
      else:
        st.error("Bitte gib mindestens einen Titel ein.")
