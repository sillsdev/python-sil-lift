# Création d'un fichier LIFT conforme

Ce guide s'adresse à toute personne développant un _exportateur_ LIFT : un programme, quel que soit le langage utilisé, qui convertit le modèle de données d'une autre application au format LIFT 0.13. « sil-lift » remplit deux fonctions dans ce contexte :

- un contrôle de conformité qui vérifie que la sortie respecte à la fois le schéma et la sémantique qu’un schéma ne peut pas exprimer ;
- un guide précisant les formes et les règles de mise en page que le résultat final doit respecter.

Écrire du code LIFT est bien plus simple que de l'analyser : un exportateur ne génère que le sous-ensemble de constructions produit par son propre modèle, et n'est jamais confronté à l'ensemble des options prévues par la spécification complète. Le plus difficile, ce sont les détails (le compagnon `.lift-ranges`, le texte propre à chaque système d'écriture, les identifiants stables et l'échappement XML), et c'est précisément ce que détectent les vérifications ci-dessous.

## Fichiers compressés

LIFT est généralement transféré sous la forme d'un seul fichier `.zip` ; FieldWorks et The Combine importent et exportent tous deux les données de cette manière. `sil-lift` lit et écrit directement les paquets compressés, quelle que soit la structure utilisée par l'écosystème : les fichiers se trouvant à la racine de l'archive ou imbriqués dans un dossier de premier niveau.

### Lire un colis

La commande `sil_lift.load("package.zip")` décompresse le fichier dans un répertoire temporaire, identifie le fichier `.lift` unique et le charge (les fichiers associés et les médias sont traités comme d'habitude).

- Les commandes CLI `validate`, `stats`, `check-media` et `export` acceptent également un chemin d'accès à un fichier `.zip` ; ainsi, le script ci-dessous s'exécute directement sur un paquet tel quel.
- les flux `stats` et `export`, et n'extraire que le fichier `.lift` plutôt que l'ensemble du paquet. Leur prix reste modique sur un fichier riche en éléments multimédias, et la limite d'extraction s'applique uniquement au fichier `.lift` et non à tout ce qui se trouve à côté.
- L'extraction est limitée à 10 GiB et à 100 000 membres. Un paquet dépassant l'une ou l'autre de ces limites est rejeté avec une erreur `LiftParseError`, tout comme ceux dont les chemins d'accès aux membres sortent du répertoire d'extraction.

### Créer un paquet

`Lexicon.save_zip("out.zip", wrap_folder="MyDict")` regroupe le fichier `.lift`, ses fichiers `.lift-ranges` et tous les autres fichiers du dossier source (médias, `WritingSystems/`, `consent/`, …) dans un fichier zip.

- `wrap_folder` utilise par défaut un dossier de niveau supérieur portant le nom du fichier zip (conformément à la convention d'importation de FieldWorks/Combine) ; passez `False` pour obtenir une archive plate.
- Les entrées dont le contenu a été modifié depuis le chargement se voient attribuer une nouvelle valeur `dateModified` lors de leur sortie, exactement comme lors de l'appel de `save()`.
  - Un paquet est la source à partir de laquelle un outil d'importation effectue la synchronisation ; par conséquent, si la date y est obsolète, un lexique mis à jour apparaîtra comme inchangé.
  - Elle accepte les mêmes options `stamp=` et `when=` que la fonction `save()` ; voir [Comment l'horodatage est appliqué](../fidelity.md#how-the-stamp-is-applied).

Les fichiers `.lift` et `.lift-ranges` conservent leur fidélité au niveau de l'octet au sein du paquet ; le conteneur zip lui-même n'est pas reproductible au niveau de l'octet.

## Valider la sortie en tant que critère de conformité

Passez l'option `sil-lift validate` sur un fichier `.lift`. Il exécute RELAX NG à la fois sur le fichier `.lift` et sur son fichier associé `.lift-ranges`, et effectue en outre des vérifications sémantiques que la grammaire ne permet pas d'exprimer :

- références « relation »/« variante » non résolues ;
- GUID en double ;
- intégrité du parent d'un élément de plage ;
- les valeurs des traits et des informations grammaticales ne sont pas définies dans leur plage ;
- Les références d'en-tête `range/@href` qui ne renvoient à aucun élément associé.

Pour le CI, signaler tout échec et générer des résultats lisibles par machine :

```
sil-lift validate export.lift --strict --no-check-media --format json
```

- L'option `--strict` fait en sorte que les avertissements (et pas seulement les erreurs) entraînent l'échec de l'exécution.
- L'option `--no-check-media` permet d'ignorer la vérification de la présence des médias dans le système de fichiers, dont les résultats indiquant « `missing-media` » constituent un faux positif lorsque les fichiers audio/photo ne se trouvent pas dans le même dossier que le fichier `.lift` dans l'environnement CI.
- L'option `--format json` affiche un seul objet JSON (`{"problems": [...], "summary": {...}}`) au lieu d'un texte lisible par l'utilisateur ; ses codes de sortie et son schéma constituent une interface prise en charge et conforme à SemVer (voir [le guide de la ligne de commande](cli.md)).
- `--allow CODE[,CODE...]` (répétable) empêche un code toléré, tel que `uri-not-rfc` de FLEx, de faire échouer l'exécution. Ses résultats sont imprimés, mais ne sont pas comptabilisés.
- `--require-ids` génère également des erreurs pour les entrées auxquelles il manque un `guid` ou détecte celles auxquelles il manque un `id`, ce qui est utile lorsqu'une réimportation ultérieure doit mettre à jour les données plutôt que de les dupliquer.

### Se prémunir contre la perte de données silencieuse

La perte de données silencieuse est le mode de défaillance qui rend l'exportation au format CSV plat sujette à des pertes. Pour éviter cela, calculez les statistiques à l'aide de la commande `stats --format json` sur votre modèle source :

```
sil-lift stats export.lift --format json
```

Il fournit le nombre d'« entrées », de « sens », d'« exemples », de « références multimédias », de « langues » et de « traits » par nom.

### Exécuter le gate sans la chaîne d'outils Python

Dans un projet TypeScript ou C#, l'environnement de CI peut effectuer la même vérification sans installer Python, grâce à l'action GitHub intégrée :

```yaml
- uses : sillsdev/python-sil-lift@v0.1.0
  with :
    path : export.lift
    strict : "true"
    no-check-media : "true"
    allow : "uri-not-rfc"
    format : json
```

ou l'image du conteneur, générée à partir du fichier `Dockerfile` du dépôt :

```
docker build -t sil-lift .
docker run --rm -v "$PWD:/work" -w /work sil-lift validate export.lift --strict
```

## Le compagnon `.lift-ranges`

Les vocabulaires contrôlés (catégories grammaticales, domaines sémantiques et tout autre ensemble de valeurs associées à des caractéristiques) sont stockés dans un fichier `.lift-ranges` associé, référencé depuis le fichier `<header>` :

```xml
<header>
  <ranges>
    <range id="grammatical-info" href="mydict.lift-ranges"/>
    <range id="semantic-domain-ddp4" href="mydict.lift-ranges"/>
  </ranges>
</header>
```

Le guide contient la définition complète de chaque gamme. Les valeurs sont des `<range-element>` ; `parent` établit une hiérarchie ; `label` / `abbrev` / `description` sont des textes multiples :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
  <range id="grammatical-info">
    <range-element id="Noun">
      <label><form lang="en"><text>nom</text></form></label>
      <abbrev><form lang="en"><text>n</text></form></abbrev>
    </range-element>
  </range>
  <range id="semantic-domain-ddp4">
    <range-element id="1.6.1.2">
      <label><form lang="en"><text>Oiseau</text></form></label>
    </range-element>
  </range>
</lift-ranges>
```

Une entrée fait alors référence à une valeur par son identifiant : la catégorie grammaticale d'un sens est `<grammatical-info value="Noun"/>`, et un domaine sémantique est `<trait name="semantic-domain-ddp4" value="1.6.1.2"/>`. La commande `sil-lift validate` vérifie ces références ; veillez donc à indiquer les plages réellement utilisées par vos données :

- une valeur qui n'est pas définie dans son intervalle génère un avertissement de type `undefined-range-value` ;
- Un « parent » qui n'est pas un identifiant de frère ou de sœur entraîne une erreur de type « range-parent ».

Ces comparaisons sont normalisées selon la norme NFC ; par conséquent, un identifiant et la valeur ou le `parent` qui s'y réfère peuvent présenter des différences au niveau de la normalisation Unicode. Cette différence correspond à un avertissement de « non-correspondance de normalisation » plutôt qu'à une erreur. Néanmoins, si possible, optez pour une normalisation unique et cohérente : les applications qui comparent des chaînes brutes ne pourront pas résoudre ces références. Voir également [Gammes et supports](folder-media.md).

Si vous créez l'exportation en Python, les méthodes `Lexicon.add_ranges_file()`, `RangesFile.add_range()` et `Range.add_element()` génèrent le fichier associé et ajoutent les références d'en-tête à votre place ; `open_writer(..., ranges=...)` effectue la même opération sur le chemin de streaming.

## Texte et textes multiples

Chaque chaîne de caractères en langue humaine dans LIFT est un _multitext_ : un `<form>` par système d'écriture, chacun contenant un `<text>` :

```xml
<lexical-unit>
  <form lang="seh"><text>kanga</text></form>
  <form lang="pt"><text>poulet</text></form>
</lexical-unit>
```

Un modèle qui indexe les chaînes de caractères par code de langue (un `MultiString`, un `Record<code, string>`, un `dict[str, str]`) s'adapte parfaitement à cette correspondance biunivoque : chaque entrée par clé correspond à un `<form lang="…">`. Un seul formulaire par langue est autorisé dans un même multitext ; dans le cas contraire, `sil-lift` affiche un avertissement de type `duplicate-form-lang`.

L'échappement XML est le seul aspect qui nécessite une grande rigueur :

- Dans le texte d'un élément, les caractères `&`, `<`, and `>` doivent être échappés (`&amp;`, `&lt;`, `&gt; `) ;
- Dans les valeurs d'attribut, le caractère de guillemet doit également être échappé.

Le programme « sil-lift » applique exactement ces règles et ne modifie jamais les espaces à l'intérieur de `<text>` : il n'y ajoute aucune indentation, car cela altérerait les données lexicales. Pour que le résultat corresponde à votre source, utilisez une bibliothèque XML pour effectuer l'échappement et conservez le contenu de `<text>` tel quel, octet par octet, comme dans votre source.
