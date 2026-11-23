# الاختلافات عن مكتبات C\#

تُعتبر «sil-lift» مشابهة بشكل عام لأدوات LIFT الخاصة بلغة C# من SIL، وهي تتألف أساسًا من جزأين من [libpalaso](https://github.com/sillsdev/libpalaso):

- `SIL.Lift`: محلل، أداة التحقق من الصحة، أداة الترحيل، `LiftSorter`.
- `SIL.DictionaryServices`: نموذج `LexEntry`/`LexSense`، المزود بقارئ/كاتب LIFT خاص به، والذي يستخدمه كل من The Combine وWeSay.

يُعد «sil-lift» تطبيقًا جديدًا، وليس نسخة معدلة. تلخص هذه الصفحة النقاط التي يختلف فيها السلوك بشكل متعمد.

## النطاق

| القدرة          | مكتبات C#                                                                              | سيل-ليفت                                                                               |
| --------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| إصدارات LIFT    | 0.10–0.13 (مع ميزة الترحيل المدمجة) | **0.13 فقط**؛ يتم رفض الإصدارات الأقدم مع ظهور خطأ واضح                |
| ترحيل الإصدار   | `Migrator` (سلسلة XSLT)                                             | لا شيء؛ استخدم ملفات XSLT الموجودة في «lift-standard» لإجراء عمليات الترقية لمرة واحدة |
| التحقق من الصحة | RELAX NG فقط (`Validator`)                                          | RELAX NG + نطاقات المخطط + الفحوصات الدلالية                                           |
| البث المباشر    | التحليل الداخلي على مستوى العناصر الفردية                                              | واجهة برمجة التطبيقات العامة `open_reader` / `open_writer`                             |

## شكل واجهة برمجة التطبيقات (API)

يعمل محلل `SIL.Lift` على أساس آلية الاستدعاء المرتد (`ILexiconMerger`): فهو يقوم بدفع أحداث التحليل إلى المستلم. بدلاً من ذلك، تُرجع sil-lift مخطط كائنات عادي (فئات بيانات مُحددة النوع لكل عنصر من عناصر LIFT) لأن مبرمجي Python يفضلون الكائنات، وليس دالات الاستدعاء.

تقوم `SIL.DictionaryServices` بتركيب نموذج كائنات `LexEntry`/`LexSense` فوق `SIL.Lift`، لكنه نموذج خاص بالتطبيقات: فهو يمثل فقط البنيات التي تستخدمها تلك التطبيقات. Re-serializing through it therefore can't preserve out-of-model content the way sil-lift's LIFT residue handling and byte fidelity do (see below).

تُنتج واجهة برمجة التطبيقات (API) الخاصة بالتدفق النوع _نفسه_ من `Entry`، لذا لا يوجد نموذج ثانٍ مبسط يتعين تعلمه.

## دقة النقل في كلا الاتجاهين

أقوى اختلاف متعمد. يؤدي الحفظ باستخدام `SIL.Lift` إلى إعادة تسلسل المستند بأكمله. تضمن شركة «سيل-ليفت» ما يلي:

- يتم حفظ المستند الذي لم يطرأ عليه تغيير **بشكل مطابق تمامًا من حيث البايتات**، و
- untouched entries keep their exact source bytes even when other entries change: per-entry byte chunking, applied automatically.

انظر [ضمانات فيديليتي](fidelity.md).

## التحقق من الصحة

يقوم `Validator` في لغة C# بتنفيذ دورة واحدة من RELAX NG ويُبلغ عن الأخطاء الأولى في شكل سلاسل نصية. sil-lift reports a structured `Problem` stream, each carrying the file, entry, and line it concerns. Its schema layer knowingly diverges in three places:

- **عناوين URI غير الصالحة تُعتبر تحذيرات وليست أخطاء.** لم يفرض محرك C# RELAX NG أبدًا نوع البيانات `anyURI`، لذا ظل برنامج FieldWorks (FLEx) لسنوات عديدة يدرج روابط href من النوع `file://C:/...` في المعاجم الفعلية. إن رفض تلك الملفات سيؤدي إلى وضع علامة على كل ملفات التصدير من FLEx تقريبًا.
- **Schematron rules are enforced** (as semantic checks): duplicate form languages and similar co-constraints in the LIFT grammar were silently ignored by C# validation.
- **Range id comparisons are Unicode-normalized** (NFC), because FLEx exports mix NFC and NFD ids. References that resolve only after normalizing are reported as `normalization-mismatch` warnings, a check with no C# counterpart. See [Real-world FieldWorks (FLEx) output](guides/validate.md#real-world-fieldworks-flex-output).

When sil-lift validates a `.lift`, it also validates the `.lift-ranges` companions against a schema for standalone ranges documents, vendored from `lift-standard`. The C# `Validator` does not check `.lift-ranges` files.

## الترتيب القياسي

تعكس دالة `Lexicon.sort()` القواعد الأساسية لـ `LiftSorter` (المدخلات حسب معرّف فريد (GUID) دون التمييز بين الأحرف الكبيرة والصغيرة؛ النطاقات وعناصر النطاقات حسب المعرّف (ID)؛ تعريفات حقول الرؤوس حسب العلامة (tag)؛ يتم الحفاظ على المعاني حسب ترتيبها في الملف؛ ولا يتم المساس أبدًا بالمسافات البيضاء داخل `<text>`)، مع وجود ثلاثة اختلافات:

- يتم فرز الإدخالات التي لا تحتوي على معرّف فريد (GUID) بشكل حتمي حسب المعرّف (ID) (يفترض `LiftSorter` وجود معرّف فريد (GUID))؛
- الترتيب مستقل عن الإعدادات المحلية (نقاط الرموز بعد إزالة التمييز بين الأحرف الكبيرة والصغيرة، وليس ترتيب .NET المستقل عن الثقافة)؛
- same-type lists such as notes, relations, and forms keep their document order rather than being re-sorted by key; grouping is already deterministic, and reordering them only adds diff noise.

لا يتم استخدام ملف `canonicalizeLift.xsl` الموجود في مستودع المواصفات على الإطلاق: فهو يدمج المسافات البيضاء داخل النص اللغوي (عملية تدميرية)، كما أن المعرّفات التي يولدها تختلف في كل عملية تشغيل.

## لم يتم ترحيله

- الميزات الخاصة بـ WeSay (لوحة التحكم/إدارة الإعدادات المتعلقة بملفات LIFT).
- `SynchronicMerger` (LIFT update-file merging): the byte-chunking idea lives on in the fidelity layer, the merging does not.
- تحليل نظام الكتابة LDML: تُعامل الملفات الموجودة في `WritingSystems/` على أنها محتوى مجلد غير شفاف.
