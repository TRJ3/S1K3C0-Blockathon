
import express from 'express';
import cors from 'cors'; // Import cors
import { Nautilus, NautilusComputeAsset } from '@deltadao/nautilus';
import { loadConfig } from './config';
import 'dotenv/config';

const app = express();
app.use(express.json()); // Middleware, um JSON-Anfragen zu parsen
app.use(cors()); // Middleware, um Cross-Origin-Anfragen zu erlauben

// Dieser Endpunkt wird von Ihrer Python-App aufgerufen
app.post('/api/compute', async (req, res) => {
    try {
        const { prompt, algoDid } = req.body;

        if (!prompt || !algoDid) {
            return res.status(400).json({ error: 'Die Parameter "prompt" und "algoDid" sind erforderlich.' });
        }

        console.log(`[API-Server] Anfrage für Algorithmus ${algoDid} mit Prompt erhalten: "${prompt}"`);

        // 1. Nautilus initialisieren
        const config = await loadConfig();
        const nautilus = await Nautilus.create(config);

        // 2. Temporäres Input-Asset für den Prompt erstellen
        // Dies ist der beste Weg, um dynamische Eingaben an einen C2D-Job zu übergeben
        const tempInputAsset: NautilusComputeAsset = {
            type: 'url',
            files: [
                {
                    type: 'url',
                    url: `data:text/plain;charset=utf-8,${encodeURIComponent(prompt)}`,
                }
            ]
        };

        // 3. Compute-Job definieren
        const computeJobs = [{
            algo: {
                did: algoDid
            },
            input: [tempInputAsset],
            output: {}
        }];

        console.log('[API-Server] Starte Nautilus Compute-Job...');
        
        // 4. Compute-Job starten und auf Ergebnis warten
        // Hinweis: nautilus.compute() startet den Job und gibt eine Job-ID zurück.
        // Für ein einfaches Beispiel warten wir hier direkt auf das Ergebnis.
        // In einer echten Anwendung würden Sie den Job-Status pollen.
        const results = await nautilus.compute(computeJobs, nautilus.getAccountId(), undefined, 86400, 'v4');
        
        if (!results || results.length === 0) {
            throw new Error('Compute-Job hat keine Ergebnisse zurückgegeben.');
        }

        // 5. Ergebnis-URL abrufen und Inhalt herunterladen
        const resultUrl = results[0].url;
        const response = await fetch(resultUrl);
        const resultText = await response.text();

        console.log('[API-Server] Job erfolgreich. Sende Ergebnis zurück.');

        // 6. Ergebnis an den Python-Client zurücksenden
        res.json({ result: resultText });

    } catch (error) {
        console.error('[API-Server] Fehler bei der Verarbeitung der Anfrage:', error);
        res.status(500).json({ error: 'Fehler beim Ausführen des Nautilus-Jobs.', details: error.message });
    }
});

const port = process.env.NAUTILUS_PORT || 3001;
app.listen(port, () => {
    console.log(`[API-Server] Nautilus API Server läuft auf http://localhost:${port}`);
});
