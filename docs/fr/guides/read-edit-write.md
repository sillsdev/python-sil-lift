# Lire, modifier, rédiger

## Chargement en cours

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` accepts any well-formed LIFT **0.13** document, including schema-invalid real-world files. Tout ce qui n'est pas défini par le modèle (éléments/attributs inconnus, commentaires) est conservé sans perte sous forme de résidu LIFT dans le champ opaque `extra` de chaque nœud. Les autres versions de LIFT génèrent une exception `LiftParseError` indiquant le nom de la version.

## Le modèle

Every LIFT element is a typed dataclass: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, and so on.

### Multilingual text

Un texte multilingue est un `Multitext`, c'est-à-dire un `Mapping` entre un code de langue et un `Text` :

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # plain strings are coerced
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` is structured (an ordered list of `str` and `Span` fragments) because `<text>` can contain nested `<span>` markup. `str(text)` convertit le contenu en texte brut ; les fragments conservent le balisage pour permettre la conversion aller-retour.

The mapping shows one value per language. Underneath, `forms` holds every `<form>` in file order. A schema-valid document has at most one form per language, but real files sometimes repeat one.

Because the mapping is keyed by language, `len()` counts languages rather than forms, and the `keys()`, `values()` and `items()` views list each language once. Both mutators also act on the whole language: `del entry.lexical_unit["en"]` removes every English form, and assigning to `"en"` leaves exactly one.

For a repeated language, `entry.lexical_unit["en"]`, `get()`, `values()` and `items()` all answer with its first form, and [`validate`](validate.md#problem-codes) reports `duplicate-form-lang` until you assign to that language.

A form carrying no `lang` at all cannot be created through the mapping. It is reported as `form-missing-lang`, and is dropped when its node re-serializes.

### Senses and glosses

Dans LIFT, les glosses ont la forme d’une _forme_ (chaque `<gloss>` possède son propre langage) ; ainsi, un sens dispose de `glosses: list[Form]` ainsi que d’auxiliaires :

```python
sense = entry.senses[0]       # top level only
sense.gloss("en")             # Text | None
entry.all_senses()            # every sense and subsense, document order
entry.gloss_langs()           # {"en", "id"}, subsenses included
```

Utilisez la fonction `all_senses()` chaque fois qu'une question concerne l'entrée dans son ensemble : compter les sens, recenser les langues, trouver des supports. `entry.senses` fournit le niveau supérieur, ce qui ne vous intéresse que lorsque l'imbrication elle-même a de l'importance.

## Enregistrement

```python
lex.save()                    # back to where it was loaded from
lex.save("elsewhere.lift")
```

Les entrées que vous n'avez pas modifiées sont réécrites **à l'octet près** ; un document que vous n'avez pas du tout modifié est identique à l'octet près, du premier au dernier octet. Pour consulter le contrat dans son intégralité, voir [Garanties Fidelity](../fidelity.md).

### Horodatages

Les entrées que vous avez modifiées sont enregistrées avec une nouvelle valeur `dateModified` (et une valeur `dateCreated` si elles n'en avaient pas) ; ainsi, une modification n'est pas enregistrée avec la date à laquelle elle a été chargée. Tools that merge LIFT decide what changed from that attribute. Two arguments adjust the stamping:

- `lex.save(stamp=False)` writes the dates the model holds and nothing more.
- `lex.save(when=...)` pins the moment instead of reading the clock.

Consultez la page [Horodatages générés](../fidelity.md#generated-timestamps) pour connaître les autres règles.

### Skipping a save that changes nothing

Pour ignorer une sauvegarde qui n'entraînerait aucun changement, protégez-la à l'aide de `lex.changes()` :

```python
si lex.changes() :
    lex.save()
```

Elle ne renvoie `False` que lorsque la fonction `save()` reproduirait les octets source, en incluant les entrées, l'en-tête, l'élément racine et chaque compagnon `.lift-ranges`. Skipping the write leaves the file's modification time alone and avoids a spurious diff.

The check is cheap. Il s'arrête dès la première différence ; ainsi, sur un lexique modifié, cela ne coûte pratiquement rien. Un lexique inchangé doit être sérialisé dans son intégralité pour prouver qu'il n'a pas changé, mais cela reste moins coûteux que l'opération de sauvegarde qu'il permet d'éviter.

Il compare le contenu, et non la destination ; veillez donc à n'enregistrer qu'en place. `lex.save("elsewhere.lift")` writes the document and its companions to the new path even when `changes()` is `False`, so guarding it would skip that copy.

## Construire à partir de zéro

```python
lex = sil_lift.Lexicon(producer="my-script 1.0")
entry = sil_lift.Entry(id="hello", guid="...")
entry.lexical_unit["en"] = "hello"
sense = sil_lift.Sense()
sense.glosses.append(sil_lift.Form("fr", sil_lift.Text(["bonjour"])))
entry.senses.append(sense)
lex.entries.append(entry)
lex.save("new.lift")
```

## Tri canonique

```python
lex.sort()      # entrées classées par (guid, id) ; plages/définitions de champs par id/balise
lex.save()      # les entrées inchangées conservent exactement les mêmes octets, dans le nouvel ordre

sil_lift.canonicalize("in.lift", "out.lift")   # entièrement resérialisé, prêt pour la comparaison des différences
```

Voir aussi : [Exemple pratique : modification groupée des gloses](bulk-edit-glosses.md).
