# مثال عملي: إنشاء عملية تصدير LIFT من البداية

إذا كنت تقوم بتصدير بيانات تطبيق آخر بتنسيق LIFT (وهي المهمة التي تقف وراء [إنتاج ملفات LIFT متوافقة](lift-export-interop.md))، فيمكن لـ `sil-lift` إنشاء المستند كائنًا تلو الآخر وتسلسله، بدلاً من كتابة XML يدويًّا. يشرح هذا المقال أحد البرامج النصية التي:

- تنشئ مدخلاً يتضمن العناصر التي يتضمنها القاموس الحقيقي: أنظمة كتابة متعددة، ونطق، ومعنى مصحوبًا بمثال، ورسم توضيحي، وسمة خاصة بالمجال الدلالي، وحقل خاص بالتطبيق؛
- يكتب المفردات المحددة في ملف مصاحب باسم `.lift-ranges`؛
- يقوم بالتحقق من صحة البيانات وحفظها.

## النص

```python
from pathlib import Path

import sil_lift

lex = sil_lift.Lexicon(producer="my-exporter")

# مدخلة واحدة، تم إنشاؤها من النموذج المصدر.
entry = sil_lift.Entry(id="kanga", guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d")
entry.lexical_unit["seh"] = "nkhuku"
entry.lexical_unit["pt"] = "galinha"

pron = sil_lift.Pronunciation()
pron.forms["en"] = "المتحدث: آنا"  # اصطلاح تسمية المتحدث في "The Combine"
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

# المفردات المراقبة التي يشير إليها المدخل، في ملف .lift-ranges.
ranges = sil_lift.RangesFile()
ranges.add_range("grammatical-info").add_element("Noun").label["en"] = "noun"
ranges.add_range("semantic-domain-ddp4").add_element("1.6.1.2").label["en"] = "Bird"
lex.add_ranges_file(ranges, href="birds.lift-ranges")

# التحقق من صحة المستند كما هو، قبل كتابته على القرص.
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
<entry id="kanga" guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d" dateCreated="2026-09-02T19:19:17Z" dateModified="2026-09-02T19:19:17Z">
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
      <text>المتحدثة: آنا</text>
    </form>
    <media href="audio/nkhuku.wav"/>
  </pronunciation>
  <sense id="kanga_s1">
    <grammatical-info value="Noun"/>
    <gloss lang="en">
      <text>دجاجة</text>
    </gloss>
    <definition>
      <form lang="en">
        <text>طائر داجن يُربى من أجل بيضه ولحمه</text>
      </form>
    </definition>
    <example>
      <form lang="seh">
        <text>أريد دجاجة.</text>
      </form>
      <translation>
        <form lang="en">
          <text>أريد دجاجة.</text>
        </form>
      </translation>
    </example>
    <illustration href="pictures/hen.jpg">
      <label>
        <form lang="en">
          <text>دجاجة</text>
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
        <text>اسم</text>
      </form>
    </label>
  </range-element>
</range>
<range id="semantic-domain-ddp4">
  <range-element id="1.6.1.2">
    <label>
      <form lang="en">
        <text>طائر</text>
      </form>
    </label>
  </range-element>
</range>
</lift-ranges>
```

## ملاحظات حول واجهة برمجة التطبيقات (API)

### إنشاء المستند

- تقوم الحقول متعددة النصوص (`lexical_unit`، `definition`، تسمية `URLRef`، محتوى `Field`) بربط رموز اللغات بالنصوص، وبالتالي يتم نقل سلاسل النصوص الخاصة بكل لغة في النموذج المصدر بنسبة واحد إلى واحد.
- تقوم الدالة `Lexicon.add_ranges_file(ranges, href=...)` بإرفاق الملف المصاحب وكتابة مراجع الرؤوس `<range href>` نيابة عنك، بحيث يتم تحويل قيمتي `Noun` و`1.6.1.2` الخاصتين بالمدخل إلى النطاقات التي حددتها.
- يُعد `URLRef` عبارة عن رابط href مرفقًا بنص متعدد اختياري للتعليق أو التسمية، ويُستخدم في كل من `<media>` (الصوت) و`<illustration>` (الصور). يتبع النطق هنا قاعدة «ذا كومباين» الخاصة بالصيغة «en» التي تُقرأ على النحو التالي: «المتحدث: <name> ».
- البيانات الخاصة بالتطبيق التي لا تحتوي على رحلات LIFT محلية كـ «<field> » (أو «<trait> »): يقرأ تطبيق FieldWorks هذه البيانات كحقول مخصصة، ويحتفظ تطبيق The Combine بها.
- قم بتعيين `guid` حقيقي وثابت لكل إدخال (على سبيل المثال، من `uuid.uuid4()`، مع إعادة استخدامه عبر عمليات التصدير)؛ حيث تؤدي عملية إعادة الاستيراد لاحقًا إلى تحديث الإدخال في مكانه بدلاً من تكراره. يضمن الأمر `sil-lift validate --require-ids` تطبيق ذلك.

### الطوابع الزمنية

لا توجد قيمتي `dateCreated`/`dateModified` الواردتان في الناتج أعلاه في البرنامج النصي. قامت وظيفة `save()` بتسجيل تاريخ تنفيذها، لأن أي إدخال يتم كتابته للمرة الأولى لا يحمل تاريخًا خاصًا به.

- توفر `when=` تلك اللحظة بدلاً من قراءة الساعة، وهو ما يجعل البايت الناتج عن عملية التصدير قابلاً للتكرار بدقة البايت، مما يتيح لمهمة التكامل المستمر (CI) إجراء مقارنة الفروق.
- يؤدي `stamp=False` إلى عدم كتابة أي تواريخ على الإطلاق.

انظر [الطوابع الزمنية التي تم إنشاؤها](../fidelity.md#generated-timestamps) للاطلاع على بقية بنود العقد.

### التحقق من الصحة

تقوم الدالة `lex.iter_problems()` بالتحقق من صحة المستند الموجود في الذاكرة قبل أن يتم تخزين أي شيء على القرص؛ وهو خالٍ من الأخطاء هنا. نظرًا لعدم وجود مجلد للمعجم حتى الآن، يتم تخطي فحوصات «media-presence» و«companion-href». قم بتشغيل [`sil-lift validate`](cli.md) على المخرجات المحفوظة (أو باستخدام الخيار `--no-check-media`) بمجرد توفر ملفات الصوت والصور.

## التغليف

يؤدي الأمر `lex.save("export/birds.lift")` إلى كتابة المجلد بالصيغة التالية (ملفان `.lift` و`.lift-ranges` جنبًا إلى جنب). لإنشاء حزمة مضغوطة واحدة يمكن لبرنامجي FieldWorks وThe Combine استيرادها مباشرةً، استخدم `lex.save_zip("birds.zip")` بدلاً من ذلك. انظر [إنتاج LIFT متوافق](lift-export-interop.md).
