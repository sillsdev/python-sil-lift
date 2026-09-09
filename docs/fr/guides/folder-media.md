# Le dossier LIFT : gammes et supports

Un lexique LIFT se présente généralement sous la forme d'un _dossier_ : le fichier `.lift`, un ou plusieurs fichiers associés `.lift-ranges` (fichiers « sidecar ») et les fichiers multimédias contenus dans les dossiers `audio/` et `pictures/`.

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

### Companion discovery

Several candidates are tried, and every distinct file among them is loaded.

- A header `range/@href` that points at an existing file is used as given.
- An href that resolves to nothing falls back to its basename next to the `.lift` — FieldWorks writes dangling absolute `file://C:/...` paths from the exporting machine, and that fallback is what makes them work locally.
- The conventional `<name>.lift-ranges` sibling is picked up even when nothing references it.

Names that differ only in case or Unicode normalization still match — `Dict.LIFT` finds `Dict.lift-ranges` — unless several files match one name, which loads none of them and is reported as [`ambiguous-ranges-file`](validate.md#problem-codes).

Transmettez `resolve_ranges=False` à la fonction `load()` pour ignorer la recherche de composants associés.

## Médias

```python
for ref in lex.media_refs():        # toutes les références de type « <media> » et « <illustration>
    »     print(ref.kind, ref.href, ref.entry_id)

lex.missing_media()                 # références dont les fichiers n'existent pas
```

La résolution suit le schéma classique : un lien « href » relatif est vérifié tel qu'il est fourni (barres obliques inversées normalisées — WeSay écrit « pictures\photo with space.png ») et se trouve dans le répertoire « audio/ » (pour les fichiers audio de prononciation) ou « pictures/ » (pour les illustrations). Les liens « href » distants ou absolus ne peuvent pas être vérifiés et sont ignorés.

## Autres éléments du dossier

Un dossier LIFT contient souvent des fichiers que sil-lift ne modélise pas — le système d’écriture LDML dans `WritingSystems/`, les fichiers audio/image relatifs au consentement des locuteurs de The Combine dans `consent/`, etc. ; Les fonctions `load()` et `save()` ne les modifient pas, et [`Lexicon.save_zip()`](lift-export-interop.md) les transfère tels quels lors de la compression du dossier.
