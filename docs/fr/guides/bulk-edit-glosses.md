# Exemple pratique : modification groupée des gloses

Une tâche de maintenance courante : harmoniser l'orthographe de toutes les entrées en anglais d'un lexique (anglais britannique → anglais américain, ou inversement) sans modifier aucun autre élément du fichier. Cet exemple présente un script qui charge, modifie, valide et enregistre des données, illustrant ainsi le fonctionnement conjoint de l'API d'édition et de la garantie de fidélité.

## Le scénario

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)


def iter_senses(senses):
    """Renvoie chaque sens, y compris les sous-sens (récursif)."""
    for sense in senses:
        yield sense
        yield from iter_senses(sense.subsenses)


edited_glosses = 0
touched_entries = set()

for entry in lex.entries:
    for sense in iter_senses(entry.senses):
        for gloss in sense.glosses:
            if gloss.lang != "en":
                continue
            old = str(gloss.text)
            new = old.replace("colour", "color")
            if new != old:
                gloss.text = sil_lift.Text([new])
                edited_glosses += 1
                touched_entries.add(entry.id)

errors = [p for p in lex.iter_problems() if p.level == "error"]
if errors:
    for problem in errors:
        print(problem)
    sys.exit(f"Interruption : {len(errors)} erreur(s) de validation, rien n'a été enregistré")

lex.save()
print(f" {edited_glosses} s de glosses modifiés sur {len(touched_entries)} entrée(s)"")
```

Quelques points à retenir :

- `Sense.subsenses` est lui-même une `list[Sense]` ; ainsi, `iter_senses` effectue une itération récursive sur cet élément — une modification groupée qui ne parcourrait que `entry.senses` omettrait sans avertissement tout glossaire imbriqué sous un sens secondaire.
- `gloss.text` est un objet `Text`, et non une simple chaîne de caractères : `str(gloss.text)` l'aplatit pour permettre la correspondance, et le remplacement est réécrit à l'aide de `sil_lift.Text([new])` plutôt que de modifier la chaîne en place.
- La validation en mémoire (`lex.iter_problems()`) sérialise d'abord l'état modifié, ce qui permet de s'assurer qu'il reflète correctement les modifications avant que quoi que ce soit ne soit écrit sur le disque. L'interruption en cas de `Problem` de niveau « erreur » — les avertissements sont laissés à l'appréciation de l'appelant — garantit qu'une modification incorrecte n'atteindra jamais la fonction `save()`.

Les gloss ne sont pas les seuls produits qui méritent d'être appliqués de cette manière. La même surface de mappage `Multitext` s'applique aux définitions et à tous les autres champs multilingues d'une entrée ou d'un sens :

```python
sense.definition["en"] = "la couleur d'un objet"
```

## L'exécuter

Effectuez une recherche dans un petit lexique comportant une définition et une sous-définition qui indiquent toutes deux « couleur » :

```
modification de 2 termes dans 1 entrée
```

## Les avantages de la fidélité

La garantie s'applique à chaque _entrée_ : une entrée dont le modèle n'a pas changé est restituée **à l'identique au niveau des octets** par rapport à sa forme d'origine, et seules les entrées sur lesquelles vous avez effectivement intervenu sont à nouveau sérialisées. Dans l'extrait ci-dessus, les gloses d'une entrée ont été modifiées — toutes les autres entrées du fichier ont conservé exactement les mêmes octets. (Notez le niveau de détail : la modification d'une partie quelconque d'une entrée entraîne la resérialisation de l'intégralité de cette entrée, y compris ses sens apparentés qui n'ont pas été modifiés.) La modification d'un terme dans un lexique de 50 000 entrées génère donc un fichier « diff » ne concernant qu'une seule entrée, et non un fichier reformaté. Pour consulter le contrat dans son intégralité, voir [Garanties Fidelity](../fidelity.md).
