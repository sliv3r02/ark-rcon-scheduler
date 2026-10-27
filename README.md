# ARK RCON Scheduler

Petits scripts Python pour **envoyer automatiquement des commandes RCON** à un ou plusieurs serveurs ARK (messages d'avertissement avant redémarrage, sauvegardes, etc.), depuis un Raspberry Pi ou n'importe quelle machine Linux toujours allumée. Aucun mod n'est nécessaire.

Ce que fait le projet :

- envoie des messages dans le chat du jeu (`serverchat`) et des commandes (`saveworld`, ...) sur un ou plusieurs serveurs ;
- gère des serveurs qui **redémarrent à des heures différentes** ;
- affiche un **compte à rebours de 10 à 1 seconde** avant le redémarrage ;
- écrit un journal (`ark.log`) de tout ce qui est envoyé.

> Le redémarrage lui-même reste géré par ton hébergeur ou ton panel : ces scripts préviennent les joueurs et sauvegardent, ils ne redémarrent pas le serveur.

Testé sur ARK Survival Ascended chez un hébergeur ; les commandes RCON utilisées sont aussi présentes sur ARK Survival Evolved.

## Contenu du dépôt

| Fichier | Rôle |
|---|---|
| `ark_cmd.py` | Envoie des commandes RCON à tous les serveurs ou à certains |
| `compte_a_rebours.py` | Envoie « Redemarrage dans 10 secondes » ... « 1 seconde » |
| `servers.example.json` | Modèle de configuration (à copier en `servers.json`) |
| `crontab.example` | Exemple de planification |
| `requirements.txt` | Dépendance Python (`mcrcon`) |
| `.gitignore` | Empêche de publier `servers.json` (mots de passe) |

## 1. Prérequis

- Une machine Linux toujours allumée et connectée à Internet (Raspberry Pi, mini-PC, VPS...) avec **Python 3.8 ou plus récent**.
- Un serveur ARK avec le **RCON activé** :
  - `RCONEnabled=True` dans `GameUserSettings.ini`, section `[ServerSettings]` (ou l'option équivalente du panel de ton hébergeur) ;
  - un `ServerAdminPassword` défini ;
  - le **port RCON** accessible depuis ta machine. Chez un hébergeur, le port est attribué par le panel et doit parfois être ouvert par le support.
  - Redémarre le serveur après avoir activé le RCON.

## 2. Installation

```bash
git clone https://github.com/VOTRE-COMPTE/ark-rcon-scheduler.git
cd ark-rcon-scheduler
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

Si `python3 -m venv` échoue sur Debian ou Raspberry Pi OS : `sudo apt install python3-venv`.

## 3. Configuration

```bash
cp servers.example.json servers.json
nano servers.json
chmod 600 servers.json
```

Pour chaque serveur, renseigne :

| Champ | Description |
|---|---|
| `name` | Nom court **sans espace**, utilisé avec `-s` et dans le cron |
| `label` | Nom d'affichage (optionnel, remplace `{nom}` dans les messages) |
| `host` | Adresse IP du serveur, **sans le port** |
| `port` | Port **RCON** (pas le port de jeu ni le port de requête) |
| `password` | Le `ServerAdminPassword` du serveur |

`servers.json` contient tes mots de passe : il est ignoré par Git (`.gitignore`), ne le publie jamais.

## 4. Tester la connexion

Vérifie d'abord que le port RCON répond :

```bash
sudo apt install -y netcat-openbsd
nc -zv IP_DU_SERVEUR PORT_RCON
```

`succeeded` = le port est ouvert. `Connection refused` = RCON désactivé, mauvais port ou port fermé (voir Dépannage).

Puis teste le script :

```bash
./venv/bin/python ark_cmd.py "listplayers"
./venv/bin/python ark_cmd.py -s Serveur1 "serverchat Test"
```

Le message doit apparaître dans le chat du jeu. La réponse `Server received, But no response!!` est normale pour les commandes qui ne renvoient pas de texte.

> Utilise `serverchat` plutôt que `broadcast` : sur ARK Ascended, `broadcast` ne s'affiche pas toujours chez les joueurs.
> Évite aussi les accents dans les messages (le chat du jeu les affiche mal) : écris « Redemarrage » et non « Redémarrage ».

### Options de `ark_cmd.py`

```bash
./venv/bin/python ark_cmd.py "saveworld"                                # tous les serveurs
./venv/bin/python ark_cmd.py -s Serveur1 "serverchat Bonjour"           # un serveur
./venv/bin/python ark_cmd.py -s Serveur1,Serveur2 "saveworld"           # plusieurs
./venv/bin/python ark_cmd.py "serverchat [{nom}] Bienvenue"             # {nom} = label du serveur
```

## 5. Planifier avec cron

```bash
crontab -e
```

Colle le contenu de `crontab.example` en adaptant :

- les **chemins** (`PY`, `CMD`, `CR`) vers ton dossier ;
- les **noms de serveurs** (ceux de `servers.json`) ;
- les **horaires** selon l'heure de redémarrage de chacun.

Principe pour un serveur qui redémarre à `H:00` :

| Quand | Quoi |
|---|---|
| `H-1:55` | message « dans 5 minutes » |
| `H-1:58` | message « dans 2 minutes » |
| `H-1:59` | message « dans 1 minute » + `saveworld` |
| `H-1:59` | lance `compte_a_rebours.py 0 NomDuServeur` |
| `H-1:59:50` à `H-1:59:59` | « dans 10 secondes » ... « 1 seconde » |

Pour un redémarrage à `H:05`, décale toutes les minutes de +5 et passe `5` en argument à `compte_a_rebours.py`. Le premier argument est **la minute de l'heure** à laquelle le redémarrage a lieu.

Exemple de ligne cron pour un redémarrage à 6h30 :

```cron
29 5 * * * /chemin/venv/bin/python /chemin/compte_a_rebours.py 30 Serveur1
```

Vérifie ensuite avec `crontab -l`. Les horaires de cron utilisent l'heure du système : vérifie-la avec `date` et règle le fuseau avec `sudo raspi-config` (Localisation Options > Timezone) ou `sudo timedatectl set-timezone Europe/Paris`.

> Sous Windows, le Planificateur de tâches peut jouer le rôle de cron (non testé).

## 6. Tester le compte à rebours sans attendre

Si on est à `:37:30`, vise la minute `38` sur un seul serveur :

```bash
./venv/bin/python compte_a_rebours.py 38 Serveur1
```

Le script se connecte 15 secondes avant, puis envoie « Redemarrage dans 10 secondes » ... « 1 seconde » (de `:37:50` à `:37:59`). Il n'y a **aucun redémarrage** : le script ne fait qu'envoyer des messages. Préviens les joueurs ou teste sur un serveur vide.

## 7. Ajuster la précision

Dans `compte_a_rebours.py` :

```python
SAUVEGARDE_AVANT = None   # ex. 20 : sauvegarde 20 s avant le redémarrage
DECALAGE = 0              # en secondes : + si le redémarrage part plus tard, - plus tôt
```

Après le premier vrai redémarrage, compare l'heure du dernier message (`ark.log`) avec celle de l'arrêt du serveur et corrige `DECALAGE` si besoin.

## 8. Surveiller

```bash
tail -n 30 ark.log
```

Une ligne `ERREUR` pendant que le serveur redémarre est normale.

## Dépannage

| Symptôme | Cause probable |
|---|---|
| `Connection refused` | RCON désactivé, mauvais port, ou port non ouvert par l'hébergeur. Teste avec `nc -zv IP PORT`. |
| Timeout / ça bloque | Un pare-feu filtre la connexion |
| Erreur d'authentification | Mauvais mot de passe : doit être le `ServerAdminPassword` |
| Rien en jeu avec `broadcast` | Utilise `serverchat` |
| Lettres manquantes dans le message | Retire les accents |
| Les messages partent à la mauvaise heure | Heure ou fuseau du système incorrects (`date`) |
| `No such file or directory` pour `./venv/bin/python` | Tu n'es pas dans le dossier du projet (`cd` dedans) |
| Rien ne se passe via cron | Vérifie `crontab -l`, les chemins absolus et `ark.log` |

## Licence

MIT, voir le fichier `LICENSE` 
