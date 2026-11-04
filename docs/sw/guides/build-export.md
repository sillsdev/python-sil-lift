# Mfano uliofanyiwa kazi: kujenga usafirishaji wa LIFT kutoka mwanzo

Ikiwa unatuma data za programu nyingine kama LIFT — kazi iliyopo nyuma ya [Kutengeneza LIFT inayokidhi viwango](lift-export-interop.md) — `sil-lift` inaweza kujenga kipengee cha hati kipengee kwa kipengee na kukisierializa, badala ya kutoa XML kwa mkono. Hii inaelezea hatua kwa hatua skripti moja inayounda kipengee chenye vipengele ambavyo kamusi halisi ina (mifumo mingi ya uandishi, matamshi, maana yenye mfano, mfano wa picha, sifa ya eneo la semanti, na sehemu maalum kwa programu), inaandika kamusi zilizodhibitiwa katika faili mwandani la `.lift-ranges`, inathibitisha, na huhifadhi.

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

- Maeneo ya maandishi mengi (`lexical_unit`, `definition`, lebo ya `Form`/`URLRef`, yaliyomo ya `Field`, ...) Chukua mnyororo mmoja kwa kila mfumo wa uandishi kupitia kiolesura cha upangaji: `entry.lexical_unit["seh"] = "nkhuku"` huongeza `<form lang="seh">`. Mfano wa chanzo unaotumia misimbo ya lugha kupanga nyuzi unaendana moja kwa moja na hili.
- `RangesFile.add_range()` /  `Range.add_element()` hujenga vokabularia zilizodhibitiwa, na `Lexicon.add_ranges_file(ranges, href=...)` huunganisha faili ya ziada na kuongeza kichwa `<range href>` kwa marejeleo — hivyo `<grammatical-info value="Noun">` na `<trait name="semantic-domain-ddp4" value="1.6.1.2">` za kipengee hurejelea masafa uliyoyabainisha.
- URLRef ni href pamoja na maandishi mengi ya kichwa/lebo ya hiari — hutumika kwa `<media>` (sauti) na `<illustration>` (picha). Matamshi hapa yanafuata kanuni ya The Combine ya aina ya 'en', kama inavyosomwa na msemaji: <name>
- Data maalum kwa programu bila safari za nyumbani za LIFT za asili kama `<field>` (au `<trait>`): FieldWorks husoma hizi kama viwanja maalum na The Combine huzihifadhi.
- Panga kila kipengee na `guid` halisi, thabiti (kwa mfano kutoka `uuid.uuid4()`), inayotumika tena katika usafirishaji wa data — kuingiza tena baadaye husasisha kipengee mahali pake badala ya kuunda nakala yake. `sil-lift validate --require-ids` inahakikisha hili.
- `dateCreated`/`dateModified` katika matokeo hapo juu hayapo kwenye skripti: `save()` iliweka alama hizo kwa wakati skripti ilipokuwa ikiendeshwa, kwa kuwa kumbukumbu iliyotengenezwa kwa mara ya kwanza haina tarehe yake mwenyewe. `when=` hutoa wakati huo badala ya kusoma saa, jambo linalofanya faili la nje lililotengenezwa liwe linaloweza kuzalishwa tena kwa kila baiti kwa ajili ya kazi ya CI kulinganisha; `stamp=False` haandiki tarehe yoyote kabisa. Tazama [Alama za muda zilizotengenezwa](../fidelity.md#generated-timestamps) kwa sehemu iliyobaki ya mkataba.
- `lex.iter_problems()` inathibitisha hati iliyopo kwenye kumbukumbu kabla ya chochote kuhifadhiwa kwenye diski; hapa iko sawa. Kwa sababu kamusi bado haina folda, ukaguzi wa media-presence na companion-href umeachwa — endesha [`sil-lift validate`](cli.md) kwenye matokeo yaliyohifadhiwa (au kwa kutumia `--no-check-media`) mara tu faili za sauti na picha zitakapokuwa zimewekwa.

## Ufungashaji

`lex.save("export/birds.lift")` huandika muundo wa saraka (`.lift` + `.lift-ranges` kando kando). Ili kutoa kifurushi kimoja cha zip ambacho FieldWorks na The Combine huingiza moja kwa moja, tumia `lex.save_zip("birds.zip")` badala yake — angalia [Kutengeneza LIFT inayofuata viwango](lift-export-interop.md).
