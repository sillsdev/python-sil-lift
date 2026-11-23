# Différences par rapport aux bibliothèques C\#

sil-lift s'apparente, dans une certaine mesure, à l'outil LIFT de SIL pour C# ; il s'agit principalement de deux composants de [libpalaso](https://github.com/sillsdev/libpalaso) :

- `SIL.Lift` : analyseur syntaxique, validateur, outil de migration, `LiftSorter`.
- `SIL.DictionaryServices` : le modèle `LexEntry`/`LexSense`, doté de son propre lecteur/enregistreur LIFT, utilisé par The Combine et WeSay.

sil-lift est une nouvelle implémentation, et non un portage. Cette page résume les points sur lesquels le comportement diffère délibérément.

## Champ d'application

| Capacité             | Bibliothèques C#                                     | sil-lift                                                                                                   |
| -------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Versions de LIFT     | 0,10–0,13 (migration intégrée)    | **0.13 uniquement** ; les versions antérieures sont rejetées et génèrent une erreur claire |
| Migration de version | `Migrator` (chaîne XSLT)          | aucun ; utilisez les fichiers XSLT du répertoire « lift-standard » pour les mises à jour ponctuelles       |
| Validation           | RELAX NG uniquement (`Validator`) | RELAX NG + vérifications du schéma et de la sémantique                                                     |
| Streaming            | analyse syntaxique interne à granularité d'entrée    | API publique `open_reader` / `open_writer`                                                                 |

## Forme de l'API

Le parseur de `SIL.Lift` fonctionne par callbacks (`ILexiconMerger`) : il transmet les événements d'analyse à un consommateur. sil-lift renvoie en revanche un simple graphe d'objets (des classes de données typées pour chaque élément LIFT), car les développeurs Python préfèrent les objets aux callbacks.

`SIL.DictionaryServices` superpose effectivement un modèle d'objets `LexEntry`/`LexSense` à `SIL.Lift`, mais il s'agit d'un modèle d'application : il ne représente que les constructions utilisées par ces applications. La resérialisation via ce mécanisme ne permet donc pas de préserver le contenu hors modèle, contrairement à la gestion des résidus LIFT et à la fidélité au niveau des octets proposées par sil-lift (voir ci-dessous).

L'API de streaming renvoie le _même_ type `Entry` ; il n'y a donc pas de deuxième modèle simplifié à apprendre.

## Fidélité aller-retour

La différence la plus marquée et la plus délibérée. L'enregistrement avec `SIL.Lift` entraîne la resérialisation de l'intégralité du document. sil-lift garantit :

- un document inchangé est enregistré **avec une taille en octets identique**, et
- Les entrées inchangées conservent exactement les octets de leur source, même lorsque d'autres entrées sont modifiées : le découpage en blocs d'octets par entrée est appliqué automatiquement.

Consultez les [garanties de fidélité](fidelity.md).

## Validation

Le `Validator` C# effectue un passage RELAX NG et renvoie les premières erreurs sous forme de chaînes de caractères. sil-lift génère un flux structuré de « problèmes », chacun contenant le fichier, l'entrée et la ligne concernés. Sa couche de schéma présente sciemment trois divergences :

- **Les URI non valides constituent des avertissements, et non des erreurs.** Le moteur RELAX NG de C# n'a jamais imposé le type de données `anyURI` ; c'est pourquoi FieldWorks (FLEx) insère depuis des années des liens `file://C:/...` dans des lexiques réels. Le rejet de ces fichiers entraînerait le marquage de pratiquement toutes les exportations FLEx.
- **Les règles Schematron sont appliquées** (sous forme de vérifications sémantiques) : les langages de formulaire en double et les co-contraintes similaires dans la grammaire LIFT étaient ignorés sans avertissement par la validation C#.
- **Les comparaisons d'identifiants de plage sont normalisées selon la norme Unicode** (NFC), car les exportations FLEx mélangent des identifiants NFC et NFD. Les références qui ne sont résolues qu'après normalisation sont signalées sous forme d'avertissements de type « `normalization-mismatch` », une vérification qui n'a pas d'équivalent en C#. Voir [les résultats de FieldWorks (FLEx) en conditions réelles](guides/validate.md#real-world-fieldworks-flex-output).

Lorsque sil-lift valide un fichier `.lift`, il valide également les fichiers compagnons `.lift-ranges` par rapport à un schéma destiné aux documents de plages autonomes, fourni par `lift-standard`. Le `Validator` de C# ne vérifie pas les fichiers `.lift-ranges`.

## Tri canonique

La méthode `Lexicon.sort()` reprend les règles fondamentales de `LiftSorter` (entrées classées par GUID sans distinction de majuscules/minuscules ; plages et éléments de plage classés par ID ; définitions des champs d'en-tête classées par balise ; sens conservés dans l'ordre du fichier ; espaces à l'intérieur de `<text>` jamais modifiés), à trois différences près :

- Les entrées sans GUID sont triées de manière déterministe par ID (la classe `LiftSorter` part du principe qu'un GUID est présent) ;
- l'ordre est indépendant des paramètres régionaux (points de code sans distinction de casse, et non le classement « invariant-culture » de .NET) ;
- Les listes de même type, telles que les notes, les relations et les formulaires, conservent leur ordre d'origine dans le document au lieu d'être triées à nouveau par clé ; le regroupement est déjà déterministe, et les réorganiser ne ferait qu'ajouter du bruit aux différences.

Le fichier `canonicalizeLift.xsl` du dépôt de spécifications n'est absolument pas utilisé : il supprime les espaces blancs à l'intérieur du texte lexical (opération destructive) et les identifiants qu'il génère varient à chaque exécution.

## Non reporté

- Fonctionnalités spécifiques à WeSay (tableau de bord / gestion des paramètres liés aux fichiers LIFT).
- `SynchronicMerger` (fusion de fichiers de mise à jour LIFT) : le principe du découpage en blocs d'octets est conservé dans la couche de fidélité, mais pas la fusion.
- Analyse syntaxique du système d'écriture LDML : les fichiers situés dans le répertoire `WritingSystems/` sont considérés comme du contenu de dossier opaque.
