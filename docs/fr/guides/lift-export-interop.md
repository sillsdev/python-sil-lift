# Création d'un fichier LIFT conforme

Ce guide s'adresse à toute personne développant un _exportateur_ LIFT — c'est-à-dire un programme, quel que soit le langage utilisé, qui convertit le modèle de données d'une autre application au format LIFT 0.13. « sil-lift » remplit deux fonctions dans ce contexte : d'une part, il sert de filtre de conformité qui vérifie que la sortie respecte le schéma ainsi que les aspects sémantiques que ce dernier ne peut pas exprimer ; d'autre part, il sert de référence pour les formes et les règles de mise en forme du texte que la sortie doit respecter.

Écrire du code LIFT est bien plus simple que de l'analyser : un exportateur ne génère que le sous-ensemble de constructions produit par son propre modèle, et n'est jamais confronté à l'ensemble des options prévues par la spécification complète. Le plus difficile, ce sont les détails — le compagnon `.lift-ranges`, le texte propre à chaque système d'écriture, les identifiants stables et l'échappement XML — et c'est précisément ce que détectent les vérifications ci-dessous.

## Fichiers compressés

LIFT est généralement transféré sous la forme d'un seul fichier `.zip` — FieldWorks et The Combine importent et exportent tous deux de cette manière — ; ainsi, `sil-lift` lit et écrit directement les paquets compressés, quelle que soit la structure utilisée par l'écosystème : les fichiers à la racine de l'archive ou imbriqués dans un dossier de premier niveau.

- **À noter :** la commande `sil_lift.load("package.zip")` extrait le contenu dans un répertoire temporaire, localise le fichier `.lift` unique et le charge (les fichiers associés et les médias sont traités comme d'habitude). Les commandes CLI `validate`, `stats`, `check-media` et `export` acceptent également un chemin d'accès à un fichier `.zip` ; ainsi, le script ci-dessous s'exécute directement sur un paquet tel quel. La fonction d'extraction est protégée contre les fichiers malveillants : les éléments impliquant un parcours de chemin sont refusés, et le nombre d'entrées ainsi que la taille totale non compressée (10 GiB) sont plafonnés afin d'empêcher les « bombes ZIP ».
- **Écrivez :** `Lexicon.save_zip("out.zip", wrap_folder="MyDict")` regroupe le fichier `.lift`, ses fichiers `.lift-ranges` et tous les autres fichiers du dossier source (media, `WritingSystems/`, `consent/`, …) dans un fichier zip. `wrap_folder` utilise par défaut un dossier de niveau supérieur portant le nom du fichier zip (conformément à la convention d'importation de FieldWorks/Combine) ; passez `False` pour obtenir une archive plate.

Les fichiers `.lift` et `.lift-ranges` conservent leur fidélité au niveau de l'octet au sein du paquet ; le conteneur zip lui-même n'est pas reproductible au niveau de l'octet.

## Valider la sortie en tant que critère de conformité

Passez `sil-lift validate` sur le fichier `.lift` généré. Il exécute RELAX NG (à la fois sur le fichier `.lift` et son fichier associé `.lift-ranges`) et effectue des vérifications sémantiques que la grammaire ne peut pas exprimer : références `relation`/`variant` orphelines, GUID en double, intégrité du parent des éléments de plage, valeurs de traits et d’informations grammaticales non définies dans leur plage, et références `range/@href` d’en-tête qui ne renvoient à aucun élément associé.

Pour le CI, signaler tout échec et générer des résultats lisibles par machine :

```
sil-lift validate export.lift --strict --no-check-media --format json
```

- L'option `--strict` fait en sorte que les avertissements (et pas seulement les erreurs) entraînent l'échec de l'exécution.
- L'option `--no-check-media` permet d'ignorer la vérification de la présence des médias dans le système de fichiers, dont les résultats indiquant « `missing-media` » constituent un faux positif lorsque les fichiers audio/photo ne se trouvent pas dans le même répertoire que le fichier `.lift` dans l'environnement de CI.
- L'option `--format json` affiche un seul objet JSON (`{"problems": [...], "summary": {...}}`) au lieu d'un texte lisible par l'utilisateur ; ses codes de sortie et son schéma constituent une interface prise en charge et conforme à SemVer (voir [le guide de la ligne de commande](cli.md)).
- `--require-ids` génère également des erreurs lorsque des entrées ne comportent pas de `guid` ou détecte l'absence d'un `id` — ce qui s'avère utile lorsqu'une réimportation ultérieure doit mettre à jour les données existantes plutôt que de les dupliquer.

Prévenez les pertes de données silencieuses (le type de défaillance qui entraîne des pertes lors d'une exportation CSV au format plat) en vérifiant les comptages à l'aide de la commande `stats --format json` sur votre modèle source :

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
    format : json
```

ou l'image du conteneur, générée à partir du fichier `Dockerfile` du dépôt :

```
docker build -t sil-lift .
docker run --rm -v "$PWD:/work" -w /work sil-lift validate export.lift --strict
```

## Le compagnon `.lift-ranges`

Les vocabulaires contrôlés — catégories grammaticales, domaines sémantiques et tout autre ensemble de valeurs associées à des caractéristiques — sont stockés dans un fichier `.lift-ranges` associé, référencé depuis le fichier `<header>` :

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

Une entrée fait alors référence à une valeur par son identifiant : la catégorie grammaticale d'un sens est `<grammatical-info value="Noun"/>`, et un domaine sémantique est `<trait name="semantic-domain-ddp4" value="1.6.1.2"/>`. La commande `sil-lift validate` génère un avertissement (`undefined-range-value`) lorsqu'une valeur n'est pas définie dans son intervalle et une erreur (`range-parent`) lorsqu'un `parent` n'est pas un identifiant de frère — veillez donc à définir les intervalles réellement utilisés par vos données. Voir également [Gammes et supports](folder-media.md).

Si vous créez l'exportation en Python, les méthodes `Lexicon.add_ranges_file()`, `RangesFile.add_range()` et `Range.add_element()` génèrent le fichier associé et ajoutent les références d'en-tête à votre place ; `open_writer(..., ranges=...)` effectue la même opération sur le chemin de streaming.

## Texte et textes multiples

Chaque chaîne de caractères en langue humaine dans LIFT est un _multitext_ : un `<form>` par système d'écriture, chacun contenant un `<text>` :

```xml
<lexical-unit>
  <form lang="seh"><text>kanga</text></form>
  <form lang="pt"><text>poulet</text></form>
</lexical-unit>
```

Un modèle qui indexe les chaînes de caractères par code de langue (un `MultiString`, un `Record<code, string>`, un `dict[str, str]`) s'adapte parfaitement à cette correspondance biunivoque : chaque entrée par clé correspond à un `<form lang="…">`. Un seul formulaire par langue est autorisé dans un même multitext — sinon, `sil-lift` affiche un avertissement `duplicate-form-lang`.

L'échappement XML est le seul aspect qui nécessite une grande rigueur. Dans le texte d'un élément, les caractères `&`, `<`, and `>` doivent être échappés (`&amp;`, `&lt;`, `&gt;`) ; dans les valeurs d'attribut, le caractère de guillemet doit également être échappé. Le programme « sil-lift » applique exactement ces règles et ne modifie jamais les espaces à l'intérieur de `<text>` — il n'y ajoute aucune indentation, car cela altérerait les données lexicales. Si vous souhaitez obtenir le même résultat, réutilisez l'échappement d'un véritable sérialiseur XML (et non un remplacement fait maison qui oublie le caractère `&`) et conservez le contenu de `<text>` octet par octet, tel qu'il apparaît dans votre source.
