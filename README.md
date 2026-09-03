# CS Tournament — Squad Finder & Tournament Organizer

Applicazione web Django per la community di Counter-Strike 2: permette di
creare e gestire **squadre**, trovarne una tramite lo **Squad Finder**, e
organizzare **tornei** con bracket a eliminazione diretta e classifica
generale.

Progetto realizzato per il corso di Web Development (IWC 2026, prof.
Francesco Faenza).

🔗 In produzione su **https://germiniasi.com**

## Funzionalità

**Account e profilo**
- Registrazione/login con utente custom (`core.User`), esteso con paese,
  numero di telefono, link Steam e foto profilo
- Modifica profilo ed eliminazione account

**Squadre (`teams`)**
- Creazione, modifica ed eliminazione squadra (max 5 membri)
- Squad Finder: ricerca squadre aperte con posti liberi
- Ricerca utenti via AJAX per invitarli in squadra
- Sistema di inviti (squadra → utente) e richieste di ingresso
  (utente → squadra), entrambi con flusso di accettazione/rifiuto
- Rimozione membri, uscita volontaria dalla squadra

**Tornei (`tournaments`)**
- Creazione tornei con nome, data, location, montepremi, icona e banner
- Iscrizione squadre (fino a un numero massimo configurabile)
- Generazione automatica del bracket a eliminazione diretta (richiede un
  numero di squadre pari a una potenza di 2)
- Inserimento risultati dei match, avanzamento automatico al turno
  successivo e calcolo del vincitore del torneo
- Stato del torneo (aperto / in corso / chiuso) calcolato dinamicamente,
  mai salvato manualmente

**Classifica (`leaderboard`)**
- Classifica generale delle squadre ordinata per numero di vittorie

**Import dati da CSV**
- Import squadre (`name`, `description`, `leader_username`)
- Import risultati match (`match_id`, `score_team1`, `score_team2`)
- Import utenti (`username`, più campi opzionali; genera una password
  temporanea se non specificata)

**Altro**
- Invio email transazionali via Resend (es. email di test)
- Pannello di amministrazione Django per la gestione diretta dei dati

## Stack tecnico

- **Backend**: Django 6.0, Python 3.14
- **Database**: SQLite
- **Frontend**: Bootstrap, template Django con ereditarietà a 3 blocchi
  (header/content/footer)
- **Immagini**: Pillow
- **Email**: Resend
- **Gestione pacchetti**: uv
- **Produzione**: Gunicorn + Nginx + Let's Encrypt, su server Ubuntu

## Struttura del progetto

```
cs_tournament.nosync/
├── config/          # settings, URL root, WSGI/ASGI
├── core/            # utente custom, home, auth, import CSV
├── teams/           # squadre, inviti, richieste di ingresso
├── tournaments/      # tornei, bracket, match
├── leaderboard/      # classifica squadre
├── static/           # asset di sviluppo
├── media/             # file caricati dagli utenti
└── manage.py
```

## Setup in locale

```bash
uv sync
cp .env.example .env   # compila SECRET_KEY, RESEND, DEBUG=True
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

## Deploy in produzione

Il progetto gira in produzione su un server Ubuntu con Gunicorn dietro
Nginx e certificato HTTPS via Let's Encrypt. La guida completa passo-passo
(preparazione server, systemd, Nginx, DNS, certbot) è in `DEPLOY.md`.

## Modello dati (riassunto)

- **User** (estende AbstractUser): paese, telefono, foto profilo, link Steam
- **Team**: nome, descrizione, icona, membri (M2M), leader, aperto/chiuso, vittorie
- **TeamJoinRequest** / **TeamInvite**: richieste e inviti con stato pending/accepted/rejected
- **Tournament**: nome, data, location, montepremi, squadre iscritte (M2M), vincitore
- **Match**: torneo, turno, due squadre, punteggi, vincitore, stato