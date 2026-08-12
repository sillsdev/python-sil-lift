# कमांड लाइन

पैकेज (`pip install sil-lift`) इंस्टॉल करने पर `sil-lift` कमांड भी इंस्टॉल हो जाता है — यह LiftTools की भावना में एक समर्थित टूल है जो पैकेज के साथ आता है (और `validate` के लिए लाइब्रेरी API का एक कार्यशील उदाहरण)।

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media] [--require-ids]
                                           सभी समस्याएँ, फ़ाइल/प्रविष्टि/पंक्ति के साथ; त्रुटियों पर 1 पर बाहर निकलें
sil-lift stats PATH [--format {text,json}]
                                           प्रविष्टि/अर्थ/भाषा की गिनती (स्ट्रीमिंग; कोई भी आकार)
sil-lift sort PATH [-o OUT]               मानकीकृत रूप से क्रमबद्ध, diff-तैयार प्रतिलिपि (डिफ़ॉल्ट: उसी स्थान पर)
sil-lift check-media PATH                 अनुपस्थित और अनाथ मीडिया रिपोर्ट; यदि अनुपस्थित हो तो 1 पर निकास
sil-lift export PATH [-o OUT] [--langs L] [--tsv]
                                           प्रत्येक लीफ़ सेंस के लिए एक पंक्ति (सबसेंस समतल) CSV/TSV में (स्ट्रीमिंग)
```

`--format json` CI/ऑटोमेशन के उपयोग के लिए stdout पर एक ही JSON ऑब्जेक्ट लिखता है (और कुछ नहीं); नीचे दिए गए उदाहरण में स्कीमा देखें। `--strict` चेतावनियों को त्रुटियों के रूप में मानता है, और कोई भी चेतावनी मिलने पर 1 पर बाहर निकल जाता है — इसका उपयोग बिल्ड को केवल त्रुटियों पर नहीं बल्कि बिल्कुल भी चेतावनी न होने पर रोकने के लिए करें। `--no-check-media` फ़ाइल सिस्टम मीडिया-उपस्थिति जाँच को छोड़ देता है (`missing-media` निष्कर्षों को दबाते हुए), जो तब उपयोगी होता है जब किसी ताज़ा उत्पन्न निर्यात का सत्यापन किया जा रहा हो, जिसकी ऑडियो/फ़ोटो फ़ाइलें उसी फ़ोल्डर में होने के बजाय कहीं और स्थित हों। `--require-ids` अतिरिक्त रूप से किसी भी ऐसी प्रविष्टि पर विफल होता है जिसमें `guid` न हो या किसी सेंस में `id` न हो — यह LIFT की तुलना में अधिक सख्त है, उन वर्कफ़्लो के लिए जो एक स्थिर id द्वारा पुनः आयात करते हैं। पथ के रूप में `-` पास करने पर दस्तावेज़ stdin से पढ़ा जाता है (एक पाइप्ड दस्तावेज़ का कोई फ़ोल्डर नहीं होता, इसलिए इसका साथी `.lift-ranges` और मीडिया हल नहीं होते)। `stats` भी `--format json` लेता है, और गिनतियों को एक ही JSON ऑब्जेक्ट के रूप में उत्पन्न करता है।

!!! note
    `validate` के एग्जिट कोड और `--format json` स्कीमा एक समर्थित ऑटोमेशन इंटरफ़ेस हैं: दोनों टेस्ट द्वारा कवर किए गए हैं और केवल SemVer के तहत ही बदलते हैं।

`sort` केवल `.lift` फ़ाइल को ही पुनः लिखता है; साथी `.lift-ranges` फ़ाइलें अछूती रह जाती हैं (उन्हें `RangesFile` API के साथ अलग से क्रमबद्ध करें)।

`validate`, `stats`, `check-media`, और `export` एक ज़िप किए गए LIFT पैकेज को भी स्वीकार करते हैं (दोनों लेआउट में एक `.zip` — आर्काइव रूट में फ़ाइलें, या एक टॉप-लेवल फ़ोल्डर के अंदर); इसे एक अस्थायी निर्देशिका में निकाला जाता है और कमांड समाप्त होने पर हटा दिया जाता है।

उदाहरण:

```
$ sil-lift validate dictionary.lift
त्रुटि [dangling-ref] dictionary.lift:88 (entry apu): ref 'nope' किसी भी एंट्री आईडी/GUID या सेंस आईडी से मेल नहीं खाता
चेतावनी [uri-not-rfc] dictionary.lift:6: <range href='file://C:/...'>: URI प्राधिकरण के रूप में Windows ड्राइव अक्षर का उपयोग (FLEx-शैली file://C:/)
1 त्रुटि(एँ), 1 चेतावनी(एँ)

$ sil-lift validate dictionary.lift --format json
{
  "problems": [
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "ref 'nope' matches no entry id/guid or sense id",
      "file": "dictionary.lift",
      "entry_id": "apu",
      "guid": null,
      "line": 88
    },
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: Windows ड्राइव अक्षर को URI प्राधिकरण के रूप में उपयोग किया गया (FLEx-शैली file://C:/)",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 1
  }
}

$ sil-lift stats sango.lift
entries:   3507
senses:    4541
...

$ sil-lift export dictionary.lift --langs en,fr -o dictionary.csv
```

एग्जिट कोड: `0` सफलता (चेतावनियाँ अनुमत हैं, जब तक `--strict` न हो), `1` निष्कर्ष (मान्यकरण त्रुटियाँ / मीडिया अनुपस्थित / `--strict` के तहत चेतावनियाँ), `2` अपठनीय इनपुट।
