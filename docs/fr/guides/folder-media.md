# Le dossier LIFT : gammes et supports

Un lexique LIFT se présente généralement sous la forme d'un _dossier_ : le fichier `.lift`, un ou plusieurs fichiers associés `.lift-ranges` (fichiers « sidecar ») et les fichiers multimédias contenus dans les dossiers `audio/` et `pictures/`.

## Gammes

```python
lex = sil_lift.load("dictionary.lift")      # compagnons suivis automatiquement

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # vue fusionnée {id: Range}
lex.all_ranges()["grammatical-info"].elements
```

La fonctionnalité « Companion Discovery » gère le monde réel : un `range/@href` pointant vers un fichier existant est utilisé ; les liens absolus « file://C:/... » orphelins de FieldWorks se rabattent sur le nom de base du lien situé à côté du fichier `.lift` ; et le fichier frère conventionnel `<name>.lift-ranges` est pris en compte même lorsqu'aucun autre élément ne le référence.

La fonction `lex.save()` enregistre le fichier `.lift` ainsi que tous les fichiers compagnons suivis. Les modifications apportées à un fichier `RangesFile` sont réenregistrées dans _ce_ fichier ; les plages non modifiées conservent exactement les mêmes octets. Utilisation autonome :

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

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
