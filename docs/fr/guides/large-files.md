# Fichiers volumineux (diffusion en continu)

La fonction `load()` construit l'ensemble du graphe d'objets. Pour les lexiques de plusieurs centaines de Mo, l'API de traitement en continu traite les entrées une par une dans une mémoire limitée — il s'agit du même type `Entry` ; ainsi, le code écrit pour un mode fonctionne également dans l'autre.

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # analysé au début (précède les entrées)
    for entry in reader:              # itérateur paresseux de type Iterator[Entry]
        ...
```

```python
avec sil_lift.open_reader("big.lift") en tant que lecteur, sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) en tant qu'écrivain :
    pour chaque entrée dans le lecteur :
        if not entry.date_deleted:    # par ex. supprimer les entrées obsolètes
            writer.write(entry)
```

Remarques :

- Le résultat généré par l'éditeur correspond exactement à ce que produirait le sérialiseur canonique « plein document » pour le même contenu — les deux modes ne divergent jamais.
- Le mode streaming ne réutilise aucun octet source : la sortie est toujours canonique. Les résidus LIFT de niveau racine — commentaires entre les entrées et attributs hors schéma sur `<lift>` — ne sont pas transférés ; les entrées et l'en-tête sont complets, résidus compris.
- Si une exception est levée dans le corps d'un bloc `open_writer`, le fichier reste visiblement inachevé (pas de commande de fermeture `</lift>`) — un lexique à moitié écrit ne doit pas donner l'impression d'être complet.
