# 示例：批量编辑释义

一项常见的维护任务：将词汇表中所有英语释义的拼写统一为标准形式（英式英语 → 美式英语，或反之），同时不影响文件中的其他内容。 本文将逐步演示一个脚本，该脚本负责加载、编辑、验证和保存数据，从而展示编辑 API 与保真度保证如何协同工作。

## 剧本

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)


def iter_senses(senses):
    """返回每个词义，包括子词义（递归）。”""
    for sense in senses:
        yield sense
        yield from iter_senses(sense.subsenses)


edited_glosses = 0

for entry in lex.entries:
    for sense in iter_senses(entry.senses):
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

- `Sense.subsenses` 本身是一个 `list[Sense]`，因此 `iter_senses` 会递归遍历它——如果批量编辑操作仅遍历 `entry.senses`，则会无提示地跳过任何嵌套在子义项下的释义。
- `gloss.text` 是一个 `Text` 对象，而不是普通的字符串：`str(gloss.text)` 会将其扁平化以便进行匹配，而替换后的内容会通过 `sil_lift.Text([new])` 写回，而不是直接修改原字符串。
- `lex.changed_entries()` 会报告哪些条目与加载的文件存在差异。 由于条目的摘要涵盖了其整个子树，因此对嵌套的子义项进行编辑时，系统会报告包含该子义项的条目。
  - 它会比较序列化的内容，因此将某个字段赋值为其原有的值时，系统不会报告该操作。
  - 它仅报告内容变更；`lex.added_entries()` 和 `lex.removed_entries()` 涵盖自加载以来新增或删除的条目。
  - 它返回条目本身，不受 `id` 重复或缺失的影响（LIFT 允许这种情况）。
  - 作为一种计数方式，只有在有可比较对象的情况下才有意义。 当字节扫描器无法读取源数据时（例如编码与 ASCII 不兼容，或者扫描器与解析器之间存在分歧），由于缺乏基准，`changed_entries()` 会报告 _所有_ 条目。 对于写保护而言，这确实是一个诚实的答案，因为在这种情况下 `save()` 会重新序列化整个文件，但这意味着计数值代表的是词汇表的大小，而不是编辑内容的大小。
- `lex.changes()` 用于判断文档是否_有任何_更改。 它不仅涵盖了条目，还包括页眉、根元素以及所有 `.lift-ranges` 关联元素。
  - 只有当 `save()` 能重现源字节时，该条件才会为假，因此 `if not lex.changes(): ...` 才是跳过不必要写入的正确方法。 该保证是单向的：对于本应被重写的文档，它绝不会报告“无内容可写”；而那些会触发完整重新序列化的更改，即使最终结果与原始字节完全一致，仍会被报告。
  - 它比较的是内容，而非目标路径，因此仅应将其用于就地保存：`lex.save(some_other_dir / "dictionary.lift")` 会将文档及其相关文件写入一个目前尚无内容的目录，无论内容是否发生变化。
  - 这是一种保护机制，而非加速手段——调用该函数会处理每个条目，这与 `save()` 决定哪些源字节可以复用的工作完全相同，因此你跳过的只是写入操作本身（文件修改时间保持不变，不会产生虚假差异），而非决策过程。
- 内存验证（`lex.iter_problems()`）会先将编辑后的状态序列化，因此能在将任何内容写入磁盘之前，准确反映编辑后的状态。 一旦遇到任何 `"error"` 级别的 `Problem` 就会中止处理——警告信息将保留给调用方自行决定如何处理——这意味着错误的编辑操作永远不会进入 `save()` 方法。

值得这样处理的不仅仅是光泽。 相同的 `Multitext` 映射规则同样适用于定义以及条目或词义中的所有其他多语言字段：

```python
sense.definition["en"] = "事物的颜色"
```

## 运行它

针对一个包含简短词汇表的小型词库进行比对，其中该词的释义和子义释义均显示为“colour”：

```
编辑了 1 个条目中的 2 个释义
```

## 忠诚的回报

该保证针对每个_条目_：模型未发生变化的条目，其输出与读取时的内容在**字节级**完全一致，且只有您实际修改过的条目才会被重新序列化。 在上面的处理过程中，有一个条目的注释被编辑了——文件中的其他所有条目都保留了原有的字节内容。 （请注意粒度：编辑条目中的任何部分都会导致整个条目重新序列化，包括未被修改的同级释义。） 因此，在一部包含50,000条目词典中编辑一条释义，生成的差异文件仅涉及一条条目，而非重新格式化的文件。 具体合同条款请参见[富达保证](../fidelity.md)。
