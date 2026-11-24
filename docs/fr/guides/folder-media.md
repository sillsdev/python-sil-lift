# Le dossier LIFT : gammes et supports

Un lexique LIFT est généralement un _dossier_ : le fichier `.lift`, un ou plusieurs fichiers associés `.lift-ranges` (fichiers « sidecar ») et des fichiers multimédias situés dans les dossiers `audio/` et `pictures/`.

## Gammes

```python
lex = sil_lift.load("dictionary.lift")      # compagnons suivis automatiquement

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # vue fusionnée {id: Range}
lex.all_ranges()["grammatical-info"].elements
```

La fonction `lex.save()` enregistre le fichier `.lift` ainsi que tous les fichiers compagnons suivis. Les modifications apportées à un fichier `RangesFile` sont réenregistrées dans _ce_ fichier ; les plages non modifiées conservent exactement les mêmes octets. Utilisation autonome :

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

### Découverte de compagnons

Plusieurs candidats sont testés, et chaque fichier distinct parmi ceux-ci est chargé.

- Un en-tête `range/@href` pointant vers un fichier existant est utilisé tel quel.
- Un lien `href` qui ne renvoie rien utilise par défaut son nom de base suivi de `.lift`. FieldWorks génère des chemins absolus « dangling » de type `file://C:/...` à partir de la machine d'exportation, et c'est grâce à cette solution de secours qu'ils fonctionnent en local.
- L'élément frère conventionnel `<name>.lift-ranges` est pris en compte même si aucun élément ne le référence.

Les noms qui ne diffèrent que par la casse ou la normalisation Unicode sont toujours considérés comme identiques (`Dict.LIFT` trouve `Dict.lift-ranges`), sauf si plusieurs fichiers correspondent à un même nom : dans ce cas, aucun d'entre eux n'est chargé et une erreur [`ambiguous-ranges-file`](validate.md#problem-codes) est signalée.

Un fichier candidat qui ne peut pas être lu en tant que document `<lift-ranges>` (par exemple, un fichier de zéro octet issu d'une exportation interrompue) est ignoré plutôt que de provoquer l'échec du chargement, et est signalé comme [`unreadable-ranges-file`](validate.md#problem-codes). En revanche, le chargement direct à l'aide de `RangesFile.load()` provoque une exception.

Transmettez `resolve_ranges=False` à la fonction `load()` pour ignorer la recherche de composants associés.

## Médias

```python
for ref in lex.media_refs():        # toutes les références de type <media> et <illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.check_media()                   # références qui ne peuvent pas être résolues correctement
```

La résolution suit la structure classique : un lien « href » relatif est vérifié tel quel et se trouve dans le répertoire `audio/` (pour les fichiers audio de prononciation) ou `pictures/` (pour les illustrations). Les barres obliques inversées sont traitées comme des barres obliques, car WeSay génère des liens de type `pictures\photo with space.png`. Les liens « href » distants et absolus ne peuvent pas être vérifiés et sont ignorés.

La fonction `check_media()` ne signale que les références qui n'ont pas pu être résolues correctement, à raison d'un objet `MediaResolution` par référence :

- `status="missing"` : aucun fichier n'a correspondu à l'URL, quelle que soit la façon dont elle a été orthographiée.
- `status="mismatch"` : l'un d'entre eux l'a fait, mais uniquement en mode « case folding » ou NFC ; `found` indique le nom du fichier sur le disque.

Une erreur de correspondance est signalée alors que le fichier a bien été trouvé. Un nom de fichier associé est pris en compte de manière approximative sans commentaire, mais l'attribut href du média est également lu par le serveur qui héberge le dossier par la suite, et un hôte sensible à la casse ne trouvera pas le fichier. La validation signale le même problème que [`media-href-mismatch`](validate.md#problem-codes).

## Autres éléments du dossier

Un dossier LIFT contient souvent des fichiers que sil-lift ne modélise pas, tels que le système d'écriture LDML dans le répertoire `WritingSystems/` ou les fichiers de consentement des locuteurs de The Combine dans le répertoire `consent/`. Les fonctions `load()` et `save()` ne les modifient pas, et [`Lexicon.save_zip()`](lift-export-interop.md) les conserve tels quels lors de la compression du dossier.
