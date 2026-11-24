# LIFT 文件夹：范围与媒体

一个 LIFT 词汇表通常是一个 _文件夹_：包含 `.lift` 文件、一个或多个 `.lift-ranges` 配套文件（辅助文件），以及位于 `audio/` 和 `pictures/` 文件夹中的多媒体文件。

## 范围

```python
lex = sil_lift.load("dictionary.lift")      # 自动追踪伴随对象

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # 合并后的 {id: Range} 视图
lex.all_ranges()["grammatical-info"].elements
```

`lex.save()` 会将 `.lift` 以及所有被追踪的伴生类一起写入。对 `RangesFile` 进行的修改将保存回该文件；未修改的范围将保留其精确的字节数据。独立使用：

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

### 伴星发现

尝试了几个候选项，并加载了其中每个不同的文件。

- 指向现有文件的 `range/@href` 标头按原样使用。
- 如果 href 解析后没有结果，则会回退到其基础名称，并在后面加上 `.lift`。 FieldWorks 会从导出机器写入不完整的绝对 `file://C:/...` 路径，正是这种备选方案使得它们能在本地正常运行。
- 即使没有任何内容引用它，系统仍会自动识别常规的 `<name>.lift-ranges` 同级元素。

仅在大小写或 Unicode 规范化方面存在差异的名称仍会被视为匹配（`Dict.LIFT` 会找到 `Dict.lift-ranges`），除非有多个文件匹配同一个名称——这种情况下不会加载任何一个文件，并会报告为 [`ambiguous-ranges-file`](validate.md#problem-codes)。

无法作为 `<lift-ranges>` 文档读取的候选项（例如，因导出中断而产生的零字节文件）将被跳过，而非导致加载失败，并报告为 [`unreadable-ranges-file`](validate.md#problem-codes)。如果直接使用 `RangesFile.load()` 加载，则会引发异常。

向 `load()` 传递 `resolve_ranges=False` 参数，以跳过伴侣节点发现。

## 媒体

```python
for ref in lex.media_refs():        # 所有<media> 和<illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.check_media()                   # 无法正确解析的引用
```

解析遵循常规布局：检查相对 href 是否按给定形式存在，且位于 `audio/`（用于发音媒体）或 `pictures/`（用于插图）目录下。反斜杠会被视为正斜杠，因为 WeSay 生成的 href 链接格式为 `pictures\photo with space.png`。无法验证远程和绝对 href，因此会跳过这些链接。

`check_media()` 仅报告那些未成功解析的引用，每个引用对应一个 `MediaResolution`：

- `status="missing"`：无论拼写如何，均未找到与该 href 对应的文件。
- `status="mismatch"`：确实存在匹配，但仅在进行大小写转换或NFC处理时；`found` 指代磁盘上的文件。

尽管找到了该文件，但系统仍报告了不匹配。关联名称的匹配较为宽松且不作提示，但媒体资源的 href 属性也会被后续提供该文件夹服务的任何系统读取，而区分大小写的主机名将无法找到该文件。验证结果与 [`media-href-mismatch`](validate.md#problem-codes) 中的情况相同。

## 其他文件夹内容

LIFT 文件夹通常包含 sil-lift 未建模的文件，例如位于 `WritingSystems/` 下的书写系统 LDML，或位于 `consent/` 下的 The Combine 发言者同意文件。 `load()` 和 `save()` 不会修改这些内容，而 [`Lexicon.save_zip()`](lift-export-interop.md) 在打包文件夹时会原样保留它们。
