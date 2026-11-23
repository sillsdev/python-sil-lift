# سيل-ليفت

مكتبة برمجية بلغة بايثون لـ [LIFT](https://github.com/sillsdev/lift-standard) (Lexicon Interchange FormaT) الإصدار 0.13: قراءة وكتابة مجلد LIFT دون فقدان البيانات (`.lift` + `.lift-ranges` + مراجع الوسائط)، والتحقق من صحة المخطط والسمات الدلالية، والفرز القياسي، بالإضافة إلى واجهات برمجة تطبيقات (APIs) للبث المباشر للمعاجم الكبيرة.

**الحالة: إصدار تجريبي، قيد التطوير النشط.**

## تثبيت

من [PyPI](https://pypi.org/project/sil-lift/):

```
pip install sil-lift   # المكتبة + الأمر sil-lift
```

يتطلب إصدار Python 3.11 أو أحدث. التبعية الوحيدة في وقت التشغيل هي lxml.

## جولة مدتها 30 ثانية

قم بتحميل قاموس، وابحث عن المدخلات المتعلقة باللغة الهوايية التي لا تحتوي على تفسير باللغة الإنجليزية، وقم بتعديل التعريف، ثم احفظه:

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # يتتبع أيضًا المرادفات ذات نطاقات .lift

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("haw") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # أو lex.find(id="poʻo_a1b2")
entry.senses[0].definition["en"] = "head (anatomy)"

lex.save()   # تمت إعادة تسلسل المدخل المعدل وإعادة ختمه؛ أما الباقي فهو مطابق تمامًا من حيث البايتات
```
