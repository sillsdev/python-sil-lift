# 验证

验证总是显式的——加载和保存操作绝不会进行隐式验证。

```python
import sil_lift

# 穷举：一个由问题（模式层 + 语义层）组成的惰性流。
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # 错误 [悬空引用] dictionary.lift:88 (条目 apu)：引用 'nope' 与 ... 匹配

# 快速失败：在遇到第一个错误级别的问题时抛出 LiftValidationError。
sil_lift.validate_file("dictionary.lift")

# 内存状态（先进行序列化——这是大型词典中已记录的开销）：
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

每个 `Problem` 包含 `level`（`"error"`/`"warning"`）、一个稳定的 `code`、`message`，以及该问题所涉及的尽可能完整的地址信息： `file`（当词典中没有路径时为 `None`）、当涉及单个条目时的 `entry_id`、当相关对象（条目或范围元素）具有唯一标识符时的 `guid`，以及当其映射到文档中的某行时对应的 `line`。 关于一个范围的发现结果将发送给定义该范围的 `.lift-ranges` 伴生对象，且不包含任何条目。 未设置的字段为 `None` —— 在 `--format json` 中为 `null`，其中每个键都必然存在。

## 各层

1. **RELAX NG** 基于 LIFT 0.13 语法（从 lift-standard 引入——这是一个与本包中提交的版本字节级完全一致的副本）。
2. **范围模式** —— 本项目的 `lift-ranges-0.13.rng` —— 覆盖了所有被追踪的 `.lift-ranges` 伴生类，其作用对象是伴生类本身，而非 `.lift`。
3. **语义检查**——这些是语法无法表达的，共有九项，每项对应一个代码。

## 问题代码

每个检测结果都包含其中之一，无论它来自哪个层级——`schema` 和 `uri-not-rfc` 来自模式层，其余九个则是语义检查。 字符串是一个受支持的接口；`--strict` 会将所有警告提升为错误。

| 代码                     | 级别 | 它标记的是什么                                         |
| ---------------------- | -- | ----------------------------------------------- |
| `dangling-ranges-href` | 警告 | 一个解析为无关联文件的 `range/@href` 标头                    |
| `悬空引用`                 | 错误 | 一个 `relation/@ref` 或 `variant/@ref` 未匹配到任何条目或释义 |
| `duplicate-form-lang`  | 警告 | 一种多文本中包含两种形式，且使用同一种语言                           |
| `duplicate-guid`       | 错误 | 在不同条目之间，或在一个文档的范围/范围元素之间重复使用的GUID               |
| `缺失的ID`                | 错误 | 通过 `require_ids` 进行选择加入：没有 GUID 的条目，没有 ID 的条目   |
| `缺失媒体`                 | 警告 | 引用的音频或图片文件不在磁盘上                                 |
| `归一化不匹配`               | 警告 | 一个仅在NFC环境下才能访问其所引用的ID的名称                        |
| `range-parent`         | 错误 | a `range-element/@parent` 未定义同级元素 ID            |
| `schema`               | 错误 | `.lift` 文件或伴生文件中存在 RELAX NG 语法错误                |
| `未定义的范围值`              | 警告 | 一个语法信息或基于范围键的特征值，而该范围中未列出该值                     |
| `uri-not-rfc`          | 警告 | 一个不是有效 URI 的 href — FLEx 的 `file://C:/...`      |

这三层都基于 `save()` 会写入的内容进行处理，因此，如果某个文档完全无法序列化，则会报告一个 `lone-surrogate` 错误——参见 [保真度保证](../fidelity.md#content-xml-cannot-represent)。

## FieldWorks（FLEx）的实际应用输出

FieldWorks 会系统性地生成一些会被严格工具过滤掉的内容。 以下是 sil-lift 的政策，旨在确保真实的词汇表能够发挥实际作用：

- `file://C:/...` 格式的 href（无效的 URI）会被报告为 **警告**（`uri-not-rfc`），而非模式错误——C# 验证器从未拒绝过此类 URI。
- 合法交错的子元素（例如，某种意义上的 `field, note, field, note`）**不会**被标记，以此规避 libxml2 中的误报问题。
- FLEx 在 `range-element` 中的 `trait`/`field` 扩展 **会被** 报告（针对范围模式的模式错误）：这些确实是规范偏差。
- 名称是根据Unicode **NFC规范化**下的范围和范围元素`id`进行解析的——包括`parent`链接、范围值，以及作为范围键的`trait`名称或`range`标识符。 FLEx 在导出时会将内容规范化为 NFC，但某些写入操作会绕过这一步，因此一个范围元素的 `id` 可能为 NFD，而其标签、自身的 `parent` 以及用于命名该元素的 `.lift` 值则为 NFC。
  - 若进行精确比较，一个看似正常的导出会显示为错误——而`id`拼写相反的范围则完全不会被检查，因为未覆盖任何范围的特性名称会被默默接受。
  - 只有在进行规范化处理后才匹配的名称会被报告为 `normalization-mismatch` **警告**，无论存在多少个引用不一致的情况，每个 ID 仅报告一次，该警告针对定义该名称的文件。 数据本身没有问题，但消费者在比较原始字符串时无法解析这些引用。
  - ID 绝不会被重写：文件会保留其原始拼写。
