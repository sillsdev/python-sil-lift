# القراءة، التحرير، الكتابة

## جاري التحميل

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

تقبل الدالة `load()` أي مستند LIFT **0.13** صحيح التكوين — بما في ذلك الملفات الواقعية التي لا تتوافق مع المخطط. يتم نقل أي شيء لا يحدده النموذج (العناصر/السمات غير المعروفة، التعليقات) دون أي فقدان للبيانات باعتباره «بقايا LIFT» في الحقل غير الشفاف `extra` لكل عقدة. أما الإصدارات الأخرى من LIFT، فتُحدث استثناءً من نوع `LiftParseError` مع ذكر اسم الإصدار.

## النموذج

كل عنصر في LIFT هو فئة بيانات محددة النوع: `Entry`، `Sense`، `Example`، `Pronunciation`، `Variant`، `Relation`، `Etymology`، `Reversal`، وهكذا دواليك. النص متعدد اللغات هو كائن من نوع `Multitext`، والذي يعمل كخريطة تربط رمز اللغة بكائن من نوع `Text`:

```python
entry = lex.find(id="abat")

str(entry.lexical_unit["seh"])          # "abat"
entry.lexical_unit["en"] = "grove"      # يتم تحويل السلاسل العادية
"en" in entry.citation                  # False
```

يتم تنظيم `Text` — كقائمة مرتبة من أجزاء `str` و`Span` — لأن `<text>` يمكن أن تحتوي على علامات `<span>` متداخلة. يُحول `str(text)` النص إلى نص عادي؛ بينما تحتفظ الأجزاء بعلامات الترميز لضمان إمكانية العودة إلى الصيغة الأصلية.

تكون «التفسيرات» _على شكل صيغ_ في LIFT (حيث يحمل كل `<gloss>` لغته الخاصة)، لذا فإن «المعنى» يحتوي على `glosses: list[Form]` بالإضافة إلى دالة مساعدة:

```python
sense = entry.senses[0]
sense.gloss("en")                       # Text | None
entry.gloss_langs()                     # {"en", "id"}
```

## الحفظ

```python
lex.save()                # العودة إلى المكان الذي تم التحميل منه
lex.save("elsewhere.lift")
```

يتم إعادة كتابة الإدخالات التي لم تقم بتعديلها **بشكل مطابق تمامًا على مستوى البايت**؛ أما المستند الذي لم تقم بتعديله على الإطلاق، فهو مطابق تمامًا على مستوى البايت من البايت الأول وحتى الأخير. انظر [ضمانات فيديليتي](../fidelity.md) للاطلاع على نص العقد الدقيق.

## البناء من الصفر

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

## الترتيب القياسي

```python
lex.sort()      # ترتيب الإدخالات حسب (guid، id)؛ النطاقات/تعريفات الحقول حسب id/tag
lex.save()      # تحتفظ الإدخالات التي لم يتم التعديل عليها ببايتاتها بالضبط، بالترتيب الجديد

sil_lift.canonicalize("in.lift", "out.lift")   # أعيد تسلسلها بالكامل، وجاهزة للمقارنة
```

انظر أيضًا: [مثال توضيحي: التحرير الجماعي للتعليقات التوضيحية](bulk-edit-glosses.md).
