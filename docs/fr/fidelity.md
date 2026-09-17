# Garanties de fidélité

LIFT est un format d'_échange_ ; la première règle est donc de **ne jamais ignorer ce que vous ne comprenez pas**. Le contrat de `sil-lift`, vérifié par la suite de tests à chaque exécution (fichiers de corpus et génération basée sur les propriétés) :

## Lecture

Tout document LIFT 0.13 bien formé se charge, même s'il contient du contenu non conforme au schéma. Tout ce qui n’est pas défini par le modèle est transféré dans le conteneur opaque `Extras` du nœud le plus proche sous la forme d’un « résidu LIFT » — nom donné par FieldWorks à ce concept, qu’il stocke dans un champ `LiftResidue` : attributs et éléments inconnus, commentaires XML et instructions de traitement, texte parasite et attributs typés mal formés (une date incorrecte reste sous forme de chaîne d’origine dans `Extras` ; le champ de type est `None`).

## Enregistrer un document sans modification

`load()` → `save()` sans modification génère une **sortie identique au niveau des octets** — pas de reformatage, pas de ré-échappement, pas de réorganisation ; les marques d'ordre des octets et les déclarations XML sont incluses. Il n'existe actuellement aucune liste de normalisation : l'identité est exacte. Les horodatages sont générés à partir du contenu ; par conséquent, un document qui n'a pas été modifié n'en comporte pas non plus.

Exceptions (le programme de lecture revient à la sérialisation canonique complète, qui est sémantiquement complète mais ne préserve pas les octets) :

- le codage source n'est pas compatible ASCII (il ne s'agit ni d'UTF-8 ni d'US-ASCII), ou
- le code source contient une déclaration DOCTYPE, ou
- le scanner d'octets et l'analyseur syntaxique ne s'accordent pas sur la structure de haut niveau du document — par exemple, un deuxième `<header>` non conforme à la spécification, que l'analyseur syntaxique ne conserve qu'une seule fois (le scanner est délibérément prudent : en cas de doute, il ne capture aucun octet de la source), ou
- le code source a été généré en mémoire plutôt que chargé à partir d'un fichier.

## Enregistrer un document modifié

- **Les entrées non modifiées sont transmises telles quelles, à partir de leurs octets d'origine.** Une entrée est considérée comme modifiée si une partie quelconque de son objet modèle a changé depuis l'analyse (ce qui est détecté par l'instantané de sérialisation canonique, et non par un indicateur de modification).
- **Les entrées modifiées sont à nouveau sérialisées de manière canonique et complète.** La forme canonique est la suivante :
  - UTF-8.
  - Indentation de 2 espaces _à l'extérieur_ du contenu mixte ; les espaces à l'intérieur de `<text>` et `<span>` ne sont jamais modifiés.
  - Un regroupement d'enfants documenté par élément ; pour `<entry>` : unité lexicale, citation, prononciations, variantes, sens, notes, relations, étymologies, annotations, traits, domaines.
  - Ordre des attributs corrigé.
  - Dates au format ISO-8601 (`Z` pour l'UTC).
- **Tous les résidus sont réémis.** Leur position est rétablie dans l’index enfant d’origine, en étant ancrée à la nouvelle liste des enfants — il s’agit d’une approximation, car les positions exactes en octets ne sont garanties que pour les entrées qui n’ont pas été modifiées.
- L'ajout, la suppression ou le réordonnancement d'entrées entraîne une nouvelle sérialisation de la structure du document, mais les octets de chaque entrée inchangée sont toujours restitués à l'identique.
- **Une entrée modifiée est marquée** d'une nouvelle valeur `dateModified`, ainsi que d'une valeur `dateCreated` si elle n'en avait pas — voir [Horodatages générés](#generated-timestamps).

!!! note "&quot;Le fichier XML canonique&quot; ne fait référence à aucun autre fichier XML canonique."
    Sur cette page, on entend par « forme canonique » la forme propre à `sil-lift`, telle qu'elle est décrite dans l'un des points ci-dessus. Cela n'a aucun rapport avec le processus « Canonical XML (C14N) » du W3C. Cela n'a aucun rapport avec la classe `CanonicalXmlSettings` de `SIL.Core`.

## Horodatages générés

Un tampon généré est le seul élément de la sortie qui ne dépend pas de l'entrée.

- **Ce qui est marqué.** Chaque entrée dont le contenu a changé depuis sa lecture, avec une nouvelle valeur `dateModified` et, si elle n'en avait pas, une valeur `dateCreated` correspondant au même moment. Une modification enregistrée après la date de chargement apparaît comme inchangée pour tous les outils qui effectuent un rapprochement sur cet attribut, y compris FieldWorks et l’importation LIFT de The Combine.
- **Entrées uniquement.** Aucun nœud ne doit se trouver sous un `<entry>`, et l'en-tête ne doit contenir aucun élément.
- **Ce qui est laissé tel quel.** Une entrée dont la date a été définie délibérément par l'appelant, et une entrée créée après le chargement qui comporte déjà une date.
- **La suppression d'une date est prise en compte.** La ligne `entry.date_modified = None` appliquée à une entrée lue avec cette valeur est une opération délibérée, comme n'importe quelle autre ; l'entrée est donc renvoyée sans `dateModified`, que son contenu ait été modifié ou non. Une entrée lue sans modification est un cas à part : `None` correspond à une valeur déjà présente, impossible à distinguer d'une situation où le champ n'a jamais été modifié ; par conséquent, une modification laisse tout de même une trace.
- **Une date impossible à analyser est remplacée.** Une date que le modèle n'a pas pu analyser est considérée comme un [résidu](#reading) plutôt que comme une date ; un horodatage vient donc la remplacer et la chaîne d'origine est supprimée — il vaut mieux qu'une entrée modifiée comporte une date réelle plutôt que `dateModified="whenever"`.
- **L'instant.** Heure UTC à la seconde près (`AAAA-MM-JJTHH:MM:SSZ`, le format utilisé par toutes les exportations FieldWorks de l'enquête), lu sur l'horloge murale. Une seconde correspond à une seule date ; ainsi, une modification enregistrée dans la seconde qui suit la précédente porte le même horodatage.
- **`save(when=...)`** fournit l'instant plutôt que l'heure de l'horloge, ce qui garantit la reproductibilité des résultats horodatés pour une porte de CI basée sur les différences. Il doit tenir compte du fuseau horaire et est normalisé en secondes entières UTC.
- **`save(stamp=False)`** enregistre le modèle tel quel, résidu compris.
- **Valider les commits avec l'écriture `.lift`.** Tout ce qui empêche cette écriture d'être validée fait remonter les dates. Une fois qu'elle a atterri, elles restent en place, même si une autre écriture échoue par la suite.

## Le format XML ne permet pas de représenter

Les caractères non BMP — emojis, extension CJK B, Adlam, tout ce qui se trouve au-delà de U+FFFF — constituent du contenu ordinaire et sont transférés à l'identique, octet par octet, dans les deux sens. Une « paire de substitution » est une subtilité de l'encodage UTF-16 : les chaînes Python étant des séquences de points de code, ni le lecteur, ni le scanner d'octets, ni l'écrivain n'en voient jamais.

Un caractère de remplacement _isolé_ (U+D800–U+DFFF) est différent : une chaîne Python peut en contenir un, mais ce n'est pas forcément le cas d'un document XML, quel que soit son encodage. Elle ne peut en aucun cas provenir d'un fichier — l'analyseur syntaxique rejette les deux orthographes, à savoir la référence de caractère `&#xD800;` et les octets CESU-8/WTF-8 — mais uniquement d'une chaîne attribuée via l'API. L'enregistrement d'un tel modèle génère une erreur `LiftWriteError` indiquant le nom du nœud et le point de code, sans rien écrire ; la validation signale cela comme une seule erreur de type `lone-surrogate`, car le document ne peut pas être sérialisé pour permettre aux couches de schéma de le vérifier.

## Approximations connues (nœuds touchés uniquement)

- Les commentaires situés _à l'intérieur_ d'une exécution `<text>` sont conservés, mais déplacés à côté de l'exécution, et non pas maintenus à leur position exacte dans le texte.
- L'ordre croisé des enfants au sein d'un élément modifié est normalisé selon le regroupement canonique (la propriété `interleave` du schéma LIFT rend cet ordre sans importance sur le plan sémantique).
- Un `<form>` ou un `<gloss>` ne comportant pas d'attribut `lang` n'est pas réémis, pas plus que son contenu ; la validation signale cette omission sous la forme `form-missing-lang`. Un nœud non modifié conserve ses octets d'origine ; ce format est donc conservé jusqu'à ce qu'un élément de son entrée soit modifié.
- Un élément multitext présent mais ne contenant rien — ni forme, ni résidu, par exemple `<definition></definition>` — n'est pas réémis. Le modèle représente ces champs sous la forme d'un `Multitext` toujours présent (`lexical-unit`, `citation`, `definition`, l'`usage` d'une relation et `label` / `abbrev` / `description` sur les références URL, les intervalles, les éléments d’intervalle et l’en-tête), de sorte qu’un champ vide est impossible à distinguer d’un champ absent après analyse. Il n'y a aucune perte sémantique.
