import os
import pandas as pd
import streamlit as st

# Datei, in der die Daten dauerhaft abgelegt werden
DATA_FILE = "gespeicherte_daten.csv"


# 1. Funktion zum Laden der Daten beim Start
def lade_daten():
  if os.path.exists(DATA_FILE):
    return pd.read_csv(DATA_FILE)
  else:
    # Hier definierst du deine Start-Spalten, falls noch keine Datei da ist
    return pd.DataFrame(columns=["Eingabe", "Ergebnis"])


# Daten in die Session State laden, damit sie flüssig im Programm bleiben
if "data" not in st.session_state:
  st.session_state.data = lade_daten()

st.title("Meine Streamlit-App mit dauerhaftem Speicher")

# 2. Deine Eingabefelder (Beispiel)
neue_eingabe = st.text_input("Gib hier deinen Text/Code ein:")
neues_ergebnis = st.text_input("Ergebnis dazu:")

# 3. Speicher-Button, damit die Änderung sofort in die Datei geschrieben wird
if st.button("Änderung direkt speichern"):
  if neue_eingabe:
    # Neue Zeile anfügen
    neue_zeile = pd.DataFrame(
        {"Eingabe": [neue_eingabe], "Ergebnis": [neues_ergebnis]}
    )
    st.session_state.data = pd.concat(
        [st.session_state.data, neue_zeile], ignore_index=True
    )

    # Direkt auf der Festplatte speichern (das ist der "fortlaufende" Teil)
    st.session_state.data.to_csv(DATA_FILE, index=False)
    st.success("Erfolgreich dauerhaft gespeichert!")
  else:
    st.warning("Bitte fülle mindestens die Eingabe aus.")

# 4. Anzeige der bisher dauerhaft gespeicherten Daten
st.subheader("Bisherige gespeicherte Einträge:")
st.dataframe(st.session_state.data)
