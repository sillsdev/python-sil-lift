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

Chaque `Problème` comporte un `niveau` (`"erreur"`/`"avertissement"`), un `code` fixe, un `message` et, le cas échéant, l'adresse associée au problème : `fichier` (`None` lorsque le lexique ne comporte pas de chemin d’accès), `entry_id` lorsqu’il concerne une entrée, `guid` lorsque l’objet concerné en possède un (une entrée ou un élément de plage), et `ligne` lorsqu’il correspond à une ligne du document. Une observation concernant un intervalle est adressée au compagnon `.lift-ranges` qui le définit, et ne comporte aucune entrée. Les champs non définis prennent la valeur `None` — `null` dans `--format json`, où chaque clé est toujours présente.

## Les couches

1. **RELAX NG** par rapport à la grammaire LIFT 0.13 (fournie par lift-standard — une copie identique au niveau des octets intégrée à ce paquet).
2. **Schéma des plages** — le fichier `lift-ranges-0.13.rng` de ce projet — s’applique à chaque compagnon `.lift-ranges` suivi ; il s’adresse au compagnon plutôt qu’au fichier `.lift`.
3. **Vérifications sémantiques** que la grammaire ne permet pas d'exprimer — neuf au total, à raison d'un code par vérification.

## Codes d'erreur

Chaque résultat comporte l'un de ces éléments, quelle que soit la couche qui l'a généré : « `schema` » et « `uri-not-rfc` » proviennent des couches de schéma, tandis que les neuf autres correspondent à des vérifications sémantiques. Les chaînes de caractères constituent une interface prise en charge ; l'option `--strict` transforme chaque avertissement en erreur.

| code                        | niveau        | ce qu'il signale                                                                                                  |
| --------------------------- | ------------- | ----------------------------------------------------------------------------------------------------------------- |
| `dangling-ranges-href`      | avertissement | un en-tête `range/@href` qui ne renvoie vers aucun fichier associé                                                |
| `référence pendante`        | erreur        | une `relation/@ref` ou une `variant/@ref` ne correspondant à aucune entrée ni à aucun sens                        |
| `duplicate-form-lang`       | avertissement | deux formes dans un même multitexte partageant une même langue                                                    |
| `duplicate-guid`            | erreur        | un identifiant réutilisé entre plusieurs entrées, ou entre les plages et les éléments de plage d'un même document |
| `identifiant manquant`      | erreur        | inscription via `require_ids` : une entrée sans GUID, une entrée sans identifiant                 |
| `fichiers-manquants`        | avertissement | un fichier audio ou image référencé qui ne se trouve pas sur le disque                                            |
| `décalage de normalisation` | avertissement | un nom qui n'accède à l'identifiant auquel il fait référence que via NFC                                          |
| `range-parent`              | erreur        | un élément `range-element/@parent` sans identifiant de frère n'est pas défini                                     |
| `schéma`                    | erreur        | une violation de la grammaire RELAX NG, dans le fichier `.lift` ou dans un fichier compagnon                      |
| `valeur hors plage`         | avertissement | une valeur de caractère liée à une information grammaticale ou à une plage que cette plage ne mentionne pas       |
| `uri-not-rfc`               | avertissement | un lien `href` qui n'est pas un URI valide — `file://C:/...` dans FLEx                                            |

Ces trois couches s'appuient sur ce que la fonction `save()` écrirait ; ainsi, un document qui ne peut absolument pas être sérialisé est signalé par une seule erreur de type `lone-surrogate` — voir [Garanties de fidélité](../fidelity.md#content-xml-cannot-represent).

## Résultats concrets de FieldWorks (FLEx)

FieldWorks génère systématiquement certains contenus qui sont rejetés par des outils de validation rigoureux. Voici la politique de sil-lift, afin que les véritables lexiques puissent être validés de manière utile :

- Les liens `file://C:/...` (URI non valides) sont signalés comme des **avertissements** (`uri-not-rfc`), et non comme des erreurs de schéma — le validateur C# ne les a jamais rejetés.
- Les éléments enfants légalement entrelacés (par exemple, « champ, note, champ, note » en quelque sorte) ne sont **pas** signalés, ce qui permet de contourner un faux positif dans libxml2.
- Les extensions `trait`/`field` de FLEx à l'intérieur de `range-element` **sont** signalées (erreurs de schéma par rapport au schéma des plages) : il s'agit de véritables écarts par rapport à la spécification.
- Les noms sont résolus par rapport aux plages et aux identifiants `id` des éléments de plage selon la **normalisation NFC** Unicode — liens `parent`, valeurs de plage, ainsi que le nom du `trait` ou l'identifiant `range` de l'en-tête qui sert de clé à une plage. Le format FLEx est normalisé en NFC lors de l'exportation, mais certaines opérations d'écriture contournaient cette étape ; ainsi, l'`id` d'un élément de plage peut être en NFD alors que ses étiquettes, son propre `parent` et les valeurs `.lift` qui le désignent sont en NFC.
  - Si l'on compare les deux cas, une exportation correcte semble présenter une erreur — et une plage dont l'`id` est orthographié différemment n'est absolument pas vérifiée, car un nom de trait qui ne correspond à aucune plage est accepté sans avertissement.
  - Un nom qui ne correspond qu'après normalisation fait l'objet d'un **avertissement** de type « `normalization-mismatch` », une fois par identifiant, quel que soit le nombre de références divergentes, adressé au fichier qui le définit. Les données sont correctes, mais un utilisateur qui comparerait des chaînes brutes ne parviendrait pas à résoudre ces références.
  - Les identifiants ne sont jamais modifiés : le fichier conserve l'orthographe d'origine.
