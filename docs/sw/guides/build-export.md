# Mfano uliofanyiwa kazi: kujenga usafirishaji wa LIFT kutoka mwanzo

If you are exporting another application's data as LIFT (the task behind [Producing conformant LIFT](lift-export-interop.md)), `sil-lift` can build the document object by object and serialize it, instead of emitting XML by hand. This walks through one script that:

- constructs an entry with the pieces a real dictionary has: multiple writing systems, a pronunciation, a sense with an example, an illustration, a semantic-domain trait, and an app-specific field;
- writes the controlled vocabularies into a `.lift-ranges` companion;
- validates and saves.

## Maandishi

```python
from pathlib import Path

import sil_lift

lex = sil_lift.Lexicon(producer="my-exporter")

# Kuingia moja, iliyojengwa kutoka kwa mfano wa chanzo.
entry = sil_lift.Entry(id="kanga", guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d")
entry.lexical_unit["seh"] = "nkhuku"
entry.lexical_unit["pt"] = "galinha"

pron = sil_lift.Pronunciation()
pron.forms["en"] = "Speaker: Ana"  # Kanuni ya lebo ya mzungumzaji ya Combine
pron.media.append(sil_lift.URLRef(href="audio/nkhuku.wav"))
entry.pronunciations.append(pron)

sense = sil_lift.Sense(id="kanga_s1")
sense.grammatical_info = sil_lift.GrammaticalInfo(value="Nomino")
sense.glosses.append(sil_lift.Form(lang="en", text=sil_lift.Text(["chicken"])))
sense.definition["en"] = "a domestic fowl kept for its eggs and meat"

example = sil_lift.Example()
example.forms["seh"] = "Ndinafuna nkhuku."
translation = sil_lift.Translation()
translation.forms["en"] = "Nataka kuku."
example.translations.append(translation)
sense.examples.append(example)

photo = sil_lift.URLRef(href="pictures/hen.jpg")
photo.label["en"] = "Kuku"
sense.illustrations.append(photo)

sense.traits.append(sil_lift.Trait(name="semantic-domain-ddp4", value="1.6.1.2"))

scientific = sil_lift.Field(type="scientific-name")  # uwanja wa ziada maalum kwa programu
scientific.content["en"] = "Gallus gallus domesticus"
sense.fields.append(scientific)

entry.senses.append(sense)
lex.entries.append(entry)

# Vyao vya maneno vilivyodhibitiwa ambavyo kipengee kinavyorejelea, katika .lift-ranges.
ranges = sil_lift.RangesFile()
ranges.add_range("grammatical-info").add_element("Noun").label["en"] = "noun"
ranges.add_range("semantic-domain-ddp4").add_element("1.6.1.2").label["en"] = "Ndege"
lex.add_ranges_file(ranges, href="birds.lift-ranges")

# Thibitisha hati kama ilivyo, kabla ya kugusa diski.
problems = list(lex.iter_problems())
print(f"uthibitishaji: {len(problems)} problem(s)")

out = Path("export")
out.mkdir(exist_ok=True)
lex.save(out / "birds.lift")
print("=== birds.lift ===")
print((out / "birds.lift").read_text(encoding="utf-8"), end="")
print("=== birds.lift-ranges ===")
print((out / "birds.lift-ranges").read_text(encoding="utf-8"), end="")
```

## Kinachozalisha

`uthibitishaji: 0 matatizo`, kisha `.lift` na mwenzake kando kwa kando:

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
      <text>kuku</text>
    </form>
    <form lang="pt">
      <text>kuku</text>
    </form>
  </lexical-unit>
  <pronunciation>
    <form lang="en">
      <text>Spika: Ana</text>
    </form>
    <media href="audio/nkhuku.wav"/>
  </pronunciation>
  <sense id="kanga_s1">
    <grammatical-info value="Noun"/>
    <gloss lang="en">
      <text>kuku</text>
    </gloss>
    <definition>
      <form lang="en">
        <text>kuku wa kufuga anayelishwa kwa mayai na nyama yake</text>
      </form>
    </definition>
    <example>
      <form lang="seh">
        <text>Nataka kuku.</text>
      </form>
      <translation>
        <form lang="en">
          <text>Nataka kuku.</text>
        </form>
      </translation>
    </example>
    <illustration href="pictures/hen.jpg">
      <label>
        <form lang="en">
          <text>Kuku jike</text>
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
        <text>nomino</text>
      </form>
    </label>
  </range-element>
</range>
<range id="semantic-domain-ddp4">
  <range-element id="1.6.1.2">
    <label>
      <form lang="en">
        <text>Ndege</text>
      </form>
    </label>
  </range-element>
</range>
</lift-ranges>
```

## Maelezo kuhusu API

### Building the document

- Multitext fields (`lexical_unit`, `definition`, a `URLRef`'s label, a `Field`'s content) map language codes to text, so a source model's per-language strings carry over one-to-one.
- `Lexicon.add_ranges_file(ranges, href=...)` attaches the companion and writes the header `<range href>` references for you, so the entry's `Noun` and `1.6.1.2` values resolve against the ranges you defined.
- A `URLRef` is an href plus an optional caption/label multitext, used for both `<media>` (audio) and `<illustration>` (photos). Matamshi hapa yanafuata kanuni ya The Combine ya aina ya 'en', kama inavyosomwa na msemaji: <name>
- Data maalum kwa programu bila safari za nyumbani za LIFT za asili kama `<field>` (au `<trait>`): FieldWorks husoma hizi kama viwanja maalum na The Combine huzihifadhi.
- Give every entry a real, stable `guid` (e.g. from `uuid.uuid4()`, reused across exports); a later re-import updates the entry in place rather than duplicating it. `sil-lift validate --require-ids` inahakikisha hili.

### Timestamps

The `dateCreated`/`dateModified` in the output above are not in the script. `save()` stamped them with the moment it ran, since an entry written for the first time carries no date of its own.

- `when=` supplies that moment instead of reading the clock, which is what makes a generated export byte-reproducible for a CI job to diff.
- `stamp=False` writes no dates at all.

Tazama [Alama za muda zilizotengenezwa](../fidelity.md#generated-timestamps) kwa sehemu iliyobaki ya mkataba.

### Uthibitishaji

`lex.iter_problems()` inathibitisha hati iliyopo kwenye kumbukumbu kabla ya chochote kuhifadhiwa kwenye diski; hapa iko sawa. Because the lexicon has no folder yet, the media-presence and companion-href checks are skipped. Run [`sil-lift validate`](cli.md) on the saved output (or with `--no-check-media`) once the audio and photo files are in place.

## Ufungashaji

`lex.save("export/birds.lift")` huandika muundo wa saraka (`.lift` + `.lift-ranges` kando kando). To emit a single zipped package that FieldWorks and The Combine import directly, use `lex.save_zip("birds.zip")` instead. See [Producing conformant LIFT](lift-export-interop.md).
