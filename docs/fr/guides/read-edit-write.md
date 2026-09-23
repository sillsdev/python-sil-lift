# Lire, modifier, rédiger

## Chargement en cours

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

La fonction `load()` accepte tout document LIFT **0.13** correctement formé, y compris les fichiers réels dont le schéma n'est pas valide. Tout ce qui n'est pas défini par le modèle (éléments/attributs inconnus, commentaires) est conservé sans perte sous forme de résidu LIFT dans le champ opaque `extra` de chaque nœud. Les autres versions de LIFT génèrent une exception `LiftParseError` indiquant le nom de la version.

## Le modèle

Chaque élément de LIFT est une classe de données typée : `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, etc. Un texte multilingue est un `Multitext`, c'est-à-dire un `Mapping` entre un code de langue et un `Text` :

```python
entry = lex.find(id="abat")

str(entry.lexical_unit["seh"])          # « abat »
entry.lexical_unit["en"] = "grove"      # les chaînes de caractères brutes sont converties
"en" in entry.citation                  # Faux
list(entry.lexical_unit.keys())         # ["seh", "en"]
```

`keys()`, `values()` et `items()` sont des vues, avec une clé par langue, et `len()` compte le nombre de langues plutôt que le nombre de formulaires. Ces deux mutateurs agissent sur la langue dans son ensemble plutôt que sur une forme en particulier : `del entry.lexical_unit["en"]` supprime toutes les formes en anglais, tandis qu'une affectation à `"en"` n'en laisse qu'une seule.

Un document conforme au schéma ne contient rien de plus, mais les fichiers réels reprennent parfois un langage. `forms` contient tous les formulaires classés par ordre de fichier ; il lit la réponse du premier formulaire, et [`validate`](validate.md#problem-codes) signale l'erreur `duplicate-form-lang` tant que vous n'avez pas attribué de langue à ce formulaire. Un formulaire ne comportant aucun attribut `lang` ne peut pas être créé via le mappage ; il est signalé comme `form-missing-lang` et est supprimé lors de la resérialisation de son nœud.

Le `Texte` est structuré — il s'agit d'une liste ordonnée de fragments `str` et `Span` — car `<text>` peut contenir des balises `<span>` imbriquées. `str(text)` convertit le contenu en texte brut ; les fragments conservent le balisage pour permettre la conversion aller-retour.

Dans LIFT, les glosses ont la forme d’une _forme_ (chaque `<gloss>` possède son propre langage) ; ainsi, un sens dispose de `glosses: list[Form]` ainsi que d’auxiliaires :

```python
sense = entry.senses[0]                 # niveau supérieur uniquement
sense.gloss("en")                       # Texte | None
entry.all_senses()                      # tous les sens et sous-sens, dans l'ordre du document
entry.gloss_langs()                     # {"en", "id"}, sous-sens inclus
```

Utilisez la fonction `all_senses()` chaque fois qu'une question concerne l'entrée dans son ensemble : compter les sens, recenser les langues, trouver des supports. `entry.senses` fournit le niveau supérieur, ce qui ne vous intéresse que lorsque l'imbrication elle-même a de l'importance.

## Enregistrement

```python
lex.save()                # retour à l'emplacement d'où il a été chargé
lex.save("elsewhere.lift")
```

Les entrées que vous n'avez pas modifiées sont réécrites **à l'octet près** ; un document que vous n'avez pas du tout modifié est identique à l'octet près, du premier au dernier octet. Pour consulter le contrat dans son intégralité, voir [Garanties Fidelity](../fidelity.md).

Les entrées que vous avez modifiées sont envoyées avec une nouvelle valeur `dateModified` (et une valeur `dateCreated` si elles n'en avaient pas) ; ainsi, une modification n'est pas transmise avec la date à laquelle elle a été chargée — ce sont les outils qui fusionnent LIFT qui déterminent ce qui a changé à partir de cet attribut. `lex.save(stamp=False)` enregistre uniquement les dates contenues dans le modèle, sans rien d'autre ; `lex.save(when=...)` fixe un instant précis au lieu de se baser sur l'heure. Consultez la page [Horodatages générés](../fidelity.md#generated-timestamps) pour connaître les autres règles.

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
