# مثال عملي: إنشاء عملية تصدير LIFT من البداية

إذا كنت تقوم بتصدير بيانات تطبيق آخر بتنسيق LIFT — وهي المهمة التي تقف وراء [إنشاء ملفات LIFT متوافقة](lift-export-interop.md) — فيمكن لـ `sil-lift` إنشاء المستند كائنًا تلو الآخر وتسلسله، بدلاً من إنشاء ملف XML يدويًّا. يشرح هذا المثال أحد البرامج النصية التي تقوم بإنشاء مدخل يتضمن العناصر التي يتألف منها القاموس الفعلي (أنظمة كتابة متعددة، ونطق، ومعنى مع مثال، ورسم توضيحي، وسمة المجال الدلالي، وحقل خاص بالتطبيق)، وتقوم بكتابة المفردات المحددة في ملف مصاحب بتنسيق `.lift-ranges`، ثم تتحقق من صحتها، وتحفظها.

## النص

```python
from pathlib import Path

import sil_lift

lex = sil_lift.Lexicon(producer="my-exporter")

# إدخال واحد، تم إنشاؤه من النموذج المصدر.
entry = sil_lift.Entry(id="kanga", guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d")
entry.lexical_unit["seh"] = "nkhuku"
entry.lexical_unit["pt"] = "galinha"

pron = sil_lift.Pronunciation()
pron.forms["en"] = "المتحدث: آنا"  # اتفاقية تسمية المتحدث في "The Combine"
pron.media.append(sil_lift.URLRef(href="audio/nkhuku.wav"))
entry.pronunciations.append(pron)

sense = sil_lift.Sense(id="kanga_s1")
sense.grammatical_info = sil_lift.GrammaticalInfo(value="Noun")
sense.glosses.append(sil_lift.Form(lang="en", text=sil_lift.Text(["chicken"])))
sense.definition["en"] = "a domestic fowl kept for its eggs and meat"

example = sil_lift.Example()
example.forms["seh"] = "Ndinafuna nkhuku."
translation = sil_lift.Translation()
translation.forms["en"] = "I want a chicken."
example.translations.append(translation)
sense.examples.append(example)

photo = sil_lift.URLRef(href="pictures/hen.jpg")
photo.label["en"] = "A hen"
sense.illustrations.append(photo)

sense.traits.append(sil_lift.Trait(name="semantic-domain-ddp4", value="1.6.1.2"))

scientific = sil_lift.Field(type="scientific-name")  # حقل إضافي خاص بالتطبيق
scientific.content["en"] = "Gallus gallus domesticus"
sense.fields.append(scientific)

entry.senses.append(sense)
lex.entries.append(entry)

# المفردات المراقبة التي يشير إليها الإدخال، في ملف .lift-ranges مصاحب.
ranges = sil_lift.RangesFile()
ranges.add_range("grammatical-info").add_element("Noun").label["en"] = "noun"
ranges.add_range("semantic-domain-ddp4").add_element("1.6.1.2").label["en"] = "Bird"
lex.add_ranges_file(ranges, href="birds.lift-ranges")

# التحقق من صحة ما ستكتبه save()، قبل الكتابة على القرص.
problems = list(lex.iter_problems())
print(f"التحقق من الصحة: {len(problems)} مشكلة (مشاكل)")

out = Path("export")
out.mkdir(exist_ok=True)
lex.save(out / "birds.lift")
print("=== birds.lift ===")
print((out / "birds.lift").read_text(encoding="utf-8"), end="")
print("=== birds.lift-ranges ===")
print((out / "birds.lift-ranges").read_text(encoding="utf-8"), end="")
```

## ما الذي تنتجه

`التحقق من الصحة: 0 مشكلة(مشاكل)`، ثم `.lift` وما يرافقه جنبًا إلى جنب:

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

## ملاحظات حول واجهة برمجة التطبيقات (API)

- الحقول متعددة النصوص (`lexical_unit`، `definition`، تسمية `Form`/`URLRef`، محتوى `Field`، ...) يتم أخذ سلسلة واحدة لكل نظام كتابة عبر واجهة التعيين: `entry.lexical_unit["seh"] = "nkhuku"` تضيف `<form lang="seh">`. ويتم تعيين نموذج المصدر الذي يربط السلاسل برموز اللغات مباشرةً إلى هذا النموذج.
- `RangesFile.add_range()` / `Range.add_element()` تُنشئ المفردات المُحددة، و`Lexicon.add_ranges_file(ranges, href=...)` تُرفق الملف المصاحب وتضيف رأس الملف `<range href>` — بحيث يتم تحويل `<grammatical-info value="Noun">` و`<trait name="semantic-domain-ddp4" value="1.6.1.2">` الخاصين بالمدخل إلى النطاقات التي حددتها.
- `URLRef` هو رابط href مصحوب بنص متعدد اختياري للتعليق أو التسمية — ويُستخدم لكل من `<media>` (الصوت) و`<illustration>` (الصور). يتبع النطق هنا قاعدة «ذا كومباين» الخاصة بالصيغة «en» التي تُقرأ على النحو التالي: «المتحدث: <name> ».
- البيانات الخاصة بالتطبيق التي لا تحتوي على رحلات LIFT محلية كـ «<field> » (أو «<trait> »): يقرأ تطبيق FieldWorks هذه البيانات كحقول مخصصة، ويحتفظ تطبيق The Combine بها.
- قم بتعيين `guid` حقيقي وثابت لكل إدخال (على سبيل المثال، من `uuid.uuid4()`، مع إعادة استخدامه عبر عمليات التصدير) — حيث تؤدي عملية إعادة الاستيراد لاحقًا إلى تحديث الإدخال في مكانه بدلاً من تكراره. يضمن الأمر `sil-lift validate --require-ids` تطبيق ذلك.
- تقوم الدالة `lex.iter_problems()` بالتحقق من صحة المستند الموجود في الذاكرة (ما ستقوم الدالة `save()` بكتابته) قبل أن يتم تسجيل أي شيء على القرص؛ وهو هنا خالٍ من الأخطاء. نظرًا لعدم وجود مجلد للمعجم حتى الآن، يتم تخطي فحوصات وجود الوسائط ورابط الملف المصاحب — قم بتشغيل [`sil-lift validate`](cli.md) على المخرجات المحفوظة (أو باستخدام الخيار `--no-check-media`) بمجرد توفر ملفات الصوت والصور.

## التغليف

يؤدي الأمر `lex.save("export/birds.lift")` إلى كتابة المجلد بالصيغة التالية (ملفان `.lift` و`.lift-ranges` جنبًا إلى جنب). لإنشاء حزمة مضغوطة واحدة يمكن لبرنامجي FieldWorks و The Combine استيرادها مباشرةً، استخدم `lex.save_zip("birds.zip")` بدلاً من ذلك — انظر [إنتاج ملفات LIFT متوافقة](lift-export-interop.md).
