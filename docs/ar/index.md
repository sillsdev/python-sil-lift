# سيل-ليفت

مكتبة Python لـ [LIFT](https://github.com/sillsdev/lift-standard) (Lexicon Interchange FormaT) 0.13: قراءة/كتابة بدون فقدان البيانات لمجلد LIFT (`.lift` + `.lift-ranges` + مراجع الوسائط)، والتحقق من صحة المخطط والسمات الدلالية، والفرز القياسي — مع واجهات برمجة تطبيقات (APIs) للتدفق المباشر للمعاجم الكبيرة.

**الحالة: إصدار تجريبي، قيد التطوير النشط.**

## تثبيت

من [PyPI](https://pypi.org/project/sil-lift/):

```
pip install sil-lift   # المكتبة + الأمر sil-lift
```

يتطلب إصدار Python 3.11 أو أحدث. التبعية الوحيدة في وقت التشغيل هي lxml.

## جولة مدتها 30 ثانية

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # يتتبع أيضًا المرادفات ذات النطاقات .lift

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("seh") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # أو lex.find(id="hoofd_a1b2")
entry.senses[0].definition["en"] = "head (anatomy)"

lex.save()   # المدخلات التي لم يتم تعديلها متطابقة من حيث البايتات؛ أما المدخلات التي تم تعديلها فقد أعيد تسلسلها
```
