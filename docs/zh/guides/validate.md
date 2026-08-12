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

每个 `Problem` 包含 `level`（`"error"`/`"warning"`）、一个固定的 `code`、`message` 以及一个地址：`file`、`entry_id`、`guid`、`line`。

## 各层

1. **RELAX NG** 基于 LIFT 0.13 语法（从 lift-standard 引入——这是一个与本包中提交的版本字节级完全一致的副本）。
2. **范围模式** —— 本项目的 `lift-ranges-0.13.rng` —— 适用于所有被追踪的 `.lift-ranges` 伴生类。
3. **语义检查**：语法无法表达以下情况：`duplicate-guid`、`dangling-ref`、`range-parent`、`undefined-range-value`、`duplicate-form-lang`、`missing-media`。

## FieldWorks（FLEx）的实际应用输出

FieldWorks 会系统性地生成一些会被严格工具过滤掉的内容。 以下是 sil-lift 的政策，旨在确保真实的词汇表能够发挥实际作用：

- `file://C:/...` 格式的 href（无效的 URI）会被报告为 **警告**（`uri-not-rfc`），而非模式错误——C# 验证器从未拒绝过此类 URI。
- 合法交错的子元素（例如，某种意义上的 `field, note, field, note`）**不会**被标记，以此规避 libxml2 中的误报问题。
- 范围值的比较是在 Unicode NFC 规范化下进行的——FLEx 在同一导出文件中将 `.lift` 写为 NFC 格式，而将 `.lift-ranges` 写为 NFD 格式。
- FLEx 在 `range-element` 中的 `trait`/`field` 扩展 **会被** 报告（针对范围模式的模式错误）：这些确实是规范偏差。
