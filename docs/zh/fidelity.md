# 富达保证

LIFT 是一种_交换_格式，因此第一条规则是：**切勿省略你不理解的内容**。 `sil-lift` 的契约，在每次运行时均由测试套件进行验证（包括语料库文件以及基于属性的生成）：

## 阅读

Any well-formed LIFT 0.13 document loads, schema-invalid content included. Whatever the model does not define is carried in the nearest node's opaque `Extras` container as _LIFT residue_. (That is FieldWorks' name for the same idea, which it stores in a `LiftResidue` field.) Residue includes:

- unknown attributes and elements;
- XML comments and processing instructions;
- stray text;
- malformed typed attributes: a bad date stays as the original string in `Extras`, and the typed field is `None`.

## 保存未作修改的文档

`load()` → `save()` with no edits writes **byte-identical output**: no reformatting, no re-escaping, no reordering, byte-order marks and XML declarations included. 目前没有规范化列表：恒等式是精确的。时间戳是根据内容生成的，因此未作修改的文档也不会生成时间戳。

例外情况（写入器将回退到完整的规范序列化，这种序列化在语义上完整，但无法保留字节顺序）：

- 源编码与 ASCII 不兼容（非 UTF-8/US-ASCII），或者
- 源文件中包含 DOCTYPE 声明，或者
- the byte scanner and the parser disagree about the document's top-level structure, for instance an out-of-spec second `<header>`, which the parser keeps only once, or
- 源代码是在内存中构建的，而不是从文件中加载的。

The byte scanner is deliberately conservative: on any doubt it captures no source bytes at all.

## 保存已编辑的文档

- \*\*未被修改的条目将按其原始字节内容原样输出。\*\*如果条目的模型对象自解析以来有任何部分发生变化（通过规范序列化快照检测，而非通过“已修改”标志），则该条目被视为已被修改。
- **被修改的条目将按照规范格式进行完全重新序列化。** 规范格式如下：
  - UTF-8。
  - 混合内容_外部_的2个空格缩进；`<text>`和`<span>`内部的空格绝不会被更改。
  - 每个元素对应一组有记录的子项；以 `<entry>` 为例：词汇单元、引文、读音、变体、词义、注释、关系、词源、标注、特征、领域。
  - 修复了属性的顺序。
  - ISO-8601格式的日期（`Z` 表示协调世界时）。
- **All residue is re-emitted.** Its position is restored to the original child index, clamped to the new child list; that is an approximation, since exact byte positions are only guaranteed for untouched entries.
- 添加、删除或重新排序条目会重新序列化文档结构，但仍会原样输出每个未更改条目的字节。
- **A touched entry is stamped** with a fresh `dateModified`, and a `dateCreated` if it had none. See [Generated timestamps](#generated-timestamps).

!!! note "&quot;此处的规范&quot; 与任何其他规范XML均无关"

    本页所指的“规范形式”是指 `sil-lift` 自身文档中记载的形态，如上文项目符号中所述。这与 W3C 的规范 XML（C14N）流程无关。这与 `SIL.Core` 中的 `CanonicalXmlSettings` 类无关。

## 生成的时间戳

生成的标记是输出中唯一不取决于输入的内容。

### Which entries are stamped

- **标记对象。** 所有自上次读取以来内容发生变化的条目，这些条目会带有新的 `dateModified` 字段；如果原本没有 `dateModified` 字段，则其 `dateCreated` 字段将设置为同一时间点。在加载日期之后发布的编辑，对于所有对该属性进行对账的系统（包括 FieldWorks 和 The Combine 的 LIFT 导入功能）而言，都显示为未修改。
- **仅限条目。** `<entry>` 下方不得有节点，且标题中不得包含任何内容。
- **被保留的条目。** 调用方刻意设置了日期的条目，以及在加载后创建且已包含日期的条目。
- **清除日期操作将被执行。** 对于使用 `one` 读取的条目，`entry.date_modified = None` 与其他任何值一样都是一个预设值，因此无论其内容是否发生变化，该条目在输出时都不会包含 `dateModified` 字段。
  - 如果该字段的值是 `None`，情况则不同：此时该字段已有值，且与从未修改过该字段的情况无法区分，因此编辑操作仍会对其进行标记。
- **An unparseable date is replaced.** A date the model could not parse is [residue](#reading) rather than a date, so a stamp overwrites it and the original string is dropped. An edited entry is better off carrying a real date than `dateModified="whenever"`.

### How the stamp is applied

- **该时刻。** 以秒为单位的协调世界时（UTC）（格式为 `YYYY-MM-DDTHH:MM:SSZ`，即所有经调查的 FieldWorks 导出文件均采用的格式），从墙上时钟读取。一秒钟对应一个日期，因此与前一次编辑相隔不到一秒保存的编辑将带有相同的日期戳。
- **`save(when=...)`** 提供的是时间戳而非墙上时钟的时间，正是这一点使得带时间戳的输出在基于 diff 的 CI 检查点中具有可重复性。它必须支持时区，并被标准化为以UTC为基准的整秒。
- **`save(stamp=False)`** 会将模型按当前状态原样保存，包括残差。
- **使用 `.lift` 写入操作标记提交。** 任何阻止该写入操作生效的操作都会将日期回滚。一旦命中，它们就会站立，即使随后同伴的攻击失败了也是如此。

## 内容 XML 无法表示

Non-BMP characters (emoji, CJK Extension B, Adlam, anything above U+FFFF) are ordinary content and round-trip byte-identically. “代理对”是 UTF-16 编码中的一个细节：Python 字符串是由码点组成的序列，因此读取器、字节扫描器或写入器在任何情况下都不会接触到它。

一个 _孤立_ 的占位符（U+D800–U+DFFF）则有所不同：在任何编码下，Python 字符串可能包含一个，而 XML 文档则可能不包含。 It can never arrive from a file, because the parser rejects both spellings (a `&#xD800;` character reference and CESU-8/WTF-8 bytes). It can only come from a string assigned through the API.

Saving such a model raises `LiftWriteError` naming the node and the codepoint, and writes nothing. Validation reports it as a single `lone-surrogate` error, since the document cannot be serialized for the schema layers to check.

## 已知的近似值（仅限已访问节点）

- `<text>` 运行块`内部`的注释会被保留，但会移至运行块旁边，而非保留在原有的精确字符偏移位置。
- 在已编辑元素内的交叉型子元素顺序会被规范化为规范分组（LIFT 模式中的 `interleave` 使得该顺序在语义上不具意义）。
- 没有 `lang` 属性的 `<form>` 或 `<gloss>` 不会被重新生成，其包含的内容也不会被重新生成；验证时会将此遗漏报告为 `form-missing-lang`。未被修改的节点会保留其源字节，因此这种形式会一直保留，直到其条目中的内容被编辑为止。
- A multitext element that is present but carries nothing (no forms, no residue, e.g. `<definition></definition>`) is not re-emitted. 没有任何语义上的损失。
  - The model represents these fields as an always-present `Multitext`, so an empty one is indistinguishable from an absent one after parsing. The fields are `lexical-unit`, `citation`, `definition`, a relation's `usage`, and `label` / `abbrev` / `description` on url-refs, ranges, range-elements and the header.
