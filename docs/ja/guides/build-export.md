# 実践例：LIFTエクスポートをゼロから作成する

他のアプリケーションのデータをLIFTとしてエクスポートする場合（[準拠したLIFTの生成](lift-export-interop.md)で説明されているタスク）、`sil-lift`を使用すれば、手動でXMLを生成する代わりに、ドキュメントをオブジェクト単位で構築してシリアライズすることができます。ここでは、次のような機能を持つスクリプトを1つ解説します：

- 実際の辞書が持つ要素（複数の表記体系、発音、例文付きの語義、図解、意味領域の特徴、およびアプリ固有のフィールド）を用いて、項目を構築します。
- 制御語彙を `.lift-ranges` コンパニオンに記述し；
- 検証を行い、保存します。

## 脚本

```python
from pathlib import Path

import sil_lift

lex = sil_lift.Lexicon(producer="my-exporter")

# ソースモデルから構築された 1 つのエントリ。
entry = sil_lift.Entry(id="kanga", guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d")
entry.lexical_unit["seh"] = "nkhuku"
entry.lexical_unit["pt"] = "galinha"

pron = sil_lift.Pronunciation()
pron.forms["en"] = "Speaker: Ana"  # The Combine の話者ラベルの規則
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

scientific = sil_lift.Field(type="scientific-name")  # アプリ固有の追加フィールド
scientific.content["en"] = "Gallus gallus domesticus"
sense.fields.append(scientific)

entry.senses.append(sense)
lex.entries.append(entry)

# 対応する .lift-ranges ファイル内にある、そのエントリが参照する統制語彙。
ranges = sil_lift.RangesFile()
ranges.add_range("grammatical-info").add_element("Noun").label["en"] = "noun"
ranges.add_range("semantic-domain-ddp4").add_element("1.6.1.2").label["en"] = "Bird"
lex.add_ranges_file(ranges, href="birds.lift-ranges")

# ディスクに書き込む前に、ドキュメントを現状のまま検証します。
problems = list(lex.iter_problems())
print(f"validation: {len(problems)} 個の問題")

out = Path("export")
out.mkdir(exist_ok=True)
lex.save(out / "birds.lift")
print("=== birds.lift ===")
print((out / "birds.lift").read_text(encoding="utf-8"), end="")
print("=== birds.lift-ranges ===")
print((out / "birds.lift-ranges").read_text(encoding="utf-8"), end="")
```

## どのような成果が得られるか

`validation: 0 problem(s)` と表示されたら、`.lift` とそのコンパニオンを並べて表示します：

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
<entry id="kanga" guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d" dateCreated="2026-09-02T19:19:17Z" dateModified="2026-09-02T19:19:17Z">
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
      <text>話者：アナ</text>
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
        <text>卵や肉を得るために飼育される家禽</text>
      </form>
    </definition>
    <example>
      <form lang="seh">
        <text>Ndinafuna nkhuku.</text>
      </form>
      <translation>
        <form lang="en">
          <text>鶏が欲しい。</text>
        </form>
      </translation>
    </example>
    <illustration href="pictures/hen.jpg">
      <label>
        <form lang="en">
          <text>雌鶏</text>
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
        <text>名詞</text>
      </form>
    </label>
  </range-element>
</range>
<range id="semantic-domain-ddp4">
  <range-element id="1.6.1.2">
    <label>
      <form lang="en">
        <text>鳥</text>
      </form>
    </label>
  </range-element>
</range>
</lift-ranges>
```

## APIに関する注意事項

### ドキュメントの作成

- マルチテキストフィールド（`lexical_unit`、`definition`、`URLRef`のラベル、`Field`のコンテンツ）は、言語コードをテキストにマッピングするため、ソースモデルの言語ごとの文字列は1対1で引き継がれます。
- `Lexicon.add_ranges_file(ranges, href=...)` はコンパニオンを紐付け、ヘッダー `<range href>` の参照を自動的に記述するため、エントリの `Noun` および `1.6.1.2` の値は、定義した範囲に対して解決されます。
- `URLRef` とは、href にオプションのキャプションやラベルなどのマルチテキストを加えたもので、`<media>`（音声）と `<illustration>`（写真）の両方で使用されます。ここでの発音は、The Combine の慣例に従い、`en` 形式で「<name> 」と読みます。
- ネイティブのLIFTホームライドが含まれないアプリ固有のデータは、`<field>`（または`<trait>`）として指定されます。FieldWorksはこれらをカスタムフィールドとして読み取り、The Combineはそれらを保持します。
- すべてのエントリに、実際の安定した `guid`（例：`uuid.uuid4()` から生成されたもの。エクスポート間で再利用可能）を割り当ててください。後で再インポートした際、エントリが複製されることなく、その場で更新されます。 `sil-lift validate --require-ids` はこのルールを強制します。

### タイムスタンプ

上記の出力にある `dateCreated`/`dateModified` は、スクリプトには含まれていません。 `save()` は、初めて書き込まれたエントリには日付情報が含まれていないため、実行された時点の日付をそれらに付与しました。

- `when=` は、時計を読み取る代わりにその瞬間を指定するため、生成されたエクスポートデータは CI ジョブでの差分比較においてバイト単位で再現可能になります。
- `stamp=False` を指定すると、日付は一切記録されません。

契約書の残りの部分については、[生成されたタイムスタンプ](../fidelity.md#generated-timestamps) をご覧ください。

### 検証

`lex.iter_problems()` は、データがディスクに書き込まれる前にメモリ内のドキュメントを検証します。ここでは、ドキュメントに問題はありません。この辞書にはまだフォルダがないため、media-presence および companion-href のチェックはスキップされます。音声ファイルと写真ファイルの準備が整ったら、保存した出力ファイルに対して [`sil-lift validate`](cli.md) を実行してください（または `--no-check-media` オプションを指定して実行してください）。

## パッケージ

`lex.save("export/birds.lift")` を実行すると、フォルダ形式（`.lift` と `.lift-ranges` を並べて配置）で保存されます。 FieldWorks や The Combine が直接インポートできる単一の ZIP パッケージを出力するには、代わりに `lex.save_zip("birds.zip")` を使用してください。「準拠した LIFT の作成」[(lift-export-interop.md )]を参照してください。
