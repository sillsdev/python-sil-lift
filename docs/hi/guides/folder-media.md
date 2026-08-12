# LIFT फ़ोल्डर: श्रेणियाँ और मीडिया

एक LIFT शब्दकोश आमतौर पर एक _फ़ोल्डर_ होता है: `.lift` फ़ाइल, एक या अधिक `.lift-ranges` साथी (साइडकार फ़ाइलें), और `audio/` / `pictures/` मीडिया।

## दायरे

```python

lex = sil_lift.load("dictionary.lift")      # साथी स्वचालित रूप से ट्रैक किए जाते हैं

lex.ranges_files                            # {Path(...): RangesFile} view
lex.all_ranges()["grammatical-info"].elements
```

साथी खोज वास्तविक दुनिया को संभालती है: एक `range/@href` जिसका संदर्भ किसी मौजूदा फ़ाइल की ओर है, का उपयोग किया जाता है; FieldWorks के dangling absolute `file://C:/...` hrefs `.lift` के पास होने पर href के basename पर वापस आ जाते हैं; और पारंपरिक `<name>.lift-ranges` sibling तब भी लिया जाता है जब कोई भी इसे संदर्भित नहीं करता।

`lex.save()` `.lift` और प्रत्येक ट्रैक किए गए साथी को एक साथ लिखता है। `RangesFile` में किए गए संपादन _उसकी_ फ़ाइल में वापस सहेजे जाते हैं; बिना बदले रेंज अपने सटीक बाइट्स बनाए रखते हैं। स्वतंत्र उपयोग:

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

साथी खोज को छोड़ने के लिए `load()` को `resolve_ranges=False` पास करें।

## माध्यम

```python
for ref in lex.media_refs():        # हर <media> और <illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.missing_media()                 # उन रेफ़रेंसों के लिए जिनकी फाइलें मौजूद नहीं हैं
```

रिज़ॉल्यूशन पारंपरिक लेआउट का अनुसरण करता है: एक सापेक्ष href को दिए गए रूप में जांचा जाता है (बैकस्लैश को सामान्यीकृत किया गया — WeSay लिखता है `pictures\photo with space.png`) और `audio/` (उच्चारण मीडिया के लिए) या `pictures/` (चित्रण के लिए) के अंतर्गत। रिमोट/एब्सोल्यूट hrefs की जाँच नहीं की जा सकती और उन्हें छोड़ दिया जाता है।

## अन्य फ़ोल्डर की सामग्री

एक LIFT फ़ोल्डर में अक्सर ऐसी फ़ाइलें होती हैं जिन्हें sil-lift मॉडल नहीं करता — जैसे `WritingSystems/` के अंतर्गत लेखन-प्रणाली LDML, `consent/` के अंतर्गत The Combine के वक्ता सहमति ऑडियो/छवि फ़ाइलें, और इसी तरह की अन्य फ़ाइलें; `load()`/`save()` इन्हें बिना छुए छोड़ देते हैं, और [`Lexicon.save_zip()`](lift-export-interop.md) फ़ोल्डर को पैकेज करते समय इन्हें शब्दशः शामिल करता है।
