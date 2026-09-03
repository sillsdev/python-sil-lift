# कार्य उदाहरण: शून्य से LIFT एक्सपोर्ट बनाना

यदि आप किसी अन्य एप्लिकेशन का डेटा LIFT के रूप में निर्यात कर रहे हैं — [अनुरूप LIFT उत्पन्न करने](lift-export-interop.md) के पीछे का कार्य — तो `sil-lift` दस्तावेज़ के प्रत्येक ऑब्जेक्ट को क्रमबद्ध करके उसे सीरियलाइज़ कर सकता है, बजाय इसके कि आप XML को हाथ से उत्पन्न करें। यह एक स्क्रिप्ट के माध्यम से दिखाता है कि कैसे एक प्रविष्टि तैयार की जाती है, जिसमें एक वास्तविक शब्दकोश के सभी घटक होते हैं (कई लेखन प्रणालियाँ, उच्चारण, एक अर्थ उदाहरण के साथ, एक चित्रण, एक अर्थ-क्षेत्रीय गुण, और एक ऐप-विशिष्ट फ़ील्ड), नियंत्रित शब्दावलियों को `.lift-ranges` साथी फ़ाइल में लिखा जाता है, सत्यापित किया जाता है, और सहेजा जाता है।

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
pron.forms["en"] = "Speaker: Ana"  # द कंबाइन का स्पीकर-लेबल कन्वेंशन
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

# डिस्क पर लिखने से पहले save() क्या लिखेगा, इसकी जांच करें।
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

## यह क्या उत्पन्न करता है

`validation: 0 problem(s)`, फिर `.lift` और उसका साथी एक साथ:

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

## एपीआई पर नोट्स

- मल्टीटेक्स्ट फ़ील्ड (`lexical_unit`, `definition`, एक `Form`/`URLRef` लेबल, एक `Field` की सामग्री, ...) लेखन प्रणाली के लिए एक स्ट्रिंग मैपिंग इंटरफ़ेस के माध्यम से लें: `entry.lexical_unit["seh"] = "nkhuku"` एक `<form lang="seh">` जोड़ता है। एक स्रोत मॉडल जो भाषा कोड के आधार पर स्ट्रिंग्स को मैप करता है, सीधे इस पर लागू होता है।
- `RangesFile.add_range()` / `Range.add_element()` नियंत्रित शब्दावलियाँ बनाती हैं, और `Lexicon.add_ranges_file(ranges, href=...)` साथी फ़ाइल को जोड़ती है और हेडर `<range href>` संदर्भ जोड़ती है — ताकि प्रविष्टि के `<grammatical-info value="Noun">` और `<trait name="semantic-domain-ddp4" value="1.6.1.2">` आपके द्वारा परिभाषित रेंज के अनुसार हल हों।
- `URLRef` एक href और एक वैकल्पिक कैप्शन/लेबल मल्टीटेक्स्ट है — जो `<media>` (ऑडियो) और `<illustration>` (फ़ोटो) दोनों के लिए उपयोग किया जाता है। यहाँ का उच्चारण द कॉम्बाइन की परंपरा का पालन करता है, जिसमें `en` रूप को `Speaker: <name>` के रूप में पढ़ा जाता है।
- ऐप-विशिष्ट डेटा जिसमें कोई नेटिव LIFT होम राइड्स नहीं होतीं, एक `<field>` (या `<trait>`) के रूप में: FieldWorks इन्हें कस्टम फ़ील्ड्स के रूप में पढ़ता है और The Combine इन्हें संरक्षित करता है।
- प्रत्येक प्रविष्टि को एक वास्तविक, स्थिर `guid` दें (उदाहरण के लिए `uuid.uuid4()` से, जो एक्सपोर्ट्स में पुन: उपयोग किया जाता है) — बाद में पुनः आयात करने पर यह प्रविष्टि को डुप्लिकेट करने के बजाय उसी स्थान पर अपडेट कर देता है। `sil-lift validate --require-ids` इसे लागू करता है।
- `lex.iter_problems()` मेमोरी में मौजूद दस्तावेज़ (जिसे `save()` लिखता) को डिस्क पर लिखने से पहले सत्यापित करता है; यहाँ यह सही है। चूंकि लेक्सिकॉन में अभी तक कोई फ़ोल्डर नहीं है, इसलिए मीडिया-उपस्थिति और साथी-href जांच छोड़ दी जाती हैं — ऑडियो और फोटो फ़ाइलें तैयार होने पर सहेजे गए आउटपुट पर [`sil-lift validate`](cli.md) चलाएँ (या `--no-check-media` के साथ)।

## पैकेजिंग

`lex.save("export/birds.lift")` फ़ोल्डर फ़ॉर्म (`.lift` + `.lift-ranges` एक साथ) लिखता है। FieldWorks और The Combine द्वारा सीधे आयात किए जाने वाले एकल ज़िप पैकेज को उत्पन्न करने के लिए, इसके बजाय `lex.save_zip("birds.zip")` का उपयोग करें — देखें [अनुरूप LIFT का उत्पादन](lift-export-interop.md)।
