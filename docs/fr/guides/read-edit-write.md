# Lire, modifier, rédiger

## Chargement en cours

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

La fonction `load()` accepte tout document LIFT **0.13** correctement formé, y compris les fichiers réels dont le schéma n'est pas valide. Tout ce qui n'est pas défini par le modèle (éléments ou attributs inconnus, commentaires) est conservé sans perte dans le compartiment opaque `extra` de chaque nœud. Les autres versions de LIFT génèrent une exception `LiftParseError` indiquant le nom de la version.

## Le modèle

Chaque élément de LIFT est une classe de données typée : `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, etc. Un texte multilingue est un `Multitext`, qui se comporte comme une correspondance entre un code de langue et un `Text` :

```python
entry = lex.find(id="abat")

str(entry.lexical_unit["seh"])          # "abat"
entry.lexical_unit["en"] = "grove"      # les chaînes de caractères brutes sont converties
"en" in entry.citation                  # False
```

Le `Texte` est structuré — il s'agit d'une liste ordonnée de fragments `str` et `Span` — car `<text>` peut contenir des balises `<span>` imbriquées. `str(text)` convertit le contenu en texte brut ; les fragments conservent le balisage pour permettre la conversion aller-retour.

Dans LIFT, les glosses ont la forme d’une _forme_ (chaque `<gloss>` possède son propre langage) ; ainsi, un sens est défini par `glosses: list[Form]` et dispose d’une fonction d’aide :

```python
sense = entry.senses[0]
sense.gloss("en")                       # Texte | None
entry.gloss_langs()                     # {"en", "id"}
```

## Enregistrement

```python
lex.save()                # retour à l'emplacement d'où il a été chargé
lex.save("elsewhere.lift")
```

Les entrées que vous n'avez pas modifiées sont réécrites **à l'octet près** ; un document que vous n'avez pas du tout modifié est identique à l'octet près, du premier au dernier octet. Pour consulter le contrat dans son intégralité, voir [Garanties Fidelity](../fidelity.md).

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
