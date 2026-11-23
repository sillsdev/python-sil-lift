# 与 C# 库的区别

sil-lift 与 SIL 的 C# LIFT 工具集大致类似，主要由 [libpalaso](https://github.com/sillsdev/libpalaso) 的两个部分组成：

- `SIL.Lift`：解析器、验证器、迁移器、`LiftSorter`。
- `SIL.DictionaryServices`：一种 `LexEntry`/`LexSense` 模型，配有专用的 LIFT 读写器，被 The Combine 和 WeSay 所采用。

sil-lift 是一个全新的实现，而非移植版本。本页总结了行为在哪些方面存在有意差异。

## 范围

| 能力      | C# 库                                              | sil-lift                                |
| ------- | ------------------------------------------------- | --------------------------------------- |
| LIFT 版本 | 0.10–0.13（内置迁移功能） | **仅限 0.13 版**；旧版本将被明确拒绝 |
| 版本迁移    | `Migrator`（XSLT 链）                                | 无；对于一次性升级，请使用 lift-standard 中的 XSLT 文件  |
| 验证      | 仅限 RELAX NG（`Validator`）                          | RELAX NG + 范围模式 + 语义检查                  |
| 流媒体     | 内部条目级别的解析                                         | 公共 `open_reader` / `open_writer` API    |

## API 结构

`SIL.Lift` 的解析器采用回调驱动模式（`ILexiconMerger`）：它会将解析事件推送给消费者。 sil-lift instead returns a plain object graph (typed dataclasses for every LIFT element) because Python scripters want objects, not callbacks.

`SIL.DictionaryServices` does layer a `LexEntry`/`LexSense` object model over `SIL.Lift`, but it is an application model: it represents only the constructs those apps use. Re-serializing through it therefore can't preserve out-of-model content the way sil-lift's LIFT residue handling and byte fidelity do (see below).

流式处理 API 返回的是_相同的_ `Entry` 类型，因此无需学习第二个精简版模型。

## 往返保真度

最显著的刻意差异。使用 `SIL.Lift` 保存时，会将整个文档重新序列化。 sil-lift 保证：

- 未发生更改的文档在存储时**字节完全一致**，并且
- untouched entries keep their exact source bytes even when other entries change: per-entry byte chunking, applied automatically.

请参阅[富达保证](fidelity.md)。

## 验证

C# 的 `Validator` 会执行一次 RELAX NG 验证，并将首次检测到的错误以字符串形式返回。 sil-lift reports a structured `Problem` stream, each carrying the file, entry, and line it concerns. Its schema layer knowingly diverges in three places:

- **无效的 URI 属于警告，而非错误。** C# RELAX NG 引擎从未强制执行 `anyURI` 数据类型，因此 FieldWorks (FLEx) 多年来一直将 `file://C:/...` 格式的 href 写入实际词汇表中。如果拒绝这些文件，几乎所有 FLEx 导出文件都会被标记。
- **Schematron rules are enforced** (as semantic checks): duplicate form languages and similar co-constraints in the LIFT grammar were silently ignored by C# validation.
- **Range id comparisons are Unicode-normalized** (NFC), because FLEx exports mix NFC and NFD ids. References that resolve only after normalizing are reported as `normalization-mismatch` warnings, a check with no C# counterpart. See [Real-world FieldWorks (FLEx) output](guides/validate.md#real-world-fieldworks-flex-output).

When sil-lift validates a `.lift`, it also validates the `.lift-ranges` companions against a schema for standalone ranges documents, vendored from `lift-standard`. The C# `Validator` does not check `.lift-ranges` files.

## 规范排序

`Lexicon.sort()` 遵循 `LiftSorter` 的核心规则（条目按不区分大小写的 GUID 排序；范围和范围元素按 ID 排序；标头字段定义按标签排序；词义按文件顺序排列；`<text>` 内的空格绝不被修改），但有三点不同：

- 没有 GUID 的条目将按 ID 进行确定性排序（`LiftSorter` 假设存在 GUID）；
- 排序与区域设置无关（采用纯大写/小写转换后的码点，而非 .NET 的“不变文化”排序规则）；
- same-type lists such as notes, relations, and forms keep their document order rather than being re-sorted by key; grouping is already deterministic, and reordering them only adds diff noise.

规范代码库中的 `canonicalizeLift.xsl` 完全未被使用：它会压缩词法文本中的空白（破坏性操作），且每次运行生成的 ID 都不相同。

## 未结转

- WeSay 特有的便捷功能（围绕 LIFT 文件的仪表盘/配置管理）。
- `SynchronicMerger` (LIFT update-file merging): the byte-chunking idea lives on in the fidelity layer, the merging does not.
- LDML 书写系统解析：`WritingSystems/` 目录下的文件将被视为不透明的文件夹内容。
