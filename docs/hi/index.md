# सिल-लिफ्ट

[LIFT](https://github.com/sillsdev/lift-standard) (लेक्सिकन इंटरचेंज फॉर्मैट) 0.13 के लिए एक पाइथन लाइब्रेरी: LIFT फ़ोल्डर (`.lift` + `.lift-ranges` + मीडिया संदर्भ) का बिना हानि के रीड/राइट, स्कीमा और सेमांटिक सत्यापन, तथा मानक क्रमबद्धकरण, साथ ही बड़े शब्दकोशों के लिए स्ट्रीमिंग एपीआई।

स्थिति: प्री-रिलीज़, सक्रिय विकास के अधीन।

## स्थापित करें

[PyPI](https://pypi.org/project/sil-lift/) से:

```
pip install sil-lift   # लाइब्रेरी + sil-lift कमांड
```

पाइथन 3.11+ आवश्यक है। एकमात्र रनटाइम निर्भरता lxml है।

## 30-सेकंड का दौरा

एक शब्दकोश लोड करें, अंग्रेज़ी व्याख्या के बिना हवाई प्रविष्टियाँ खोजें, परिभाषा संपादित करें, और सहेजें:

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # tracks .lift-ranges companions too

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("haw") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # या lex.find(id="poʻo_a1b2")
entry.senses[0].definition["en"] = "head (anatomy)"

lex.save()   # संपादित प्रविष्टि पुनः सीरियलाइज़ और पुनः स्टैम्प की गई; बाकी बाइट-समान
```
