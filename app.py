// ==========================================
// SENDER- & PROGRAMM-MANAGER (UPDATE 2026)
// ==========================================

// Beispiel-Datenbank für Serien inklusive max. Staffeln und Episoden pro Staffel
const serieDatabase = {
    "Hacks": {
        seasons: {
            1: { totalEpisodes: 10, defaultDurationMinutes: 30 },
            2: { totalEpisodes: 8, defaultDurationMinutes: 30 },
            3: { totalEpisodes: 9, defaultDurationMinutes: 30 }
        }
    },
    "Grey's Anatomy": {
        seasons: {
            1: { totalEpisodes: 9, defaultDurationMinutes: 43 },
            2: { totalEpisodes: 27, defaultDurationMinutes: 43 }
            // Erweiterbar...
        }
    }
};

/**
 * Validiert die Eingabe und berechnet Sendezeiten (Daytime vs. Primetime Logik)
 */
function validateAndScheduleEpisode(serieName, seasonNum, episodeNum, startTimeStr, isPrimetimeSlot = false) {
    const serie = serieDatabase[serieName];
    
    if (!serie) {
        return { success: false, error: `Serie "${serieName}" ist nicht in der Datenbank vorhanden.` };
    }

    const season = serie.seasons[seasonNum];
    if (!season) {
        return { success: false, error: `Staffel ${seasonNum} existiert für ${serieName} nicht. (Max. Staffel: ${Object.keys(serie.seasons).length})` };
    }

    if (episodeNum < 1 || episodeNum > season.totalEpisodes) {
        return { 
            success: false, 
            error: `Ungültige Episode ${episodeNum}. Staffel ${seasonNum} von ${serieName} hat maximal ${season.totalEpisodes} Episoden.` 
        };
    }

    const duration = season.defaultDurationMinutes;
    const endTimeStr = calculateEndTime(startTimeStr, duration);

    // Slot-Validierung (Daytime bis 20:00 Uhr / Primetime ab 20:00 Uhr)
    const startHour = parseInt(startTimeStr.split(":")[0], 10);
    const targetSlot = startHour >= 20 ? "Primetime (ab 20:00)" : "Daytime (bis 20:00)";

    return {
        success: true,
        data: {
            serie: serieName,
            season: seasonNum,
            episode: episodeNum,
            durationMinutes: duration,
            startTime: startTimeStr,
            endTime: endTimeStr,
            slotType: targetSlot
        }
    };
}

/**
 * Hilfsfunktion zur Endzeit-Berechnung
 */
function calculateEndTime(startTime, durationMinutes) {
    const [hours, minutes] = startTime.split(":").map(Number);
    const totalMinutes = hours * 60 + minutes + durationMinutes;
    const endHours = Math.floor(totalMinutes / 60) % 24;
    const endMinutes = totalMinutes % 60;
    return `${String(endHours).padStart(2, '0')}:${String(endMinutes).padStart(2, '0')}`;
}

/**
 * Wochentag-Template-Generator (Mo-Fr Automatik für wiederkehrende Slots)
 */
function generateWeeklyTemplate(serieName, seasonNum, startEpisodeNum, startTime = "16:00") {
    const days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"];
    const schedulePlan = {};
    
    let currentEpisode = startEpisodeNum;

    days.forEach(day => {
        const result = validateAndScheduleEpisode(serieName, seasonNum, currentEpisode, startTime);
        if (result.success) {
            schedulePlan[day] = result.data;
            currentEpisode++; // Automatatzug für den nächsten Wochentag
        } else {
            schedulePlan[day] = { error: result.error };
        }
    });

    return schedulePlan;
}
