# Exemple pratique : créer une exportation LIFT à partir de zéro

Si vous exportez les données d'une autre application au format LIFT — ce qui correspond à la tâche décrite dans [« Produire un LIFT conforme »](lift-export-interop.md) —, `sil-lift` peut construire le document objet par objet et le sérialiser, au lieu de générer manuellement du code XML. Ce guide présente un script qui construit une entrée comprenant les éléments caractéristiques d'un véritable dictionnaire (plusieurs systèmes d'écriture, une prononciation, un sens accompagné d'un exemple, une illustration, un trait de domaine sémantique et un champ spécifique à l'application), écrit les vocabulaires contrôlés dans un fichier compagnon `.lift-ranges`, effectue une validation, puis enregistre le tout.

## Le scénario

```python
from pathlib import Path

import sil_lift

lex = sil_lift.Lexicon(producer="my-exporter")

# Une entrée, construite à partir du modèle source.
entry = sil_lift.Entry(id="kanga", guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d")
entry.lexical_unit["seh"] = "nkhuku"
entry.lexical_unit["pt"] = "galinha"

pron = sil_lift.Pronunciation()
pron.forms["en"] = "Speaker: Ana"  # Convention de nommage des locuteurs du Combine
pron.media.append(sil_lift.URLRef(href="audio/nkhuku.wav"))
entry.pronunciations.append(pron)

sense = sil_lift.Sense(id="kanga_s1")
sense.grammatical_info = sil_lift.GrammaticalInfo(value="Noun")
sense.glosses.append(sil_lift.Form(lang="en", text=sil_lift.Text(["chicken"])))
sense.definition["en"] = "une volaille domestique élevée pour ses œufs et sa viande"

example = sil_lift.Example()
example.forms["seh"] = "Ndinafuna nkhuku."
translation = sil_lift.Translation()
translation.forms["en"] = "I want a chicken."
example.translations.append(translation)
sense.examples.append(example)

photo = sil_lift.URLRef(href="pictures/hen.jpg")
photo.label["en"] = "Une poule"
sense.illustrations.append(photo)

sense.traits.append(sil_lift.Trait(name="semantic-domain-ddp4", value="1.6.1.2"))

scientific = sil_lift.Field(type="scientific-name")  # un champ supplémentaire spécifique à l’application
scientific.content["en"] = "Gallus gallus domesticus"
sense.fields.append(scientific)

entry.senses.append(sense)
lex.entries.append(entry)

# Les vocabulaires contrôlés auxquels l'entrée fait référence, dans un fichier .lift-ranges associé.
ranges = sil_lift.RangesFile()
ranges.add_range("grammatical-info").add_element("Noun").label["en"] = "noun"
ranges.add_range("semantic-domain-ddp4").add_element("1.6.1.2").label["en"] = "Bird"
lex.add_ranges_file(ranges, href="birds.lift-ranges")

# Valider ce que save() écrirait, avant d'écrire sur le disque.
problems = list(lex.iter_problems())
print(f"validation : {len(problems)} problème(s)")

out = Path("export")
out.mkdir(exist_ok=True)
lex.save(out / "birds.lift")
print("=== birds.lift ===")
print((out / "birds.lift").read_text(encoding="utf-8"), end="")
print("=== birds.lift-ranges ===")
print((out / "birds.lift-ranges").read_text(encoding="utf-8"), end="")
```

## Ce qu'il produit

`validation : 0 problème(s)`, puis le `.lift` et son équivalent côte à côte :

```
=== birds.lift ===
<?xml version="1.0" encoding="UTF-8"?>
<lift version="0.13" producer="my-exporter">
<header>
  <ranges>
    <range id="grammatical-info" href="birds.lift-ranges"/>
    <range id="semantic-domain-ddp4" href="birds.lift-ranges"/>
  </ranges>
</header>
<entry id="kanga" guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d">
  <lexical-unit>
    <form lang="seh">
      <text>nkhuku</text>
    </form>
    <form lang="pt">
      <text>galinha</text>
    </form>
  </lexical-unit>
  <pronunciation>
    <form lang="en">
      <text>Intervenante : Ana</text>
    </form>
    <media href="audio/nkhuku.wav"/>
  </pronunciation>
  <sense id="kanga_s1">
    <grammatical-info value="Noun"/>
    <gloss lang="en">
      <text>poulet</text>
    </gloss>
    <definition>
      <form lang="en">
        <text>volaille élevée pour ses œufs et sa viande</text>
      </form>
    </definition>
    <example>
      <form lang="seh">
        <text>Ndinafuna nkhuku.</text>
      </form>
      <translation>
        <form lang="en">
          <text>Je veux un poulet.</text>
        </form>
      </translation>
    </example>
    <illustration href="pictures/hen.jpg">
      <label>
        <form lang="en">
          <text>Une poule</text>
        </form>
      </label>
    </illustration>
    <trait name="semantic-domain-ddp4" value="1.6.1.2"/>
    <field type="scientific-name">
      <form lang="en">
        <text>Gallus gallus domesticus</text>
      </form>
    </field>
  </sense>
</entry>
</lift>
=== birds.lift-ranges ===
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
<range id="grammatical-info">
  <range-element id="Noun">
    <label>
      <form lang="en">
        <text>nom</text>
      </form>
    </label>
  </range-element>
</range>
<range id="semantic-domain-ddp4">
  <range-element id="1.6.1.2">
    <label>
      <form lang="en">
        <text>Oiseau</text>
      </form>
    </label>
  </range-element>
</range>
</lift-ranges>
```

## Remarques sur l'API

- Champs multitexte (`lexical_unit`, `definition`, une étiquette `Form`/`URLRef`, le contenu d'un `Field`, etc.) Prendre une chaîne par système d'écriture via l'interface de mappage : `entry.lexical_unit["seh"] = "nkhuku"` ajoute un `<form lang="seh">`. Un modèle source qui indexe les chaînes de caractères par code de langue s'adapte parfaitement à cette structure.
- `RangesFile.add_range()` / `Range.add_element()` permettent de créer les vocabulaires contrôlés, tandis que `Lexicon.add_ranges_file(ranges, href=...)` associe le fichier correspondant et ajoute les références d’en-tête `<range href>`, de sorte que les entrées `<grammatical-info value="Noun">` et `<trait name="semantic-domain-ddp4" value="1.6.1.2">` renvoient aux plages que vous avez définies.
- Un `URLRef` est un attribut `href` accompagné d'un texte multiple facultatif (légende ou étiquette) — utilisé à la fois pour `<media>` (audio) et `<illustration>` (photos). La prononciation suivie ici respecte la convention de The Combine, qui prévoit une forme « en » se lisant « Intervenant : <name> ».
- Les données spécifiques à l'application ne comportant pas de trajets de retour LIFT natifs, sous la forme «<field> » (ou «<trait> ») : FieldWorks les interprète comme des champs personnalisés et The Combine les conserve.
- Attribuez à chaque entrée un `guid` réel et stable (généré par exemple par `uuid.uuid4()`, réutilisé d'une exportation à l'autre) : une réimportation ultérieure mettra à jour l'entrée sur place plutôt que de la dupliquer. La commande `sil-lift validate --require-ids` garantit le respect de cette règle.
- La fonction `lex.iter_problems()` valide le document en mémoire (ce que la fonction `save()` écrirait) avant que quoi que ce soit ne soit enregistré sur le disque ; ici, il est correct. Comme le lexique ne dispose pas encore de dossier, les vérifications « media-presence » et « companion-href » sont ignorées — exécutez [`sil-lift validate`](cli.md) sur le fichier de sortie enregistré (ou avec l'option `--no-check-media`) une fois que les fichiers audio et photo sont en place.

## Emballage

La commande `lex.save("export/birds.lift")` enregistre le dossier sous la forme (fichiers `.lift` et `.lift-ranges` côte à côte). Pour générer un seul fichier compressé que FieldWorks et The Combine importent directement, utilisez plutôt `lex.save_zip("birds.zip")` — voir [Création de fichiers LIFT conformes](lift-export-interop.md).
