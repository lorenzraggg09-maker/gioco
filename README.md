# GIOCARE CON UN AMICO — GUIDA COMPLETA

Questa cartella contiene un server WebSocket (`prova_server.py`) e un client Pygame (`prova_client.py`) per giocare in due su rete LAN o Internet.

Questa guida raccoglie tutti i passaggi, comandi e suggerimenti per avviare una partita con un amico.

---

Requisiti
- Python 3.8+ installato sul computer che esegue server e client
- I file del progetto (inclusi asset: `freccia_sinistra.png`, `freccia_sotto.png`, `freccia_sopra.png`, `freccia_destra.png`, `goku_GIOCO.png`)
- Connessione di rete fra i due computer (LAN o Internet)
- Dipendenze: `pygame`, `websockets` (elencate in `requirements.txt`)

1) Preparazione — installare le dipendenze
- Apri PowerShell nella cartella del progetto (dove sono `prova_server.py` e `prova_client.py`).
- Esegui:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

2) Avviare il server (sulla macchina che ospita la partita)
- Sul computer che farà da server apri PowerShell nella cartella del progetto ed esegui:

```powershell
python prova_server.py
```

Il server ascolterà sulla porta TCP `8765` per default e stamperà in console qualcosa come:
```
Server starting on ws://0.0.0.0:8765
```

3) Trovare l'indirizzo IP del server (LAN)
- Su Windows, apri PowerShell e esegui:

```powershell
ipconfig
```

- Prendi l'indirizzo `IPv4` della scheda di rete attiva (es. `192.168.1.42`) e condividilo con il tuo amico.

4) Aprire la porta nel firewall del server (Windows)
- Se il firewall blocca la porta, permettila con:

```powershell
netsh advfirewall firewall add rule name="GiocoProva8765" dir=in action=allow protocol=TCP localport=8765
```

5) (Opzionale) Port forwarding se vuoi giocare via Internet
- Se i giocatori non sono nella stessa LAN, sul router del server devi inoltrare la porta TCP `8765` all'IP locale del server.
- Accedi alla pagina di configurazione del router (es. `http://192.168.1.1`) e cerca "Port Forwarding" o "NAT".
- Regola:
    - Porta pubblica: 8765
    - Protocollo: TCP
    - IP locale: l'IPv4 del server (es. `192.168.1.42`)
    - Porta locale: 8765

- Ottieni l'IP pubblico (chiami il sito https://ifconfig.me o digiti "what is my ip" su un motore di ricerca) e dallo al tuo amico.

Nota: i menu e i nomi delle impostazioni variano per modello di router.

6) Avviare il client (ogni giocatore)
- Sul PC del giocatore, apri PowerShell nella cartella del progetto e lancia:

```powershell
python prova_client.py --host <IP_SERVER>
```

- Sostituisci `<IP_SERVER>` con `localhost` (se stai testando tutto sulla stessa macchina), l'IP LAN del server (es. `192.168.1.42`) o l'IP pubblico del router (se hai fatto il port forwarding).
- Alla richiesta, inserisci il nome del giocatore.

7) Test locale rapido (tutto sulla stessa macchina)
- Apri 3 terminali:
    - Terminale A (server): `python prova_server.py`
    - Terminale B (client 1): `python prova_client.py --host localhost`
    - Terminale C (client 2): `python prova_client.py --host localhost`

- I client mostreranno "In attesa dell'altro giocatore..." finché non si connettono 2 giocatori; poi partirà la traccia sincronizzata.

Comandi rapidi da condividere con un amico
- Installa dipendenze (una volta sola):

```powershell
python -m pip install -r requirements.txt
```
- Avvia client (sostituisci `IP_SERVER`):

```powershell
python prova_client.py --host IP_SERVER
```

Controlli e tasti
- Giocatore 1: `W` (up), `A` (left), `S` (down), `D` (right) — mappati come nel client
- Giocatore 2: tasti freccia

Problemi comuni e soluzioni
- Errore "No module named 'websockets'": esegui `python -m pip install -r requirements.txt`.
- Connessione rifiutata / timeout: verifica che `prova_server.py` sia in esecuzione e che l'IP/porta siano corretti.
- Avversario non si connette / disconnessione: assicurati che la porta 8765 sia aperta sul firewall e che il router inoltri la porta se necessario.
- Asset mancanti (immagini non caricate): copia i file immagine nella cartella del progetto.

Consigli avanzati (facoltativi)
- Se giochi su Internet e hai IP dinamico, considera un servizio di Dynamic DNS (es. DuckDNS) per evitare di condividere l'IP pubblico ogni volta.
- Se vuoi che il server sia sempre disponibile, puoi avviarlo come servizio o usare `nohup` / `screen` / eseguibile Windows per tenerlo in background.

Se vuoi, genero una versione "solo comandi" da copiare e inviare agli amici, oppure ti aiuto a configurare il port forwarding se mi dici il modello del router.

---

Problema noto: PowerShell blocca l'attivazione del venv (.ps1)

Su alcune installazioni Windows PowerShell impedisce l'esecuzione di script (.ps1) e quindi l'attivazione del venv fallisce con un errore riguardante `Activate.ps1`.
Ecco tre soluzioni pratiche; usa quella che preferisci:

1) Avviare il server direttamente con il Python dentro il venv (nessuna attivazione richiesta):

```powershell
& 'C:\Users\hp\Desktop\gioco\gioco\.venv\Scripts\python.exe' -u prova_server.py
```

2) Abilitare gli script per l'utente (persistente, raccomandato se ti fidi della macchina):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
. .\.venv\Scripts\Activate.ps1
python -u prova_server.py
```

3) Bypass temporaneo (solo per la sessione corrente):

```powershell
PowerShell -ExecutionPolicy Bypass -NoProfile -Command "& '.\\.venv\\Scripts\\Activate.ps1'; python -u prova_server.py"
```

Se preferisci usare il prompt `cmd.exe` al posto di PowerShell puoi attivare il venv con:

```cmd
.venv\Scripts\activate.bat
python -u prova_server.py
```

Se vuoi, sostituisco i percorsi con il path esatto del tuo venv oppure aggiungo una riga "solo comandi" da inviare ai tuoi amici.

---

Verifica rapida del server (test)

Ho incluso uno script di test leggero `test_ws_client.py` nella cartella del progetto. Serve a verificare che il server WebSocket risponda correttamente.

Esegui sullo stesso computer del server:

```powershell
c:\Users\hp\Desktop\gioco\gioco\.venv\Scripts\python.exe test_ws_client.py
```

Output atteso (esempio):

```
Connected to ws://localhost:8765
RECV: {"type": "welcome", "player_id": 1}
RECV: {"type": "waiting", "players": 1}
Test finished, closing
```

Se vedi questi messaggi il server funziona e può accettare client.

---

    
   