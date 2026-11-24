# 生成符合规范的 LIFT

本指南适用于任何编写 LIFT _导出器_ 的开发者：无论使用何种编程语言，只要其代码能将其他应用程序的数据模型转换为 LIFT 0.13 格式即可。在该工作中，`sil-lift` 发挥着两个作用：

- 一个符合性检查点，用于将输出与模式以及模式无法表达的语义进行比对；
- 关于输出必须遵循的形状和文本规则的参考。

编写 LIFT 要比解析它容易得多：导出器只会输出其自身模型生成的子集结构，而无需处理完整规范中的可选项。难点在于细节（`.lift-ranges` 伴生对象、按书写系统划分的文本、稳定的标识符以及 XML 转义），而下文中的检查项恰恰能捕捉到这些细节。

## 压缩包

LIFT 通常以单个 `.zip` 文件的形式进行传输；FieldWorks 和 The Combine 都采用这种方式进行导入和导出。 `sil-lift` 可以直接读取和写入压缩包，无论采用生态系统中的哪种布局：文件位于归档根目录下，还是嵌套在某个顶级文件夹中。

### 读取一个包

`sil_lift.load("package.zip")` 会将文件解压到一个临时目录中，找到唯一的 `.lift` 文件，并将其加载（相关文件和媒体资源将按常规方式解析）。

- `validate`、`stats`、`check-media` 和 `export` 命令行命令也支持 `.zip` 路径，因此下面的门控脚本可直接对该包进行处理。
- `stats` 和 `export` 流，并仅提取 `.lift` 文件，而非整个包。在媒体密集型场景中，它们的成本依然很低，且提取限制仅适用于 `.lift` 本身，而不适用于其旁边的其他内容。
- 提取操作的上限为 10 GiB 和 100,000 个成员。超过任一限制的包将被拒绝，并抛出 `LiftParseError` 异常；同样，其成员路径超出提取目录范围的包也会被拒绝。

### 编写软件包

`Lexicon.save_zip("out.zip", wrap_folder="MyDict")` 会将 `.lift`、其 `.lift-ranges` 以及源文件夹中的所有其他文件（media、`WritingSystems/`、`consent/` 等）打包在一起打包成zip文件。

- `wrap_folder` 的默认行为是创建一个以压缩包命名的顶级文件夹（遵循 FieldWorks/Combine 的导入规范）；若要生成扁平化归档，请传入 `False`。
- 对于自加载以来内容发生变化的条目，在输出时会标记一个新的 `dateModified`，这与 `save()` 中的处理完全一致。
  - 包是导入工具进行核对的对象，因此如果包中的日期已过期，更新后的词汇表就会显示为未被修改。
  - 它与 `save()` 函数使用相同的 `stamp=` 和 `when=` 选项；请参阅 [时间戳的应用方式](../fidelity.md#how-the-stamp-is-applied)。

`.lift` 和 `.lift-ranges` 在包内部保持字节级精确性；而 zip 容器本身无法实现字节级还原。

## 将输出作为符合性检查点进行验证

将 `sil-lift validate` 指向一个 `.lift` 文件。它会对 `.lift` 及其配套的 `.lift-ranges` 同时运行 RELAX NG 验证，并进行语法无法表达的语义检查：

- 悬空的 `relation`/`variant` 引用；
- 重复的 GUID；
- 范围元素的父元素完整性；
- 特征和语法信息值未在其范围内定义；
- `range/@href` 标头引用无法解析为任何对应项。

对于持续集成（CI），只要出现任何问题就应报错，并输出机器可读的检测结果：

```
sil-lift validate export.lift --strict --no-check-media --format json
```

- `--strict` 会使警告（而不仅仅是错误）导致运行失败。
- `--no-check-media` 会跳过文件系统的媒体存在性检查；当音频/照片文件与 CI 中的 `.lift` 文件不在同一文件夹时，该检查得出的 `missing-media` 结果属于误报。
- `--format json` 会输出一个 JSON 对象（`{"problems": [...], "summary": {...}}`），而非可读文本；其退出代码和模式构成一个受支持且符合 SemVer 规范的接口（参见 [命令行指南](cli.md)）。
- `--allow CODE[,CODE...]`（可重复）可防止某些可容忍的代码（例如 FLEx 的 `uri-not-rfc`）导致运行失败。其结果已打印出来，但尚未统计。
- `--require-ids` 还会对缺少 `guid` 的条目或缺少 `id` 的字段报错，这在后续重新导入时需要更新而非重复导入的情况下非常有用。

### 防范隐性数据丢失

“隐性数据丢失”是一种导致平面 CSV 导出存在数据丢失的故障模式。要防范这种情况，请对源模型使用 `stats --format json` 命令来统计计数：

```
sil-lift 统计数据导出：export.lift --format json
```

它报告了`条目`、`释义`、`例句`、`媒体引用`、`语言`以及按名称划分的`特征`数量。

### 在不使用 Python 工具链的情况下运行 Gate

TypeScript 或 C# 项目的持续集成（CI）可以通过内置的 GitHub Action 运行相同的检查，而无需安装 Python：

```yaml
- uses: sillsdev/python-sil-lift@v0.1.0
  with:
    path: export.lift
    strict: "true"
    no-check-media: "true"
    allow: "uri-not-rfc"
    format: json
```

或者由仓库中的 `Dockerfile` 构建的容器镜像：

```
docker build -t sil-lift .
docker run --rm -v "$PWD:/work" -w /work sil-lift validate export.lift --strict
```

## `.lift-ranges` 伴生组件

受控词汇表（词性、语义领域以及任何其他基于特征的键值对集合）存储在同级的 `.lift-ranges` 文件中，并在 `<header>` 中引用该文件：

```xml
<header>
  <ranges>
    <range id="grammatical-info" href="mydict.lift-ranges"/>
    <range id="semantic-domain-ddp4" href="mydict.lift-ranges"/>
  </ranges>
</header>
```

该手册收录了各系列产品的完整定义。这些值是 `<range-element>`；`parent` 构建层次结构；`label` / `abbrev` / `description` 是多文本：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
  <range id="grammatical-info">
    <range-element id="Noun">
      <label><form lang="en"><text>名词</text></form></label>
      <abbrev><form lang="en"><text>n</text></form></abbrev>
    </range-element>
  </range>
  <range id="semantic-domain-ddp4">
    <range-element id="1.6.1.2">
      <label><form lang="en"><text>鸟</text></form></label>
    </range-element>
  </range>
</lift-ranges>
```

随后，条目通过 ID 引用该值：词类的 ID 为 `<grammatical-info value="Noun"/>`，语义领域的 ID 为 `<trait name="semantic-domain-ddp4" value="1.6.1.2"/>`。 `sil-lift validate` 会检查这些引用，因此请输出数据实际使用的范围：

- 在其定义范围内未定义的值会触发 `undefined-range-value` 警告；
- 如果 `parent` 不是兄弟节点 ID，则会引发 `range-parent` 错误。

这些比较是基于NFC规范化的，因此一个ID及其值或引用该ID的`parent`在Unicode规范化方面可能会有所不同。该差异属于`归一化不匹配`警告，而非错误。不过，如果可以的话，还是编写一种一致的规范化处理方式吧：比较原始字符串的消费者无法解析这些引用。另请参阅 [频段与传输介质](folder-media.md)。

如果你使用 Python 构建导出文件，`Lexicon.add_ranges_file()`、`RangesFile.add_range()` 和 `Range.add_element()` 会自动为你构建关联对象并添加头文件引用； `open_writer(..., ranges=...)` 则在流式路径上执行相同操作。

## 文本和多文本

LIFT 中的每条人类语言字符串都是一个 _多文本_：每个书写系统对应一个 `<form>`，每个 ` ` 都包含一个 `<text>`：

```xml
<lexical-unit>
  <form lang="seh"><text>kanga</text></form>
  <form lang="pt"><text>小鸡</text></form>
</lexical-unit>
```

一个按语言代码对字符串进行索引的模型（`MultiString`、`Record<code, string>` 或 `dict[str, str]`）与该模型之间存在一对一映射：每个键对应一个条目，即一个 `<form lang="…">`。在单个多文本中，每种语言最多允许出现一个形式；否则，`sil-lift` 会发出 `duplicate-form-lang` 警告。

XML转义是唯一真正需要严格确保正确性的部分：

- 在元素文本中，`&`、`<`, and `>` 必须进行转义（`&amp;`、`&lt;`、`&gt;`）；
- 在属性值中，引号也必须进行转义。

`sil-lift` 的编写者严格遵循这些规则，绝不会修改 `<text>` 内部的空白符：它不会在此处添加任何缩进，因为那样会破坏词法数据。为了与输出内容保持一致，请使用 XML 库进行转义处理，并将 `<text>` 中的内容按源文件中的字节顺序原样保留。
