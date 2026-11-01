# Vérifications de livraison 0.2.0 — 30 octobre 2026

## Réussies

| Contrôle | Résultat |
| --- | --- |
| Résolution `uv lock --check --offline` | Lockfile cohérent avec `pyproject.toml` |
| Installation `uv sync --locked --offline` | Réussie, Python 3.12.3 sur l’hôte |
| `uv run --locked ruff check .` | Réussi |
| `uv run --locked ruff format --check .` | Réussi |
| `uv run --locked mypy` | Mode strict, 43 fichiers source, aucune erreur |
| `uv run --locked pytest -q` | 220 tests réussis, connexions réseau bloquées dans les tests |
| Catalogue de référence | 81 noms épinglés au commit `e134c03714cfadf786b686e3045b92537042a240`, tous couverts parmi 88 outils |
| Appels MCP du catalogue | Les 88 outils appelés avec le client officiel et des doublures Discord, résultats structurés vérifiés |
| Sondages | Payload `discord.Poll`, bornes et mentions, fraîcheur REST, clôture limitée au bot, décomptes inconnus et votants paginés |
| Administration | Refus de serveurs exclus et de catégories étrangères, fusion des permissions, DM opt-in avec appartenance REST, propriété des messages, validation d’événements et d’images |
| `docker build -t pydiscord-mcp-server:local .` | Réussi avec installation `uv sync --locked --no-dev --no-editable` |
| Validation Compose | `docker compose --env-file .env.example config --no-env-resolution --quiet` réussie, sans créer de `.env` |
| Exécution non root | UID 10001 confirmé dans le conteneur, `.env` absent de l’image |
| HTTP dans Docker | Deux clients du SDK officiel simultanés, découverte des 88 outils, appel de `list_guilds`, validation du schéma de sondage et rejet d’un sondage invalide |
| Santé HTTP | `/health/live` et `/health/ready` à 200 dans le conteneur isolé |
| Healthcheck de l’image | Statut `healthy` confirmé pendant l’exécution |
| SIGTERM dans Docker | Fermeture du faux client observée, arrêt ASGI propre, code de sortie 0 |
| Absence de token | Validation obligatoire testée ; refus du lanceur sans secret déjà vérifié dans la livraison initiale |

Les commandes uv ont utilisé une installation temporaire de uv 0.13.6 et le cache
de dépendances, hors du code du projet. L’image utilise Python 3.12.16 et uv 0.13.6 ;
sa taille locale mesurée est d’environ 254 Mio (265 848 098 octets).

Les essais Docker HTTP et SIGTERM ont remplacé **uniquement la connexion Discord**
par une doublure et ont utilisé `--network none`, un système de fichiers en lecture
seule et un `/tmp` temporaire. Les requêtes HTTP ont circulé sur la boucle locale
du conteneur. Les conteneurs temporaires ont été arrêtés et supprimés. Cela vérifie
le packaging, Uvicorn, le SDK MCP, les routes et l’arrêt, sans prétendre valider une
authentification Discord.

Les tests automatisés couvrent également un échec fatal de la tâche bot après le
démarrage : la supervision demande l’arrêt d’HTTP et retourne un code d’échec.
Deux clients du SDK en mémoire partagent une seule tâche Discord. Les requêtes
Streamable HTTP sont aussi exercées via ASGI en mémoire, avec initialisation,
appels structurés, absence de session HTTP, refus Host et santé dégradée.

Un avertissement amont subsiste : discord.py importe `audioop`, déprécié sous
Python 3.12. Il ne fait échouer aucun contrôle ; le projet gère les salons et états
vocaux sans établir de connexion audio.

## Non exécutées

- Authentification et reconnexion avec un **vrai bot Discord** : aucun token réel
  n’a été utilisé. Suivre la procédure de validation du README.
- Vérification des permissions et intents réels du portail, contenu d’un vrai
  salon, accès à un vrai fil privé/archivé et recherche de vrais membres.
- Actions d’écriture réelles : aucun envoi, sondage, édition, suppression, changement
  de rôle, permission, réaction ou ressource n’a été réalisé. Une instruction
  explicite et un serveur/salon de test sont requis.
- Déploiement distant avec authentification/HTTPS : hors périmètre de cette
  version locale ; les exigences sont documentées dans le README.
- Création de commit Git : aucun commit demandé ni créé pour cette extension.
  Le dépôt local a été initialisé entre les livraisons ; la mention de `.git`
  inutilisable de la livraison initiale ne décrit plus son état actuel.

## Contrôles bloqués

Aucun contrôle de lint, types, tests ou construction Docker ne reste bloqué.
La connexion réelle demeure à valider avec votre bot. L’ancien projet `discord-mcp`
n’a pas été modifié.
