# C# लाइब्रेरियों से अंतर

सिल-लिफ्ट, SIL के C# LIFT टूलिंग से ढीले तौर पर मिलता-जुलता है, मुख्य रूप से [libpalaso](https://github.com/sillsdev/libpalaso) के दो भागों से:

- `SIL.Lift`: पार्सर, वैलिडेटर, माइग्रेटर, `LiftSorter`.
- `SIL.DictionaryServices`: `LexEntry`/`LexSense` मॉडल, अपने स्वयं के LIFT रीडर/राइटर के साथ, जिसका उपयोग The Combine और WeSay करते हैं।

sil-lift एक नया कार्यान्वयन है, पोर्ट नहीं। यह पृष्ठ उन स्थानों का सारांश प्रस्तुत करता है जहाँ व्यवहार जानबूझकर भिन्न होता है।

## दायरा

| क्षमता            | सी# लाइब्रेरीज़                                                                      | सिल-लिफ्ट                                                                                            |
| ----------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| लिफ्ट संस्करण     | 0.10–0.13 (स्थानांतरण अंतर्निहित) | केवल **0.13**; पुराने संस्करणों को एक स्पष्ट त्रुटि के साथ अस्वीकार कर दिया जाता है। |
| संस्करण माइग्रेशन | `Migrator` (XSLT श्रृंखला)                                        | कोई नहीं; एकबारगी अपग्रेड के लिए लिफ्ट-स्टैंडर्ड में मौजूद XSLTs का उपयोग करें।                      |
| प्रमाणीकरण        | केवल RELAX NG (`Validator`)                                       | RELAX NG + रेंज स्कीमा + सेमांटिक जाँच                                                               |
| स्ट्रीमिंग        | आंतरिक प्रविष्टि-कणिकीय पार्सिंग                                                     | सार्वजनिक `open_reader` / `open_writer` एपीआई                                                        |

## एपीआई आकार

`SIL.Lift` का पार्सर कॉलबैक-चालित (`ILexiconMerger`) है: यह पार्स इवेंट्स को एक कंज्यूमर पर पुश करता है। sil-lift instead returns a plain object graph (typed dataclasses for every LIFT element) because Python scripters want objects, not callbacks.

`SIL.DictionaryServices` does layer a `LexEntry`/`LexSense` object model over `SIL.Lift`, but it is an application model: it represents only the constructs those apps use. Re-serializing through it therefore can't preserve out-of-model content the way sil-lift's LIFT residue handling and byte fidelity do (see below).

स्ट्रीमिंग एपीआई वही `Entry` प्रकार देता है, इसलिए सीखने के लिए कोई दूसरा, संक्षिप्त मॉडल नहीं है।

## गमन-आगमन निष्ठा

सबसे मजबूत जानबूझकर किया गया अंतर। `SIL.Lift` के साथ सेव करने पर पूरा दस्तावेज़ पुनः सीरियलाइज़ हो जाता है। सिल-लिफ्ट गारंटियाँ:

- एक अपरिवर्तित दस्तावेज़ **बाइट-समान रूप से** सहेजता है, और
- untouched entries keep their exact source bytes even when other entries change: per-entry byte chunking, applied automatically.

देखें [फिडेलिटी गारंटी](fidelity.md)।

## प्रमाणीकरण

C# `Validator` एक RELAX NG पास चलाता है और पहली त्रुटियों को स्ट्रिंग्स के रूप में रिपोर्ट करता है। sil-lift reports a structured `Problem` stream, each carrying the file, entry, and line it concerns. Its schema layer knowingly diverges in three places:

- अमान्य URI चेतावनियाँ हैं, त्रुटियाँ नहीं। C# RELAX NG इंजन ने कभी भी `anyURI` डेटाटाइप को लागू नहीं किया, इसलिए FieldWorks (FLEx) वर्षों से वास्तविक शब्दकोशों में `file://C:/...` hrefs लिख रहा है। उन फ़ाइलों को अस्वीकार करने से लगभग हर FLEx एक्सपोर्ट पर निशान लग जाएगा।
- **Schematron rules are enforced** (as semantic checks): duplicate form languages and similar co-constraints in the LIFT grammar were silently ignored by C# validation.
- **Range id comparisons are Unicode-normalized** (NFC), because FLEx exports mix NFC and NFD ids. References that resolve only after normalizing are reported as `normalization-mismatch` warnings, a check with no C# counterpart. See [Real-world FieldWorks (FLEx) output](guides/validate.md#real-world-fieldworks-flex-output).

When sil-lift validates a `.lift`, it also validates the `.lift-ranges` companions against a schema for standalone ranges documents, vendored from `lift-standard`. The C# `Validator` does not check `.lift-ranges` files.

## कैनोनिकल क्रमबद्धकरण

`Lexicon.sort()` `LiftSorter` के मुख्य नियमों का पालन करता है (प्रविष्टियाँ केस-असंवेदनशील GUID द्वारा; रेंज और रेंज-तत्व ID द्वारा; हेडर फ़ील्ड परिभाषाएँ टैग द्वारा; अर्थ फ़ाइल क्रम में रखे जाते हैं; `<text>` के अंदर की रिक्त स्थान को कभी भी छुआ नहीं जाता), तीन अंतरों के साथ:

- guid के बिना प्रविष्टियाँ id के अनुसार क्रमबद्ध रूप से व्यवस्थित होती हैं (`LiftSorter` मानता है कि guid मौजूद है);
- ऑर्डरिंग लोकेल-स्वतंत्र है (साधारण केस-फोल्ड किए गए कोड पॉइंट्स, .NET इन्वेरिएंट-कल्चर कोलेशन नहीं);
- same-type lists such as notes, relations, and forms keep their document order rather than being re-sorted by key; grouping is already deterministic, and reordering them only adds diff noise.

spec रिपॉजिटरी का `canonicalizeLift.xsl` बिल्कुल भी उपयोग नहीं किया जाता है: यह लेक्सिकल टेक्स्ट के भीतर रिक्त स्थान को संकुचित कर देता है (विनाशकारी) और इसके उत्पन्न आईडी हर रन पर भिन्न होते हैं।

## आगे नहीं बढ़ाया गया

- WeSay-विशिष्ट सुविधाएँ (LIFT फ़ाइलों के संबंध में डैशबोर्ड/कॉन्फ़िग हैंडलिंग)
- `SynchronicMerger` (LIFT update-file merging): the byte-chunking idea lives on in the fidelity layer, the merging does not.
- LDML लेखन-प्रणाली पार्सिंग: `WritingSystems/` में मौजूद फ़ाइलों को अपारदर्शी फ़ोल्डर सामग्री के रूप में माना जाता है।
