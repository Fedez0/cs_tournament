#!/usr/bin/env bash
# Lancia questo script sul server (dentro cs_tournament.nosync/) ogni volta
# che aggiorni il codice, per applicare migrazioni, static file e riavviare
# il servizio.
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Installazione/aggiornamento dipendenze"
uv sync --frozen

echo "==> Migrazioni database"
uv run python manage.py migrate --noinput

echo "==> Raccolta static file"
uv run python manage.py collectstatic --noinput

echo "==> Riavvio gunicorn"
sudo systemctl restart cs_tournament

echo "==> Fatto. Stato del servizio:"
sudo systemctl status cs_tournament --no-pager
