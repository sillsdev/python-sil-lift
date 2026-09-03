# पढ़ें, संपादित करें, लिखें

## लोड हो रहा है

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` कोई भी सुव्यवस्थित LIFT **0.13** दस्तावेज़ स्वीकार करता है — जिसमें स्कीमा-अमान्य वास्तविक-विश्व फ़ाइलें भी शामिल हैं। मॉडल द्वारा परिभाषित न किए गए कोई भी तत्व (अज्ञात तत्व/गुणधर्म, टिप्पणियाँ) प्रत्येक नोड के अपारदर्शी `extra` फ़ील्ड में LIFT अवशेष के रूप में बिना किसी हानि के संचित किया जाता है। अन्य LIFT संस्करण संस्करण का नाम बताते हुए `LiftParseError` उत्पन्न करते हैं।

## मॉडल

प्रत्येक LIFT तत्व एक प्रकारित डेटाक्लास है: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, आदि। बहुभाषी पाठ एक `Multitext` है, जो भाषा कोड से `Text` तक एक मैपिंग की तरह व्यवहार करता है:

```python
entry = lex.find(id="abat")

str(entry.lexical_unit["seh"])          # "abat"
entry.lexical_unit["en"] = "grove"      # साधारण स्ट्रिंग्स को कोअर्स्ड किया जाता है
"en" in entry.citation                  # False
```

`Text` संरचित है — `str` और `Span` खंडों की एक क्रमबद्ध सूची — क्योंकि `<text>` में घिरी हुई `<span>` मार्कअप हो सकती है। `str(text)` सादे पाठ में बदल देता है; खंड राउंड-ट्रिपिंग के लिए मार्कअप बनाए रखते हैं।

LIFT में ग्लॉसेज़ _फॉर्म-आकार के_ होते हैं (प्रत्येक `<gloss>` अपनी भाषा स्वयं साथ ले चलता है), इसलिए एक सेंस में `glosses: list[Form]` होता है और साथ ही एक हेल्पर भी:

```python
sense = entry.senses[0]
sense.gloss("en")                       # Text | None
entry.gloss_langs()                     # {"en", "id"}
```

## बचत

```python
lex.save()                # उस स्थान पर वापस जहाँ से इसे लोड किया गया था
lex.save("elsewhere.lift")
```

आपने जिन प्रविष्टियों में कोई बदलाव नहीं किया, वे बाइट-समान रूप से वापस लिखी जाती हैं; एक ऐसा दस्तावेज़ जिसे आपने बिल्कुल भी संशोधित नहीं किया, वह पहले बाइट से लेकर आखिरी बाइट तक बाइट-समान होता है। सटीक अनुबंध के लिए [फिडेलिटी गारंटी](../fidelity.md) देखें।

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
