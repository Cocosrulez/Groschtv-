<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sendeplan & Programm-Manager</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f7f6;
            color: #333;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: #fff;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }
        h1, h2 {
            color: #2c3e50;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            font-weight: 600;
            margin-bottom: 5px;
            font-size: 14px;
        }
        select, input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 14px;
            box-sizing: border-box;
        }
        .row {
            display: flex;
            gap: 15px;
        }
        .col {
            flex: 1;
        }
        button {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 12px 20px;
            font-size: 16px;
            border-radius: 6px;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
            font-weight: 600;
        }
        button:hover {
            background-color: #0056b3;
        }
        .output-box {
            margin-top: 25px;
            background: #e9ecef;
            padding: 15px;
            border-radius: 6px;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 13px;
        }
        .error {
            color: #d9534f;
            font-weight: bold;
            background: #fde8e8;
            padding: 10px;
            border-radius: 6px;
            margin-top: 15px;
        }
        .success {
            color: #28a745;
            font-weight: bold;
        }
    </style>
</head>
<body>

<div class="container">
    <h1>Sendeplan & Programm-Manager</h1>
    <p>Plane deine Serien mit automatischer Episoden-Prüfung und festen Sende-Slots (Daytime & Primetime).</p>

    <div class="row">
        <div class="col">
            <div class="form-group">
                <label for="serieSelect">Serie auswählen:</label>
                <select id="serieSelect" onchange="updateMaxEpisodes()">
                    <option value="Hacks">Hacks</option>
                    <option value="Grey's Anatomy">Grey's Anatomy</option>
                    <option value="Curb Your Enthusiasm">Curb Your Enthusiasm</option>
                </select>
            </div>
        </div>
        <div class="col">
            <div class="form-group">
                <label for="slotType">Sende-Slot:</label>
                <select id="slotType" onchange="adjustSlotTime()">
                    <option value="daytime">Daytime (Mo–Fr, standardmäßig 16:00 Uhr)</option>
                    <option value="primetime">Primetime (ab 20:00 Uhr)</option>
                </select>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col">
            <div class="form-group">
                <label for="seasonInput">Staffel:</label>
                <input type="number" id="seasonInput" value="1" min="1" onchange="updateMaxEpisodes()">
            </div>
        </div>
        <div class="col">
            <div class="form-group">
                <label for="episodeInput">Episode:</label>
                <input type="number" id="episodeInput" value="1" min="1">
                <small id="maxEpInfo" style="color: #666; font-size: 12px;"></small>
            </div>
        </div>
        <div class="col">
            <div class="form-group">
                <label for="startTimeInput">Startzeit:</label>
                <input type="time" id="startTimeInput" value="16:00">
            </div>
        </div>
    </div>

    <button onclick="addToSchedule()">Sendung einfügen (Mo–Fr Template)</button>

    <div id="messageArea"></div>

    <h2>Aktueller Sendeplan</h2>
    <div id="scheduleOutput" class="output-box">Noch keine Sendungen eingetragen.</div>
</div>

<script>
    // Integrierte Datenbank mit maximalen Staffeln und Episoden
    const serieDatabase = {
        "Hacks": {
            seasons: {
                1: { totalEpisodes: 10, duration: 30 },
                2: { totalEpisodes: 8, duration: 30 },
                3: { totalEpisodes: 9, duration: 30 }
            }
        },
        "Grey's Anatomy": {
            seasons: {
                1: { totalEpisodes: 9, duration: 43 },
                2: { totalEpisodes: 27, duration: 43 }
            }
        },
        "Curb Your Enthusiasm": {
            seasons: {
                1: { totalEpisodes: 10, duration: 30 },
                2: { totalEpisodes: 10, duration: 30 }
            }
        }
    };

    let weeklySchedule = [];

    function updateMaxEpisodes() {
        const serieName = document.getElementById("serieSelect").value;
        const seasonNum = parseInt(document.getElementById("seasonInput").value, 10);
        const serie = serieDatabase[serieName];
        const infoElem = document.getElementById("maxEpInfo");

        if (serie && serie.seasons[seasonNum]) {
            const maxEp = serie.seasons[seasonNum].totalEpisodes;
            infoElem.innerText = `Max. Episoden in Staffel ${seasonNum}: ${maxEp}`;
            document.getElementById("episodeInput").max = maxEp;
        } else {
            infoElem.innerText = "Staffel existiert nicht!";
            document.getElementById("episodeInput").max = 99;
        }
    }

    function adjustSlotTime() {
        const slotType = document.getElementById("slotType").value;
        const timeInput = document.getElementById("startTimeInput");
        if (slotType === "daytime") {
            timeInput.value = "16:00";
        } else {
            timeInput.value = "20:15";
        }
    }

    function calculateEndTime(startTime, durationMinutes) {
        const [hours, minutes] = startTime.split(":").map(Number);
        const totalMinutes = hours * 60 + minutes + durationMinutes;
        const endHours = Math.floor(totalMinutes / 60) % 24;
        const endMinutes = totalMinutes % 60;
        return `${String(endHours).padStart(2, '0')}:${String(endMinutes).padStart(2, '0')}`;
    }

    function addToSchedule() {
        const messageArea = document.getElementById("messageArea");
        messageArea.innerHTML = "";

        const serieName = document.getElementById("serieSelect").value;
        const seasonNum = parseInt(document.getElementById("seasonInput").value, 10);
        const episodeNum = parseInt(document.getElementById("episodeInput").value, 10);
        const startTime = document.getElementById("startTimeInput").value;
        const slotType = document.getElementById("slotType").value;

        // --- VALIDIERUNG (Dein Kernwunsch) ---
        const serie = serieDatabase[serieName];
        if (!serie || !serie.seasons[seasonNum]) {
            messageArea.innerHTML = `<div class="error">Fehler: Staffel ${seasonNum} für "${serieName}" existiert nicht!</div>`;
            return;
        }

        const seasonData = serie.seasons[seasonNum];
        if (episodeNum < 1 || episodeNum > seasonData.totalEpisodes) {
            messageArea.innerHTML = `<div class="error">Fehler: Episode ${episodeNum} ist ungültig! Staffel ${seasonNum} von "${serieName}" hat maximal ${seasonData.totalEpisodes} Episoden.</div>`;
            return;
        }

        const duration = seasonData.duration;
        const endTime = calculateEndTime(startTime, duration);
        const slotLabel = slotType === "daytime" ? "Daytime (bis 20:00)" : "Primetime (ab 20:00)";

        // --- MO-FR TEMPLATE GENERIERUNG ---
        const days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"];
        let currentEp = episodeNum;

        days.forEach(day => {
            // Prüfen ob die fortlaufende Episode für den Wochentag noch im Rahmen ist
            if (currentEp <= seasonData.totalEpisodes) {
                weeklySchedule.push({
                    day: day,
                    slot: slotLabel,
                    serie: serieName,
                    season: seasonNum,
                    episode: currentEp,
                    time: `${startTime} - ${endTime}`
                });
                currentEp++;
            }
        });

        messageArea.innerHTML = `<div class="success">Erfolgreich als Mo-Fr Template eingetragen!</div>`;
        renderSchedule();
    }

    function renderSchedule() {
        const output = document.getElementById("scheduleOutput");
        if (weeklySchedule.length === 0) {
            output.innerText = "Noch keine Sendungen eingetragen.";
            return;
        }

        let text = "";
        weeklySchedule.forEach(item => {
            text += `[${item.day}] ${item.slot} | ${item.time} Uhr -> ${item.serie} (S${item.season}E${item.episode})\n`;
        });
        output.innerText = text;
    }

    // Initialisierung beim Laden
    updateMaxEpisodes();
</script>

</body>
</html>
