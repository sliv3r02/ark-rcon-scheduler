#!/usr/bin/env python3
"""Envoie une ou plusieurs commandes RCON a un ou plusieurs serveurs ARK.

Exemples :
    python ark_cmd.py "listplayers"                          # tous les serveurs
    python ark_cmd.py -s Serveur1 "serverchat Bonjour"       # un seul serveur
    python ark_cmd.py -s Serveur1,Serveur2 "saveworld"       # plusieurs serveurs
"""
import argparse
import datetime
import json
from pathlib import Path

from mcrcon import MCRcon

BASE = Path(__file__).parent
SERVERS = json.loads((BASE / "servers.json").read_text(encoding="utf-8"))


def log(msg):
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line)
    with open(BASE / "ark.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def send(server, commands):
    try:
        with MCRcon(server["host"], server["password"], port=server["port"], timeout=10) as mcr:
            for c in commands:
                # {nom} est remplace par le "label" du serveur (ou son "name")
                c = c.replace("{nom}", server.get("label", server["name"]))
                reponse = mcr.command(c).strip()
                log(f"[{server['name']}] {c} -> {reponse}")
    except Exception as e:
        log(f"[{server['name']}] ERREUR : {e}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("-s", "--serveurs", help="noms separes par des virgules (par defaut : tous)")
    p.add_argument("commandes", nargs="+")
    args = p.parse_args()

    cibles = SERVERS
    if args.serveurs:
        noms = [n.strip() for n in args.serveurs.split(",")]
        cibles = [s for s in SERVERS if s["name"] in noms]
        inconnus = set(noms) - {s["name"] for s in cibles}
        if inconnus:
            log(f"Serveur(s) inconnu(s) : {', '.join(inconnus)}")

    for s in cibles:
        send(s, args.commandes)
