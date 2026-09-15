# 示例：从零开始构建 LIFT 导出

如果你正在将另一个应用程序的数据导出为 LIFT 格式——这正是 [生成符合规范的 LIFT](lift-export-interop.md) 背后的任务——`sil-lift` 可以逐个构建文档对象并将其序列化，而无需手动生成 XML。 本文将逐步演示一个脚本，该脚本利用真实词典所包含的各项要素（多种书写系统、发音、带例句的词义、插图、语义领域特征以及应用程序特定字段）来构建词条，将受控词汇写入 `.lift-ranges` 伴生文件，进行验证并保存。

## 剧本

```python
from pathlib import Path

import sil_lift

lex = sil_lift.Lexicon(producer="my-exporter")

# 一个条目，基于源模型构建。
entry = sil_lift.Entry(id="kanga", guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d")
entry.lexical_unit["seh"] = "nkhuku"
entry.lexical_unit["pt"] = "galinha"

pron = sil_lift.Pronunciation()
pron.forms["en"] = "Speaker: Ana"  # Combine 的说话人标签约定
pron.media.append(sil_lift.URLRef(href="audio/nkhuku.wav"))
entry.pronunciations.append(pron)

sense = sil_lift.Sense(id="kanga_s1")
sense.grammatical_info = sil_lift.GrammaticalInfo(value="Noun")
sense.glosses.append(sil_lift.Form(lang="en", text=sil_lift.Text(["chicken"])))
sense.definition["en"] = "a domestic fowl kept for its eggs and meat"

example = sil_lift.Example()
example.forms["seh"] = "Ndinafuna nkhuku."
translation = sil_lift.Translation()
translation.forms["en"] = "I want a chicken."
example.translations.append(translation)
sense.examples.append(example)

photo = sil_lift.URLRef(href="pictures/hen.jpg")
photo.label["en"] = "A hen"
sense.illustrations.append(photo)

sense.traits.append(sil_lift.Trait(name="semantic-domain-ddp4", value="1.6.1.2"))

scientific = sil_lift.Field(type="scientific-name")  # 一个应用程序专用的额外字段
scientific.content["en"] = "Gallus gallus domesticus"
sense.fields.append(scientific)

entry.senses.append(sense)
lex.entries.append(entry)

# 该词条所引用的受控词汇表，位于配套的 .lift-ranges 中。
ranges = sil_lift.RangesFile()
ranges.add_range("grammatical-info").add_element("Noun").label["en"] = "noun"
ranges.add_range("semantic-domain-ddp4").add_element("1.6.1.2").label["en"] = "Bird"
lex.add_ranges_file(ranges, href="birds.lift-ranges")

# 在写入磁盘之前，验证 save() 会写入什么内容。
problems = list(lex.iter_problems())
print(f"validation: {len(problems)} 个问题")

out = Path("export")
out.mkdir(exist_ok=True)
lex.save(out / "birds.lift")
print("=== birds.lift ===")
print((out / "birds.lift").read_text(encoding="utf-8"), end="")
print("=== birds.lift-ranges ===")
print((out / "birds.lift-ranges").read_text(encoding="utf-8"), end="")
```

## 其产出

`验证结果：0 个问题`，然后是 `.lift` 及其配套代码的并列展示：

```
=== birds.lift ===
<?xml version="1.0" encoding="UTF-8"?>
<lift version="0.13" producer="my-exporter">
<header>
  <ranges>
    <range id="grammatical-info" href="birds.lift-ranges"/>
    <range id="semantic-domain-ddp4" href="birds.lift-ranges"/>
  </ranges>
</header>
<entry id="kanga" guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d">
  <lexical-unit>
    <form lang="seh">
      <text>nkhuku</text>
    </form>
    <form lang="pt">
      <text>galinha</text>
    </form>
  </lexical-unit>
  <pronunciation>
    <form lang="en">
      <text>Speaker: Ana</text>
    </form>
    <media href="audio/nkhuku.wav"/>
  </pronunciation>
  <sense id="kanga_s1">
    <grammatical-info value="Noun"/>
    <gloss lang="en">
      <text>chicken</text>
    </gloss>
    <definition>
      <form lang="en">
        <text>a domestic fowl kept for its eggs and meat</text>
      </form>
    </definition>
    <example>
      <form lang="seh">
        <text>Ndinafuna nkhuku.</text>
      </form>
      <translation>
        <form lang="en">
          <text>I want a chicken.</text>
        </form>
      </translation>
    </example>
    <illustration href="pictures/hen.jpg">
      <label>
        <form lang="en">
          <text>A hen</text>
        </form>
      </label>
    </illustration>
    <trait name="semantic-domain-ddp4" value="1.6.1.2"/>
    <field type="scientific-name">
      <form lang="en">
        <text>Gallus gallus domesticus</text>
      </form>
    </field>
  </sense>
</entry>
</lift>
=== birds.lift-ranges ===
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
<range id="grammatical-info">
  <range-element id="Noun">
    <label>
      <form lang="en">
        <text>noun</text>
      </form>
    </label>
  </range-element>
</range>
<range id="semantic-domain-ddp4">
  <range-element id="1.6.1.2">
    <label>
      <form lang="en">
        <text>Bird</text>
      </form>
    </label>
  </range-element>
</range>
</lift-ranges>
```

## API说明

- 多文本字段（`lexical_unit`、`definition`、`Form`/`URLRef` 的标签、`Field` 的内容等） 通过映射接口，为每个书写系统取一条字符串：`entry.lexical_unit["seh"] = "nkhuku"` 会添加一个 `<form lang="seh">`。 一个以语言代码为键对字符串进行索引的源模型可以直接映射到此处。
- `RangesFile.add_range()` / `Range.add_element()` 用于构建受控词汇表，而 `Lexicon.add_ranges_file(ranges, href=...)` 则关联相应的范围文件并添加 `<range href>` 引用——这样，条目的 `<grammatical-info value="Noun">` 和 `<trait name="semantic-domain-ddp4" value="1.6.1.2">` 就能解析为您定义的范围。
- `URLRef` 由 href 以及可选的标题/标签多文本组成——既适用于 `<media>`（音频），也适用于 `<illustration>`（照片）。 此处的发音遵循“The Combine”的惯例，即采用读作“<name> ”的`en`形式。
- 不包含原生 LIFT 回家行程的应用程序专用数据，格式为 `<field>`（或 `<trait>`）：FieldWorks 会将其识别为自定义字段，而 The Combine 会保留这些数据。
- 为每个条目分配一个真实且稳定的 `guid`（例如通过 `uuid.uuid4()` 生成，并在不同导出之间复用）——这样，后续重新导入时会就地更新该条目，而非创建重复条目。 `sil-lift validate --require-ids` 会强制执行此要求。
- `lex.iter_problems()` 会在任何数据写入磁盘之前，对内存中的文档（即 `save()` 会写入的内容）进行验证；此时该文档是干净的。 由于词汇表目前还没有文件夹，因此会跳过媒体存在性检查和关联链接检查——待音频和照片文件就位后，请对保存的输出结果运行 [`sil-lift validate`](cli.md)（或使用 `--no-check-media` 选项）。

## 包装

`lex.save("export/birds.lift")` 会生成文件夹结构（`.lift` 和 `.lift-ranges` 并列存放）。 若要生成一个可被 FieldWorks 和 The Combine 直接导入的单个压缩包，请改用 `lex.save_zip("birds.zip")` —— 参见 [生成符合规范的 LIFT 文件](lift-export-interop.md)。
