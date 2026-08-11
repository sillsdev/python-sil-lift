# 示例：批量编辑释义

一项常见的维护任务：将词汇表中所有英语释义的拼写统一为标准形式（英式英语 → 美式英语，或反之），同时不影响文件中的其他内容。 本文将逐步演示一个脚本，该脚本负责加载、编辑、验证和保存数据，从而展示编辑 API 与保真度保证如何协同工作。

## 剧本

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)


def iter_senses(senses):
    """Yield every sense, including subsenses (recursive)."""
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
    sys.exit(f"aborting: {len(errors)} validation error(s), nothing saved")

lex.save()
print(f"edited {edited_glosses} gloss(es) across {len(changed)} entry(ies)")
```

有几点值得注意：

- `Sense.subsenses` 本身是一个 `list[Sense]`，因此 `iter_senses` 会递归遍历它——如果批量编辑操作仅遍历 `entry.senses`，则会无提示地跳过任何嵌套在子义项下的释义。
- `gloss.text` 是一个 `Text` 对象，而不是普通的字符串：`str(gloss.text)` 会将其扁平化以便进行匹配，而替换后的内容会通过 `sil_lift.Text([new])` 写回，而不是直接修改原字符串。
- `lex.changed_entries()` reports which entries differ from the file as loaded. Since an entry's digest covers its whole subtree, an edit to a nested subsense reports the entry that contains it.
  - It compares serialized content, so assigning a field the value it already had isn't reported.
  - It reports content changes only; `lex.added_entries()` and `lex.removed_entries()` cover entries that appeared or disappeared since loading.
  - It returns the entries themselves, unaffected by `id` being duplicated or absent (which LIFT allows).
  - As a count, it is meaningful only where there is something to compare against. When the passthrough layer declines to byte-scan the source — an encoding that is not ASCII-compatible, or a scanner/parser disagreement — there is no baseline, and `changed_entries()` reports _every_ entry. That is the honest answer for a write guard, since `save()` re-serializes the whole file in that case, but it means the count is the size of the lexicon rather than the size of the edit.
- `lex.changes()` reports whether the document changed _at all_. It covers not just the entries, but also the header, the root element, and every `.lift-ranges` companion.
  - It is falsy only when `save()` would reproduce the source bytes, which makes `if not lex.changes(): ...` the right way to skip an unnecessary write. The guarantee runs one way: it never reports "nothing to write" for a document that would be rewritten, while a change that forces a full re-serialization can land back on the original bytes and still be reported.
  - It compares content, not destination, so guard only an in-place save with it: `lex.save(some_other_dir / "dictionary.lift")` writes the document and its companions to a location that has nothing in it yet, whether or not anything changed.
  - It is a guard, not a speed-up — answering it digests every entry, which is the same work `save()` does to decide passthrough, so what you skip is the write itself (an untouched mtime, no spurious diff), not the effort of deciding.
- 内存验证（`lex.iter_problems()`）会先将编辑后的状态序列化，因此能在将任何内容写入磁盘之前，准确反映编辑后的状态。 一旦遇到任何 `"error"` 级别的 `Problem` 就终止处理——警告信息将留给调用方自行判断——这意味着错误的编辑操作永远不会进入 `save()` 方法。

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
