# कार्य उदाहरण: शून्य से LIFT एक्सपोर्ट बनाना

If you are exporting another application's data as LIFT (the task behind [Producing conformant LIFT](lift-export-interop.md)), `sil-lift` can build the document object by object and serialize it, instead of emitting XML by hand. This walks through one script that:

- constructs an entry with the pieces a real dictionary has: multiple writing systems, a pronunciation, a sense with an example, an illustration, a semantic-domain trait, and an app-specific field;
- writes the controlled vocabularies into a `.lift-ranges` companion;
- validates and saves.

## पटकथा

```python
from pathlib import Path

import sil_lift

lex = sil_lift.Lexicon(producer="my-exporter")

# एक प्रविष्टि, स्रोत मॉडल से निर्मित।
entry = sil_lift.Entry(id="kanga", guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d")
entry.lexical_unit["seh"] = "nkhuku"
entry.lexical_unit["pt"] = "galinha"

pron = sil_lift.Pronunciation()
pron.forms["en"] = "Speaker: Ana"  # The Combine's speaker-label convention
pron.media.append(sil_lift.URLRef(href="audio/nkhuku.wav"))
entry.pronunciations.append(pron)

sense = sil_lift.Sense(id="kanga_s1")
sense.grammatical_info = sil_lift.GrammaticalInfo(value="संज्ञा")
sense.glosses.append(sil_lift.Form(lang="en", text=sil_lift.Text(["chicken"])))
sense.definition["en"] = "a domestic fowl kept for its eggs and meat"

example = sil_lift.Example()
example.forms["seh"] = "Ndinafuna nkhuku."
translation = sil_lift.Translation()
translation.forms["en"] = "मुझे एक मुर्गी चाहिए।"
example.translations.append(translation)
sense.examples.append(example)

photo = sil_lift.URLRef(href="pictures/hen.jpg")
photo.label["en"] = "एक मुर्गी"
sense.illustrations.append(photo)

sense.traits.append(sil_lift.Trait(name="semantic-domain-ddp4", value="1.6.1.2"))

scientific = sil_lift.Field(type="scientific-name")  # एक ऐप-विशिष्ट अतिरिक्त फ़ील्ड
scientific.content["en"] = "Gallus gallus domesticus"
sense.fields.append(scientific)

entry.senses.append(sense)
lex.entries.append(entry)

# एंट्री जिन नियंत्रित शब्दावलियों का संदर्भ देती है, एक साथी .lift-ranges में।
ranges = sil_lift.RangesFile()
ranges.add_range("grammatical-info").add_element("Noun").label["en"] = "noun"
ranges.add_range("semantic-domain-ddp4").add_element("1.6.1.2").label["en"] = "Bird"
lex.add_ranges_file(ranges, href="birds.lift-ranges")

# डिस्क को छूने से पहले दस्तावेज़ को जैसा है वैसा मान्य करें।
problems = list(lex.iter_problems())
print(f"मान्यकरण: {len(problems)} problem(s)")

out = Path("export")
out.mkdir(exist_ok=True)
lex.save(out / "birds.lift")
print("=== birds.lift ===")
print((out / "birds.lift").read_text(encoding="utf-8"), end="")
print("=== birds.lift-ranges ===")
print((out / "birds.lift-ranges").read_text(encoding="utf-8"), end="")
```

## यह क्या उत्पन्न करता है

`validation: 0 problem(s)`, फिर `.lift` और उसका साथी एक साथ:

```
पक्षी।लिफ्ट
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
      <text>मुर्गी</text>
    </form>
    <form lang="pt">
      <text>मुर्गी</text>
    </form>
  </lexical-unit>
  <pronunciation>
    <form lang="en">
      <text>वक्ता: आना</text>
    </form>
    <media href="audio/nkhuku.wav"/>
  </pronunciation>
  <sense id="kanga_s1">
    <grammatical-info value="Noun"/>
    <gloss lang="en">
      <text>मुर्गी</text>
    </gloss>
    <definition>
      <form lang="en">
        <text>अंडे और मांस के लिए पाला जाने वाला एक घरेलू मुर्गी</text>
      </form>
    </definition>
    <example>
      <form lang="seh">
        <text>मुझे मुर्गी चाहिए।</text>
      </form>
      <translation>
        <form lang="en">
          <text>मुझे एक मुर्गी चाहिए।</text>
        </form>
      </translation>
    </example>
    <illustration href="pictures/hen.jpg">
      <label>
        <form lang="en">
          <text>एक मादा मुर्गी</text>
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
        <text>संज्ञा</text>
      </form>
    </label>
  </range-element>
</range>
<range id="semantic-domain-ddp4">
  <range-element id="1.6.1.2">
    <label>
      <form lang="en">
        <text>पक्षी</text>
      </form>
    </label>
  </range-element>
</range>
</lift-ranges>
```

## एपीआई पर नोट्स

### Building the document

- Multitext fields (`lexical_unit`, `definition`, a `URLRef`'s label, a `Field`'s content) map language codes to text, so a source model's per-language strings carry over one-to-one.
- `Lexicon.add_ranges_file(ranges, href=...)` attaches the companion and writes the header `<range href>` references for you, so the entry's `Noun` and `1.6.1.2` values resolve against the ranges you defined.
- A `URLRef` is an href plus an optional caption/label multitext, used for both `<media>` (audio) and `<illustration>` (photos). यहाँ का उच्चारण द कॉम्बाइन की परंपरा का पालन करता है, जिसमें `en` रूप को `Speaker: <name>` के रूप में पढ़ा जाता है।
- ऐप-विशिष्ट डेटा जिसमें कोई नेटिव LIFT होम राइड्स नहीं होतीं, एक `<field>` (या `<trait>`) के रूप में: FieldWorks इन्हें कस्टम फ़ील्ड्स के रूप में पढ़ता है और The Combine इन्हें संरक्षित करता है।
- Give every entry a real, stable `guid` (e.g. from `uuid.uuid4()`, reused across exports); a later re-import updates the entry in place rather than duplicating it. `sil-lift validate --require-ids` इसे लागू करता है।

### Timestamps

The `dateCreated`/`dateModified` in the output above are not in the script. `save()` stamped them with the moment it ran, since an entry written for the first time carries no date of its own.

- `when=` supplies that moment instead of reading the clock, which is what makes a generated export byte-reproducible for a CI job to diff.
- `stamp=False` writes no dates at all.

बाकी कॉन्ट्रैक्ट के लिए [जेनरेट किए गए टाइमस्टैम्प](../fidelity.md#generated-timestamps) देखें।

### प्रमाणीकरण

`lex.iter_problems()` डिस्क पर कुछ भी लिखने से पहले इन-मेमोरी दस्तावेज़ की वैधता जांचता है; यहाँ यह त्रुटिरहित है। Because the lexicon has no folder yet, the media-presence and companion-href checks are skipped. Run [`sil-lift validate`](cli.md) on the saved output (or with `--no-check-media`) once the audio and photo files are in place.

## पैकेजिंग

`lex.save("export/birds.lift")` फ़ोल्डर फ़ॉर्म (`.lift` + `.lift-ranges` एक साथ) लिखता है। To emit a single zipped package that FieldWorks and The Combine import directly, use `lex.save_zip("birds.zip")` instead. See [Producing conformant LIFT](lift-export-interop.md).
