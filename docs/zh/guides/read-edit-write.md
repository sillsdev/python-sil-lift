# 阅读、编辑、撰写

## 正在加载

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` 接受任何格式正确的 LIFT **0.13** 文档——包括那些不符合模式规范的实际文件。 模型未定义的任何内容（未知元素/属性、注释）都会作为 LIFT 残余信息，无损地保存在每个节点的不透明 `extra` 字段中。 其他 LIFT 版本会抛出一个名称中包含该版本号的 `LiftParseError` 异常。

## 该模型

每个 LIFT 元素都是一个带类型的数据类：`Entry`、`Sense`、`Example`、`Pronunciation`、`Variant`、`Relation`、`Etymology`、`Reversal` 等。 多语言文本是一个 `Multitext`，它是一个从语言代码映射到 `Text` 的 `Mapping`：

```python
entry = lex.find(id="abat")

str(entry.lexical_unit["seh"])          # "abat"
entry.lexical_unit["en"] = "grove"      # 普通字符串会被强制转换
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["seh", "en"]
```

`keys()`、`values()` 和 `items()` 是视图，每个语言对应一个键，而 `len()` 统计的是语言的数量，而不是表单的数量。 这两个变异器作用于整个语言，而非某个具体形式：`del entry.lexical_unit["en"]` 会移除所有英语形式，而将值赋给 `"en"` 则会保留恰好一个。

一个符合模式的文档中不会包含其他内容，但实际文件中有时会重复某种语言。 `forms` 按文件顺序存储所有表单，从第一个表单开始读取答案，并且 [`validate`](validate.md#problem-codes) 会持续报告 `duplicate-form-lang` 错误，直到你为该语言进行赋值为止。 通过映射无法创建完全不包含 `lang` 的表单，系统会报告为 `form-missing-lang`，且当其节点重新序列化时，该表单将被丢弃。

`Text` 具有结构化特征——即由 `str` 和 `Span` 片段组成的有序列表——因为 `<text>` 可能包含嵌套的 `<span>` 标记。 `str(text)` 会将其转换为纯文本；这些片段保留了标记，以便进行往返转换。

在 LIFT 中，释义是 _Form 类型的_（每个 `<gloss>` 都承载着自己的语言），因此一个语义具有 `glosses: list[Form]` 以及一些辅助函数：

```python
sense = entry.senses[0]                 # 仅顶级释义
sense.gloss("en")                       # Text | None
entry.all_senses()                      # 所有释义和子释义，按文档顺序排列
entry.gloss_langs()                     # {"en", "id"}，包含子释义
```

只要问题涉及整个条目——例如统计词义、收集语言信息或查找媒体资源——请使用 `all_senses()`。 `entry.senses` 返回顶级层级，这仅在嵌套关系本身重要时才符合你的需求。

## 保存

```python
lex.save()                # 保存回原始加载位置
lex.save("elsewhere.lift")
```

未修改的条目将以**字节完全一致**的方式写回；完全未修改的文档从第一个字节到最后一个字节都与原文档字节完全一致。 具体合同条款请参见[富达保证](../fidelity.md)。

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
