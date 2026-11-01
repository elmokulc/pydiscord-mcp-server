# pydiscord-mcp-server

Serveur MCP Python permettant à plusieurs assistants de consulter des serveurs Discord
et d’y agir avec **un seul compte bot partagé par processus**. Transport principal :
Streamable HTTP sur `http://localhost:8085/mcp`.

La version 0.2 expose **88 outils** : les 81 opérations du
[dépôt SaseQ/discord-mcp](https://github.com/SaseQ/discord-mcp) comparées au commit
`e134c03714cfadf786b686e3045b92537042a240`, les trois outils propres au projet déjà
présents, et **quatre outils de sondages natifs Discord**. Voir le
[catalogue complet](docs/tools.md), les [différences de parité](docs/parity.md) et
le [guide des sondages](docs/polls.md).

## Démarrage Docker

Installer Docker Engine et le plugin Compose, créer et inviter le bot comme indiqué
ci-dessous, puis depuis ce dossier :

```bash
cp .env.example .env
# Renseigner DISCORD_TOKEN ; choisir les intents et les serveurs autorisés.
docker compose up -d --build
docker compose ps
curl --fail http://localhost:8085/health/ready
```

Le token est chargé à l’exécution via `.env`, exclu du contexte Docker et de Git.
Protéger ce fichier (`chmod 600 .env`). Aucun secret n’est nécessaire pour construire
l’image. L’image utilise Python 3.12 slim, deux étapes de construction, `uv sync
--locked --no-dev --no-editable`, un utilisateur UID 10001 et un healthcheck Python
sans dépendre de curl. Compose ajoute un système de fichiers en lecture seule, un
`/tmp` temporaire et `restart: unless-stopped`.

Le port est publié **uniquement sur 127.0.0.1**, port 8085 par défaut. Dans le
conteneur, `MCP_HOST=0.0.0.0` et `MCP_PORT=8085` sont imposés par Compose ; `MCP_PORT`
dans `.env` change le port publié sur l’hôte. Ne pas multiplier les réplicas ni les
workers : cela créerait plusieurs connexions bot.

```bash
docker compose logs --tail=100 discord-mcp
docker compose up -d --build       # après une modification du code
docker compose up -d --force-recreate  # après une modification de .env
docker compose down
```

## Versions et choix

Les documentations et publications officielles ont été consultées le 30 octobre
2026 : [discord.py](https://discordpy.readthedocs.io/en/stable/index.html),
[SDK MCP officiel](https://github.com/modelcontextprotocol/python-sdk),
[documentation MCP v2](https://py.sdk.modelcontextprotocol.io/).
Cette version utilise **MCP 2.3.0** (`mcp.server.MCPServer`, pas le FastMCP v1),
**discord.py 2.7.1**, Python 3.12 et Pydantic v2. `uv.lock` fixe les versions et les
empreintes des dépendances ; conserver ce fichier avec `pyproject.toml` dans Git.
Les images de base sont des tags versionnés et peuvent recevoir des correctifs ;
pour figer également la base système, épingler leurs digests selon votre politique
de mise à jour.

L’application Starlette possède le cycle de vie du bot et du gestionnaire HTTP MCP.
Le mode `stateless_http=True`, avec réponses JSON, ne conserve pas de session HTTP
ni de contexte d’appel partagé. Plusieurs clients appellent le même service ;
aucune connexion Discord n’est créée par session. Le SDK gère la négociation des
versions de protocole, dont les clients utilisant l’initialisation historique.
Cette version ne propose ni stdio, ni élicitation, ni abonnement ni diffusion
de notifications vers les clients.

## Architecture

```text
src/pydiscord_mcp_server/
  config.py          configuration Pydantic, secrets et validation
  discord_client.py  intents, connexion unique, disponibilité et arrêt
  server.py          application ASGI, HTTP MCP et santé
  __main__.py        Uvicorn, un worker, supervision des échecs fatals
  errors.py          codes d’erreur sûrs vers ToolError MCP
  models/            paramètres validés et résultats structurés
  services/          accès autorisés, cache/REST et logique par domaine
  tools/             fonctions MCP typées et registre explicite
tests/               doublures Discord, SDK et HTTP ASGI sans réseau
docs/adding-tools.md tutoriel avec l’outil réel get_channel_info
```

`register_tools(mcp, access)` appelle explicitement chaque domaine. Les outils
reçoivent le même objet `DiscordAccess` dans leur fermeture ; celui-ci référence le
runtime partagé. Les variables propres à une requête restent locales. Pas de base
de données ni de découverte dynamique de modules.

## Créer et inviter le bot

1. Créer une application dans le [portail développeur Discord](https://discord.com/developers/applications).
2. Dans **Bot**, créer/réinitialiser le token et le placer dans `DISCORD_TOKEN`.
   Ne jamais utiliser un token utilisateur ni un self-bot. Ne pas coller le token
   dans un assistant, une URL, une commande versionnée ou des logs.
3. Dans **Bot → Privileged Gateway Intents**, activer **Message Content Intent**
   pour lire normalement le texte et les pièces jointes des messages, et
   **Server Members Intent** pour activer la recherche de membres du projet.
   Les applications vérifiées peuvent nécessiter une autorisation Discord.
4. Activer aussi les options correspondantes dans `.env` :
   `DISCORD_INTENT_MESSAGE_CONTENT=true` et/ou `DISCORD_INTENT_MEMBERS=true`.
   Les intents sont désactivés par défaut. Le code les applique à `discord.Intents`.
5. Dans **OAuth2 → URL Generator**, choisir le scope **bot**, sélectionner les
   permissions nécessaires, puis ouvrir l’URL d’invitation pour votre serveur.
   Le scope `applications.commands` n’est pas nécessaire : aucun slash command.
6. Activer le mode développeur dans Discord pour copier les IDs de serveur,
   salon, fil, membre et message.

Permissions à accorder sur les salons concernés, en tenant compte des rôles et
des surcharges de salon/fil :

| Usage | Permissions |
| --- | --- |
| Lire messages et historique | View Channel, Read Message History |
| Envoyer et répondre | Send Messages ; Send Messages in Threads pour les fils |
| Ajouter une réaction | Read Message History, Add Reactions si nécessaire |
| Supprimer un message d’autrui ou retirer sa réaction | Manage Messages |
| Lister toutes les archives privées accessibles au bot gestionnaire | Manage Threads, Read Message History |
| Archives privées auxquelles le bot participe | Accès au fil et Read Message History |
| Emoji externe | Use External Emojis selon le cas |
| Créer un sondage natif | Send Polls, Send Messages ; Send Messages in Threads dans un fil |
| Créer/modifier/supprimer des salons, catégories et forums | Manage Channels |
| Rôles et surcharges de permission | Manage Roles, avec une hiérarchie suffisante |
| Webhooks | Manage Webhooks |
| Inviter / lister les invitations | Create Instant Invite / Manage Guild selon l’opération |
| Modération | Kick Members, Ban Members, Moderate Members, Manage Nicknames selon l’action |
| Déplacer / rendre muet / assourdir en vocal | Move Members, Mute Members, Deafen Members |
| Événements / emojis | Create Events ou Manage Events ; Create Expressions ou Manage Expressions selon propriétaire et action |

Ne pas accorder Administrator par défaut. Discord reste l’autorité finale sur les
permissions, y compris l’accès aux fils privés/archivés. Envoyer dans un fil archivé
peut entraîner sa réouverture selon les règles Discord ; un fil verrouillé peut
nécessiter Manage Threads. Cette version ne crée, ne rejoint et ne déverrouille
pas automatiquement de fil.

Références : [création du bot](https://discordpy.readthedocs.io/en/stable/discord.html),
[intents et limites du cache](https://discordpy.readthedocs.io/en/stable/intents.html).

## Configuration

Les variables d’environnement priment sur `.env`. Les tableaux utilisent du JSON
avec des **IDs entre guillemets** ; `.env.example` donne la syntaxe complète.

| Variable | Défaut / effet |
| --- | --- |
| `DISCORD_TOKEN` | Obligatoire, secret du compte bot |
| `DISCORD_GUILD_ID` | Facultatif, serveur utilisé quand `guild_id` est omis ; vide autorisé |
| `DISCORD_ALLOWED_GUILD_IDS` | Facultatif, liste JSON de serveurs autorisés ; absent = tous ceux accessibles au bot, `[]` = aucun |
| `DISCORD_INTENT_MESSAGE_CONTENT` | `false` ; activer aussi dans le portail |
| `DISCORD_INTENT_MEMBERS` | `false` ; activer aussi dans le portail |
| `DISCORD_ENABLE_DMS` | `false` ; active les quatre outils privés, qui exigent aussi un serveur autorisé et l’appartenance actuelle du destinataire |
| `MCP_HOST` | `127.0.0.1` en local, `0.0.0.0` dans Docker |
| `MCP_PORT` | `8085` ; avec Compose, port publié de l’hôte |
| `MCP_ALLOWED_HOSTS` | Liste JSON : localhost, IP de boucle locale, `discord-mcp:8085` |
| `MCP_ALLOWED_ORIGINS` | Liste JSON vide ; ajouter seulement les origines nécessaires |
| `LOG_LEVEL` | `INFO` ; DEBUG, WARNING, ERROR, CRITICAL également disponibles |
| `DISCORD_READY_TIMEOUT` | `30` secondes, attente au démarrage et lors d’une déconnexion |
| `DISCORD_OPERATION_TIMEOUT` | `30` secondes par opération après disponibilité |
| `DISCORD_SHUTDOWN_TIMEOUT` | `10` secondes pour fermer, puis pour annuler la tâche |

**Serveur par défaut et restriction sont distincts.** Fournir un autre `guild_id`
reste autorisé si aucune liste restrictive n’est définie. Si la liste est définie,
le serveur est vérifié aussi après résolution d’un ID direct de salon ou de fil,
avant toute lecture/écriture de message. Les outils de salon refusent les messages
privés. Les outils `*_private_message*` restent désactivés par défaut : leur
activation explicite exige un `guild_id` fourni ou par défaut, autorisé par la
liste, et une vérification REST de l’appartenance du destinataire à ce serveur.

## Accès MCP et santé

Dans un client MCP compatible Streamable HTTP, ajouter l’URL
`http://localhost:8085/mcp` (ou le port hôte choisi). Le format de configuration
exact dépend du client. Un navigateur ou un simple GET ne constitue pas une
initialisation MCP ; utiliser un client MCP ou l’Inspector.

Depuis un autre conteneur du **même réseau Compose**, utiliser
`http://discord-mcp:8085/mcp`. Pour un conteneur sur un autre réseau, le rattacher
explicitement au réseau de ce service. `localhost` y désigne le conteneur appelant.
Ajouter tout autre nom d’hôte dans `MCP_ALLOWED_HOSTS`. Une liste d’origines n’active
pas à elle seule CORS ; les clients navigateur nécessitent une configuration CORS
du proxy/adaptateur conforme aux en-têtes MCP.

| Endpoint | Réponse |
| --- | --- |
| `/health/live` | 200 : processus HTTP vivant, indépendamment de la connexion Discord |
| `/health/ready` | 200 : bot prêt ; 503 pendant une déconnexion ou après un échec |
| `/mcp` | Streamable HTTP, outils et résultats JSON structurés |

Le démarrage attend le bot avant d’accepter HTTP ; si le token, les intents ou le
réseau empêchent sa disponibilité dans le délai configuré, le processus échoue.
Pendant une reconnexion, les appels attendent au plus `DISCORD_READY_TIMEOUT`,
puis échouent explicitement. discord.py gère les reconnexions et limites de débit.
Une terminaison inattendue de la tâche Discord est journalisée sans son message
d’exception ; le lanceur arrête HTTP et sort en échec pour permettre le redémarrage.
Un simple statut Docker unhealthy ne redémarre pas à lui seul un conteneur Compose.

SIGTERM est traité par Uvicorn : les appels se terminent dans la limite de l’arrêt
gracieux, puis le lifespan ferme le client et annule sa tâche. Utiliser le lanceur
fourni (`python -m pydiscord_mcp_server`) pour conserver cette supervision.

### Exposition distante

Le service n’embarque pas de mécanisme d’identité MCP. Toute personne atteignant
`/mcp` peut utiliser les capacités du bot dans les serveurs autorisés. Garder la
publication locale ou un réseau privé maîtrisé. Avant une exposition distante,
placer une passerelle d’authentification compatible avec vos clients MCP et les
exigences d’autorisation MCP, activer HTTPS, vérifier les en-têtes Host/Origin et
limiter le réseau. La liste des serveurs autorisés et les annotations des outils
ne remplacent pas l’authentification ni les permissions Discord. Aucun système
maison de mot de passe ou de token HTTP n’est ajouté dans cette version.

## Catalogue des outils

Tous les IDs sont des **chaînes décimales**, y compris dans les résultats. Les
limites de page sont strictement comprises entre 1 et 100. Les résultats Pydantic
sont exposés en `structuredContent` avec un schéma de sortie MCP. Les paramètres
utilisent les noms `snake_case` de ce projet, pas les paramètres Java du dépôt de
référence. Les outils de modification complexes acceptent un objet `settings`
validé ; seuls les champs fournis sont modifiés. Voir les **88 outils** et leurs
paramètres dans [docs/tools.md](docs/tools.md).

Les outils de consultation et de message comprennent :

| Outil | Paramètres et résultat |
| --- | --- |
| `list_guilds` | `limit=50`, `after?` ; serveurs autorisés du cache, IDs croissants |
| `get_guild_info` | `guild_id?` ; métadonnées du serveur |
| `list_channels` | `guild_id?`, `limit=50`, `after?` ; salons hors fils, IDs croissants |
| `get_channel_info` | `channel_id` ; salon ou fil, type, parent, sujet, lien et métadonnées de fil |
| `read_messages` | `channel_id`, `limit=50`, un seul de `before?`, `after?`, `around?` |
| `get_message` | `channel_id`, `message_id` ; un message |
| `send_message` | `channel_id`, `content`, `reply_to_message_id?`, `allow_mentions=false` |
| `edit_message` | `channel_id`, `message_id`, `content`, `allow_mentions=false` ; messages du bot seulement |
| `delete_message` | `channel_id`, `message_id`, `allow_other_author=false` ; suppression |
| `add_reaction` | `channel_id`, `message_id`, `emoji` ; ajout par le bot |
| `remove_reaction` | `channel_id`, `message_id`, `emoji`, `member_id?` ; bot par défaut |
| `list_threads` | `channel_id` du parent, `mode=active`, `limit=50`, `cursor?` |
| `get_thread_info` | `thread_id` ; fonctionne aussi pour une archive accessible hors cache |
| `get_member` | `member_id`, `guild_id?` ; cache puis récupération REST ciblée |
| `search_members` | `query`, `guild_id?`, `limit=25` ; ID ciblé ou noms disponibles, portée bornée |

Les autres domaines couvrent la création et la gestion des salons, catégories,
forums et posts, rôles, modération, état vocal, événements, surcharges de
permissions, invitations, webhooks, emojis et messages privés optionnels.
`search_messages` et `get_message_replies` effectuent un balayage borné dans **un
seul salon ou fil**. Les sondages utilisent `create_poll`, `get_poll`, `end_poll`
et `get_poll_answer_voters` ; [exemple complet](docs/polls.md).

Les messages incluent auteur, IDs, dates ISO 8601, contenu, pièces jointes et leurs
URLs, référence de réponse et lien Discord. Les cartes sont conservées dans
`embeds` (titre, description, champs, auteur, pied de page, médias et métadonnées),
sans troncature supplémentaire. Les stickers et composants Discord, y compris les
composants imbriqués, sont disponibles dans `stickers` et `components`. Le type,
l’état épinglé, les mentions résolues et le texte des messages système sont aussi
inclus (`type`, `pinned`, `mentions`, `role_mentions`, `channel_mentions`,
`mention_everyone`, `is_system`, `system_content`). Un `content` vide peut donc
contenir un embed ou un autre contenu structuré. Un message cité résolu est inclus sur
un seul niveau dans `reply_to` ; un message supprimé ou non résolu conserve sa
référence par ID. Les sondages sont sérialisés dans `poll`. Salons textuels, fils, salons vocaux et
scènes avec messagerie sont acceptés. Un forum est un parent de fils, pas un salon
dans lequel `send_message` publie directement. Les messages texte sont limités à
1–2000 caractères ; cette version ne téléverse pas de fichiers et ne modifie pas
les pièces jointes ou embeds.

Les mentions utilisateur, rôle, everyone/here et auteur d’une réponse sont
désactivées dans `send_message` et `edit_message`. `allow_mentions=true` les
autorise **toutes**, sous réserve des permissions Discord. L’édition d’un message
d’autrui est refusée. Sa suppression exige `allow_other_author=true` **et** Manage
Messages ; supprimer son propre message n’exige pas cette permission. Retirer la
réaction d’autrui exige également Manage Messages.

### Pagination et portée

Pour les serveurs et salons, passer `next_cursor` dans `after`. Pour l’historique,
`before` donne les messages précédents du plus récent au plus ancien ; `after`
donne les suivants du plus ancien au plus récent. La borne est exclusive.
`cursor_parameter` indique où replacer `next_cursor`. `around` retourne une fenêtre
bornée sans curseur de continuation. Une page lit au plus `limit + 1` messages pour
déterminer s’il en reste. `next_cursor=null` termine la pagination.

`search_messages` recherche dans `content` et le texte des embeds (titre,
description, noms et valeurs des champs, auteur et pied de page), sans tenir
compte de la casse, dans au plus
`scan_limit=1000` messages d’un salon/fil, les plus récents d’abord ; reprendre avec
`before=next_cursor`. `get_message_replies` cherche les références explicites dans
les messages postérieurs au message cible, les plus anciens d’abord ; reprendre
avec `after=next_cursor`. Les résultats indiquent `scanned`, `scan_limit`,
`exhausted` et leur portée. Une page peut être vide avec un curseur si le budget de
balayage est atteint. **Aucune recherche globale Discord ni exhaustivité ne sont promises.**

`list_threads` traite **un seul salon parent** par appel :

| Mode | Portée et ordre |
| --- | --- |
| `active` | Fils actifs renvoyés par l’API du serveur et filtrés sur le parent, IDs décroissants |
| `archived_public` | Archives publiques accessibles, date d’archivage décroissante |
| `archived_private` | Archives privées que Discord autorise au bot gestionnaire, date décroissante |
| `archived_joined_private` | Archives privées rejointes par le bot, IDs décroissants |

Réutiliser le curseur opaque avec le même `channel_id` et le même `mode`. Il ne
contient aucun secret et ne confère aucun droit. Les forums/médias ne proposent
que des archives publiques. La lecture est bornée à `limit + 1` archives ; l’API
discord.py peut récupérer un lot HTTP minimal supérieur à la taille demandée.
Pour les actifs, Discord fournit toute la liste du serveur en un appel avant le
filtrage local. Les pages ne sont pas un instantané : les modifications concurrentes
peuvent déplacer les éléments. Les archives non rejointes utilisent le curseur
temporel imposé par Discord ; des dates d’archivage exactement égales à la frontière
peuvent limiter la pagination. L’accès direct par ID reste disponible.

`search_members` résout un ID par cache puis REST, même sans Members intent. Pour
un nom, il combine le cache disponible (nom, nom global, surnom, nom affiché) avec
une requête Gateway `Guild.query_members` par préfixe du nom/surnom, bornée à
100 candidats. Le projet exige Members intent pour ce parcours de recherche par
nom et pour la liste des personnes intéressées par un événement. Un nom global
non présent en cache et non découvert par le préfixe peut ne pas être trouvé.
La réponse n’est jamais annoncée exhaustive et n’a pas de curseur. Les petites
limites demandent au moins 5 candidats à la Gateway puis tronquent les résultats.
Aucun chunk complet des membres n’est lancé au démarrage. `get_user_id_by_name`
exige une correspondance exacte non ambiguë ; utiliser l’ID stable sinon.

### Erreurs

Les échecs métier lèvent `ToolError` : le résultat MCP porte `isError=true`, avec
un préfixe stable `ACCESS_DENIED`, `NOT_FOUND`, `INVALID_PARAMETER`,
`DISCORD_UNAVAILABLE` ou `TIMEOUT`. Les paramètres invalides sont aussi rejetés par
le SDK avant l’appel métier. Aucun succès ne contient simplement un texte d’erreur.
Le détail brut des erreurs HTTP Discord n’est pas renvoyé. Un timeout d’écriture
peut survenir après que Discord a appliqué l’action : vérifier avant de réessayer,
en particulier pour éviter un double envoi.

## Développement local

Installer [uv](https://docs.astral.sh/uv/getting-started/installation/) puis :

```bash
uv sync --locked
cp .env.example .env
# Renseigner le compte bot et les options souhaitées.
uv run --locked python -m pydiscord_mcp_server
```

Contrôles sans token et sans accès réseau Discord :

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest -q
docker build -t pydiscord-mcp-server:local .
```

Les tests bloquent l’ouverture des connexions réseau, utilisent des `AsyncMock` et
exercent le SDK MCP et HTTP via ASGI en mémoire. Ils couvrent validation, pages,
sérialisation, erreurs, autorisation des serveurs, caches absents, mentions,
propriété des messages, réactions, archives, connexion partagée, arrêt et
supervision des échecs. Un avertissement de dépréciation `audioop` peut provenir de
discord.py sous Python 3.12 ; les fonctionnalités vocales ne sont pas utilisées.

Pour ajouter un outil, suivre [le tutoriel complet](docs/adding-tools.md).
Pour une mise à jour délibérée : modifier les bornes si nécessaire, exécuter
`uv lock --upgrade-package NOM`, relancer les contrôles et reconstruire l’image.
Ne pas recopier des exemples SDK v1 dans ce projet v2.

## Validation avec votre bot

Cette procédure est à exécuter avec vos identifiants ; les tests automatisés ne
se connectent jamais à Discord et ne prouvent pas les permissions réelles.

1. Inviter le bot dans un serveur de test et configurer les intents des deux côtés.
2. Renseigner `.env`, idéalement `DISCORD_ALLOWED_GUILD_IDS` avec ce seul serveur.
3. Démarrer Compose ; attendre `/health/ready` à 200 et vérifier `Discord bot ready`.
4. Depuis votre client MCP, appeler uniquement `list_guilds`, `list_channels`,
   `get_channel_info`, puis `read_messages` sur un salon lisible. Vérifier les
   contenus, pièces jointes, IDs et curseurs attendus.
5. Tester `get_thread_info` avec l’ID connu d’une archive et les modes d’archives
   compatibles avec les permissions du bot. Tester les membres selon l’intent.
6. Vérifier qu’un salon d’un autre serveur est refusé par la liste restrictive.
7. Arrêter avec `docker compose stop` et vérifier l’arrêt propre dans les logs.

Les outils d’écriture ne doivent être testés que sur votre instruction explicite,
dans un salon dédié. Aucun message réel ni aucune ressource Discord n’a été modifié
pour réaliser les contrôles de ce projet. [Bilan des vérifications](docs/verification.md).

## Limites et dépannage

- **Configuration invalide** : token vide, ID numérique au lieu d’une chaîne JSON,
  liste mal formée ou port hors limites. Le lanceur affiche un diagnostic générique
  pour éviter d’exposer des valeurs secrètes.
- **LoginFailure / PrivilegedIntentsRequired** : vérifier le token bot et les
  autorisations d’intents dans le portail ; recréer le conteneur après correction.
- **Contenu vide** : vérifier Message Content intent, le portail et les limitations
  Discord. Sans cet intent, certains contenus/pièces jointes sont omis hors
  exceptions Discord ; ne pas interpréter une chaîne vide comme une absence certaine.
- **ACCESS_DENIED / NOT_FOUND** : vérifier liste des serveurs, View Channel,
  historique, surcharges et appartenance au fil privé. Discord peut masquer une
  ressource inaccessible comme introuvable.
- **TIMEOUT / not_ready** : vérifier réseau, DNS, sortie HTTPS/WSS vers Discord,
  statut Discord et délais. Les attentes de rate limit comptent dans le délai.
- **421** : Host non autorisé ; adapter `MCP_ALLOWED_HOSTS` au nom réellement utilisé.
- **400 Origin / 406 Accept** : vérifier les origines autorisées et utiliser un vrai
  client Streamable HTTP. Pas de CORS permissif ajouté par défaut.
- **Plusieurs connexions au même bot** : conserver une instance et un worker,
  arrêter les lancements locaux simultanés ou les anciens services utilisant ce token.
- Les métadonnées et messages présents en cache peuvent être légèrement anciens.
  Les membres, fils privés et salons restent limités par ce que Discord expose au
  bot. Les DM restent une option explicite ; aucune recherche globale ou garantie
  d’exhaustivité n’est annoncée. Les sondages et leurs décomptes sont rafraîchis via REST.
- Les logs applicatifs n’incluent ni token ni contenu des messages ; les logs HTTP
  détaillés HTTP, Gateway et webhooks Discord sont bridés même avec
  `LOG_LEVEL=DEBUG` dans le lanceur fourni.
  Les résultats MCP contiennent naturellement les données demandées : les clients
  peuvent les conserver selon leur propre configuration.
