# पढ़ें, संपादित करें, लिखें

## लोड हो रहा है

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` accepts any well-formed LIFT **0.13** document, including schema-invalid real-world files. मॉडल द्वारा परिभाषित न किए गए कोई भी तत्व (अज्ञात तत्व/गुणधर्म, टिप्पणियाँ) प्रत्येक नोड के अपारदर्शी `extra` फ़ील्ड में LIFT अवशेष के रूप में बिना किसी हानि के संचित किया जाता है। अन्य LIFT संस्करण संस्करण का नाम बताते हुए `LiftParseError` उत्पन्न करते हैं।

## मॉडल

Every LIFT element is a typed dataclass: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, and so on.

### Multilingual text

बहुभाषी पाठ एक `Multitext` है, जो भाषा कोड से `Text` के लिए एक `Mapping` है:

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # plain strings are coerced
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` is structured (an ordered list of `str` and `Span` fragments) because `<text>` can contain nested `<span>` markup. `str(text)` सादे पाठ में बदल देता है; खंड राउंड-ट्रिपिंग के लिए मार्कअप बनाए रखते हैं।

The mapping shows one value per language. Underneath, `forms` holds every `<form>` in file order. A schema-valid document has at most one form per language, but real files sometimes repeat one.

Because the mapping is keyed by language, `len()` counts languages rather than forms, and the `keys()`, `values()` and `items()` views list each language once. Both mutators also act on the whole language: `del entry.lexical_unit["en"]` removes every English form, and assigning to `"en"` leaves exactly one.

For a repeated language, `entry.lexical_unit["en"]`, `get()`, `values()` and `items()` all answer with its first form, and [`validate`](validate.md#problem-codes) reports `duplicate-form-lang` until you assign to that language.

A form carrying no `lang` at all cannot be created through the mapping. It is reported as `form-missing-lang`, and is dropped when its node re-serializes.

### Senses and glosses

LIFT में ग्लॉसेज़ _फॉर्म-आकार_ होते हैं (प्रत्येक `<gloss>` अपनी भाषा स्वयं साथ लेता है), इसलिए एक सेंस में `glosses: list[Form]` होता है और साथ ही कुछ हेल्पर होते हैं:

```python
sense = entry.senses[0]       # top level only
sense.gloss("en")             # Text | None
entry.all_senses()            # every sense and subsense, document order
entry.gloss_langs()           # {"en", "id"}, subsenses included
```

जब भी कोई प्रश्न पूरी प्रविष्टि से संबंधित हो, तो `all_senses()` का उपयोग करें: संवेदनाओं की गिनती करने, भाषाओं को एकत्रित करने, मीडिया खोजने के लिए। `entry.senses` शीर्ष स्तर देता है, जो तब ही काम आता है जब स्वयं नेस्टिंग मायने रखती हो।

## बचत

```python
lex.save()                    # back to where it was loaded from
lex.save("elsewhere.lift")
```

आपने जिन प्रविष्टियों में कोई बदलाव नहीं किया, वे बाइट-समान रूप से वापस लिखी जाती हैं; एक ऐसा दस्तावेज़ जिसे आपने बिल्कुल भी संशोधित नहीं किया, वह पहले बाइट से लेकर आखिरी बाइट तक बाइट-समान होता है। सटीक अनुबंध के लिए [फिडेलिटी गारंटी](../fidelity.md) देखें।

### समय-मुद्रांक

आपने जिन प्रविष्टियों में संशोधन किया, वे एक नए `dateModified` (और यदि उनके पास कोई `dateCreated` नहीं था तो `dateCreated`) के साथ भेजी जाती हैं, इसलिए कोई संपादन उस तारीख के तहत नहीं भेजा जाता जिस पर इसे लोड किया गया था। Tools that merge LIFT decide what changed from that attribute. Two arguments adjust the stamping:

- `lex.save(stamp=False)` writes the dates the model holds and nothing more.
- `lex.save(when=...)` pins the moment instead of reading the clock.

बाकी नियमों के लिए [जेनरेट किए गए टाइमस्टैम्प](../fidelity.md#generated-timestamps) देखें।

### Skipping a save that changes nothing

ऐसे सेव को छोड़ने के लिए जो कुछ भी नहीं बदलेगा, उसे `lex.changes()` से गार्ड करें:

```python
यदि lex.changes():
    lex.save()
```

यह केवल तभी `False` लौटाता है जब `save()` स्रोत बाइट्स को पुन: उत्पन्न कर सके, जिसमें प्रविष्टियाँ, हेडर, रूट एलिमेंट और प्रत्येक `.lift-ranges` साथी शामिल हों। Skipping the write leaves the file's modification time alone and avoids a spurious diff.

The check is cheap. यह पहले अंतर पर ही रुक जाता है, इसलिए संपादित शब्दकोश पर इसका खर्च लगभग शून्य होता है। एक अपरिवर्तित शब्दकोश को अपरिवर्तित साबित करने के लिए उसे पूरी तरह से सीरियलाइज करना पड़ता है, लेकिन फिर भी इसकी लागत उस सेव की तुलना में कम होती है जिसे यह छोड़ देता है।

यह सामग्री की तुलना करता है, गंतव्य की नहीं, इसलिए केवल उसी स्थान पर सहेजने की रक्षा करें। `lex.save("elsewhere.lift")` writes the document and its companions to the new path even when `changes()` is `False`, so guarding it would skip that copy.

## शुरू से निर्माण

```python
lex = sil_lift.Lexicon(producer="my-script 1.0")
entry = sil_lift.Entry(id="hello", guid="...")
entry.lexical_unit["en"] = "hello"
sense = sil_lift.Sense()
sense.glosses.append(sil_lift.Form("fr", sil_lift.Text(["bonjour"])))
entry.senses.append(sense)
lex.entries.append(entry)
lex.save("new.lift")
```

## कैनोनिकल क्रमबद्धकरण

```python
lex.sort()      # प्रविष्टियाँ (guid, id) के अनुसार; id/tag द्वारा रेंज/फ़ील्ड परिभाषाएँ
lex.save()      # बिना बदले प्रविष्टियाँ अपने सटीक बाइट्स बनाए रखती हैं, नई व्यवस्था में

sil_lift.canonicalize("in.lift", "out.lift")   # पूरी तरह से पुनः-सीरियलाइज़्ड, diff-तैयार
```

यह भी देखें: [कार्य-उदाहरण: ग्लॉसेज़ के थोक-संपादन](bulk-edit-glosses.md)।
