# القراءة، التحرير، الكتابة

## جاري التحميل

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` accepts any well-formed LIFT **0.13** document, including schema-invalid real-world files. يتم نقل أي شيء لا يحدده النموذج (العناصر/السمات غير المعروفة، التعليقات) دون أي فقدان للبيانات باعتباره «بقايا LIFT» في الحقل غير الشفاف `extra` لكل عقدة. أما الإصدارات الأخرى من LIFT، فتُحدث استثناءً من نوع `LiftParseError` مع ذكر اسم الإصدار.

## النموذج

Every LIFT element is a typed dataclass: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, and so on.

### Multilingual text

النص متعدد اللغات هو `Multitext`، وهو عبارة عن `Mapping` يربط رمز اللغة بـ `Text`:

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # plain strings are coerced
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` is structured (an ordered list of `str` and `Span` fragments) because `<text>` can contain nested `<span>` markup. يُحول `str(text)` النص إلى نص عادي؛ بينما تحتفظ الأجزاء بعلامات الترميز لضمان إمكانية العودة إلى الصيغة الأصلية.

The mapping shows one value per language. Underneath, `forms` holds every `<form>` in file order. A schema-valid document has at most one form per language, but real files sometimes repeat one.

Because the mapping is keyed by language, `len()` counts languages rather than forms, and the `keys()`, `values()` and `items()` views list each language once. Both mutators also act on the whole language: `del entry.lexical_unit["en"]` removes every English form, and assigning to `"en"` leaves exactly one.

For a repeated language, `entry.lexical_unit["en"]`, `get()`, `values()` and `items()` all answer with its first form, and [`validate`](validate.md#problem-codes) reports `duplicate-form-lang` until you assign to that language.

A form carrying no `lang` at all cannot be created through the mapping. It is reported as `form-missing-lang`, and is dropped when its node re-serializes.

### Senses and glosses

تكون «التفسيرات» في LIFT على شكل _نماذج_ (حيث يحمل كل `<gloss>` لغته الخاصة)، لذا فإن «المعنى» يحتوي على `glosses: list[Form]` بالإضافة إلى وظائف مساعدة:

```python
sense = entry.senses[0]       # top level only
sense.gloss("en")             # Text | None
entry.all_senses()            # every sense and subsense, document order
entry.gloss_langs()           # {"en", "id"}, subsenses included
```

استخدم دالة `all_senses()` كلما تعلق السؤال بالمدخل بأكمله: سواء كان ذلك لحساب المعاني، أو جمع اللغات، أو البحث عن الوسائط. تُقدم `entry.senses` المستوى الأعلى، وهو ما تريده فقط عندما يكون التداخل بحد ذاته أمرًا مهمًا.

## الحفظ

```python
lex.save()                    # back to where it was loaded from
lex.save("elsewhere.lift")
```

يتم إعادة كتابة الإدخالات التي لم تقم بتعديلها **بشكل مطابق تمامًا على مستوى البايت**؛ أما المستند الذي لم تقم بتعديله على الإطلاق، فهو مطابق تمامًا على مستوى البايت من البايت الأول وحتى الأخير. انظر [ضمانات فيديليتي](../fidelity.md) للاطلاع على نص العقد الدقيق.

### الطوابع الزمنية

يتم إرسال السجلات التي قمت بتعديلها مع قيمة جديدة لـ `dateModified` (وكذلك قيمة لـ `dateCreated` إذا لم تكن موجودة من قبل)، لذا لا يتم إرسال التعديل بتاريخ التحميل الأصلي. Tools that merge LIFT decide what changed from that attribute. Two arguments adjust the stamping:

- `lex.save(stamp=False)` writes the dates the model holds and nothing more.
- `lex.save(when=...)` pins the moment instead of reading the clock.

انظر [الطوابع الزمنية التي تم إنشاؤها](../fidelity.md#generated-timestamps) للاطلاع على بقية القواعد.

### Skipping a save that changes nothing

لتخطي عملية حفظ لن تؤدي إلى أي تغيير، قم بحمايتها باستخدام `lex.changes()`:

```python
إذا كان lex.changes():
    lex.save()
```

لا تُرجع القيمة `False` إلا عندما تكون دالة `save()` قادرة على إعادة إنتاج البايتات المصدرية، بما في ذلك الإدخالات، والرأس، والعنصر الجذري، وجميع العناصر المصاحبة من نوع `.lift-ranges`. Skipping the write leaves the file's modification time alone and avoids a spurious diff.

The check is cheap. إنه يتوقف عند أول اختلاف، لذا فإن تكلفته تكاد تكون معدومة عند استخدام معجم مُعدَّل. يجب تسلسل المعجم الذي لم يتغير بالكامل لإثبات أنه لم يتغير، لكن تكلفة ذلك تظل أقل من تكلفة عملية الحفظ التي يتم تخطيها.

فهي تقارن المحتوى، وليس الوجهة، لذا احرص فقط على الحفظ في المكان نفسه. `lex.save("elsewhere.lift")` writes the document and its companions to the new path even when `changes()` is `False`, so guarding it would skip that copy.

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
