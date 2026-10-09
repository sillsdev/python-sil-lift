# La ligne de commande

L'installation du paquet (`pip install sil-lift`) installe également la commande `sil-lift` — un outil pris en charge, dans l'esprit de LiftTools, fourni avec le paquet (et, pour `validate`, un exemple concret d'utilisation de l'API de la bibliothèque).

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media] [--allow CODE[,CODE...]]...
                  [--require-ids]
                                           tous les problèmes, avec fichier/entrée/ligne ; sortie 1 en cas d’erreurs
sil-lift stats PATH [--format {text,json}]
                                           nombre d’entrées/sens/langues (en continu ; taille indifférente)
sil-lift sort PATH [-o OUT]               copie triée de manière canonique et prête pour la comparaison (par défaut : sur place)
sil-lift check-media PATH                 rapport sur les médias manquants, mal orthographiés et orphelins ; sortie 1 en cas de médias manquants ou mal orthographiés
sil-lift export PATH [-o OUT] [--langs L] [--tsv]
                                           une ligne par sens feuille (sous-sens aplatis) vers CSV/TSV (en continu)
```

Options de la fonction `validate` :

- `--format json` écrit un seul objet JSON sur la sortie standard (et rien d'autre) à l'intention des outils d'intégration continue (CI) et d'automatisation ; voir le schéma dans l'exemple ci-dessous.
- L'option `--strict` traite les avertissements comme des erreurs et renvoie la valeur 1 si elle en détecte — utilisez-la pour conditionner la réussite d'une compilation à l'absence totale d'avertissements, plutôt qu'aux seules erreurs.
- L'option `--no-check-media` permet d'ignorer la vérification de la présence des médias dans le système de fichiers, supprimant ainsi les résultats `missing-media` et `media-href-mismatch`. Utile pour valider une exportation qui vient d'être générée et dont les fichiers audio/photo se trouvent ailleurs que dans le même dossier.
- `--allow CODE[,CODE...]` (répétable) affiche les résultats relatifs aux codes indiqués, mais ne les prend pas en compte dans la décision de réussite ou d'échec. Cela s'applique aussi bien aux erreurs qu'aux avertissements ; ainsi, un avertissement autorisé ne déclenche pas non plus l'option `--strict`. La ligne de synthèse récapitule le nombre de résultats autorisés par code ; la propriété `allowed` du résumé JSON indique leur total. Un code qui n'apparaît jamais est ignoré ; ainsi, une liste blanche continue de fonctionner même après la suppression d'un contrôle.
- `--require-ids` génère également une erreur (`missing-id`) pour toute entrée ne disposant pas d'un `guid` ou pour tout sens ne disposant pas d'un `id` — cette règle est plus stricte que celle de LIFT, pour les flux de travail qui réimportent à l'aide d'un identifiant stable.

Si l'on passe `-` comme chemin d'accès, le document est lu à partir de l'entrée standard (stdin). Un document « piped » n'a pas de dossier ; par conséquent, son fichier associé `.lift-ranges` et ses ressources multimédias ne sont pas pris en compte.

La commande `stats` accepte également l'option `--format json`, qui renvoie les statistiques sous la forme d'un objet JSON unique.

!!! note
    Les codes de sortie de `validate` et le schéma `--format json` constituent une interface d'automatisation prise en charge : ils font tous deux l'objet de tests et ne sont modifiés que dans le respect de la norme SemVer.

La commande `sort` ne modifie que le fichier `.lift` ; les fichiers `.lift-ranges` associés restent inchangés
(triez-les séparément à l'aide de l'API `RangesFile`).

Les commandes `validate`, `stats`, `check-media` et `export` acceptent également un paquet LIFT compressé (un fichier `.zip` dans l'une ou l'autre des structures suivantes : fichiers à la racine de l'archive ou imbriqués dans un dossier de niveau supérieur) ; celui-ci est extrait dans un répertoire temporaire puis supprimé une fois la commande terminée. Les commandes de streaming `stats` et `export` n'extraient que le fichier `.lift` lui-même, ce qui leur permet de rester peu gourmandes en ressources pour les paquets contenant beaucoup de données multimédia ; les commandes `validate` et `check-media` ont besoin du dossier entier et l'extraient dans son intégralité.

Exemples :

```
$ sil-lift validate dictionary.lift
erreur [dangling-ref] dictionary.lift:88 (entrée apu) : la référence « nope » ne correspond à aucun ID/GUID d'entrée ni à aucun ID de sens
avertissement [uri-not-rfc] dictionary.lift:6 : <range href='file://C:/...'>: lettre de lecteur Windows utilisée comme autorité URI (style FLEx file://C:/)
1 erreur(s), 1 avertissement(s)

$ sil-lift validate dictionary.lift --format json
{
  « problems » : [
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "la référence 'nope' ne correspond à aucun ID d'entrée/GUID ni à aucun ID de sens",
      "file": "dictionary.lift",
      "entry_id" : "apu",
      "guid" : null,
      "line" : 88
    },
    {
      "level" : "warning",
      "code" : "uri-not-rfc",
      "message" : "<range href='file://C:/...'>: Lettre de lecteur Windows utilisée comme autorité URI (style FLEx file://C:/)",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    }
  ],
  « summary » : {
    « errors » : 1,
    « warnings » : 1,
    « allowed » : 0
  }
}

$ sil-lift stats sango.lift
entrées :   3507
sens :    4541
...

$ sil-lift export dictionary.lift --langs en,fr -o dictionary.csv
```

Toutes les sorties sont au format UTF-8, quelle que soit la plateforme et qu'elles soient destinées à une console, à un tuyau ou à une redirection `>` — jamais au format d'encodage de la locale (cp1252 sous Windows, ASCII sous une locale C/POSIX), qui ne permet pas de représenter le contenu LIFT. La commande `sil-lift export dictionary.lift > dictionary.csv` écrit donc exactement les mêmes octets que la commande `-o dictionary.csv`, y compris les caractères de fin de ligne CRLF.

Codes de sortie : `0` : succès (les avertissements n’entraînent pas l’échec de l’exécution, sauf si l’option `--strict` est activée), `1` : problèmes détectés (erreurs de validation / supports manquants ou mal orthographiés / avertissements avec l’option `--strict`, sans compter les codes attribués à l’option `--allow`), `2` : échec d’E/S à l’une ou l’autre extrémité — entrée illisible ou sortie impossible (un lecteur tel que `head` fermant le tuyau, un disque plein).
