# 示例：批量编辑释义

一项常见的维护任务：将词汇表中所有英语释义的拼写统一为标准形式（英式英语 → 美式英语，或反之），同时不影响文件中的其他内容。本文通过一个演示脚本，展示了如何加载、编辑、验证和保存数据，从而说明了编辑 API 与保真度保证如何协同工作。

## 剧本

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)

edited_glosses = 0

for entry in lex.entries:
    for sense in entry.all_senses():
        for gloss in sense.glosses:
            if gloss.lang != "en":
                continue
            old = str(gloss.text)
            new = old.replace("colour", "color")
            if new != old:
                gloss.text = sil_lift.Text([new])
                edited_glosses += 1

changed = lex.changed_entries()

errors = [p for p in lex.iter_problems() if p.level == "error"]
if errors:
    for problem in errors:
        print(problem)
    sys.exit(f"中止：{len(errors)} 个验证错误，未保存任何内容")

lex.save()
print(f"已编辑 {edited_glosses} {len(changed)} 个条目中的释义")
```

有几点值得注意：

- `entry.all_senses()` 会按文档顺序以深度优先的方式返回每个词义及其子词义。
  - `entry.senses` 仅包含顶级条目，因此，在批量编辑过程中遍历该数组时，会默默跳过嵌套在子义项下的任何释义。
- `gloss.text` 是一个 `Text` 对象，而不是普通的字符串：`str(gloss.text)` 会将其扁平化以便进行匹配，而替换后的内容会通过 `sil_lift.Text([new])` 写回，而不是直接修改原字符串。
- `lex.changed_entries()` 会列出内容与已加载文件不一致的条目。在条目内的任何位置（即使是在嵌套的子义项中）进行编辑，都会将该条目计入统计。将一个字段的值设置为它原本的值时，系统不会显示任何信息，因为内容没有发生变化。
- `changed_entries()` 仅涵盖条目内容，因此它是一个计数器，而非写保护机制。若要跳过不会产生任何更改的保存操作，请使用 `lex.changes()`；请参阅 [保存](read-edit-write.md#saving)。
- 内存验证（`lex.iter_problems()`）会先将编辑后的状态序列化，因此能在将任何内容写入磁盘之前，准确反映编辑后的状态。在遇到任何 `"error"` 级别的 `Problem` 时中止操作（警告则留由调用方自行决定），这意味着错误的编辑永远不会进入 `save()` 方法。
- `lex.save()` 会在本脚本修改过的条目上标记一个新的 `dateModified`，并将 `dateCreated` 字段（若为空）填上相应值。
  - FieldWorks 和 The Combine 的 LIFT 导入功能都会根据 `dateModified` 来决定更新哪些内容，因此如果没有最新日期，它们会将已编辑的条目视为未修改。
  - 仅对 `<entry>` 元素进行标记。编辑子义释时，日期会显示在包含该释义的条目上，而不是显示在该义项上。

## 运行它

针对一个包含简短词汇表的小词典进行比对，该词典中“colour”的释义和子义释义均显示为“colour”：

```
编辑了 1 个条目中的 2 个释义
```

## 忠诚带来的回报

该保证针对每个_条目_：模型未发生变化的条目在读出时与读取时的**字节内容完全一致**，且只有您实际修改过的条目才会被重新序列化。在上述处理过程中，有一个条目的注释被编辑过；文件中的其他所有条目都保留了原有的字节内容。因此，在一部包含50,000条目词典中编辑一条释义，生成的差异文件仅涉及一条条目，而非重新格式化的文件。

请注意其粒度：编辑条目中的任何部分都会导致整个条目重新序列化，包括未被修改的同级释义。具体合同条款请参见[富达保证](../fidelity.md)。

## 超越注释

同样的方法也适用于其他多语言字段。注释是一个 `Form` 列表，但定义以及大多数其他多语言字段都是以语言为键的 `Multitext` 映射，因此编辑操作就是一次简单的赋值：

```python
sense.definition["en"] = "事物的颜色"
```

有关映射行为的详细信息，请参阅 [多语言文本](read-edit-write.md#multilingual-text)。
