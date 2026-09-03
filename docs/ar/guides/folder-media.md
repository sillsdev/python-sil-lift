# مجلد LIFT: النطاقات ووسائل الإعلام

عادةً ما يكون معجم LIFT عبارة عن _مجلد_: ملف `.lift`، وملف واحد أو أكثر من ملفات `.lift-ranges` المصاحبة (ملفات sidecar)، وملفات الوسائط الموجودة في مجلدي `audio/` و`pictures/`.

## النطاقات

```python
lex = sil_lift.load("dictionary.lift")      # يتم تتبع المرافقات تلقائيًا

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # عرض {id: Range} المدمج
lex.all_ranges()["grammatical-info"].elements
```

تتعامل ميزة «Companion discovery» مع الواقع الفعلي: حيث يتم استخدام `range/@href` يشير إلى ملف موجود؛ تعود روابط href المطلقة المعلقة في FieldWorks `file://C:/...` إلى الاسم الأساسي لـ href الموجود بجوار `.lift`؛ ويتم التقاط العنصر الشقيق التقليدي `<name>.lift-ranges` حتى في حالة عدم وجود أي مرجع له.

تقوم الدالة `lex.save()` بكتابة ملف `.lift` وجميع الملفات المصاحبة التي يتم تتبعها معًا. يتم حفظ التعديلات التي تُجرى على ملف `RangesFile` في ملفه الخاص؛ أما النطاقات التي لم يتم التعديل عليها فتحتفظ بقيم البايتات الخاصة بها تمامًا. الاستخدام المستقل:

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

قم بتمرير المعلمة `resolve_ranges=False` إلى الدالة `load()` لتخطي عملية اكتشاف المرافقات.

## وسائل الإعلام

```python
for ref in lex.media_refs():        # كل عنصر من نوع <media> و <illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.missing_media()                 # المراجع التي لا توجد ملفاتها
```

يتم تحديد المسار وفقًا للتنسيق التقليدي: يتم فحص رابط href النسبي كما هو مكتوب (مع توحيد علامات الخط المائل العكسي — حيث يكتب WeSay `pictures\photo with space.png`) وتحت مجلد `audio/` (لوسائط النطق) أو `pictures/` (للرسوم التوضيحية). لا يمكن التحقق من روابط href البعيدة/المطلقة، لذا يتم تخطيها.

## محتويات المجلد الأخرى

غالبًا ما يحتوي مجلد LIFT على ملفات لا يقوم sil-lift بنمذجتها — مثل نظام الكتابة LDML الموجود ضمن `WritingSystems/`، وملفات الصوت/الصور الخاصة بموافقة المتحدثين في The Combine الموجودة ضمن `consent/`، وما شابه ذلك؛ تترك الدالتان `load()` و`save()` هذه الملفات دون تغيير، بينما تقوم الدالة [`Lexicon.save_zip()`](lift-export-interop.md) بنقلها حرفياً عند حزم المجلد.
