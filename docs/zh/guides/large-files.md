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
- 流式传输模式不复用源字节：输出始终是规范的。 根级 LIFT 残留数据——即 `<lift>` 中条目之间的注释以及不符合模式的属性——不会被保留；条目和头部信息是完整的，其中包含残留数据。
- 如果 `open_writer` 代码块内部抛出异常，该文件将被标记为未终止（即没有关闭的 `</lift>`）——一个只写了一半的词汇表绝不能看起来像是完整的。
