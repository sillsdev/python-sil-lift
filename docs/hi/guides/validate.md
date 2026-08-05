# सत्यापित करें

प्रमाणीकरण हमेशा स्पष्ट होता है — लोडिंग और सेविंग कभी भी निहित रूप से प्रमाणीकरण नहीं करते।

```python
import sil_lift

# Exhaustive: समस्याओं की एक लेज़ी स्ट्रीम (स्कीमा + सेमंटिक लेयर्स).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # error [dangling-ref] dictionary.lift:88 (entry apu): ref 'nope' matches ...

# Fail-fast: पहली त्रुटि-स्तर की समस्या पर LiftValidationError उठाता है।
sil_lift.validate_file("dictionary.lift")

# इन-मेमोरी स्थिति (पहले सीरियलाइज़ होती है — बड़े शब्दकोशों पर एक दस्तावेजीकृत लागत):
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

प्रत्येक `Problem` में `level` (`"error"`/`"warning"`), एक स्थिर `code`, `message`, और एक पता होता है: `file`, `entry_id`, `guid`, `line`.

## परतें

1. LIFT 0.13 व्याकरण (lift-standard से विक्रेता) के विरुद्ध RELAX NG।
2. **रेंज स्कीमा** — इस प्रोजेक्ट का `lift-ranges-0.13.rng` — प्रत्येक ट्रैक किए गए `.lift-ranges` साथी पर।
3. **सेमांटिक जाँचें** जिन्हें व्याकरण व्यक्त नहीं कर सकता: `duplicate-guid`, `dangling-ref`, `range-parent`, `undefined-range-value`, `duplicate-form-lang`, `missing-media`।

## वास्तविक-विश्व फील्डवर्क्स (FLEx) आउटपुट

FieldWorks व्यवस्थित रूप से कुछ सामग्री लिखता है जिसे सख्त टूलिंग अस्वीकार कर देती है। यहाँ sil-lift की नीति है, ताकि वास्तविक शब्दकोश उपयोगी रूप से मान्य हों:

- `file://C:/...` hrefs (अमान्य URI) को स्कीमा त्रुटियों के रूप में नहीं, बल्कि **चेतावनियाँ** (`uri-not-rfc`) के रूप में रिपोर्ट किया जाता है — C# वैलिडेटर ने उन्हें कभी अस्वीकार नहीं किया।
- कानूनी रूप से इंटरलीव किए गए चाइल्ड एलिमेंट्स (उदाहरण के लिए, एक तरह से `field, note, field, note`) को **फ्लैग नहीं** किया जाता है, जो libxml2 में एक फॉलस पॉजिटिव से बचने का काम करता है।
- रेंज मानों की तुलना यूनिकोड NFC सामान्यीकरण के तहत की जाती है — FLEx एक ही एक्सपोर्ट में `.lift` को NFC में और `.lift-ranges` को NFD में लिखता है।
- FLEx के `trait`/`field` एक्सटेंशन `range-element` के अंदर रिपोर्ट किए जाते हैं (रेंज स्कीमा के खिलाफ स्कीमा त्रुटियाँ): ये वास्तव में विनिर्देश से विचलन हैं।
