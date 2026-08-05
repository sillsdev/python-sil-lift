# La ligne de commande

L'installation du paquet (`pip install sil-lift`) installe également la commande `sil-lift` — un outil de type LiftTools pris en charge et fourni avec le paquet (ainsi que, pour `validate`, un exemple concret d'utilisation de l'API de la bibliothèque).

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media] [--require-ids]
                                           tous les problèmes, traités par entrée/ligne ; sortie 1 en cas d’erreurs
sil-lift stats CHEMIN [--format {text,json}]
                                           nombre d’entrées/sens/langues (en continu ; taille indifférente)
sil-lift sort CHEMIN [-o SORTIE]               copie triée de manière canonique, prête pour la comparaison (par défaut : sur place)
sil-lift check-media PATH                 rapport sur les médias manquants et orphelins ; sortie 1 en cas de médias manquants
sil-lift export PATH [-o OUT] [--langs L] [--tsv]
                                           une ligne par sens de feuille (sous-sens aplatis) vers CSV/TSV (en continu)
```

`--format json` écrit un seul objet JSON sur la sortie standard (et rien d'autre) à l'intention des outils d'intégration continue (CI) et d'automatisation ; voir le schéma dans l'exemple ci-dessous. L'option `--strict` traite les avertissements comme des erreurs et renvoie la valeur 1 si elle en détecte — utilisez-la pour valider une compilation uniquement si tout est en ordre, et non pas uniquement en cas d'erreurs. L'option `--no-check-media` permet de ne pas effectuer la vérification de la présence des médias dans le système de fichiers (ce qui supprime les messages d'erreur de type `missing-media`), ce qui est utile lors de la validation d'une exportation fraîchement générée dont les fichiers audio/photo se trouvent ailleurs et ne sont pas stockés sur le même disque. `--require-ids` génère également une erreur (`missing-id`) pour toute entrée ne disposant pas d'un `guid` ou pour tout sens ne disposant pas d'un `id` — cette règle est plus stricte que celle de LIFT, pour les flux de travail qui réimportent à l'aide d'un identifiant stable. En passant `-` comme chemin d'accès, le document est lu à partir de l'entrée standard (un document transmis par canalisation n'ayant pas de dossier, son fichier associé `.lift-ranges` et ses médias ne sont pas résolus). La commande `stats` accepte également l'option `--format json`, qui renvoie les statistiques sous la forme d'un objet JSON unique.

!!! note
    Les codes de sortie de `validate` et le schéma `--format json` constituent une interface d'automatisation prise en charge : ils font tous deux l'objet de tests et ne sont modifiés que dans le respect de la norme SemVer.

La commande `sort` ne modifie que le fichier `.lift` ; les fichiers `.lift-ranges` associés restent inchangés
(triez-les séparément à l'aide de l'API `RangesFile`).

Les commandes `validate`, `stats`, `check-media` et `export` acceptent également un paquet LIFT compressé (un fichier `.zip` dans l'une ou l'autre des structures suivantes : fichiers à la racine de l'archive ou imbriqués dans un dossier de niveau supérieur) ; celui-ci est extrait dans un répertoire temporaire puis supprimé une fois la commande terminée.

Exemples :

```
$ sil-lift validate dictionary.lift
erreur [dangling-ref] dictionary.lift:88 (entrée apu) : la référence « nope » ne correspond à aucun ID/GUID d'entrée ni à aucun ID de sens
avertissement [uri-not-rfc] dictionary.lift:6 : <range href='file://C:/...'>: lettre de lecteur Windows utilisée comme autorité URI (style FLEx file://C:/)
1 erreur(s), 1 avertissement(s)

$ sil-lift validate dictionary.lift --format json
{
  "problems": [
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
    « warnings » : 1
  }
}

$ sil-lift stats sango.lift
entrées :   3507
sens :    4541
...

$ sil-lift export dictionary.lift --langs en,fr -o dictionary.csv
```

Codes de sortie : `0` : opération réussie (avertissements autorisés, sauf si l'option `--strict` est activée), `1` : problèmes détectés (erreurs de validation / fichiers multimédias manquants / avertissements lorsque l'option `--strict` est activée), `2` : données d'entrée illisibles.
