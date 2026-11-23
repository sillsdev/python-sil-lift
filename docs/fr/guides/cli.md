# La ligne de commande (CLI)

L'installation du paquet (`pip install sil-lift`) installe également la commande `sil-lift`.

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media]
                  [--allow CODE[,CODE...]]... [--require-ids]
    tous les problèmes, avec fichier/entrée/ligne ; sortie 1 en cas d’erreurs

sil-lift stats PATH [--format {text,json}]
    nombres d’entrées/sens/langues (en continu ; taille indifférente)

sil-lift sort PATH [-o OUT]
    copie triée de manière canonique, prête pour la comparaison (par défaut : sur place)

sil-lift check-media PATH
    rapport sur les médias manquants, mal orthographiés et orphelins ; sortie 1 en cas de médias manquants ou mal orthographiés

sil-lift export PATH [-o OUT] [--langs L] [--tsv]
    une ligne par sens de feuille (sous-sens aplatis) vers CSV/TSV (en continu)
```

## valider

La commande `validate` affiche une ligne par résultat, puis un résumé. `--format json` donne les mêmes résultats sous la forme d'un objet JSON :

```
$ sil-lift validate dictionary.lift
avertissement [uri-not-rfc] dictionary.lift:6: <range href='file://C:/...'>: lettre de lecteur Windows utilisée comme autorité URI (style FLEx file://C:/)
erreur [dangling-ref] dictionary.lift:88 (entrée poʻo_a1b2) : la référence « nope » ne correspond à aucun ID/GUID d'entrée ni à aucun ID de sens
1 erreur(s), 1 avertissement(s)

$ sil-lift validate dictionary.lift --format json
{
  "problems": [
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: lettre de lecteur Windows utilisée comme autorité URI (style FLEx file://C:/)",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    },
    {
      "level": "error",
      "code": "dangling-ref",
      "message" : "la référence 'nope' ne correspond à aucun ID d'entrée, GUID ou ID de sens",
      "file" : "dictionary.lift",
      "entry_id" : "po\u02bbo_a1b2",
      "guid" : null,
      "line": 88
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 1,
    "allowed": 0
  }
}
```

Options de la fonction `validate` :

- `--format json` écrit un seul objet JSON sur la sortie standard (et rien d'autre) à des fins d'intégration continue (CI) ou d'automatisation. Consultez le schéma de l'exemple ci-dessus.
- L'option `--strict` traite les avertissements comme des erreurs et renvoie la valeur 1 si elle en détecte. Utilisez-le pour conditionner la réussite d'une compilation à l'absence totale d'avertissements, plutôt qu'à la seule absence d'erreurs.
- L'option `--no-check-media` permet d'ignorer la vérification de la présence des médias dans le système de fichiers, supprimant ainsi les résultats `missing-media` et `media-href-mismatch`. Utile lorsque les fichiers audio et photo d'une exportation sont stockés ailleurs ou n'ont pas encore été copiés à côté du fichier `.lift`.
- `--allow CODE[,CODE...]` (répétable) affiche les résultats relatifs aux codes indiqués, mais ne les prend pas en compte dans la décision de réussite ou d'échec.
  - Cela s'applique aussi bien aux erreurs qu'aux avertissements ; ainsi, un avertissement autorisé ne déclenche pas non plus l'option `--strict`.
  - La ligne de synthèse récapitule le nombre de résultats autorisés par code ; la propriété `allowed` du résumé JSON indique leur total.
  - Un code qui n'apparaît jamais est ignoré ; ainsi, une liste blanche continue de fonctionner même si une vérification est supprimée.
- `--require-ids` génère également une erreur (erreur `missing-id`) pour toute entrée ne comportant pas de `guid` ou pour tout sens ne comportant pas d'`id`. Cette règle est plus stricte que celle de LIFT, pour les workflows qui réimportent à l'aide d'un identifiant stable.

Si l'on passe `-` comme chemin d'accès, le document est lu à partir de l'entrée standard (stdin). Un document « piped » n'a pas de dossier ; par conséquent, son fichier associé `.lift-ranges` et ses ressources multimédias ne sont pas pris en compte.

!!! note

    Les codes de sortie de `validate` et le schéma `--format json` constituent une interface d'automatisation prise en charge : ils font tous deux l'objet de tests et ne sont modifiés que dans le respect de la norme SemVer.

## statistiques

```
$ sil-lift stats sango.lift
entrées :   3507
détections :    4541
...
```

La commande `stats` accepte également l'option `--format json`, qui renvoie les statistiques sous la forme d'un objet JSON unique.

## trier

La commande `sort` ne modifie que le fichier `.lift` ; les fichiers `.lift-ranges` associés ne sont pas modifiés (triez-les séparément à l'aide de l'API [`RangesFile`](folder-media.md#ranges)).

## exportation

La commande `export` écrit une ligne par piste de mémoire. `--langs` permet de choisir les langues pour lesquelles les colonnes `gloss_` et `definition_` sont générées ; par défaut, celles-ci sont détectées à partir du document.

```
$ sil-lift export dictionary.lift --langs en,id -o dictionary.csv
```

## Fichiers compressés

Les commandes `validate`, `stats`, `check-media` et `export` acceptent également un paquet LIFT compressé (`.zip`). Ses fichiers peuvent se trouver à la racine de l'archive ou dans un dossier de premier niveau. Tout ce qu'une commande extrait est placé dans un répertoire temporaire et est supprimé une fois la commande terminée.

- Les commandes de streaming `stats` et `export` n'extraient que le fichier `.lift` lui-même, ce qui leur permet de rester peu gourmandes en ressources sur les paquets contenant beaucoup de données multimédias.
- Les commandes `validate` et `check-media` ont besoin du dossier complet et doivent extraire l'intégralité de son contenu.

## Codage de sortie

Toutes les sorties sont au format UTF-8, quelle que soit la plateforme et qu'elles soient destinées à une console, à un tuyau ou à une redirection `>`. Ce n'est jamais l'encodage de la locale (cp1252 sous Windows, ASCII sous une locale C/POSIX) qui ne permet pas de représenter le contenu LIFT. La commande `sil-lift export dictionary.lift > dictionary.csv` écrit donc exactement les mêmes octets que la commande `-o dictionary.csv`, y compris les caractères de fin de ligne CRLF.

## Codes de sortie

- `0` : réussite. Les avertissements n'entraînent pas l'échec de l'exécution, sauf si l'option `--strict` est spécifiée.
- `1` : résultats. Une erreur de validation, un fichier multimédia manquant ou mal orthographié, ou un avertissement sous l'option `--strict` entraîne la sortie 1, sauf si son code a été spécifié avec l'option `--allow`.
- `2` : Échec d'E/S. Il n'a pas été possible de lire l'entrée ou d'écrire la sortie, par exemple parce que le disque est plein ou qu'un programme de lecture tel que `head` a fermé le canal.
