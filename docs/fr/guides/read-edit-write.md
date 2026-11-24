# Lire, modifier, rédiger

## Chargement en cours

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

La fonction `load()` accepte tout document LIFT **0.13** correctement formé, y compris les fichiers réels non conformes au schéma. Tout ce qui n'est pas défini par le modèle (éléments/attributs inconnus, commentaires) est conservé sans perte sous forme de résidu LIFT dans le champ opaque `extra` de chaque nœud. Les autres versions de LIFT génèrent une exception `LiftParseError` indiquant le nom de la version.

## Le modèle

Chaque élément de LIFT est une classe de données typée : `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, etc.

### Texte multilingue

Un texte multilingue est un `Multitext`, c'est-à-dire un `Mapping` entre un code de langue et un `Text` :

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # « poʻo »
entry.lexical_unit["en"] = "head"       # les chaînes de caractères brutes sont converties
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

Le `Texte` est structuré (une liste ordonnée de fragments `str` et `Span`) car `<text>` peut contenir des balises `<span>` imbriquées. `str(text)` convertit le contenu en texte brut ; les fragments conservent le balisage pour permettre la conversion aller-retour.

Le tableau indique une valeur par langue. En dessous, `forms` contient tous les `<form>` classés par ordre de fichier. Un document conforme au schéma comporte au maximum une forme par langue, mais dans la pratique, certains fichiers en comportent parfois plusieurs.

Comme le mappage est indexé par langue, la fonction `len()` compte le nombre de langues plutôt que le nombre de formulaires, et les vues `keys()`, `values()` et `items()` répertorient chaque langue une seule fois. Ces deux mutateurs agissent également sur l'ensemble du langage : `del entry.lexical_unit["en"]` supprime toutes les formes en anglais, et l'affectation à `"en"` n'en laisse qu'une seule.

Pour une langue répétée, `entry.lexical_unit["en"]`, `get()`, `values()` et `items()` renvoient tous sa première forme, et [`validate`](validate.md#problem-codes) signale l'erreur `duplicate-form-lang` tant que vous n'avez pas attribué de langue à cet élément.

Il n'est pas possible de créer, via le mappage, un formulaire ne comportant aucun attribut `lang`. Il est signalé sous le nom « form-missing-lang » et est supprimé lors de la resérialisation de son nœud.

### Sens et gloses

Dans LIFT, les glosses ont la forme d’une _forme_ (chaque `<gloss>` possède son propre langage) ; ainsi, un sens dispose de `glosses: list[Form]` ainsi que d’auxiliaires :

```python
sense = entry.senses[0]       # niveau supérieur uniquement
sense.gloss("en")             # Texte | None
entry.all_senses()            # tous les sens et sous-sens, dans l'ordre du document
entry.gloss_langs()           # {"en", "id"}, sous-sens inclus
```

Utilisez la fonction `all_senses()` chaque fois qu'une question concerne l'entrée dans son ensemble : compter les sens, recenser les langues, trouver des supports. `entry.senses` fournit le niveau supérieur, ce qui ne vous intéresse que lorsque l'imbrication elle-même a de l'importance.

## Enregistrement

```python
lex.save()                    # retour à l'emplacement d'où il a été chargé
lex.save("elsewhere.lift")
```

Les entrées que vous n'avez pas modifiées sont réécrites **à l'octet près** ; un document que vous n'avez pas du tout modifié est identique à l'octet près, du premier au dernier octet. Pour consulter le contrat dans son intégralité, voir [Garanties Fidelity](../fidelity.md).

### Horodatages

Les entrées que vous avez modifiées sont enregistrées avec une nouvelle valeur `dateModified` (et une valeur `dateCreated` si elles n'en avaient pas) ; ainsi, une modification n'est pas enregistrée avec la date à laquelle elle a été chargée. Les outils qui fusionnent LIFT déterminent ce qui a changé à partir de cet attribut. Deux arguments permettent de régler l'estampage :

- La fonction `lex.save(stamp=False)` enregistre uniquement les dates contenues dans le modèle, sans rien d'autre.
- La fonction `lex.save(when=...)` fige l'instant au lieu de se référer à l'horloge.

Consultez la page [Horodatages générés](../fidelity.md#generated-timestamps) pour connaître les autres règles.

### Ignorer une sauvegarde qui ne change rien

Pour ignorer une sauvegarde qui n'entraînerait aucun changement, protégez-la à l'aide de `lex.changes()` :

```python
si lex.changes() :
    lex.save()
```

Elle ne renvoie `False` que lorsque la fonction `save()` reproduirait les octets source, en incluant les entrées, l'en-tête, l'élément racine et chaque compagnon `.lift-ranges`. En omettant l'écriture, on conserve l'heure de modification du fichier et on évite ainsi un diff erroné.

Le chèque ne coûte pas cher. Il s'arrête dès la première différence ; ainsi, sur un lexique modifié, cela ne coûte pratiquement rien. Un lexique inchangé doit être sérialisé dans son intégralité pour prouver qu'il n'a pas changé, mais cela reste moins coûteux que l'opération de sauvegarde qu'il permet d'éviter.

Il compare le contenu, et non la destination ; veillez donc à n'enregistrer qu'en place. `lex.save("elsewhere.lift")` enregistre le document et ses fichiers associés dans le nouveau chemin d'accès même lorsque `changes()` vaut `False` ; par conséquent, en ajoutant une condition de vérification, on éviterait cette copie.

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
