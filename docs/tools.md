# Catalogue des 88 outils

Tous les outils sont enregistrés explicitement et possèdent un schéma d’entrée,
un schéma de sortie structuré et des annotations MCP. Le serveur partage un seul
client bot. Les outils de mutation restent soumis aux permissions Discord.

Les noms de paramètres sont en `snake_case`. `guild_id` omis utilise
`DISCORD_GUILD_ID` ; il reste obligatoire si aucun défaut n’est configuré.
Chaque ID Discord doit être une chaîne. `limit` vaut de 1 à 100.
`reason` est un motif facultatif pour le journal d’audit Discord.

| Outil | Paramètres requis | Paramètres facultatifs | Opération |
| --- | --- | --- | --- |
| `list_guilds` | — | `limit`, `after` | Lister les serveurs autorisés. |
| `get_guild_info` | — | `guild_id` | Lire les métadonnées d’un serveur. |
| `get_server_info` | — | `guild_id` | Lire les métadonnées du serveur (équivalent de get_guild_info). |
| `list_channels` | — | `guild_id`, `limit`, `after` | Lister les salons hors fils. |
| `get_channel_info` | `channel_id` | — | Lire un salon ou un fil, même archivé hors cache. |
| `read_messages` | `channel_id` | `limit`, `before`, `after`, `around` | Lire une page d’historique avec une seule borne. |
| `get_message` | `channel_id`, `message_id` | — | Lire un message et sa référence de réponse. |
| `send_message` | `channel_id`, `content` | `reply_to_message_id`, `allow_mentions` | Envoyer du texte, éventuellement en réponse. |
| `edit_message` | `channel_id`, `message_id`, `content` | `allow_mentions` | Modifier uniquement un message du bot. |
| `delete_message` | `channel_id`, `message_id` | `allow_other_author` | Supprimer un message ; opt-in et Manage Messages pour autrui. |
| `add_reaction` | `channel_id`, `message_id`, `emoji` | — | Ajouter une réaction au nom du bot. |
| `remove_reaction` | `channel_id`, `message_id`, `emoji` | `member_id` | Retirer une réaction ; Manage Messages pour celle d’autrui. |
| `list_threads` | `channel_id` | `mode`, `limit`, `cursor` | Lister les fils d’un parent, actifs ou archives accessibles. |
| `get_thread_info` | `thread_id` | — | Lire les métadonnées d’un fil directement par ID. |
| `get_member` | `member_id` | `guild_id` | Lire un membre avec cache puis REST. |
| `search_members` | `query` | `guild_id`, `limit` | Chercher un ID ciblé ou des noms dans le cache et les candidats Gateway. |
| `get_member_by_id` | `user_id` | `guild_id` | Lire un membre par ID stable (équivalent de get_member). |
| `get_user_id_by_name` | `username` | `guild_id` | Résoudre un nom d’utilisateur exact et non ambigu dans la portée disponible. |
| `create_poll` | `channel_id`, `question`, `answers` | `duration_hours`, `allow_multiselect` | Créer un sondage natif Discord avec question et options. |
| `get_poll` | `channel_id`, `message_id` | — | Rafraîchir un sondage et ses décomptes via REST. |
| `end_poll` | `channel_id`, `message_id` | — | Clôturer un sondage créé par ce bot. |
| `get_poll_answer_voters` | `channel_id`, `message_id`, `answer_id` | `limit`, `after` | Lister les personnes ayant choisi une réponse du sondage. |
| `create_text_channel` | `name` | `guild_id`, `settings`, `reason` | Créer un salon textuel avec options validées. |
| `edit_text_channel` | `channel_id`, `settings` | `reason` | Modifier nom, sujet, NSFW, slowmode, catégorie ou position. |
| `delete_channel` | `channel_id` | `reason` | Supprimer définitivement un salon ou un fil. |
| `find_channel` | `name` | `guild_id`, `limit`, `after` | Trouver les salons dont le nom correspond exactement, sans tenir compte de la casse. |
| `move_channel` | `channel_id` | `category_id`, `position`, `remove_category`, `reason` | Déplacer un salon dans une catégorie du même serveur ou changer sa position. |
| `create_category` | `name` | `guild_id`, `position`, `reason` | Créer une catégorie. |
| `edit_category` | `category_id`, `settings` | `reason` | Renommer ou repositionner une catégorie. |
| `delete_category` | `category_id` | `reason` | Supprimer la catégorie en conservant ses salons enfants. |
| `find_category` | `name` | `guild_id`, `limit`, `after` | Trouver les catégories dont le nom correspond exactement. |
| `list_channels_in_category` | `category_id` | `limit`, `after` | Lister les salons enfants d’une catégorie. |
| `create_voice_channel` | `name` | `guild_id`, `settings`, `reason` | Créer un salon vocal avec ses limites et sa région. |
| `create_stage_channel` | `name` | `guild_id`, `settings`, `reason` | Créer un salon de conférence Stage. |
| `edit_voice_channel` | `channel_id`, `settings` | `reason` | Modifier un salon vocal ou Stage. |
| `create_forum_channel` | `name` | `guild_id`, `settings`, `reason` | Créer un forum avec ses réglages par défaut. |
| `edit_forum_channel` | `channel_id`, `settings` | `reason` | Modifier les réglages d’un forum ou média. |
| `list_forum_channels` | — | `guild_id`, `limit`, `after` | Lister les forums et médias du serveur. |
| `get_forum_channel_info` | `channel_id` | — | Lire les métadonnées, tags et réglages d’un forum. |
| `list_forum_tags` | `channel_id` | — | Lister les tags disponibles d’un forum. |
| `create_forum_post` | `channel_id`, `title`, `content` | `tag_ids`, `allow_mentions`, `reason` | Créer un post avec son premier message et des tags valides. |
| `list_forum_posts` | `channel_id` | `limit`, `cursor` | Lister les posts actifs d’un forum ; archives via list_threads. |
| `modify_forum_post` | `post_id`, `settings` | `reason` | Verrouiller, archiver, épingler ou remplacer les tags d’un post. |
| `list_active_threads` | — | `guild_id`, `limit`, `after` | Lister les fils actifs accessibles d’un serveur. |
| `list_roles` | — | `guild_id`, `limit`, `after` | Lister les rôles et leurs permissions. |
| `create_role` | `name` | `guild_id`, `settings`, `reason` | Créer un rôle avec permissions, couleur et options. |
| `edit_role` | `role_id`, `settings` | `guild_id`, `reason` | Modifier les propriétés ou la position d’un rôle. |
| `delete_role` | `role_id` | `guild_id`, `reason` | Supprimer définitivement un rôle. |
| `assign_role` | `member_id`, `role_id` | `guild_id`, `reason` | Ajouter un rôle sans remplacer les autres rôles du membre. |
| `remove_role` | `member_id`, `role_id` | `guild_id`, `reason` | Retirer un rôle sans remplacer les autres rôles du membre. |
| `kick_member` | `member_id` | `guild_id`, `reason` | Expulser un membre du serveur. |
| `ban_member` | `member_id` | `guild_id`, `delete_message_seconds`, `reason` | Bannir un utilisateur ; suppression facultative de 0 à 7 jours de messages. |
| `unban_member` | `member_id` | `guild_id`, `reason` | Lever un bannissement, sans faire revenir automatiquement l’utilisateur. |
| `timeout_member` | `member_id`, `duration_seconds` | `guild_id`, `reason` | Restreindre la communication pendant 1 seconde à 28 jours. |
| `remove_timeout` | `member_id` | `guild_id`, `reason` | Lever une restriction temporaire de communication. |
| `set_nickname` | `member_id`, `nickname` | `guild_id`, `reason` | Changer le surnom ; null restaure le nom d’utilisateur. |
| `get_bans` | — | `guild_id`, `limit`, `after` | Lister les utilisateurs bannis et les motifs. |
| `move_member` | `member_id`, `channel_id` | `guild_id`, `reason` | Déplacer un membre vers un salon vocal du même serveur. |
| `disconnect_member` | `member_id` | `guild_id`, `reason` | Déconnecter un membre de son salon vocal. |
| `modify_voice_state` | `member_id` | `guild_id`, `mute`, `deafen`, `reason` | Appliquer ou retirer le mute/deafen serveur. |
| `list_channel_permission_overwrites` | `channel_id` | `limit`, `after` | Lister les surcharges explicites par rôle ou membre. |
| `upsert_role_channel_permissions` | `channel_id`, `role_id`, `changes` | `reason` | Fusionner les permissions d’un rôle avec sa surcharge existante. |
| `upsert_member_channel_permissions` | `channel_id`, `member_id`, `changes` | `reason` | Fusionner les permissions d’un membre avec sa surcharge existante. |
| `delete_channel_permission_overwrite` | `channel_id`, `target_id`, `target_type` | `reason` | Supprimer complètement une surcharge pour rétablir l’héritage. |
| `create_webhook` | `channel_id`, `name` | `reason` | Créer un webhook et retourner ses métadonnées sans secret. |
| `list_webhooks` | `channel_id` | `limit`, `after` | Lister les webhooks d’un salon sans exposer leurs tokens. |
| `delete_webhook` | `webhook_id` | `reason` | Supprimer un webhook après contrôle de son serveur. |
| `send_webhook_message` | `webhook_id`, `content` | `allow_mentions`, `thread_id` | Envoyer via un webhook autorisé, éventuellement dans l’un de ses fils. |
| `create_invite` | `channel_id` | `max_age`, `max_uses`, `temporary`, `unique`, `reason` | Créer une invitation avec durée et nombre d’usages bornés. |
| `list_invites` | — | `guild_id`, `limit`, `after` | Lister les invitations du serveur avec statistiques. |
| `delete_invite` | `code` | `reason` | Révoquer une invitation après contrôle de son serveur. |
| `get_invite_details` | `code` | — | Lire une invitation publique tout en appliquant la liste des serveurs autorisés. |
| `list_emojis` | — | `guild_id`, `limit`, `after` | Lister les emojis personnalisés du serveur. |
| `get_emoji_details` | `emoji_id` | `guild_id` | Lire un emoji personnalisé avec cache puis REST. |
| `create_emoji` | `name`, `image_base64` | `guild_id`, `role_ids`, `reason` | Téléverser un emoji depuis une image base64 de 256 Kio maximum. |
| `edit_emoji` | `emoji_id` | `guild_id`, `name`, `role_ids`, `reason` | Renommer un emoji ou remplacer ses restrictions par rôle. |
| `delete_emoji` | `emoji_id` | `guild_id`, `reason` | Supprimer définitivement un emoji personnalisé. |
| `create_guild_scheduled_event` | `name`, `start_time`, `entity_type` | `guild_id`, `channel_id`, `end_time`, `location`, `description`, `reason` | Créer un événement vocal, Stage ou externe avec dates et lieu cohérents. |
| `edit_guild_scheduled_event` | `event_id`, `settings` | `guild_id`, `reason` | Modifier les détails ou le statut d’un événement. |
| `delete_guild_scheduled_event` | `event_id` | `guild_id`, `reason` | Supprimer définitivement un événement. |
| `list_guild_scheduled_events` | — | `guild_id`, `with_user_count`, `limit`, `after` | Lister les événements planifiés et actifs du serveur. |
| `get_guild_scheduled_event_users` | `event_id` | `guild_id`, `limit`, `after` | Lister les personnes intéressées ; Members intent requis. |
| `search_messages` | `channel_id`, `query` | `limit`, `scan_limit`, `before` | Balayer au plus 1000 messages d’un salon ou fil pour du texte. |
| `get_message_replies` | `channel_id`, `message_id` | `limit`, `scan_limit`, `after` | Chercher des réponses explicites dans au plus 1000 messages postérieurs. |
| `send_private_message` | `user_id`, `content` | `guild_id`, `reply_to_message_id`, `allow_mentions` | Envoyer un DM après activation et vérification REST du serveur commun. |
| `read_private_messages` | `user_id` | `guild_id`, `limit`, `before`, `after`, `around` | Lire l’historique DM du bot après activation et autorisation. |
| `edit_private_message` | `user_id`, `message_id`, `content` | `guild_id`, `allow_mentions` | Modifier uniquement un DM envoyé par ce bot. |
| `delete_private_message` | `user_id`, `message_id` | `guild_id` | Supprimer uniquement un DM envoyé par ce bot. |

## Objets de modification

Les objets `settings` rejettent les champs inconnus. Omettre un champ conserve
sa valeur. Les exceptions ci-dessous décrivent les remises à zéro explicites.

| Objet | Champs |
| --- | --- |
| Salon textuel | `name`, `topic` (1024 caractères maximum), `nsfw`, `slowmode_delay` (0–21600 s), `category_id` (null retire la catégorie), `position` |
| Catégorie | `name`, `position` |
| Vocal / Stage | `name`, `bitrate` (8000–384000, borné aussi par Discord), `user_limit` (0–99), `rtc_region` (null = automatique), `category_id`, `position` |
| Forum | `name`, `topic` (4096 caractères maximum), `nsfw`, `slowmode_delay`, `default_thread_slowmode_delay`, `category_id`, `position`, `default_sort_order` (`latest_activity`/`creation_date`), `default_layout` (`not_set`/`list_view`/`gallery_view`) |
| Post de forum | `locked`, `archived`, `pinned`, `tag_ids` (0–5 IDs du forum ; [] vide les tags) |
| Rôle | `name`, `permissions` (bitset décimal en chaîne), `colour` (entier RGB 0–16777215), `hoist`, `mentionable`, `position` (édition seulement) |
| Événement | `name`, `description`, `start_time`, `end_time`, `location` (externe), `status` (`scheduled`/`active`/`completed`/`cancelled`) |

Les surcharges utilisent `changes={"permissions":{"send_messages":false}}` :
`true` autorise, `false` interdit et `null` rétablit l’héritage de ce champ.
Les autres champs de la surcharge sont conservés. Les noms valides sont ceux
de `discord.Permissions` ; discord.py peut retourner leur nom canonique, par
exemple `read_messages` pour l’alias `view_channel`. Les fils héritent des
permissions de leur parent et ne reçoivent pas de surcharge indépendante.

## Pagination, portée et effets

- Les listes triées par ID utilisent généralement `after=next_cursor` ; les
  invitations utilisent le code dans `after`. Les listes de tags sont bornées
  par Discord et n’ont pas besoin de curseur.
- `list_threads` et `list_forum_posts` utilisent un `cursor` opaque ; conserver
  le même parent et mode. `list_forum_posts` concerne les actifs ; consulter
  `list_threads(mode="archived_public")` pour les archives de forum.
- L’historique utilise une seule borne `before`, `after` ou `around`. Le champ
  `cursor_parameter` indique la direction à réutiliser ; `around` ne fournit
  pas de continuation. Les recherches sont limitées à 1000 messages par appel.
- Les listes de salons/rôles/emojis et les recherches de membres peuvent lire
  le cache. Certains endpoints Discord renvoient une collection complète avant
  la pagination locale ; la taille de la réponse MCP reste bornée.
- `allow_mentions=false` partout par défaut, y compris réponses, forums, DM et
  webhooks. Son activation explicite autorise toutes les catégories de mention.
- Un changement d’état dépend des permissions et de la hiérarchie Discord,
  même si son annotation MCP le présente comme répétable.
- Les outils privés exigent `DISCORD_ENABLE_DMS=true`, un serveur sélectionné
  autorisé et l’appartenance REST actuelle du destinataire à ce serveur.
- Les tokens de webhook ne figurent jamais dans les résultats ; l’envoi utilise
  un ID de webhook résolu par le compte bot. Les images d’emoji sont fournies
  en base64 ; aucune URL arbitraire n’est téléchargée par le serveur.

Voir [les sondages natifs](polls.md), [la parité détaillée](parity.md),
[les permissions et intents](../README.md#créer-et-inviter-le-bot) et
[le tutoriel d’ajout](adding-tools.md).
