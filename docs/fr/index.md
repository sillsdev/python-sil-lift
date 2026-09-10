# sil-lift

Une bibliothèque Python pour [LIFT](https://github.com/sillsdev/lift-standard) (Lexicon Interchange FormaT) 0.13 : lecture/écriture sans perte du dossier LIFT (`.lift` + `.lift-ranges` + références multimédias), validation du schéma et de la sémantique, et tri canonique — avec des API de streaming pour les grands lexiques.

**Statut : version préliminaire, en cours de développement.**

## Installer

Extrait de [PyPI](https://pypi.org/project/sil-lift/) :

```
pip install sil-lift   # bibliothèque + la commande sil-lift
```

Nécessite Python 3.11 ou une version ultérieure. La seule dépendance d'exécution est lxml.

## La visite guidée de 30 secondes

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # suit également les entrées associées aux plages .lift

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("seh") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # ou lex.find(id="hoofd_a1b2")
entry.senses[0].definition["en"] = "head (anatomy)"

lex.save()   # les entrées non modifiées restent identiques au niveau des octets ; l'entrée modifiée est resérialisée
```
