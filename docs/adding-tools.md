# Ajouter un outil MCP

Le parcours normal est : fonction métier → fonction MCP typée → enregistrement
explicite → test et documentation. Pas d’import automatique, de scan de fichiers
ou de nouveau client Discord. Ce tutoriel suit **`get_channel_info`**, déjà livré et
testé, pour consulter un salon ou un fil archivé accessible par ID.

## 1. Choisir le domaine et le modèle

Placer la logique dans `src/pydiscord_mcp_server/services/channels.py`, le contrat
dans `models/` et l’exposition MCP dans `tools/channels.py`. Pour un domaine nouveau,
créer deux modules correspondants dans `services/` et `tools/`.

`ChannelInfo`, dans `models/__init__.py`, est un modèle Pydantic contenant les IDs
en chaînes, `guild_id`, `name`, `type`, `parent_id`, `topic`, `url` et les métadonnées
d’un fil. Réutiliser les contrats existants au lieu de renvoyer un texte mis en forme.
Les dates utilisent `datetime` et sont sérialisées en ISO 8601 par le SDK.

## 2. Accéder au client partagé et à discord.py

La fonction métier réelle est :

```python
from ..models import ChannelInfo
from .access import DiscordAccess
from .serialization import channel_info


async def get_channel_info(access: DiscordAccess, channel_id: str) -> ChannelInfo:
    return channel_info(await access.channel(channel_id))
```

`access` est créé une seule fois par `create_application`. Il donne accès au
runtime, aux paramètres et au client `access.client`. Son helper `channel` suit
ce chemin :

```python
ident = int(channel_id)
channel = access.client.get_channel(ident) or await access.client.fetch_channel(ident)
```

`get_channel` consulte le cache ; `fetch_channel` est la coroutine REST officielle
discord.py. Le helper vérifie ensuite le type de salon et son serveur avec
`access.check_guild(channel.guild.id)`. Il refuse les DM et les serveurs hors liste.
Cela permet notamment d’obtenir directement un fil archivé absent du cache, sans
avoir appelé `list_threads` auparavant.

Réutiliser `access.guild`, `access.channel`, `access.message_channel`, `access.message`
et `access.member` selon la ressource. Pour une méthode discord.py non couverte :
résoudre et autoriser la ressource avant de l’appeler. Si la méthode retourne une
autre ressource, vérifier aussi la portée de celle-ci. Une restriction ne doit
jamais reposer uniquement sur un `guild_id` fourni par l’appelant.

Ne pas utiliser `discord.Client()` ou `client.run()` dans l’outil. Ne pas démarrer
de thread ou de boucle asyncio supplémentaire. Lire la signature dans la
[référence discord.py de la version stable](https://discordpy.readthedocs.io/en/stable/api.html)
et utiliser `await` ou `async for` selon le contrat réel de la méthode.

## 3. Déclarer les paramètres et le résultat MCP

Dans `tools/channels.py`, la fonction `register_tools` enregistre explicitement
les fonctions locales :

```python
from mcp.server import MCPServer

from ..models import ChannelInfo, Snowflake
from ..services import channels
from ..services.access import DiscordAccess
from .common import READ


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=READ)
    async def get_channel_info(channel_id: Snowflake) -> ChannelInfo:
        """Get an allowed guild channel or thread, including uncached archived threads, by ID."""
        async with access.operation():
            return await channels.get_channel_info(access, channel_id)
```

Cet exemple correspond au code existant : ne pas l’ajouter une seconde fois.
Le décorateur est exécuté quand le registre appelle `register_tools`, et jamais
simplement à l’import du module. `access` est une dépendance partagée capturée par
la fermeture, pas un paramètre exposé au modèle. Les données de l’appel restent
dans les variables locales.

Le SDK **MCP v2** utilisé ici importe `MCPServer` depuis `mcp.server`. Il déduit les
schémas d’entrée et de sortie des annotations et du modèle Pydantic. Le résultat
est disponible dans `structuredContent` ; le client Python v2 y accède par
`result.structured_content`. Ne pas utiliser les chemins FastMCP des exemples v1.

Pour les nouveaux paramètres :

- Réutiliser `Snowflake` : chaîne décimale stricte, non nulle, bornée à 64 bits.
  Convertir en `int` seulement pour discord.py ; retourner les IDs en `str`.
- Réutiliser `PageLimit` : entier strict de 1 à 100. Documenter l’ordre, la borne
  exclusive et le paramètre recevant `next_cursor` ; retourner `null` à la fin.
- Définir les chaînes et choix avec `Annotated`, `Field`, `Literal` et des bornes.
  Exemple : `Annotated[str, Field(min_length=1, max_length=100, description="...")]`.
- Documenter dans la signature/docstring les effets des paramètres optionnels.
  Pour des activations sensibles, utiliser un booléen strict comme `AllowMentions`.
- Prévoir un modèle de retour spécifique si les modèles existants ne conviennent
  pas. Ne pas renvoyer d’objet discord.py, de token ou de données internes du client.

Les validations de schéma sont appliquées à la frontière MCP. Les règles métier
contextuelles, comme l’auteur d’un message ou les permissions, restent dans les
services et s’appliquent même si le client ment sur ses capacités.

## 4. Traduire les erreurs et borner l’opération

`async with access.operation()` effectue, dans cet ordre :

1. Une attente bornée de disponibilité du runtime partagé.
2. Une opération asynchrone bornée par `DISCORD_OPERATION_TIMEOUT`.
3. Une traduction des exceptions Discord et réseau dans `errors.py`.

`discord.Forbidden` devient `ACCESS_DENIED`, `discord.NotFound` devient `NOT_FOUND`,
un rejet HTTP 400 devient `INVALID_PARAMETER`, les erreurs réseau/HTTP restantes
deviennent `DISCORD_UNAVAILABLE` et un dépassement de délai devient `TIMEOUT`.
Les annulations asyncio sont propagées pour permettre un arrêt propre.

Une règle métier explicite se traduit ainsi :

```python
from ..errors import DiscordToolError

raise DiscordToolError("INVALID_PARAMETER", "Resource is not a thread.")
```

`DiscordToolError` dérive du `ToolError` officiel v2 : le client MCP reçoit un échec
avec `isError=true`. Ne jamais écrire `return {"error": "..."}` dans un outil
déclaré comme réussi. Ne pas recopier les corps HTTP d’erreur, les tokens ou les
contenus des messages dans les logs. Les erreurs inattendues restent des échecs
SDK et doivent être corrigées ; ne pas masquer tous les bugs dans un `except Exception`.

Choisir une annotation dans `tools/common.py`, ou en créer une adaptée :

| Constante | Usage |
| --- | --- |
| `READ` | Lecture seule, répétable |
| `WRITE` | Ajout non répétable, par exemple envoi d’un message |
| `EDIT` | Remplacement/suppression partielle d’un état, par exemple édition ou retrait de réaction |
| `DELETE` | Suppression, nouvel appel pouvant échouer après le premier |
| `REACTION_ADD` | Ajout de réaction répétable |

Une annotation renseigne le client. Elle n’accorde aucun droit et ne remplace pas
les contrôles de serveur, d’auteur ou de permission.

## 5. Enregistrer le domaine

Le module `tools/channels.py` est déjà appelé dans `tools/__init__.py` :

```python
def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    guilds.register_tools(mcp, access)
    channels.register_tools(mcp, access)
    messages.register_tools(mcp, access)
    threads.register_tools(mcp, access)
    members.register_tools(mcp, access)
```

L’extrait ci-dessus montre les domaines initiaux. Le registre actuel appelle
aussi explicitement `polls`, `manage_channels`, `roles`, `moderation`, `permissions`,
`integrations`, `events`, `search` et `private_messages`. Les modèles de ces
domaines se trouvent aussi dans `models/management.py` et `models/polls.py`.

Un outil ajouté à un domaine existant n’exige aucune modification du registre
central. Un nouveau domaine doit être importé puis appelé explicitement ici.
Ne pas ajouter une deuxième instance de serveur MCP.

## 6. Tester sans token et sans réseau

Les fixtures de `tests/conftest.py` fournissent `access` et des objets avec les
spécifications discord.py. Les méthodes asynchrones utilisent `AsyncMock` et les
itérateurs une vraie fonction asynchrone. Les connexions réseau sont interdites
automatiquement pendant tous les tests.

Exemple d’un test à ajouter à `tests/test_access.py` ou à un nouveau fichier :

```python
from conftest import make_channel
from mcp import Client
from mcp.server import MCPServer

from pydiscord_mcp_server.tools.channels import register_tools


async def test_get_channel_info_mcp(access):
    access.client.fetch_channel.return_value = make_channel()
    mcp = MCPServer("test-channel-info")
    register_tools(mcp, access)
    async with Client(mcp) as client:
        result = await client.call_tool("get_channel_info", {"channel_id": "200"})
        assert not result.is_error
        assert result.structured_content["id"] == "200"
        assert result.structured_content["guild_id"] == "100"
    access.client.fetch_channel.assert_awaited_once_with(200)
```

Cet exemple utilise le client officiel en mémoire. Le bot n’est pas démarré : la
fixture fournit une attente de disponibilité doublée. Les tests de cycle de vie
sont distincts et vérifient le démarrage réel de la tâche avec une connexion doublée.

Ajouter aussi les cas pertinents : ID invalide, ressource manquante, refus Discord,
serveur hors liste, cache absent, pagination finale et effets d’écriture. Pour une
action, vérifier qu’aucune méthode mutante n’a été appelée après un refus. Pour un
outil à mentions, vérifier les `AllowedMentions`, y compris lors des réponses.
Les tests existants `test_access.py`, `test_messages.py`, `test_threads.py` et
`test_mcp.py` donnent des exemples complets.

## 7. Documenter, vérifier et reconstruire

Ajouter l’outil au catalogue du README avec ses paramètres, permissions et limites.
Compléter également `docs/tools.md` et les tests du catalogue. Le fichier épinglé
`tests/fixtures/reference_tools.json` décrit le dépôt de référence : ne pas le
modifier pour y ajouter un outil propre au projet. Les tests ajoutent séparément
les extensions et vérifient que les 81 noms de référence restent couverts.
Ne pas promettre une recherche exhaustive si l’API ou le cache ne la fournit pas.

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest -q
docker compose up -d --build
```

Le code Python est intégré à l’image ; un simple redémarrage de l’ancienne image
ne suffit pas. Relancer la découverte des outils dans le client MCP après la
reconstruction. Si une dépendance change, mettre à jour `pyproject.toml` et `uv.lock`
ensemble avec uv avant de reconstruire. Une validation réelle en écriture demande
une instruction explicite et un salon de test ; les tests automatisés restent hors réseau.
