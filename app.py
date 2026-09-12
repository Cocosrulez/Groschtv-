from datetime import datetime, timedelta

class ProgramSchema:
    def __init__(self, start_time: str = "20:15"):
        # Startzeit des Programms als datetime-Objekt für die Berechnung
        try:
            self.current_time = datetime.strptime(start_time, "%H:%M")
        except ValueError:
            # Fallback, falls das Format mal abweichen sollte
            self.current_time = datetime.strptime("20:15", "%H:%M")
        
        self.schedule = []

    def add_broadcast(self, title: str, duration_minutes: int, episodes: int = 1):
        """
        Fügt eine Sendung oder direkt mehrere Episoden hinzu
        und verknüpft sie automatisch mit der richtigen Start- und Endzeit.
        """
        for i in range(episodes):
            start_str = self.current_time.strftime("%H:%M")
            
            # Endzeit berechnen
            end_time = self.current_time + timedelta(minutes=duration_minutes)
            end_str = end_time.strftime("%H:%M")
            
            # Titel bei mehreren Episoden automatisch durchnummerieren
            display_title = f"{title} (Folge {i+1})" if episodes > 1 else title
            
            # Zum Schema hinzufügen
            self.schedule.append({
                "time": f"{start_str} - {end_str}",
                "title": display_title,
                "duration": duration_minutes
            ))
            
            # Die aktuelle Zeit für den nächsten Eintrag weitersetzen
            self.current_time = end_time

    def show_schema(self):
        print("\n" + "="*40)
        print(" DEIN PROGRAMMSCHEMA")
        print("="*40)
        if not self.schedule:
            print("Das Schema ist noch leer.")
        else:
            for item in self.schedule:
                print(f"[{item['time']}]  {item['title']}  ({item['duration']} Min.)")
        print("="*40 + "\n")


# --- Ausführung des Programms ---
if __name__ == "__main__":
    # 1. Schema initialisieren (Start um 20:15 Uhr)
    mein_schema = ProgramSchema(start_time="20:15")

    # 2. Sendungen und mehrere Episoden hinzufügen
    mein_schema.add_broadcast("Tagesschau", 15)
    mein_schema.add_broadcast("Hacks", 30, episodes=3)  # Fügt automatisch 3 Folgen ein!
    mein_schema.add_broadcast("Late-Night Movie", 110)

    # 3. Ergebnis anzeigen
    mein_schema.show_schema()
