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

### Découverte de compagnons

Plusieurs candidats sont testés, et chaque fichier distinct parmi ceux-ci est chargé.

- Un en-tête `range/@href` pointant vers un fichier existant est utilisé tel quel.
- Un lien `href` qui ne renvoie rien utilise par défaut son nom de base suivi de `.lift` — FieldWorks génère des chemins absolus « orphelins » de type `file://C:/...` à partir de la machine d'exportation, et c'est ce recours par défaut qui leur permet de fonctionner localement.
- L'élément frère conventionnel `<name>.lift-ranges` est pris en compte même si aucun élément ne le référence.

Les noms qui ne diffèrent que par la casse ou la normalisation Unicode sont toujours considérés comme identiques — `Dict.LIFT` trouve `Dict.lift-ranges` — sauf si plusieurs fichiers correspondent à un même nom, auquel cas aucun d’entre eux n’est chargé et une erreur [`ambiguous-ranges-file`](validate.md#problem-codes) est signalée.

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
