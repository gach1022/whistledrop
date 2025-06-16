## 🚀 Schnellstart

### 1. Container bauen und starten

Voraussetzung: [Docker](https://www.docker.com/) ist installiert.

```bash
docker compose up -d --build
```

### 2. Tabellen anlegen
Führe die Migration aus um die Tabellen in der DB anzulegen
```bash
sudo docker exec -it whistledrop-backend-1 bash
cd /app
pyhton migrations.py
```

### 3. Schlüssel generieren

Erzeuge die nötigen RSA-Keypaare (Public/Private Keys) für die Verschlüsselung.  
Vorher: Stelle sicher, dass die Datenbank-Container laufen!

```bash
python generate_keys.py
```

### 4. Frontend besuchen & Datei hochladen

- Rufe das **Frontend** im Browser auf:  
  [http://localhost:8080](http://localhost:8080)
- Wähle eine Datei aus und lade sie hoch.

### 5. Im Backend Datei herunterladen

- Öffne das **Backend** im Browser:  
  [http://localhost:5000/](http://localhost:5000/)
- Hier siehst du die Upload-Tabelle mit allen hochgeladenen (verschlüsselten) Dateien.
- Lade die gewünschte Datei über "Download" herunter.

### 6. Datei lokal entschlüsseln

1. Lege das Skript `decrypt_file.py` in ein beliebiges Verzeichnis auf deinem Rechner.
2. Stelle sicher, dass du Zugriff auf beide Datenbanken hast (ServerDB & JournalistDB, Zugangsdaten ggf. im Skript anpassen).
3. Installiere benötigte Pakete (falls noch nicht geschehen):

   ```bash
   pip install cryptography psycopg2-binary
   ```
4. Führe das Skript mit dem Pfad zur verschlüsselten Datei aus, z.B.:

    ```bash
    python decrypt_file.py "C:/Users/DeinName/Downloads/Dateiname.pdf.encrypted"
    ```

### Demo
[📹 Video ansehen](\Demo\Demo_Whistledrop.mp4)
