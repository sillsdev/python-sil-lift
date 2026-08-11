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

for entry in lex.entries:
    for sense in iter_senses(entry.senses):
        for gloss in sense.glosses:
            if gloss.lang != "en":
                continue
            old = str(gloss.text)
            new = old.replace("colour", "color")
            if new != old :
                gloss.text = sil_lift.Text([new])
                edited_glosses += 1

changed = lex.changed_entries()

errors = [p for p in lex.iter_problems() if p.level == "error"]
if errors :
    for problem in errors:
        print(problem)
    sys.exit(f"interruption : {len(errors)} erreur(s) de validation, rien n'a été enregistré")

lex.save()
print(f" {edited_glosses} glossaire(s) modifié(s) sur {len(changed)} entrée(s)")
```

Quelques points à retenir :

- `Sense.subsenses` est lui-même une `list[Sense]` ; ainsi, `iter_senses` effectue une itération récursive sur cet élément — une modification groupée qui ne parcourrait que `entry.senses` omettrait sans avertissement tout glossaire imbriqué sous un sens secondaire.
- `gloss.text` est un objet `Text`, et non une simple chaîne de caractères : `str(gloss.text)` l'aplatit pour permettre la correspondance, et le remplacement est réécrit à l'aide de `sil_lift.Text([new])` plutôt que de modifier la chaîne en place.
- La fonction `lex.changed_entries()` indique quelles entrées diffèrent du fichier tel qu'il a été chargé. Étant donné que le résumé d'une entrée couvre l'ensemble de sa sous-arborescence, toute modification apportée à une sous-signification imbriquée se répercute sur l'entrée qui la contient.
  - Comme il compare du contenu sérialisé, le fait d'attribuer à un champ la valeur qu'il avait déjà n'est pas signalé.
  - Elle ne signale que les modifications de contenu ; les fonctions `lex.added_entries()` et `lex.removed_entries()` concernent les entrées qui sont apparues ou ont disparu depuis le chargement.
  - Elle renvoie les entrées elles-mêmes, sans tenir compte du fait que l'`id` puisse être dupliqué ou absent (ce que permet LIFT).
  - En tant que chiffre, il n'a de sens que s'il existe un élément de comparaison. Lorsque la couche de transit refuse d'effectuer un balayage octet par octet de la source — en raison d'un encodage non compatible ASCII ou d'un désaccord entre le scanner et l'analyseur —, il n'y a pas de référence, et la fonction `changed_entries()` signale _toutes_ les entrées. C'est la réponse honnête concernant la protection en écriture, puisque `save()` resérialise l'intégralité du fichier dans ce cas, mais cela signifie que le nombre correspond à la taille du lexique plutôt qu'à celle de la modification.
- La fonction `lex.changes()` indique si le document a subi la moindre modification. Cela concerne non seulement les entrées, mais aussi l'en-tête, l'élément racine et tous les éléments associés à `.lift-ranges`.
  - Cette condition n'est fausse que lorsque la fonction `save()` reproduirait les octets source, ce qui fait que `if not lex.changes(): ...` est la bonne façon d'éviter une écriture inutile. Cette garantie fonctionne dans un seul sens : elle ne signale jamais « rien à écrire » pour un document qui serait réécrit, tandis qu'une modification imposant une resérialisation complète peut aboutir aux mêmes octets d'origine et être tout de même signalée.
  - Comme cette fonction compare le contenu et non la destination, utilisez-la uniquement pour enregistrer le document à l'emplacement actuel : `lex.save(some_other_dir / "dictionary.lift")` écrit le document et ses fichiers associés dans un emplacement encore vide, qu'il y ait eu des modifications ou non.
  - It is a guard, not a speed-up — answering it digests every entry, which is the same work `save()` does to decide passthrough, so what you skip is the write itself (an untouched mtime, no spurious diff), not the effort of deciding.
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
