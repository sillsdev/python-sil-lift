# Valider

La validation est toujours explicite : le chargement et l'enregistrement n'entraînent jamais de validation implicite.

```python
import sil_lift

# Approche exhaustive : un flux paresseux de problèmes (schéma + couches sémantiques).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # erreur [dangling-ref] dictionary.lift:88 (entrée apu) : la référence « nope » correspond à...

# Détection rapide des erreurs : lève une exception LiftValidationError dès le premier problème de niveau d'erreur.
sil_lift.validate_file("dictionary.lift")

# État en mémoire (sérialisation préalable — un coût documenté pour les grands lexiques) :
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

Chaque « problème » comporte un « niveau » (« erreur »/« avertissement »), un « code » fixe, un « message » et une adresse : « fichier », « id_entrée », « guid », « ligne ».

## Les couches

1. **RELAX NG** par rapport à la grammaire LIFT 0.13 (fournie par lift-standard).
2. **Schéma Ranges** — le fichier `lift-ranges-0.13.rng` de ce projet — s'applique à tous les compagnons `.lift-ranges` suivis.
3. **Vérifications sémantiques** que la grammaire ne permet pas d'exprimer : `duplicate-guid`, `dangling-ref`, `range-parent`, `undefined-range-value`, `duplicate-form-lang`, `missing-media`.

## Résultats concrets de FieldWorks (FLEx)

FieldWorks génère systématiquement certains contenus qui sont rejetés par des outils de validation rigoureux. Voici la politique de sil-lift, afin que les véritables lexiques puissent être validés de manière utile :

- Les liens `file://C:/...` (URI non valides) sont signalés comme des **avertissements** (`uri-not-rfc`), et non comme des erreurs de schéma — le validateur C# ne les a jamais rejetés.
- Les éléments enfants légalement entrelacés (par exemple, « champ, note, champ, note » en quelque sorte) ne sont **pas** signalés, ce qui permet de contourner un faux positif dans libxml2.
- Les valeurs de plage sont comparées selon la normalisation Unicode NFC — FLEx écrit le fichier `.lift` en NFC, mais le fichier `.lift-ranges` en NFD au sein de la même exportation.
- Les extensions `trait`/`field` de FLEx à l'intérieur de `range-element` **sont** signalées (erreurs de schéma par rapport au schéma des plages) : il s'agit de véritables écarts par rapport à la spécification.
