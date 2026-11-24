# कार्य उदाहरण: शून्य से LIFT एक्सपोर्ट बनाना

यदि आप किसी अन्य एप्लिकेशन का डेटा LIFT के रूप में निर्यात कर रहे हैं (जो [अनुरूप LIFT उत्पन्न करने](lift-export-interop.md) के पीछे का कार्य है), तो `sil-lift` दस्तावेज़ ऑब्जेक्ट को एक-एक करके बना सकता है और उसे सीरियलाइज़ कर सकता है, बजाय इसके कि आप XML को हाथ से उत्पन्न करें। यह एक स्क्रिप्ट के माध्यम से मार्गदर्शन करता है जो:

- एक प्रविष्टि का निर्माण करता है जिसमें एक वास्तविक शब्दकोश की विशेषताएँ होती हैं: कई लिपियाँ, उच्चारण, एक उदाहरण के साथ अर्थ, एक चित्र, एक अर्थ-क्षेत्रीय गुण, और एक ऐप-विशिष्ट क्षेत्र;
- नियंत्रित शब्दावलियों को एक `.lift-ranges` साथी में लिखता है;
- सत्यापित करता है और सहेजता है।

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

### दस्तावेज़ का निर्माण

- मल्टीटेक्स्ट फ़ील्ड (`lexical_unit`, `definition`, एक `URLRef` का लेबल, एक `Field` की सामग्री) भाषा कोड को टेक्स्ट में मैप करते हैं, इसलिए स्रोत मॉडल की प्रति-भाषा स्ट्रिंग्स एक-से-एक स्थानांतरित हो जाती हैं।
- `Lexicon.add_ranges_file(ranges, href=...)` साथी फ़ाइल को संलग्न करता है और आपके लिए हेडर `<range href>` संदर्भ लिखता है, ताकि प्रविष्टि के `Noun` और `1.6.1.2` मान आपके द्वारा परिभाषित रेंज के अनुसार हल हो सकें।
- `URLRef` एक href और एक वैकल्पिक कैप्शन/लेबल मल्टीटेक्स्ट है, जो `<media>` (ऑडियो) और `<illustration>` (फोटो) दोनों के लिए उपयोग किया जाता है। यहाँ का उच्चारण द कॉम्बाइन की परंपरा का पालन करता है, जिसमें `en` रूप को `Speaker: <name>` के रूप में पढ़ा जाता है।
- ऐप-विशिष्ट डेटा जिसमें कोई नेटिव LIFT होम राइड्स नहीं होतीं, एक `<field>` (या `<trait>`) के रूप में: FieldWorks इन्हें कस्टम फ़ील्ड्स के रूप में पढ़ता है और The Combine इन्हें संरक्षित करता है।
- प्रत्येक प्रविष्टि को एक वास्तविक, स्थिर `guid` दें (उदाहरण के लिए `uuid.uuid4()` से, जो एक्सपोर्ट्स में पुन: उपयोग किया जाता है); बाद में पुनः आयात करने पर प्रविष्टि को डुप्लिकेट करने के बजाय उसी स्थान पर अपडेट किया जाता है। `sil-lift validate --require-ids` इसे लागू करता है।

### समय-मुद्रांक

ऊपर दिए गए आउटपुट में `dateCreated`/`dateModified` स्क्रिप्ट में नहीं हैं। `save()` ने उन्हें उस क्षण की मुहर लगा दी जब यह चला, क्योंकि पहली बार लिखी गई प्रविष्टि में अपनी कोई तारीख नहीं होती।

- `when=` घड़ी पढ़ने के बजाय उस क्षण को प्रदान करता है, और यही एक जेनरेट किए गए एक्सपोर्ट को सीआई जॉब द्वारा डिफ करने के लिए बाइट-रिप्रोड्यूसिबल बनाता है।
- `stamp=False` बिल्कुल भी तारीख नहीं लिखता।

बाकी कॉन्ट्रैक्ट के लिए [जेनरेट किए गए टाइमस्टैम्प](../fidelity.md#generated-timestamps) देखें।

### प्रमाणीकरण

`lex.iter_problems()` डिस्क पर कुछ भी लिखने से पहले इन-मेमोरी दस्तावेज़ की वैधता जांचता है; यहाँ यह त्रुटिरहित है। चूंकि शब्दकोश में अभी तक कोई फ़ोल्डर नहीं है, इसलिए मीडिया-उपस्थिति और साथी-ह्रेफ़ जाँचें छोड़ दी जाती हैं। जब ऑडियो और फोटो फाइलें तैयार हो जाएँ, तो सहेजे गए आउटपुट पर [`sil-lift validate`](cli.md) चलाएँ (या `--no-check-media` के साथ)।

## पैकेजिंग

`lex.save("export/birds.lift")` फ़ोल्डर फ़ॉर्म (`.lift` + `.lift-ranges` एक साथ) लिखता है। FieldWorks और The Combine द्वारा सीधे आयात किए जाने वाले एकल ज़िप पैकेज को उत्सर्जित करने के लिए, इसके बजाय `lex.save_zip("birds.zip")` का उपयोग करें। देखें [अनुरूप LIFT का उत्पादन](lift-export-interop.md)।
