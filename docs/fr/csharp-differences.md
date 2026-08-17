# Différences par rapport aux bibliothèques C\#

sil-lift s'apparente vaguement aux outils LIFT de SIL en C# — principalement `SIL.Lift` dans [libpalaso](https://github.com/sillsdev/libpalaso) (analyseur syntaxique, validateur, migrateur, `LiftSorter`) et `SIL.DictionaryServices` dans le même dépôt (le modèle `LexEntry`/`LexSense`, doté de son propre lecteur/enregistreur LIFT, utilisé par The Combine et WeSay). Il s'agit d'une nouvelle implémentation, et non d'un portage. Cette page résume les points sur lesquels le comportement diffère délibérément.

## Champ d'application

| Capacité             | Bibliothèques C#                                     | sil-lift                                                                                                   |
| -------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Versions de LIFT     | 0,10–0,13 (migration intégrée)    | **0.13 uniquement** ; les versions antérieures sont rejetées et génèrent une erreur claire |
| Migration de version | `Migrator` (chaîne XSLT)          | aucun — utiliser les fichiers XSLT du répertoire « lift-standard » pour les mises à jour ponctuelles       |
| Validation           | RELAX NG uniquement (`Validator`) | RELAX NG + vérifications du schéma et de la sémantique                                                     |
| Streaming            | analyse syntaxique interne à granularité d'entrée    | API publique `open_reader` / `open_writer`                                                                 |

## Forme de l'API

Le parseur de `SIL.Lift` fonctionne par callbacks (`ILexiconMerger`) : il transmet les événements d'analyse à un consommateur. sil-lift renvoie en revanche un simple graphe d'objets — des classes de données typées pour chaque élément LIFT — car les développeurs Python souhaitent des objets, et non des callbacks. `SIL.DictionaryServices` superpose effectivement un modèle d'objets `LexEntry`/`LexSense` à `SIL.Lift`, mais en tant que modèle d’application, il ne représente que les constructions utilisées par ces applications — par conséquent, la resérialisation via ce modèle ne permet pas de préserver le contenu hors modèle, contrairement à la gestion des résidus LIFT et à la fidélité au niveau des octets offertes par sil-lift (voir ci-dessous). L'API de streaming renvoie le _même_ type `Entry` ; il n'y a donc pas de deuxième modèle simplifié à apprendre.

## Fidélité aller-retour

La différence la plus marquée et la plus délibérée. L'enregistrement avec `SIL.Lift` entraîne la resérialisation de l'intégralité du document. sil-lift garantit :

- un document inchangé est enregistré **avec une taille en octets identique**, et
- Les entrées inchangées conservent exactement les octets de leur source, même lorsque d'autres entrées sont modifiées — le découpage en blocs d'octets par entrée est appliqué automatiquement.

Consultez les [garanties de fidélité](fidelity.md).

## Validation

Le `Validator` C# effectue un passage RELAX NG et renvoie les premières erreurs sous forme de chaînes de caractères. sil-lift génère un flux structuré de « problèmes », chacun contenant le fichier, l'entrée et la ligne concernés, et son schéma présente sciemment trois divergences :

- **Les URI non valides constituent des avertissements, et non des erreurs.** Le moteur RELAX NG de C# n'a jamais imposé le type de données `anyURI` ; c'est pourquoi FieldWorks (FLEx) insère depuis des années des liens `file://C:/...` dans des lexiques réels. Le rejet de ces fichiers entraînerait le marquage de pratiquement toutes les exportations FLEx.
- **Les règles Schematron sont appliquées** (sous forme de vérifications sémantiques) : les langages de formulaire en double et les co-contraintes similaires présentes dans la grammaire LIFT étaient ignorés sans avertissement tant par la validation en C# que par celle effectuée directement avec lxml.
- **Les comparaisons entre fichiers sont normalisées selon la norme Unicode**, car FLEx enregistre le fichier `.lift` en NFC et le fichier associé `.lift-ranges` en NFD.

sil-lift valide également les fichiers `.lift-ranges` associés à un lexique chargé par rapport à un schéma destiné aux documents de plages autonomes (fourni par `lift-standard` avec la grammaire LIFT de base) — chaque fichier de plages externe suivi est vérifié à chaque validation du `.lift` — alors qu’il n’existe aucun schéma (ni vérification) de ce type dans l’univers C#. (Il n'existe aucun moyen de valider un fichier `.lift-ranges` isolément, sans qu'il soit associé à un fichier `.lift`.)

## Tri canonique

La méthode `Lexicon.sort()` reprend les règles fondamentales de `LiftSorter` (entrées classées par GUID sans distinction de majuscules/minuscules ; plages et éléments de plage classés par ID ; définitions des champs d'en-tête classées par balise ; sens conservés dans l'ordre du fichier ; espaces à l'intérieur de `<text>` jamais modifiés), à trois différences près :

- Les entrées sans GUID sont triées de manière déterministe par ID (la classe `LiftSorter` part du principe qu'un GUID est présent) ;
- l'ordre est indépendant des paramètres régionaux (points de code sans distinction de casse, et non le classement « invariant-culture » de .NET) ;
- Les listes de même type, telles que les notes, les relations et les formulaires, conservent leur ordre d'origine dans le document au lieu d'être triées à nouveau par clé — le regroupement est déjà déterministe, et les réorganiser ne ferait qu'ajouter du bruit aux différences.

Le fichier `canonicalizeLift.xsl` du dépôt de spécifications n'est absolument pas utilisé : il supprime les espaces blancs à l'intérieur du texte lexical (opération destructive) et les identifiants qu'il génère varient à chaque exécution.

## Non reporté

- Fonctionnalités spécifiques à WeSay (tableau de bord / gestion des paramètres liés aux fichiers LIFT).
- `SynchronicMerger` (fusion de fichiers de mise à jour LIFT) — le principe du découpage en blocs d'octets est toujours présent dans la couche de fidélité, mais pas la fusion.
- Analyse syntaxique du système d'écriture LDML : les fichiers situés dans le répertoire `WritingSystems/` sont considérés comme du contenu de dossier opaque.
