# Garanties de fidélité

LIFT est un format d'_échange_ ; la première règle est donc de **ne jamais ignorer ce que vous ne comprenez pas**. Le contrat de `sil-lift`, vérifié par la suite de tests à chaque exécution (fichiers de corpus et génération basée sur les propriétés) :

## Lecture

Tout document LIFT 0.13 bien formé se charge, même s'il contient du contenu non conforme au schéma. Tout ce qui n’est pas défini par le modèle est transféré dans le conteneur opaque `Extras` du nœud le plus proche sous la forme d’un « résidu LIFT » — nom donné par FieldWorks à ce concept, qu’il stocke dans un champ `LiftResidue` : attributs et éléments inconnus, commentaires XML et instructions de traitement, texte parasite et attributs typés mal formés (une date incorrecte reste sous forme de chaîne d’origine dans `Extras` ; le champ de type est `None`).

## Enregistrer un document sans modification

`load()` → `save()` sans modification génère une **sortie identique au niveau des octets** — pas de reformatage, pas de ré-échappement, pas de réorganisation ; les marques d'ordre des octets et les déclarations XML sont incluses. Il n'existe actuellement aucune liste de normalisation : l'identité est exacte.

Exceptions (le programme de lecture revient à la sérialisation canonique complète, qui est sémantiquement complète mais ne préserve pas les octets) :

- le codage source n'est pas compatible ASCII (il ne s'agit ni d'UTF-8 ni d'US-ASCII), ou
- le code source contient une déclaration DOCTYPE, ou
- le scanner d'octets et l'analyseur syntaxique ne s'accordent pas sur la structure de haut niveau du document — par exemple, un deuxième `<header>` non conforme à la spécification, que l'analyseur syntaxique ne conserve qu'une seule fois (le scanner est délibérément prudent : en cas de doute, il ne capture aucun octet de la source), ou
- le code source a été généré en mémoire plutôt que chargé à partir d'un fichier.

## Enregistrer un document modifié

- **Les entrées non modifiées sont transmises telles quelles, à partir de leurs octets d'origine.** Une entrée est considérée comme modifiée si une partie quelconque de son objet modèle a changé depuis l'analyse (ce qui est détecté par l'instantané de sérialisation canonique, et non par un indicateur de modification).
- **Les entrées modifiées sont resérialisées de manière canonique et complète** : UTF-8, indentation à 2 espaces _en dehors_ du contenu mixte (les espaces à l'intérieur de `<text>` et `<span>` ne sont jamais modifiés), un regroupement des éléments enfants documenté pour chaque élément (par exemple, entrée : unité lexicale, citation, prononciations, variantes, sens, notes, relations, étymologies, annotations, traits, champs), ordre fixe des attributs, dates au format ISO-8601 (`Z` pour l'UTC). Tous les résidus sont réémis ; leur position est rétablie dans l'index enfant d'origine, en étant ancrée à la nouvelle liste des enfants (il s'agit d'une approximation — les positions exactes en octets ne sont garanties que pour les entrées non modifiées).
- L'ajout, la suppression ou le réordonnancement d'entrées entraîne une nouvelle sérialisation de la structure du document, mais les octets de chaque entrée inchangée sont toujours restitués à l'identique.

!!! note "&quot;Le fichier XML canonique&quot; ne fait référence à aucun autre fichier XML canonique."
    Sur cette page, on entend par « forme canonique » la forme propre à `sil-lift`, telle qu'elle est décrite dans l'un des points ci-dessus. Cela n'a aucun rapport avec le processus « Canonical XML (C14N) » du W3C. Cela n'a aucun rapport avec la classe `CanonicalXmlSettings` de `SIL.Core`.

## Approximations connues (nœuds touchés uniquement)

- Les commentaires situés _à l'intérieur_ d'une exécution `<text>` sont conservés, mais déplacés à côté de l'exécution, et non pas maintenus à leur position exacte dans le texte.
- L'ordre croisé des enfants au sein d'un élément modifié est normalisé selon le regroupement canonique (la propriété `interleave` du schéma LIFT rend cet ordre sans importance sur le plan sémantique).
- Un élément multitext présent mais ne contenant rien — ni forme, ni résidu, par exemple `<definition></definition>` — n'est pas réémis. Le modèle représente ces champs sous la forme d'un `Multitext` toujours présent (`lexical-unit`, `citation`, `definition`, l'`usage` d'une relation et `label` / `abbrev` / `description` sur les références URL, les intervalles, les éléments d’intervalle et l’en-tête), de sorte qu’un champ vide est impossible à distinguer d’un champ absent après analyse. Il n'y a aucune perte sémantique.
