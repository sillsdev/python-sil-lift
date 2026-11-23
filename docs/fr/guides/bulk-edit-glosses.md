# Exemple pratique : modification groupée des gloses

Une tâche de maintenance courante : harmoniser l'orthographe de toutes les entrées en anglais d'un lexique (anglais britannique → anglais américain, ou inversement) sans modifier aucun autre élément du fichier. Cet exemple présente un script qui charge, modifie, valide et enregistre des données, illustrant ainsi le fonctionnement conjoint de l'API d'édition et de la garantie de fidélité.

## Le scénario

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)

edited_glosses = 0

for entry in lex.entries:
    for sense in entry.all_senses():
        for gloss in sense.glosses :
            if gloss.lang != "en" :
                continue
            old = str(gloss.text)
            new = old.replace("colour", "color")
            si new != old :
                gloss.text = sil_lift.Text([new])
                edited_glosses += 1

changed = lex.changed_entries()

errors = [p pour p dans lex.iter_problems() si p.level == "error"]
si errors :
    for problem in errors:
        print(problem)
    sys.exit(f"interruption : {len(errors)} erreur(s) de validation, rien n'a été enregistré")

lex.save()
print(f" {edited_glosses} glossaire(s) modifié(s) dans {len(changed)} entrée(s)")
```

Quelques points à retenir :

- La fonction `entry.all_senses()` renvoie tous les sens _et sous-sens_, en suivant l'ordre des documents selon une exploration en profondeur.
  - `entry.senses` ne contient que le niveau supérieur ; par conséquent, une modification en masse parcourant cet élément ignorerait sans avertissement tout glossaire imbriqué sous un sens secondaire.
- `gloss.text` est un objet `Text`, et non une simple chaîne de caractères : `str(gloss.text)` l'aplatit pour permettre la correspondance, et le remplacement est réécrit à l'aide de `sil_lift.Text([new])` plutôt que de modifier la chaîne en place.
- La fonction `lex.changed_entries()` renvoie les entrées dont le contenu diffère de celui du fichier tel qu'il a été chargé. Toute modification effectuée n'importe où dans une entrée, même dans un sens secondaire imbriqué, entraîne la signalisation de cette entrée. Attribuer à un champ la valeur qu'il avait déjà ne génère aucun message, puisque le contenu reste inchangé.
- La fonction `changed_entries()` ne prend en compte que le contenu des entrées ; il s'agit donc d'un comptage, et non d'une protection contre l'écriture. Pour ignorer une sauvegarde qui n'entraînerait aucun changement, utilisez `lex.changes()` ; voir [Sauvegarde](read-edit-write.md#saving).
- La validation en mémoire (`lex.iter_problems()`) sérialise d'abord l'état modifié, ce qui permet de s'assurer qu'il reflète correctement les modifications avant que quoi que ce soit ne soit écrit sur le disque. L'interruption en cas de `Problem` de niveau « erreur » (les avertissements sont laissés à l'appréciation de l'appelant) garantit qu'une modification incorrecte n'atteindra jamais la fonction `save()`.
- La fonction `lex.save()` attribue une nouvelle valeur à `dateModified` uniquement pour les entrées modifiées par ce script, et remplit le champ `dateCreated` lorsqu'il était vide.
  - FieldWorks et l'importation LIFT de The Combine se basent tous deux sur la valeur de `dateModified` pour déterminer ce qu'il faut mettre à jour ; par conséquent, en l'absence de cette nouvelle date, ils considéreraient les entrées modifiées comme inchangées.
  - Seuls les éléments `<entry>` sont marqués. Lorsqu'une note explicative d'un sens secondaire est modifiée, la date apparaît dans l'entrée qui la contient, et non dans le sens lui-même.

## L'exécuter

Effectuez une recherche dans un petit lexique contenant un terme et une explication de sens secondaire qui indiquent tous deux « couleur » :

```
modification de 2 termes dans 1 entrée
```

## Les avantages de la fidélité

La garantie s'applique à chaque _entrée_ : une entrée dont le modèle n'a pas changé est restituée **à l'identique, octet par octet** par rapport à sa forme d'origine, et seules les entrées que vous avez réellement modifiées sont à nouveau sérialisées. Dans la série ci-dessus, les gloses d'une entrée ont été modifiées ; toutes les autres entrées du fichier ont conservé exactement les mêmes octets. La modification d'un terme dans un lexique de 50 000 entrées génère donc un fichier « diff » ne concernant qu'une seule entrée, et non un fichier reformaté.

Notez le niveau de détail : la modification d'une partie quelconque d'une entrée entraîne la resérialisation de l'intégralité de cette entrée, y compris ses sens apparentés qui n'ont pas été modifiés. Pour consulter le contrat dans son intégralité, voir [Garanties Fidelity](../fidelity.md).

## Au-delà des apparences

Cette approche s'applique également aux autres champs multilingues. Les gloses sont une liste de `Form`, mais les définitions et la plupart des autres champs multilingues sont des mappages `Multitext` indexés par langue ; une modification correspond donc à une simple affectation :

```python
sense.definition["en"] = "la couleur d'un objet"
```

Consultez [Texte multilingue](read-edit-write.md#multilingual-text) pour comprendre le fonctionnement de la mise en correspondance.
