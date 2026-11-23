# 命令行（CLI）

安装该软件包（`pip install sil-lift`）时，也会一并安装 `sil-lift` 命令。

```
sil-lift 验证 PATH [--format {text,json}] [--strict] [--no-check-media]
                  [--allow CODE[,CODE...]]... [--require-ids]
    列出所有问题，包含文件/条目/行号；出现错误时退出并返回 1

sil-lift stats PATH [--format {text,json}]
    条目/语义/语言计数（流式处理；任意大小）

sil-lift sort PATH [-o OUT]
    规范排序、可进行差异比较的副本（默认：就地操作）

sil-lift check-media PATH
    缺失、拼写错误和孤立媒体报告；若存在缺失/拼写错误则退出并返回 1

sil-lift export PATH [-o OUT] [--langs L] [--tsv]
    每个叶片感测器（子感测器已扁平化）占一行，导出为 CSV/TSV（流式传输）
```

## 验证

`validate` 会针对每个检测结果打印一行，然后显示摘要。 `--format json` 生成的结果与一个 JSON 对象相同：

```
$ sil-lift validate dictionary.lift
警告 [uri-not-rfc] dictionary.lift:6:<range href='file://C:/...'>: 将 Windows 驱动器盘符用作 URI 权威（FLEx 风格的 file://C:/）
错误 [dangling-ref] dictionary.lift:88（条目 poʻo_a1b2）： 引用 'nope' 与任何条目 ID/GUID 或词义 ID 均不匹配
1 个错误，1 个警告

$ sil-lift validate dictionary.lift --format json
{
  "problems": [
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: URI 权威部分使用了 Windows 驱动器盘符（FLEx 风格的 file://C:/）",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    },
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "引用 'nope' 未匹配任何条目 ID/GUID 或语义 ID",
      "file": "dictionary.lift",
      "entry_id": "po\u02bbo_a1b2",
      "guid": null,
      "line": 88
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 1,
    "allowed": 0
  }
}
```

`validate` 的选项：

- `--format json` 会将单个 JSON 对象写入标准输出（且不输出其他内容），供持续集成/自动化流程使用。请参见上文示例中的模式。
- `--strict` 将警告视为错误，若发现任何警告，则返回 1。使用它来确保构建仅在完全没有警告的情况下通过，而不是仅在出现错误时通过。
- `--no-check-media` 会跳过文件系统中的媒体存在性检查，从而抑制 `missing-media` 和 `media-href-mismatch` 检测结果。当导出文件的音频和照片文件保存在其他位置，或者尚未复制到 `.lift` 文件旁边时，此功能非常有用。
- `--allow CODE[,CODE...]`（可重复）会报告指定代码的检测结果，但不会将其纳入通过/失败的判定中。
  - 这同样适用于错误和警告，因此允许的警告也不会触发 `--strict`。
  - 摘要行统计了每个代码下的“允许”类结果；JSON 摘要中的 `allowed` 字段给出了其总数。
  - 从未出现过的代码会被忽略，因此即使某项检查被废止，白名单仍会继续生效。
- `--require-ids` 还会因任何缺少 `guid` 的条目或缺少 `id` 的含义而报错（`missing-id` 错误）。对于通过稳定 ID 重新导入的工作流而言，这比 LIFT 更严格。

将 `-` 作为路径参数传递时，将从标准输入（stdin）读取文档。通过管道传输的文档没有文件夹，因此其配套的 `.lift-ranges` 文件和媒体资源无法解析。

!!! note

    `validate` 的退出代码和 `--format json` 模式是一种受支持的自动化接口：两者均经过测试验证，且仅在遵循 SemVer 规范的情况下才会发生变更。

## 统计数据

```
$ sil-lift stats sango.lift
条目：   3507
感知项：    4541
...
```

`stats` 同样支持 `--format json` 选项，将计数结果以单个 JSON 对象的形式输出。

## 排序

`sort` 仅重写 `.lift` 文件；配套的 `.lift-ranges` 文件则保持不变（请使用 [`RangesFile` API](folder-media.md#ranges) 单独对这些文件进行排序）。

## 导出

`export` 会为每个叶节点写入一行。 `--langs` 用于指定哪些语言会生成 `gloss_` 和 `definition_` 列；默认情况下，这些列会根据文档自动检测生成。

```
$ sil-lift export dictionary.lift --langs en,id -o dictionary.csv
```

## 压缩包

`validate`、`stats`、`check-media` 和 `export` 也支持接收压缩（`.zip`）格式的 LIFT 包。其文件可以位于归档根目录下，也可以位于某个顶级文件夹内。无论命令提取了什么内容，都会被存入一个临时目录，并在命令执行完毕后被删除。

- 流式处理命令 `stats` 和 `export` 仅提取 `.lift` 文件本身，因此在处理媒体资源密集型包时，它们的执行成本较低。
- `validate` 和 `check-media` 需要整个文件夹，并将其全部解压。

## 输出编码

所有输出均为 UTF-8 编码，无论在何种平台上，也无论输出是发送到控制台、管道还是通过 `>` 重定向。绝不是区域设置编码（Windows 上的 cp1252，C/POSIX 区域设置下的 ASCII）无法表示 LIFT 内容。因此，`sil-lift export dictionary.lift > dictionary.csv` 写入的字节内容与 `-o dictionary.csv` 写入的完全一致，包括 CRLF 行结束符。

## 退出代码

- `0`：成功。除非使用 `--strict` 选项，否则警告不会导致运行失败。
- `1`：研究结果。验证错误、媒体文件缺失或拼写错误，或者在 `--strict` 选项下出现警告时，程序将以 1 退出，除非其代码已传递给 `--allow` 选项。
- `2`：I/O 错误。无法读取输入，或者无法写入输出，例如因为磁盘已满，或者像 `head` 这样的读取程序关闭了管道。
