# 验证

验证总是显式的：加载和保存操作绝不会进行隐式验证。

```python
import sil_lift

# 穷举：一个由问题（模式层 + 语义层）组成的惰性流。
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # 错误 [悬空引用] dictionary.lift:88（条目 apu）：引用 'nope' 与 ... 匹配

# 快速失败：在第一个错误级别的错误处停止。
if any(p.level == "error" for p in sil_lift.iter_problems("dictionary.lift")):
    raise SystemExit(1)

# 内存状态（先进行序列化，据文档记载，对于大型词典这会增加开销）：
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

每个 `Problem` 包含 `level`（`"error"`/`"warning"`）、一个固定的 `code` 和一个 `message`，以及该问题所包含的尽可能完整的地址信息：

- `file`：当词典没有路径时，返回 `None`。
- `entry_id`：当检索结果仅涉及一条条目时设置。
- `guid`：当相关对象（条目或范围元素）具有该标识符时，则设置此属性。
- `line`：当搜索结果与文档中的某行对应时设置此属性。

关于一个范围的发现结果将发送给定义该范围的 `.lift-ranges` 伴生对象，且不包含任何条目。未设置的字段为 `None`（在 `--format json` 中为 `null`，因为该格式下每个键都必然存在）。

## 各层

1. **LIFT 模式**（`lift-0.13.rng`，即 LIFT 0.13 的 RELAX NG 语法，从 lift-standard 引入，字节内容完全一致）应用于 `.lift` 文件。
2. **范围模式**（`lift-ranges-0.13.rng`，同样由 lift-standard 作为依赖引入）作用于每个被追踪的 `.lift-ranges` 伴生对象，其作用对象是该伴生对象本身，而非 `.lift`。
3. **语义检查**：模式无法表达的语义检查共有十三项，每项对应一个代码。

## 问题代码

每个检测结果都包含其中之一，具体取决于其产生的层级：`schema` 和 `uri-not-rfc` 来自模式层，其余的则是语义检查。默认情况下会检查所有代码，但 `missing-id` 除外，该选项需手动启用：传递 `require_ids=True`（或 `--require-ids`）即可启用该功能。这些代码是稳定的，因此脚本可以据此进行匹配。 `--strict` 会将所有警告提升为错误。 `sil-lift validate --allow CODE` 会将该代码排除在通过/失败的判定之外。

| 代码                      | 级别 | 它标记的是什么                                                                                |
| ----------------------- | -- | -------------------------------------------------------------------------------------- |
| `ambiguous-ranges-file` | 警告 | 在大小写转换和NFC模式下，多个文件对应同一个伴侣名称                                                            |
| `dangling-ranges-href`  | 警告 | 一个解析为无关联文件的 `range/@href` 标头                                                           |
| `悬空引用`                  | 错误 | 一个 `relation/@ref` 或 `variant/@ref` 未匹配到任何条目或释义                                        |
| `duplicate-form-lang`   | 警告 | 一种多文本中包含两种形式，且使用同一种语言                                                                  |
| `duplicate-guid`        | 错误 | 在不同条目之间，或在一个文档的范围/范围元素之间重复使用的GUID                                                      |
| `form-missing-lang`     | 错误 | `<form>` 或 `<gloss>`，但缺少架构要求的 `lang` 属性                                                |
| `media-href-mismatch`   | 警告 | 一个仅在进行大小写转换或NFC处理时才能访问其文件的媒体href                                                       |
| `缺失的ID`                 | 错误 | **[opt-in]** 没有 GUID 的条目，没有 ID 的感官 |
| `缺失媒体`                  | 警告 | 引用的音频或图片文件不在磁盘上                                                                        |
| `归一化不匹配`                | 警告 | 一个仅在NFC环境下才能访问其所引用的ID的名称                                                               |
| `range-parent`          | 错误 | a `range-element/@parent` 未定义同级元素 ID                                                   |
| `schema`                | 错误 | `.lift` 文件或伴生文件中存在 RELAX NG 语法错误                                                       |
| `未定义的范围值`               | 警告 | 一个语法信息或基于范围键的特征值，而该范围中未列出该值                                                            |
| `无法读取的范围文件`             | 警告 | 一个已存在但并非可读范围文档的关联候选项                                                                   |
| `uri-not-rfc`           | 警告 | 一个不是有效 URI 的 href（FLEx 中的 `file://C:/...`）                                             |

### 验证所看到的内容

这三个层都基于文档当前被序列化的形式进行处理，因此，如果某个文档完全无法被序列化，则会报告一个单独的 `lone-surrogate` 错误。请参阅[富达保证](../fidelity.md#content-xml-cannot-represent)。

验证结果为只读：它反映的是文档当前的状态，即在保存并设置 `dateModified` 之前的情况。这些标记永远不会触发检查，因此通过验证的文档在保存后仍会被视为通过。

### 关联文件夹代码

一个匹配多个文件的伴随名称无法加载其中任何一个文件：这些文件定义的范围会失效，直到将其中所有文件重命名或删除，仅剩一个为止。

只有在执行了关联文件发现操作时，才会报告这三个关联文件代码（`ambiguous-ranges-file`、`dangling-ranges-href` 和 `unreadable-ranges-file`）：

- 使用 `resolve_ranges=False` 加载时，伴生对象会超出作用域，因此不会报告任何伴生对象。
- 事后使用 `add_ranges_file()` 添加该文件也无法恢复这些数据，因为该函数从未读取过这些代码所报告的文件夹。

`resolve_ranges=False` 不会影响 `missing-media` 或 `media-href-mismatch`：媒体资源从未被解析到模型中，因此无需进行任何排除操作。

### 媒体代码

sil-lift 会根据给定的 href 路径查找每个媒体文件，同时也会在 `audio/`（发音媒体）或 `pictures/`（插图）目录下进行查找。该文件夹名称是 sil-lift 自己的猜测，并非文档中写明的，因此它会匹配任何大小写形式，且其拼写不会被报告。

`missing-media` 和 `media-href-mismatch` 共同负责媒体检查：前者表示无论拼写如何，都没有文件与该 href 匹配；后者表示虽然有一个文件与该 href 匹配，但 href 名称与该文件名称不完全一致。第二点是关于可移植性的发现：文件就在这里，但一个区分大小写的主机在提供此文件夹时将无法找到它。

拼写有误的_文件夹_只需重命名一次，无论其中包含多少个引用，因此仅报告一次且不生成条目。每条引用都会报告一个拼写错误的_文件名_，并将其反馈给写入该条目的条目。

## FieldWorks（FLEx）的实际应用输出

FieldWorks 会系统性地生成一些会被严格工具过滤掉的内容。以下是 sil-lift 的政策，旨在确保真实的词汇表能够发挥实际作用：

- `file://C:/...` 格式的 href（无效的 URI）会被报告为 **警告**（`uri-not-rfc`），而非模式错误；C# 验证器从未拒绝过此类内容。
- 合法交错的子元素（例如，某种意义上的 `field, note, field, note`）**不会**被标记；这忽略了 libxml2 中的一个误报。
- FLEx 在 `range-element` 中的 `trait`/`field` 扩展 **会被** 报告（针对范围模式的模式错误）：这些确实是规范偏差。
- 名称是根据Unicode **NFC规范化**下的范围和范围元素`id`进行解析的：`parent`链接、范围值，以及作为范围键的`trait`名称或标头`range` id。
  - FLEx 在导出时会将内容规范化为 NFC，但某些写入操作会绕过这一步，因此一个范围元素的 `id` 可能为 NFD，而其标签、自身的 `parent` 以及用于命名该元素的 `.lift` 值则为 NFC。
  - 如果进行精确比较，会从两个方面得出错误结论。对 NFD 标识符的引用会被报告为无效，尽管导出文件本身没有问题。而一个自身 `id` 为 NFD 的范围将不会被检查：没有任何特质名称与之匹配，且名称与任何范围都不匹配的特质将被原样接受。
  - 只有在规范化后才匹配的名称会被报告为 `normalization-mismatch` **警告**，该警告针对每个 ID 仅报告一次（而非针对每个引用报告一次），并发送给定义该名称的文件。数据本身没有问题，但消费者在比较原始字符串时无法解析这些引用。
  - ID 绝不会被重写：文件会保留其原始拼写。
