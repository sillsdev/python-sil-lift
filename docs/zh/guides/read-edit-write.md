# 阅读、编辑、撰写

## 正在加载

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` 接受任何格式正确的 LIFT **0.13** 文档——包括那些不符合模式规范的实际文件。 模型未定义的任何内容（未知元素/属性、注释）都会作为 LIFT 残余信息，无损地保存在每个节点的不透明 `extra` 字段中。 其他 LIFT 版本会抛出一个名称中包含该版本号的 `LiftParseError` 异常。

## 该模型

每个 LIFT 元素都是一个带类型的数据类：`Entry`、`Sense`、`Example`、`Pronunciation`、`Variant`、`Relation`、`Etymology`、`Reversal` 等。 多语言文本是一个 `Multitext`，其行为类似于从语言代码到 `Text` 的映射：

```python
entry = lex.find(id="abat")

str(entry.lexical_unit["seh"])          # "abat"
entry.lexical_unit["en"] = "grove"      # 普通字符串会被强制转换
"en" in entry.citation                  # False
```

`Text` 具有结构化特征——即由 `str` 和 `Span` 片段组成的有序列表——因为 `<text>` 可能包含嵌套的 `<span>` 标记。 `str(text)` 会将其转换为纯文本；这些片段保留了标记，以便进行往返转换。

在 LIFT 中，释义是 _Form 类型的_（每个 `<gloss>` 都承载着自己的语言），因此一个语义具有 `glosses: list[Form]` 以及一个辅助函数：

```python
sense = entry.senses[0]
sense.gloss("en")                       # Text | None
entry.gloss_langs()                     # {"en", "id"}
```

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
