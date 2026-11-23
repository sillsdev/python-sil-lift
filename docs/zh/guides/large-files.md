# 大文件（流式传输）

`load()` 会构建整个对象图。对于大小达数百MB的词典，流式API会在有限的内存中逐条处理词条。它返回相同的 `Entry` 类型，因此针对一种模式编写的代码在另一种模式下也能正常运行。

## 阅读

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # 提前解析（位于条目之前）
    for entry in reader:              # 惰性 Iterator[Entry]
        ...
```

## 写作

```python
使用 sil_lift.open_reader("big.lift") 作为读取器，sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) 作为写入器：
    for entry in reader:
        if not entry.date_deleted:    # 例如：跳过标记为已删除的条目
            writer.write(entry)
```

注：

- 该写入器的输出结果与全文档规范序列化器针对相同内容生成的结果完全一致；这两种模式的结果永远不会出现偏差。
- 流式传输模式不复用源字节：输出始终是规范的。根级 LIFT 残留数据（条目之间的注释以及 `<lift>` 上的非模式属性）将被删除，但条目和标题仍保留其自身的残留数据。
- 与 [`Lexicon.save()`](../fidelity.md#saving-an-edited-document) 不同，流式处理模式不会生成时间戳。条目是根据其已有的日期生成的：流式读取器永远无法看到文档的原始状态，因此无法判断您修改了哪些条目。对于本次处理中被重写的条目，请自行设置 `entry.date_modified`。
- 如果 `open_writer` 代码块的主体抛出了异常，则该文件将处于明显未关闭的状态（没有关闭的 `</lift>`）。这样可以避免一个只写了一半的词汇表看起来像已经完整了。
