# Worked example: building a LIFT export from scratch

If you are exporting another application's data as LIFT — the task behind [Producing conformant LIFT](lift-export-interop.md) — `sil-lift` can build the document object by object and serialize it, instead of emitting XML by hand. This walks through one script that constructs an entry with the pieces a real dictionary has (multiple writing systems, a pronunciation, a sense with an example, an illustration, a semantic-domain trait, and an app-specific field), writes the controlled vocabularies into a `.lift-ranges` companion, validates, and saves.

## The script

```python
from pathlib import Path

import sil_lift

lex = sil_lift.Lexicon(producer="my-exporter")

# One entry, built from the source model.
entry = sil_lift.Entry(id="kanga", guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d")
entry.lexical_unit["seh"] = "nkhuku"
entry.lexical_unit["pt"] = "galinha"

pron = sil_lift.Pronunciation()
pron.forms["en"] = "Speaker: Ana"  # The Combine's speaker-label convention
pron.media.append(sil_lift.URLRef(href="audio/nkhuku.wav"))
entry.pronunciations.append(pron)

sense = sil_lift.Sense(id="kanga_s1")
sense.grammatical_info = sil_lift.GrammaticalInfo(value="Noun")
sense.glosses.append(sil_lift.Form(lang="en", text=sil_lift.Text(["chicken"])))
sense.definition["en"] = "a domestic fowl kept for its eggs and meat"

example = sil_lift.Example()
example.forms["seh"] = "Ndinafuna nkhuku."
translation = sil_lift.Translation()
translation.forms["en"] = "I want a chicken."
example.translations.append(translation)
sense.examples.append(example)

photo = sil_lift.URLRef(href="pictures/hen.jpg")
photo.label["en"] = "A hen"
sense.illustrations.append(photo)

sense.traits.append(sil_lift.Trait(name="semantic-domain-ddp4", value="1.6.1.2"))

scientific = sil_lift.Field(type="scientific-name")  # an app-specific extra field
scientific.content["en"] = "Gallus gallus domesticus"
sense.fields.append(scientific)

entry.senses.append(sense)
lex.entries.append(entry)

# The controlled vocabularies the entry refers to, in a companion .lift-ranges.
ranges = sil_lift.RangesFile()
ranges.add_range("grammatical-info").add_element("Noun").label["en"] = "noun"
ranges.add_range("semantic-domain-ddp4").add_element("1.6.1.2").label["en"] = "Bird"
lex.add_ranges_file(ranges, href="birds.lift-ranges")

# Validate the document as it stands, before touching the disk.
problems = list(lex.iter_problems())
print(f"validation: {len(problems)} problem(s)")

out = Path("export")
out.mkdir(exist_ok=True)
lex.save(out / "birds.lift")
print("=== birds.lift ===")
print((out / "birds.lift").read_text(encoding="utf-8"), end="")
print("=== birds.lift-ranges ===")
print((out / "birds.lift-ranges").read_text(encoding="utf-8"), end="")
```

## What it produces

`validation: 0 problem(s)`, then the `.lift` and its companion side by side:

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
<entry id="kanga" guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d" dateCreated="2026-09-02T19:19:17Z" dateModified="2026-09-02T19:19:17Z">
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
      <text>Speaker: Ana</text>
    </form>
    <media href="audio/nkhuku.wav"/>
  </pronunciation>
  <sense id="kanga_s1">
    <grammatical-info value="Noun"/>
    <gloss lang="en">
      <text>chicken</text>
    </gloss>
    <definition>
      <form lang="en">
        <text>a domestic fowl kept for its eggs and meat</text>
      </form>
    </definition>
    <example>
      <form lang="seh">
        <text>Ndinafuna nkhuku.</text>
      </form>
      <translation>
        <form lang="en">
          <text>I want a chicken.</text>
        </form>
      </translation>
    </example>
    <illustration href="pictures/hen.jpg">
      <label>
        <form lang="en">
          <text>A hen</text>
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
        <text>noun</text>
      </form>
    </label>
  </range-element>
</range>
<range id="semantic-domain-ddp4">
  <range-element id="1.6.1.2">
    <label>
      <form lang="en">
        <text>Bird</text>
      </form>
    </label>
  </range-element>
</range>
</lift-ranges>
```

## Notes on the API

- Multitext fields (`lexical_unit`, `definition`, a `Form`/`URLRef` label, a `Field`'s content, ...) take one string per writing system through the mapping interface: `entry.lexical_unit["seh"] = "nkhuku"` adds a `<form lang="seh">`. A source model that keys strings by language code maps straight onto this.
- `RangesFile.add_range()` / `Range.add_element()` build the controlled vocabularies, and `Lexicon.add_ranges_file(ranges, href=...)` attaches the companion and adds the header `<range href>` references — so the entry's `<grammatical-info value="Noun">` and `<trait name="semantic-domain-ddp4" value="1.6.1.2">` resolve against the ranges you defined.
- A `URLRef` is an href plus an optional caption/label multitext — used for both `<media>` (audio) and `<illustration>` (photos). The pronunciation here follows The Combine's convention of an `en` form reading `Speaker: <name>`.
- App-specific data with no native LIFT home rides as a `<field>` (or `<trait>`): FieldWorks reads these as custom fields and The Combine preserves them.
- Give every entry a real, stable `guid` (e.g. from `uuid.uuid4()`, reused across exports) — a later re-import updates the entry in place rather than duplicating it. `sil-lift validate --require-ids` enforces this.
- The `dateCreated`/`dateModified` in the output above are not in the script: `save()` stamped them with the moment it ran, because an entry it is writing for the first time carries no date of its own and the tools that import LIFT decide what to update from `dateModified`. Two knobs, both on `save()`: `when=` supplies the moment instead of reading the clock — that is what makes a generated export byte-reproducible, so a CI job can diff it — and `stamp=False` writes no dates at all. A date you set yourself is left alone either way, so an exporter carrying real timestamps over from its own data model keeps them. Nothing below `<entry>` is ever stamped.
- `lex.iter_problems()` validates the in-memory document before anything hits disk; here it is clean. Because the lexicon has no folder yet, the media-presence and companion-href checks are skipped — run [`sil-lift validate`](cli.md) on the saved output (or with `--no-check-media`) once the audio and photo files are in place.

## Packaging

`lex.save("export/birds.lift")` writes the folder form (`.lift` + `.lift-ranges` side by side). To emit a single zipped package that FieldWorks and The Combine import directly, use `lex.save_zip("birds.zip")` instead — see [Producing conformant LIFT](lift-export-interop.md).
