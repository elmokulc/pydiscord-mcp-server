# Sondages natifs Discord

`create_poll` crée un véritable message contenant un **sondage Discord**, le même
type d’objet que celui proposé par le bouton **« + » → Sondage** dans l’application.
Les membres votent dans l’interface Discord habituelle. Le serveur utilise
`discord.Poll` et `channel.send(poll=...)` ; aucune collection de réactions ne
simule le vote.

## Créer un sondage

Appeler l’outil MCP `create_poll` avec :

```json
{
  "channel_id": "123456789012345678",
  "question": "Quel jour pour la réunion ?",
  "answers": [
    {"text": "Lundi", "emoji": "📅"},
    {"text": "Mardi", "emoji": "📅"},
    {"text": "Mercredi"}
  ],
  "duration_hours": 24,
  "allow_multiselect": false
}
```

Remplacer l’ID par celui d’un salon ou d’un fil autorisé qui accepte les messages.
Un forum lui-même ne reçoit pas directement de sondage : utiliser l’ID du fil
correspondant à son post. Un emoji personnalisé peut être indiqué sous la forme
`<:nom:ID>` si le bot y a accès. Les mentions sont désactivées pour la création.

Le bot doit posséder **View Channel**, **Send Messages** et **Send Polls** ; pour
un fil, vérifier également **Send Messages in Threads** et l’accès au fil.
Pour relire le sondage, accorder **Read Message History**. Message Content intent
peut être nécessaire pour lire les données de sondages créés par d’autres membres,
selon les exceptions Discord. Les résultats des sondages du bot sont accessibles
via REST sans activer une écoute Gateway des votes.

Limites validées avant tout envoi :

| Paramètre | Contrat |
| --- | --- |
| `question` | 1–300 caractères, non blanche |
| `answers` | 2–10 objets, chacun avec `text` et éventuellement `emoji` |
| `answers[].text` | 1–55 caractères, non blanc |
| `duration_hours` | Entier de 1 à 768 heures (32 jours), défaut 24 |
| `allow_multiselect` | Booléen strict, défaut `false` |

Les durées suivent les possibilités de l’API ; elles ne sont pas limitées aux
quelques durées prédéfinies affichées par l’interface Discord.

## Consulter et terminer

La création retourne un `MessageInfo` avec son `id`, son `channel_id`, son lien
Discord et un champ `poll`. Conserver ces IDs.

| Outil | Paramètres |
| --- | --- |
| `get_poll` | `channel_id`, `message_id` ; recharge les votes via REST |
| `end_poll` | `channel_id`, `message_id` ; clôture anticipée d’un sondage créé par ce bot |
| `get_poll_answer_voters` | `channel_id`, `message_id`, `answer_id`, `limit=25`, `after?` |

`poll` contient `question`, `answers` (ID numérique de réponse, texte, emoji,
votes), `allow_multiselect`, `expires_at`, `finalized` et `total_votes`. Les mêmes
données sont incluses dans `read_messages` et `get_message` quand Discord les
fournit. Les décomptes absents restent `null` et ne sont pas transformés en zéro.
Les chiffres d’un sondage en cours peuvent être approximatifs ; attendre
`finalized=true` pour le décompte définitif. Avec les choix multiples, ne pas
assimiler la somme des votes au nombre de personnes distinctes.

Pour les votants d’une réponse, utiliser l’ID renvoyé dans `answers[].id`, pas un
index supposé. Passer `next_cursor` dans `after` pour continuer la liste des
utilisateurs. Les IDs des utilisateurs restent des chaînes ; les IDs de réponses
au sondage sont des petits entiers propres au sondage.

Discord ne permet pas aux applications de voter et n’autorise pas la modification
du message du sondage après création. Aucun outil de vote ou de modification de
question/réponses n’est proposé. Pour corriger un sondage, en créer un nouveau et,
si souhaité, supprimer l’ancien avec `delete_message` selon les contrôles habituels.
Un sondage d’un autre auteur ne peut pas être terminé par ce bot.

## Vérification réelle

Les tests livrés utilisent uniquement des doublures et ne publient aucun sondage.
Après configuration de votre bot, demander explicitement la publication d’un
sondage dans un salon de test. Vérifier son rendu natif et voter manuellement dans
Discord, puis utiliser `get_poll` pour contrôler les résultats. Tester `end_poll`
uniquement sur un sondage jetable créé par le bot.

Références officielles consultées :
[Discord Poll Resource](https://docs.discord.com/developers/resources/poll),
[discord.py Poll](https://discordpy.readthedocs.io/en/stable/api.html#discord.Poll).
