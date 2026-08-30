import csv
import io
import secrets

from teams.models import Team
from tournaments.models import Match
from .models import User


class ImportResult:
    """Contenitore semplice per il risultato di un import: quante righe
    sono state create/aggiornate con successo e quali righe sono fallite
    (con il motivo), così da poter mostrare un riepilogo all'admin senza
    interrompere l'intero import per un singolo errore."""
    def __init__(self):
        self.created = 0
        self.errors = []  # lista di stringhe "riga N: motivo"
        self.notes = []   # info non bloccanti, es. password temporanee generate

    def add_error(self, row_number, message):
        self.errors.append(f"Riga {row_number}: {message}")

    def add_note(self, row_number, message):
        self.notes.append(f"Riga {row_number}: {message}")


def _read_rows(csv_file):
    """Decodifica il file caricato e restituisce un csv.DictReader.
    utf-8-sig toglie il BOM che Excel aggiunge spesso ai CSV esportati."""
    wrapper = io.TextIOWrapper(csv_file.file, encoding='utf-8-sig')
    return csv.DictReader(wrapper)


def import_teams_csv(csv_file):
    """
    Colonne attese: name, description (opzionale), leader_username (opzionale)
    Crea una squadra per riga. Il leader, se indicato, viene aggiunto
    anche tra i membri della squadra.
    """
    result = ImportResult()
    reader = _read_rows(csv_file)

    if reader.fieldnames is None or 'name' not in reader.fieldnames:
        result.add_error(1, "il CSV deve avere una colonna 'name'.")
        return result

    for i, row in enumerate(reader, start=2):  # riga 1 = header
        name = (row.get('name') or '').strip()
        if not name:
            result.add_error(i, "campo 'name' mancante.")
            continue

        if Team.objects.filter(name__iexact=name).exists():
            result.add_error(i, f"esiste già una squadra chiamata '{name}'.")
            continue

        leader = None
        leader_username = (row.get('leader_username') or '').strip()
        if leader_username:
            leader = User.objects.filter(username__iexact=leader_username).first()
            if leader is None:
                result.add_error(i, f"utente leader '{leader_username}' non trovato.")
                continue

        team = Team.objects.create(
            name=name,
            description=(row.get('description') or '').strip(),
            leader=leader,
        )
        if leader:
            team.members.add(leader)

        result.created += 1

    return result


def import_match_results_csv(csv_file):
    """
    Colonne attese: match_id, score_team1, score_team2
    Aggiorna il risultato di match già esistenti (creati dal bracket)
    che sono ancora 'da_giocare'. Usa Match.set_result(), che si occupa
    anche di far avanzare il torneo al turno successivo.
    """
    result = ImportResult()
    reader = _read_rows(csv_file)

    required = {'match_id', 'score_team1', 'score_team2'}
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        result.add_error(1, "il CSV deve avere le colonne 'match_id', 'score_team1', 'score_team2'.")
        return result

    for i, row in enumerate(reader, start=2):
        try:
            match_id = int(row.get('match_id'))
            score1 = int(row.get('score_team1'))
            score2 = int(row.get('score_team2'))
        except (TypeError, ValueError):
            result.add_error(i, "match_id / score_team1 / score_team2 devono essere numeri interi.")
            continue

        if score1 < 0 or score2 < 0:
            result.add_error(i, "i punteggi non possono essere negativi.")
            continue

        if score1 == score2:
            result.add_error(i, "i punteggi non possono essere in parità (serve un vincitore).")
            continue

        try:
            match = Match.objects.get(pk=match_id)
        except Match.DoesNotExist:
            result.add_error(i, f"nessun match con id {match_id}.")
            continue

        if match.status != 'da_giocare':
            result.add_error(i, f"il match {match_id} è già concluso, non viene sovrascritto.")
            continue

        match.set_result(score1, score2)
        result.created += 1

    return result


def import_users_csv(csv_file):
    """
    Colonne attese: username (obbligatoria), password (opzionale — se vuota
    viene generata una password temporanea random), email, paese,
    phone_number, steam_url (tutte opzionali).
    Usa User.objects.create_user() così la password viene sempre salvata
    con hash, mai in chiaro.
    """
    result = ImportResult()
    reader = _read_rows(csv_file)

    if reader.fieldnames is None or 'username' not in reader.fieldnames:
        result.add_error(1, "il CSV deve avere una colonna 'username'.")
        return result

    for i, row in enumerate(reader, start=2):  # riga 1 = header
        username = (row.get('username') or '').strip()
        if not username:
            result.add_error(i, "campo 'username' mancante.")
            continue

        if User.objects.filter(username__iexact=username).exists():
            result.add_error(i, f"esiste già un utente '{username}'.")
            continue

        password = (row.get('password') or '').strip()
        generated_password = None
        if not password:
            generated_password = secrets.token_urlsafe(8)
            password = generated_password

        email = (row.get('email') or '').strip()
        if email and User.objects.filter(email__iexact=email).exclude(email='').exists():
            result.add_error(i, f"esiste già un utente con email '{email}'.")
            continue

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                paese=(row.get('paese') or '').strip(),
                phone_number=(row.get('phone_number') or '').strip(),
                steam_url=(row.get('steam_url') or '').strip(),
            )
        except Exception as e:
            result.add_error(i, f"errore nella creazione dell'utente: {e}")
            continue

        if generated_password:
            result.add_note(i, f"utente '{user.username}' creato con password temporanea: {generated_password}")

        result.created += 1

    return result