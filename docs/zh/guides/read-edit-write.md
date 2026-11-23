# 阅读、编辑、撰写

## 正在加载

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` accepts any well-formed LIFT **0.13** document, including schema-invalid real-world files. 模型未定义的任何内容（未知元素/属性、注释）都会作为 LIFT 残余信息，无损地保存在每个节点的不透明 `extra` 字段中。其他 LIFT 版本会抛出一个名称中包含该版本号的 `LiftParseError` 异常。

## 该模型

Every LIFT element is a typed dataclass: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, and so on.

### Multilingual text

多语言文本是一个 `Multitext`，它是一个从语言代码映射到 `Text` 的 `Mapping`：

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # plain strings are coerced
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` is structured (an ordered list of `str` and `Span` fragments) because `<text>` can contain nested `<span>` markup. `str(text)` 会将其转换为纯文本；这些片段保留了标记，以便进行往返转换。

The mapping shows one value per language. Underneath, `forms` holds every `<form>` in file order. A schema-valid document has at most one form per language, but real files sometimes repeat one.

Because the mapping is keyed by language, `len()` counts languages rather than forms, and the `keys()`, `values()` and `items()` views list each language once. Both mutators also act on the whole language: `del entry.lexical_unit["en"]` removes every English form, and assigning to `"en"` leaves exactly one.

For a repeated language, `entry.lexical_unit["en"]`, `get()`, `values()` and `items()` all answer with its first form, and [`validate`](validate.md#problem-codes) reports `duplicate-form-lang` until you assign to that language.

A form carrying no `lang` at all cannot be created through the mapping. It is reported as `form-missing-lang`, and is dropped when its node re-serializes.

### Senses and glosses

在 LIFT 中，释义是 _Form 类型的_（每个 `<gloss>` 都承载着自己的语言），因此一个语义具有 `glosses: list[Form]` 以及一些辅助函数：

```python
sense = entry.senses[0]       # top level only
sense.gloss("en")             # Text | None
entry.all_senses()            # every sense and subsense, document order
entry.gloss_langs()           # {"en", "id"}, subsenses included
```

只要问题涉及整个条目——例如统计词义、收集语言信息或查找媒体资源——请使用 `all_senses()`。 `entry.senses` 返回顶级层级，这仅在嵌套关系本身重要时才符合你的需求。

## 保存

```python
lex.save()                    # back to where it was loaded from
lex.save("elsewhere.lift")
```

未修改的条目将以**字节完全一致**的方式写回；完全未修改的文档从第一个字节到最后一个字节都与原文档字节完全一致。具体合同条款请参见[富达保证](../fidelity.md)。

### 时间戳

您修改过的条目会以新的 `dateModified` 时间戳（如果原本没有 `dateCreated` 时间戳，则会生成一个）发布，因此修改后的内容不会以加载时的日期发布。 Tools that merge LIFT decide what changed from that attribute. Two arguments adjust the stamping:

- `lex.save(stamp=False)` writes the dates the model holds and nothing more.
- `lex.save(when=...)` pins the moment instead of reading the clock.

其余规则请参见 [生成的时间戳](../fidelity.md#generated-timestamps)。

### Skipping a save that changes nothing

若要跳过一个不会产生任何变化的保存操作，请使用 `lex.changes()` 对其进行保护：

```python
if lex.changes():
    lex.save()
```

只有当 `save()` 能够重现源字节（包括条目、头信息、根元素以及每个 `.lift-ranges` 伴生对象）时，它才会返回 `False`。 Skipping the write leaves the file's modification time alone and avoids a spurious diff.

The check is cheap. 它在发现第一个差异时就停止了，因此在使用经过编辑的词典时，几乎不耗费任何资源。一个未发生变化的词汇表必须完整序列化才能证明其未发生变化，但这所耗费的资源仍少于它所跳过的保存操作。

它比较的是内容，而不是目标位置，因此只需保护就地保存操作即可。 `lex.save("elsewhere.lift")` writes the document and its companions to the new path even when `changes()` is `False`, so guarding it would skip that copy.

## 从零开始构建

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

## 规范排序

```python
lex.sort()      # 按 (guid, id) 对条目进行排序； 按 id/tag 划分的范围/字段定义
lex.save()      # 未修改的条目保留其精确字节值，并按新顺序排列

sil_lift.canonicalize("in.lift", "out.lift")   # 完全重新序列化，已准备好进行差异比较
```

另请参阅：[示例：批量编辑释义](bulk-edit-glosses.md)。
