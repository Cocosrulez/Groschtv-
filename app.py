from datetime import datetime, timedelta

class ProgramSchema:
    def __init__(self, start_date: str = "20:15"):
        # Startzeit des Programms als datetime-Objekt für den heutigen Tag
        self.current_time = datetime.strptime(start_date, "%H:%M")
        self.schedule = []

    def add_broadcast(self, title: str, duration_minutes: int, episodes: int = 1):
        """
        Fügt eine Sendung oder mehrere Episoden einer Serie hinzu 
        und berechnet die Zeiten automatisch durch.
        """
        for i in range(episodes):
            start_str = self.current_time.strftime("%H:%M")
            
            # Endzeit berechnen
            end_time = self.current_time + timedelta(minutes=duration_minutes)
            end_str = end_time.strftime("%H:%M")
            
            # Bei mehreren Episoden den Titel optional durchnummerieren
            display_title = f"{title} (Folge {i+1})" if episodes > 1 else title
            
            # Eintrag zum Schema hinzufügen
            self.schedule.append({
                "time": f"{start_str} - {end_str}",
                "title": display_title,
                "duration": duration_minutes
            })
            
            # Die aktuelle Zeit für die nächste Sendung/Episode aktualisieren
            self.current_time = end_time

    def show_schema(self):
        print("\n--- Aktuelles Programmschema ---")
        if not self.schedule:
            print("Das Schema ist noch leer.")
            return
            
        for item in self.schedule:
            print(f"[{item['time']}] {item['title']} ({item['duration']} Min.)")
        print("-" * 32)


# --- Beispiel-Nutzung ---
if __name__ == "__main__":
    # Schema startet um 20:15 Uhr (Prime Time)
    schema = ProgramSchema(start_date="20:15")

    # 1. Eine Nachrichtensendung (15 Minuten)
    schema.add_broadcast("Tagesschau", 15)

    # 2. Direkt 3 Folgen einer Serie (z.B. Hacks oder Grey's Anatomy) à 50 Minuten einplanen
    schema.add_broadcast("Hacks", 50, episodes=3)

    # 3. Ein Film zum Ausklang
    schema.add_broadcast("Late-Night Movie", 110)

    # Schema ausgeben
    schema.show_schema()
