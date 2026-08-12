# 与 C# 库的区别

sil-lift 与 SIL 的 C# LIFT 工具集大致类似——主要包括 [libpalaso](https://github.com/sillsdev/libpalaso) 中的 `SIL.Lift`（解析器、验证器、迁移器、`LiftSorter`）、同一仓库中的 `SIL.DictionaryServices`（该仓库中的 `LexEntry`/`LexSense` 模型，带有专用的 LIFT 读写器，被 The Combine 和 WeSay 所采用），以及 [Chorus](https://github.com/sillsdev/chorus) 中的 LIFT 处理程序。 这是一个全新的实现，而不是移植。 本页总结了行为在哪些方面存在有意差异。

## 范围

| 能力      | C# 库                                              | sil-lift                                 |
| ------- | ------------------------------------------------- | ---------------------------------------- |
| LIFT 版本 | 0.10–0.13（内置迁移功能） | **仅限 0.13 版**；旧版本将被明确拒绝  |
| 版本迁移    | `Migrator`（XSLT 链）                                | 无 — 对于一次性升级，请使用 lift-standard 中的 XSLT 文件 |
| 三向合并/同步 | 合唱                                                | 超出范围                                     |
| 验证      | 仅限 RELAX NG（`Validator`）                          | RELAX NG + 范围模式 + 语义检查                   |
| 流媒体     | 内部条目级别的解析                                         | 公共 `open_reader` / `open_writer` API     |

## API 结构

`SIL.Lift` 的解析器采用回调驱动模式（`ILexiconMerger`）：它会将解析事件推送给消费者。 sil-lift 反而返回一个普通的对象图——每个 LIFT 元素对应一个带类型的数据类——因为 Python 脚本开发者需要的是对象，而不是回调函数。 `SIL.DictionaryServices` 确实在 `SIL.Lift`之上构建了一个 `LexEntry`/`LexSense` 对象模型，但作为应用程序模型，它仅代表这些应用程序所使用的结构——因此，通过它进行重新序列化无法像 sil-lift 的 LIFT 残留处理和字节保真度那样保留模型之外的内容（详见下文）。 流式处理 API 返回的是_相同的_ `Entry` 类型，因此无需学习第二个精简版模型。

## 往返保真度

最显著的刻意差异。 使用 `SIL.Lift` 保存时，会将整个文档重新序列化。 sil-lift 保证：

- 未发生更改的文档在存储时**字节完全一致**，并且
- 即使其他条目发生变化，未被修改的条目仍会保留其原始字节内容——这正是 Chorus 采用的、针对每个条目自动应用的字节分块机制。

请参阅[富达保证](fidelity.md)。

## 验证

C# 的 `Validator` 会执行一次 RELAX NG 验证，并将首次检测到的错误以字符串形式返回。 sil-lift 报告了一个结构化的 `Problem` 流，其中每个 `Problem` 都包含其相关的文件、条目和行，且其模式层在三个地方有意进行了差异化处理：

- **无效的 URI 属于警告，而非错误。** C# RELAX NG 引擎从未强制执行 `anyURI` 数据类型，因此 FieldWorks (FLEx) 多年来一直将 `file://C:/...` 格式的 href 写入实际词汇表中。 如果拒绝这些文件，几乎所有 FLEx 导出文件都会被标记。
- **Schematron 规则已强制执行**（作为语义检查）：LIFT 语法中重复的表单语言和类似的协同约束，在 C# 和原生 lxml 验证中均被静默忽略。
- **跨文件比较已进行 Unicode 标准化**，因为 FLEx 将 `.lift` 文件以 NFC 格式写入，而配套的 `.lift-ranges` 文件则以 NFD 格式写入。

sil-lift 还会根据独立范围文档的模式（该模式与基础 LIFT 语法一同由 `lift-standard` 提供）来验证已加载词汇表的 `.lift-ranges` 伴随文件 —— 每次验证 `.lift` 文件时，都会检查所有被追踪的外部范围文件 —— 而 C# 领域中则不存在此类模式（或检查）。 （目前尚无独立于 `.lift` 文件之外、专门用于验证 `.lift-ranges` 文件的入口点。）

## 规范排序

`Lexicon.sort()` 遵循 `LiftSorter` 的核心规则（条目按不区分大小写的 GUID 排序；范围和范围元素按 ID 排序；标头字段定义按标签排序；词义按文件顺序排列；`<text>` 内的空格绝不被修改），但有三点不同：

- 没有 GUID 的条目将按 ID 进行确定性排序（`LiftSorter` 假设存在 GUID）；
- 排序与区域设置无关（采用纯大写/小写转换后的码点，而非 .NET 的“不变文化”排序规则）；
- 同类列表（如笔记、关系和表单）会保留其文档顺序，而非按键值重新排序——分组本身已是确定性的，重新排序只会增加差异噪声。

规范代码库中的 `canonicalizeLift.xsl` 完全未被使用：它会压缩词法文本中的空白（破坏性操作），且每次运行生成的 ID 都不相同。

## 未结转

- WeSay 特有的便捷功能（围绕 LIFT 文件的仪表盘/配置管理）。
- `SynchronicMerger`（Chorus 更新合并）——字节分块的理念在保真层中得以延续，但合并操作已不复存在。
- LDML 书写系统解析：`WritingSystems/` 目录下的文件将被视为不透明的文件夹内容。
