# 命令行

安装该包（`pip install sil-lift`）时，还会一并安装 `sil-lift` 命令——这是一个遵循 LiftTools 理念的受支持工具，随包附带（对于 `validate` 而言，它还是该库 API 的一个示例）。

```
sil-lift 验证 PATH [--format {text,json}] [--strict] [--no-check-media] [--require-ids]
                                           所有问题，包含文件/条目/行信息；出现错误时退出并返回 1
sil-lift stats PATH [--format {text,json}]
                                           条目/语义/语言计数（流式处理；任意大小）
sil-lift sort PATH [-o OUT]               按规范排序、可进行差异比较的副本（默认：就地操作）
sil-lift check-media PATH                 缺失和孤立媒体报告；若存在缺失则退出并返回 1
sil-lift export PATH [-o OUT] [--langs L] [--tsv]
                                           将每个叶片感测单元（子感测单元已扁平化）按行导出至 CSV/TSV 文件（流式输出）
```

`--format json` 会将单个 JSON 对象写入标准输出（且不输出其他内容），供持续集成（CI）和自动化流程使用；请参阅下例中的数据结构。 `--strict` 将警告视为错误，若发现任何警告则返回 1 —— 使用该选项可确保构建仅在完全没有警告的情况下通过，而非仅在没有错误的情况下通过。 `--no-check-media` 会跳过文件系统的媒体存在性检查（从而抑制 `missing-media` 错误提示），这在验证刚生成的导出文件时非常有用，尤其是当音频/照片文件位于其他位置而非同一文件夹内时。 `--require-ids` 还会对任何缺少 `guid` 的条目或缺少 `id` 的语义返回错误（`missing-id` 错误）——这比 LIFT 更严格，适用于通过稳定 ID 重新导入的工作流。 将 `-` 作为路径参数传递时，系统将从标准输入（stdin）读取文档（通过管道传递的文档没有文件夹，因此其配套的 `.lift-ranges` 文件和媒体资源不会被解析）。 `stats` 同样支持 `--format json` 选项，将计数结果以单个 JSON 对象的形式输出。

!!! note
    `validate` 的退出代码和 `--format json` 模式是一种受支持的自动化接口：两者均经过测试验证，且仅在遵循 SemVer 规范的情况下才会发生变更。

`sort` 仅重写 `.lift` 文件；配套的 `.lift-ranges` 文件则保持不变
（请使用 `RangesFile` API 单独对这些文件进行排序）。

`validate`、`stats`、`check-media` 和 `export` 还支持接收压缩的 LIFT 包（以任何一种布局格式的 `.zip` 文件——文件位于归档根目录下，或嵌套在某个顶级文件夹下）；该包会在命令执行完毕后解压到临时目录，并被自动删除。 流式处理命令 `stats` 和 `export` 仅提取 `.lift` 文件本身，因此在处理媒体资源较多的包时，其开销较低；而 `validate` 和 `check-media` 则需要整个文件夹，并将其全部提取出来。

示例：

```
$ sil-lift validate dictionary.lift
错误 [dangling-ref] dictionary.lift:88（条目 apu）：引用 'nope' 未匹配任何条目 ID/GUID 或词义 ID
警告 [uri-not-rfc] dictionary.lift:6:<range href='file://C:/...'> ：将 Windows 驱动器盘符用作 URI 权威部分（FLEx 风格的 file://C:/）
1 个错误，1 个警告

$ sil-lift validate dictionary.lift --format json
{
  "problems": [
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "引用 'nope' 未匹配任何条目 ID/GUID 或语义 ID",
      "file": "dictionary.lift",
      "entry_id": "apu",
      "guid": null,
      "line": 88
    },
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: 将 Windows 驱动器盘符用作 URI 权威部分（FLEx 风格的 file://C:/）",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 1
  }
}

$ sil-lift stats sango.lift
条目数：   3507
词义数：    4541
...

$ sil-lift export dictionary.lift --langs en,fr -o dictionary.csv
```

所有输出均为 UTF-8，无论在何种平台上，也无论输出到控制台、管道还是 `>` 重定向——绝不会使用区域设置编码（Windows 上的 cp1252、C/POSIX 区域设置下的 ASCII），因为这些编码无法表示 LIFT 内容。 因此，`sil-lift export dictionary.lift > dictionary.csv` 写入的字节内容与 `-o dictionary.csv` 写入的完全一致，包括 CRLF 行结束符。

退出代码：`0` 成功（允许出现警告，除非使用 `--strict`）， `1` 发现问题（验证错误 / 缺少媒体 / 在启用 `--strict` 时出现的警告），`2` 任一端发生 I/O 故障——无法读取输入，或无法写入输出（例如 `head` 等读取程序关闭了管道，或磁盘已满）。
