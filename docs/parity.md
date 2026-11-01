# Parité avec SaseQ/discord-mcp

Comparaison effectuée avec le catalogue et les signatures du dépôt
[SaseQ/discord-mcp](https://github.com/SaseQ/discord-mcp), commit
[`e134c03714cfadf786b686e3045b92537042a240`](https://github.com/SaseQ/discord-mcp/tree/e134c03714cfadf786b686e3045b92537042a240).
Le catalogue de référence compte **81 noms d’outils**. Ils sont tous présents dans
cette version Python ; les paramètres et les contrats restent propres à ce projet.
Le fichier `tests/fixtures/reference_tools.json` conserve cet inventaire et son
commit. Un test interdit de perdre un de ces noms ; chaque outil est aussi appelé
via le SDK MCP officiel avec des doublures Discord sans réseau.

**Total : 88 outils.** Les sept noms supplémentaires sont `list_guilds`,
`get_guild_info`, `get_member` et les quatre outils de sondage `create_poll`,
`get_poll`, `end_poll`, `get_poll_answer_voters`. Les trois premiers existaient
avant cette extension ; les équivalents `get_server_info` et `get_member_by_id`
sont conservés pour couvrir le vocabulaire du dépôt de référence.

Voir [le catalogue des 88 outils](tools.md) pour chaque nom et ses paramètres.

## Différences de contrat explicites

| Domaine | Contrat de ce serveur Python |
| --- | --- |
| Paramètres | `snake_case`, IDs en chaînes, limites numériques strictes ; objets `settings` pour les modifications complexes. La parité ne constitue pas une compatibilité automatique des arguments Java/camelCase. |
| Résultats | Objets Pydantic et `structuredContent`, erreurs MCP avec `isError=true`. |
| Sessions | Un seul client discord.py par processus HTTP ; mode HTTP sans état de session. |
| Autorisations | La liste de serveurs s’applique aussi aux accès directs, webhooks et invitations. Une invitation publique d’un serveur exclu reste refusée. |
| Messages privés | Les quatre outils existent mais sont désactivés par défaut. L’activation `DISCORD_ENABLE_DMS=true` impose aussi un serveur sélectionné autorisé et une vérification REST actuelle de l’appartenance du destinataire. Les outils de salons continuent de refuser les DM. |
| Mentions | Désactivées par défaut dans les messages, réponses, forums, webhooks et DM ; activation explicite et typée. |
| Webhooks | L’envoi reçoit `webhook_id`, pas une URL avec token. Le bot récupère le webhook, vérifie son serveur et son salon puis l’utilise. Aucun token ni URL secrète n’est renvoyé. Il faut les droits Discord permettant d’obtenir cette capacité. |
| Emojis | Images base64 (ou data URI image), 256 Kio maximum, types d’image vérifiés. Les URLs d’images arbitraires ne sont pas téléchargées ; fournir les octets encodés en base64. |
| Historique | Une seule borne `before`, `after` ou `around`. Direction et continuation explicites ; `around` reste une fenêtre sans curseur de continuation. |
| Recherche de messages | Balayage annoncé de 1–1000 messages dans un seul salon/fil ; aucun moteur de recherche global promis. Le curseur permet de reprendre après le dernier message parcouru. |
| Réponses à un message | Références explicites recherchées dans au plus 1000 messages postérieurs par appel ; le résultat expose son budget et son curseur `after`. Un message référencé déjà résolu est inclus sur un niveau dans `reply_to`. |
| Recherche de membres | ID ciblé par cache/REST ; noms dans le cache disponible et dans une requête Gateway par préfixe du nom/surnom. Noms globaux et surnoms hors cache peuvent manquer ; aucune exhaustivité promise. |
| Pagination des listes | Réponses bornées à 100 éléments ; certains endpoints Discord chargent une collection complète avant la pagination locale. |
| Fils archivés | Accès direct par ID avec récupération REST, sans découverte préalable ; pagination des archives publiques, privées et privées rejointes. |
| Forums | Posts actifs via `list_forum_posts`, archives via `list_threads`. Les tags doivent appartenir au forum ; une liste vide retire les tags. |
| Permissions | Fusion des seules permissions fournies, avec `null` pour l’héritage. Une suppression d’overwrite retire la surcharge entière. Les fils héritent du parent. |
| Modération et rôles | Motifs d’audit optionnels ; Discord impose permissions et hiérarchie. La suppression de messages lors d’un ban vaut zéro par défaut, au maximum sept jours si demandée. |
| Événements | Dates avec fuseau, cohérence début/fin, type de salon vérifié. Les événements externes exigent lieu et fin ; la liste des participants exige Members intent et retourne des identités utilisateur. |
| Sondages | Ajout spécifique utilisant les sondages natifs Discord ; création, résultats frais, clôture des sondages du bot et pagination des votants. Aucun vote automatisé par un bot. |

Cette réimplémentation utilise les API publiques de discord.py ; elle ne reprend
pas le code Java ni ses dépendances. Le catalogue épinglé documente la comparaison
à une date donnée, pas une synchronisation automatique avec les ajouts futurs du
dépôt distant.
