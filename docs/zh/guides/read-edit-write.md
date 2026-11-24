# 阅读、编辑、撰写

## 正在加载

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` 接受任何格式正确的 LIFT **0.13** 文档，包括那些不符合模式规范的实际文件。模型未定义的任何内容（未知元素/属性、注释）都会作为 LIFT 残余信息，无损地保存在每个节点的不透明 `extra` 字段中。其他 LIFT 版本会抛出一个名称中包含该版本号的 `LiftParseError` 异常。

## 该模型

每个 LIFT 元素都是一个带类型的数据类：`Entry`、`Sense`、`Example`、`Pronunciation`、`Variant`、`Relation`、`Etymology`、`Reversal` 等。

### 多语言文本

多语言文本是一个 `Multitext`，它是一个从语言代码映射到 `Text` 的 `Mapping`：

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # 普通字符串会被强制转换
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` 具有结构化特征（由 `str` 和 `Span` 片段组成的有序列表），因为 `<text>` 可能包含嵌套的 `<span>` 标记。 `str(text)` 会将其转换为纯文本；这些片段保留了标记，以便进行往返转换。

该映射表中，每种语言对应一个值。在底层，`forms` 按文件顺序存储了所有 `<form>`。符合模式规范的文档中，每种语言最多只出现一种形式，但实际文件中有时会重复出现同一种形式。

由于映射是以语言为键的，因此 `len()` 统计的是语言的数量而非表单的数量，而 `keys()`、`values()` 和 `items()` 视图中，每种语言只会列出一次。这两个变异器都会作用于整个语言：`del entry.lexical_unit["en"]` 会移除所有英语形式，而将值赋给 `"en"` 则会保留恰好一个。

对于重复出现的语言，`entry.lexical_unit["en"]`、`get()`、`values()` 和 `items()` 都会返回其第一种形式，而 [`validate`](validate.md#problem-codes) 会报告 `duplicate-form-lang` 错误，直到你为该语言赋值为止。

通过映射无法创建完全不包含 `lang` 的表单。它被报告为 `form-missing-lang`，并在其节点重新序列化时被删除。

### 词义与释义

在 LIFT 中，释义是 _Form 类型的_（每个 `<gloss>` 都承载着自己的语言），因此一个语义具有 `glosses: list[Form]` 以及一些辅助函数：

```python
sense = entry.senses[0]       # 仅顶级词义
sense.gloss("en")             # 文本 | None
entry.all_senses()            # 所有词义和子词义，按文档顺序排列
entry.gloss_langs()           # {"en", "id"}，包含子词义
```

只要问题涉及整个条目——例如统计词义、收集语言信息或查找媒体资源——请使用 `all_senses()`。 `entry.senses` 返回顶级层级，这仅在嵌套关系本身重要时才符合你的需求。

## 保存

```python
lex.save()                    # 保存回原始加载位置
lex.save("elsewhere.lift")
```

未修改的条目将以**字节完全一致**的方式写回；完全未修改的文档从第一个字节到最后一个字节都与原文档字节完全一致。具体合同条款请参见[富达保证](../fidelity.md)。

### 时间戳

您修改过的条目会以新的 `dateModified` 时间戳（如果原本没有 `dateCreated` 时间戳，则会生成一个）发布，因此修改后的内容不会以加载时的日期发布。合并 LIFT 的工具会确定该属性发生了哪些变化。有两个参数用于调整冲压：

- `lex.save(stamp=False)` 仅写入模型中存储的日期，不包含其他内容。
- `lex.save(when=...)` 会锁定该时刻，而不是读取时钟。

其余规则请参见 [生成的时间戳](../fidelity.md#generated-timestamps)。

### 跳过一个不会改变任何内容的保存操作

若要跳过一个不会产生任何变化的保存操作，请使用 `lex.changes()` 对其进行保护：

```python
if lex.changes():
    lex.save()
```

只有当 `save()` 能够重现源字节（包括条目、头信息、根元素以及每个 `.lift-ranges` 伴生对象）时，它才会返回 `False`。跳过写入操作不会更改文件的修改时间，从而避免产生虚假的差异。

这张支票面额很小。它在发现第一个差异时就停止了，因此在使用经过编辑的词典时，几乎不耗费任何资源。一个未发生变化的词汇表必须完整序列化才能证明其未发生变化，但这所耗费的资源仍少于它所跳过的保存操作。

它比较的是内容，而不是目标位置，因此只需保护就地保存操作即可。即使 `changes()` 的值为 `False`，`lex.save("elsewhere.lift")` 也会将文档及其关联文件写入新路径，因此对其添加条件判断将跳过该复制操作。

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
