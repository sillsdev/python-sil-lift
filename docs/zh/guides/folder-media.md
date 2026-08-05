# LIFT 文件夹：范围与媒体

一个 LIFT 词汇表通常是一个 _文件夹_：包含一个 `.lift` 文件、一个或多个配套的 `.lift-ranges` 文件，以及 `audio/` / `pictures/` 目录中的媒体文件。

## 范围

```python
lex = sil_lift.load("dictionary.lift")      # 自动追踪伴随对象

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # 合并后的 {id: Range} 视图
lex.all_ranges()["grammatical-info"].elements
```

Companion discovery 处理现实情况：使用指向现有文件的 `range/@href`； FieldWorks 中悬空的绝对 `file://C:/...` href 会回退到 href 的基名，并将其附加在 `.lift` 之后；而常规的 `<name>.lift-ranges` 同级文件，即使没有任何引用，也会被识别出来。

`lex.save()` 会将 `.lift` 以及所有被追踪的伴生类一起写入。 对 `RangesFile` 进行的修改将保存回该文件；未修改的范围将保留其精确的字节数据。 独立使用：

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

向 `load()` 传递 `resolve_ranges=False` 参数，以跳过伴侣节点发现。

## 媒体

```python
for ref in lex.media_refs():        # 所有<media> 和<illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.missing_media()                 # 文件不存在的引用
```

解析遵循常规布局：对相对 href 进行原样检查（反斜杠已规范化——WeSay 写的是 `pictures\photo with space.png`），并检查其是否位于 `audio/`（用于发音媒体）或 `pictures/`（用于插图）目录下。 无法验证远程/绝对 href，因此会跳过这些链接。

## 其他文件夹内容

LIFT 文件夹通常包含 sil-lift 未建模的文件——例如 `WritingSystems/` 下的书写系统 LDML、`consent/` 下的 The Combine 发言人同意书的音频/图像文件等； `load()`/`save()` 不会对这些文件进行任何操作，而 [`Lexicon.save_zip()`](lift-export-interop.md) 在打包文件夹时会原样保留这些文件。
