#!/usr/bin/env python3
"""Compte a rebours de 10 a 1 seconde avant un redemarrage planifie.

Usage : compte_a_rebours.py MINUTE_REDEMARRAGE serveur1,serveur2
    MINUTE_REDEMARRAGE = minute de l'heure a laquelle le redemarrage a lieu
    (0 pour 4h00, 5 pour 4h05, ...). Lancer le script a la minute precedente
    avec cron (ex. a 3h59 pour un redemarrage a 4h00).
"""
import datetime
import json
import sys
import time
from contextlib import ExitStack
from pathlib import Path

from mcrcon import MCRcon

BASE = Path(__file__).parent
SERVERS = json.loads((BASE / "servers.json").read_text(encoding="utf-8"))

SAUVEGARDE_AVANT = None  # sauvegarde X secondes avant le redemarrage (None = desactive)
DECALAGE = 0             # en secondes : + si le redemarrage part plus tard, - plus tot


def log(msg):
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line)
    with open(BASE / "ark.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def attendre(instant):
    reste = (instant - datetime.datetime.now()).total_seconds()
    if reste > 0:
        time.sleep(reste)
        return True
    return reste > -1   # trop en retard : on saute le message


if len(sys.argv) != 3:
    sys.exit("Usage : compte_a_rebours.py MINUTE_REDEMARRAGE serveur1,serveur2")

minute_restart = int(sys.argv[1])
noms = [n.strip() for n in sys.argv[2].split(",")]
cibles = [s for s in SERVERS if s["name"] in noms]

now = datetime.datetime.now()
cible = now.replace(minute=minute_restart, second=0, microsecond=0)
if cible <= now:
    cible += datetime.timedelta(hours=1)
cible += datetime.timedelta(seconds=DECALAGE)

# On se connecte 15 secondes avant le debut du decompte
attendre(cible - datetime.timedelta(seconds=15))

with ExitStack() as stack:
    connexions = []
    for s in cibles:
        try:
            mcr = stack.enter_context(
                MCRcon(s["host"], s["password"], port=s["port"], timeout=10)
            )
            connexions.append((s["name"], mcr))
        except Exception as e:
            log(f"[{s['name']}] ERREUR connexion : {e}")

    def envoyer(commande):
        log(f"[{','.join(n for n, _ in connexions)}] {commande}")
        for nom, mcr in connexions:
            try:
                mcr.command(commande)
            except Exception as e:
                log(f"[{nom}] ERREUR : {e}")

    if SAUVEGARDE_AVANT and attendre(cible - datetime.timedelta(seconds=SAUVEGARDE_AVANT)):
        envoyer("saveworld")

    for s in range(10, 0, -1):
        if attendre(cible - datetime.timedelta(seconds=s)):
            mot = "seconde" if s == 1 else "secondes"
            # Sans accent : le chat du jeu les affiche mal
            envoyer(f"serverchat Redemarrage dans {s} {mot}")
