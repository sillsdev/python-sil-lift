# 大文件（流式传输）

`load()` 会构建整个对象图。 对于大小达数百MB的词典，流式处理 API 会在有限的内存中逐条处理条目——由于采用的是相同的 `Entry` 类型，因此针对一种模式编写的代码在另一种模式下同样适用。

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # 提前解析（位于条目之前）
    for entry in reader:              # 惰性 Iterator[Entry]
        ...
```

```python
使用 sil_lift.open_reader("big.lift") 作为读取器，sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) 作为写入器：
    for entry in reader:
        if not entry.date_deleted:    # 例如：删除坟墓石
            writer.write(entry)
```

注：

- 该写入器的输出结果与全文档规范序列化器针对相同内容生成的结果完全一致——这两种模式的结果始终保持一致。
- 流式传输模式没有字节直通层：输出始终是规范格式。 根级残留内容——即条目之间的注释以及 `<lift>` 上超出模式范围的属性——不会被传递；条目和头部内容是完整的，其中包含残留内容。
- 如果 `open_writer` 代码块内部抛出异常，该文件将被标记为未终止（即没有关闭的 `</lift>`）——一个只写了一半的词汇表绝不能看起来像是完整的。
