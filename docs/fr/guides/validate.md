# Valider

La validation est toujours explicite : le chargement et l'enregistrement ne provoquent jamais de validation implicite.

```python
import sil_lift

# Exhaustif : un flux paresseux de problèmes (schéma + couches sémantiques).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # erreur [dangling-ref] dictionary.lift:88 (entrée apu) : la référence « nope » correspond à...

# Échec rapide : s'arrêter dès le premier problème de niveau « erreur ».
if any(p.level == "error" for p in sil_lift.iter_problems("dictionary.lift")):
    raise SystemExit(1)

# État en mémoire (sérialisation préalable, coût documenté pour les grands lexiques) :
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

Chaque `Problème` comporte un `niveau` (`« erreur »`/`« avertissement »`), un `code` fixe et un `message`, ainsi que l'adresse complète associée à ce problème, si celle-ci est disponible :

- `fichier` : `None` lorsque le lexique n'a pas de chemin d'accès.
- `entry_id` : à définir lorsque la découverte concerne une seule entrée.
- `guid` : défini lorsque l'objet concerné en possède un (une entrée ou un élément de plage).
- `ligne` : à définir lorsque le résultat correspond à une ligne du document.

Une observation concernant un intervalle est adressée au compagnon `.lift-ranges` qui le définit, et ne comporte aucune entrée. Les champs non définis prennent la valeur `None` (`null` avec l'option `--format json`, où chaque clé est toujours présente).

## Les couches

1. **Schéma LIFT** (`lift-0.13.rng`, la grammaire RELAX NG de LIFT 0.13, fournie par le fournisseur et identique au niveau des octets à celle de lift-standard) sur le fichier `.lift`.
2. **Le schéma « ranges »** (`lift-ranges-0.13.rng`, également fourni par lift-standard) s'applique à chaque compagnon `.lift-ranges` suivi, et s'adresse au compagnon plutôt qu'à `.lift`.
3. **Vérifications sémantiques** que les schémas ne permettent pas d'exprimer : treize au total, à raison d'un code par vérification.

## Codes d'erreur

Chaque résultat comporte l'un de ces éléments, quelle que soit la couche qui l'a généré : « schema » et « uri-not-rfc » proviennent des couches de schéma, les autres correspondent à des vérifications sémantiques. Tous les codes sont vérifiés par défaut, à l'exception de `missing-id`, qui est une option à activer manuellement : passez l'argument `require_ids=True` (ou `--require-ids`) pour l'activer. Les codes sont stables, ce qui permet aux scripts de les utiliser comme critères de correspondance. L'option `--strict` transforme chaque avertissement en erreur. La commande `sil-lift validate --allow CODE` exclut un code de la décision de réussite ou d'échec.

| code                           | niveau        | ce qu'il signale                                                                                                  |
| ------------------------------ | ------------- | ----------------------------------------------------------------------------------------------------------------- |
| `fichier-des-plages-ambiguës`  | avertissement | plusieurs fichiers correspondant à un même nom de compagnon en mode « case folding » et NFC                       |
| `dangling-ranges-href`         | avertissement | un en-tête `range/@href` qui ne renvoie vers aucun fichier associé                                                |
| `référence pendante`           | erreur        | une `relation/@ref` ou une `variant/@ref` ne correspondant à aucune entrée ni à aucun sens                        |
| `duplicate-form-lang`          | avertissement | deux formes dans un même multitexte partageant une même langue                                                    |
| `duplicate-guid`               | erreur        | un identifiant réutilisé entre plusieurs entrées, ou entre les plages et les éléments de plage d'un même document |
| `form-missing-lang`            | erreur        | un `<form>` ou `<gloss>` sans l'attribut `lang` requis par le schéma                                              |
| `media-href-mismatch`          | avertissement | un lien href vers un fichier multimédia qui n'est accessible qu'en mode « case folding » ou NFC                   |
| `identifiant manquant`         | erreur        | **[opt-in]** une entrée sans guid, un sens sans id            |
| `fichiers-manquants`           | avertissement | un fichier audio ou image référencé qui ne se trouve pas sur le disque                                            |
| `décalage de normalisation`    | avertissement | un nom qui n'accède à l'identifiant auquel il fait référence que via NFC                                          |
| `range-parent`                 | erreur        | un élément `range-element/@parent` sans identifiant de frère n'est pas défini                                     |
| `schéma`                       | erreur        | une violation de la grammaire RELAX NG, dans le fichier `.lift` ou dans un fichier compagnon                      |
| `valeur hors plage`            | avertissement | une valeur de caractère liée à une information grammaticale ou à une plage que cette plage ne mentionne pas       |
| `fichier-de-plages-illisibles` | avertissement | un candidat associé qui existe mais qui n'est pas un document de plages lisible                                   |
| `uri-not-rfc`                  | avertissement | un lien `href` qui n'est pas un URI valide (par exemple, `file://C:/...` dans FLEx)            |

### Ce que la validation permet de voir

Ces trois couches fonctionnent à partir du document tel qu'il est sérialisé ; ainsi, un document qui ne peut pas être sérialisé du tout est signalé par une seule erreur de type « `lone-surrogate` ». Voir [les garanties de fidélité](../fidelity.md#content-xml-cannot-represent).

La validation est en lecture seule : elle reflète l'état actuel du document, avant qu'une opération d'enregistrement n'y appose la date `dateModified`. Les tampons ne déclenchent jamais de détection d'erreur ; ainsi, un document qui passe la validation reste valide une fois enregistré.

### Codes des dossiers associés

Un nom de compagnon correspondant à plusieurs fichiers n'en charge aucun : les plages qu'ils définissent disparaissent jusqu'à ce que tous, sauf un, soient renommés ou supprimés.

Les trois codes relatifs aux dossiers associés (`ambiguous-ranges-file`, `dangling-ranges-href` et `unreadable-ranges-file`) ne sont signalés que lorsque la détection des dossiers associés a été effectuée :

- Le chargement avec `resolve_ranges=False` place les éléments associés hors de portée, ce qui fait qu'aucun d'entre eux n'est signalé.
- Le fait d'en ajouter un par la suite avec `add_ranges_file()` ne permet pas de les récupérer, car cette fonction ne lit jamais le dossier sur lequel portent ces codes.

`resolve_ranges=False` n'a aucune incidence sur `missing-media` ou `media-href-mismatch` : les médias ne sont jamais intégrés au modèle, il n'y a donc rien à désactiver.

### Codes médias

sil-lift recherche chaque fichier multimédia à l'adresse href indiquée, ainsi que dans les dossiers `audio/` (fichiers audio) ou `pictures/` (illustrations). Ce dossier correspond à une hypothèse de sil-lift, et non à une mention figurant dans le document ; il s'adapte donc à n'importe quelle casse et son orthographe n'est jamais signalée.

Les codes `missing-media` et `media-href-mismatch` se répartissent la vérification des médias : le premier indique qu'aucun fichier ne correspond à l'href, quelle que soit l'orthographe, tandis que le second signifie qu'un fichier correspond, mais que l'href ne le désigne pas exactement. Le deuxième point concerne la portabilité : le fichier se trouve ici, mais un serveur qui gère ce dossier en distinguant les majuscules des minuscules ne le trouvera pas.

Un _dossier_ mal orthographié ne nécessite qu'un seul changement de nom, quel que soit le nombre de références qui y renvoient ; il est donc signalé une seule fois et ne fait l'objet d'aucune entrée. Une erreur d'orthographe dans le _nom de fichier_ est signalée par référence, à l'attention de l'entrée qui l'a générée.

## Résultats concrets de FieldWorks (FLEx)

FieldWorks génère systématiquement certains contenus qui sont rejetés par des outils de validation rigoureux. Voici la politique de sil-lift, afin que les véritables lexiques puissent être validés de manière utile :

- Les liens `file://C:/...` (URI non valides) sont signalés comme des **avertissements** (`uri-not-rfc`), et non comme des erreurs de schéma ; le validateur C# ne les a jamais rejetés.
- Les éléments enfants légalement entrelacés (par exemple, « champ, note, champ, note » en quelque sorte) ne sont **pas** signalés ; cela permet d'ignorer un faux positif dans libxml2.
- Les extensions `trait`/`field` de FLEx à l'intérieur de `range-element` **sont** signalées (erreurs de schéma par rapport au schéma des plages) : il s'agit de véritables écarts par rapport à la spécification.
- Les noms sont résolus par rapport aux plages et aux identifiants `id` des éléments de plage selon la **normalisation NFC** Unicode : liens `parent`, valeurs de plage, ainsi que le nom du `trait` ou l'identifiant `range` de l'en-tête qui sert de clé à une plage.
  - Le format FLEx est normalisé en NFC lors de l'exportation, mais certaines opérations d'écriture contournaient cette étape ; ainsi, l'`id` d'un élément de plage peut être en NFD alors que ses étiquettes, son propre `parent` et les valeurs `.lift` qui le désignent sont en NFC.
  - Une comparaison stricte conduirait à deux erreurs. Les références à un identifiant NFD seraient signalées comme non valides, bien que l'exportation soit correcte. Et une plage dont l'`id` est NFD passerait inaperçue : aucun nom de trait ne correspondrait à celui-ci, et un trait dont le nom ne correspond à aucune plage est accepté tel quel.
  - Un nom qui ne correspond qu'après normalisation est signalé par un **avertissement** de type « `normalization-mismatch` », une fois par identifiant plutôt qu'une fois par référence, adressé au fichier qui le définit. Les données sont correctes, mais un utilisateur qui comparerait des chaînes brutes ne parviendrait pas à résoudre ces références.
  - Les identifiants ne sont jamais modifiés : le fichier conserve l'orthographe d'origine.
